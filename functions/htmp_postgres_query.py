"""
title: Tra cứu PostgreSQL ERP
author: HTMP Platform
version: 1.3.1
required_open_webui_version: 0.6.0
"""

"""Global Open WebUI tools for natural-language, read-only ERP lookup."""

import json
import os
import re
import urllib.error
import urllib.request
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from erp_ai import ConversationStateStore, ERPRequest, ERPResult, build_request
from erp_ai.validator import validate_document_result

MAX_ROWS = int(os.getenv("HTMP_DB_MAX_ROWS", "200"))
MAX_SCHEMA_TABLES = int(os.getenv("HTMP_DB_MAX_SCHEMA_TABLES", "30"))
TIMEOUT_MS = int(os.getenv("HTMP_DB_STATEMENT_TIMEOUT_MS", "15000"))
PLANNER_TABLES = int(os.getenv("HTMP_DB_PLANNER_TABLES", "180"))
PLANNER_CANDIDATE_TABLES = int(os.getenv("HTMP_DB_CANDIDATE_TABLES", "12"))
PLANNER_ATTEMPTS = int(os.getenv("HTMP_DB_PLANNER_ATTEMPTS", "3"))
ERP_CONVERSATION_STATE = ConversationStateStore()
ERP_REPORTS_DIR = Path(os.getenv("HTMP_ERP_REPORTS_DIR", "/app/backend/data/erp-reports"))
READ_QUERY = re.compile(r"^\s*(?:select|with)\b", re.I | re.S)
FORBIDDEN = re.compile(r"\b(?:insert|update|delete|merge|alter|drop|create|grant|revoke|copy|call|do|vacuum|analyze|truncate|listen|notify|execute|prepare|deallocate|set|show|reset|discard|lock)\b", re.I)


# These are product-wide Vietnamese ERP synonyms, not customer-specific mappings.
# Database metadata remains the source of truth for each installed ERP.
STOP_WORDS = frozenset({"bao", "bao_nhieu", "cho", "cua", "la", "ma", "ngay", "nhung", "tai", "the", "trong", "vao", "voi"})
SEMANTIC_ALIASES = {
    "giao": ("xuat", "ban", "delivery", "ship"),
    "hang": ("vt", "hang", "item", "product"),
    "nhap": ("receipt", "purchase", "in"),
    "xuat": ("delivery", "sale", "out"),
    "ton": ("stock", "inventory", "balance"),
    "kho": ("warehouse", "store"),
    "so_luong": ("sl", "quantity", "qty", "amount"),
    "san_xuat": ("production", "manufacturing", "work_order"),
    "don_hang": ("order", "so", "ct"),
    "vat_tu": ("vt", "material", "item"),
}
COMMON_COLUMN_ALIASES = {
    "so_ct": ("đơn", "đơn hàng", "chứng từ"),
}



def normalize_text(value: str) -> str:
    """Normalize Vietnamese text and identifiers to comparable lowercase tokens."""
    folded = unicodedata.normalize("NFD", value or "")
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    folded = folded.replace("đ", "d").replace("Đ", "d").lower()
    return re.sub(r"[^a-z0-9]+", " ", folded).strip()


def normalize_code_text(value: str) -> str:
    """Normalize text for code extraction while retaining ERP code hyphens."""
    folded = unicodedata.normalize("NFD", value or "")
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    folded = folded.replace("đ", "d").replace("Đ", "d").lower()
    return re.sub(r"[^a-z0-9-]+", " ", folded).strip()


def extract_erp_entities(text: str) -> dict[str, str]:
    """Extract stable ERP identifiers from natural-language text once."""
    source = text or ""
    document = re.search(r"\b\d{3}-\d{4}-\d{6}\b", source)
    material = re.search(r"\b[a-z]+\d[a-z0-9-]*\b", source, re.I)
    numeric_material = re.search(
        r"(?:mã\s*(?:vật\s*tư|vt)|ma\s*(?:vat\s*tu|vt))\s*[:#-]?\s*(\d{6,})\b"
        r"|\b(\d{6,})\b(?=\s+(?:mã\s*)?(?:vật\s*tư|vt)\b)",
        source,
        re.I,
    )
    raw_date = re.search(r"\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b", source)
    transaction = re.search(
        r"(?:mã\s*giao\s*dịch|ma\s*giao\s*dich|mã\s*gd|ma\s*gd)\s*[:#-]?\s*(\d{4,})",
        source,
        re.I,
    )
    return {
        "ma_vt": (
            material.group(0).upper()
            if material
            else next((group for group in (numeric_material.groups() if numeric_material else ()) if group), "")
        ),
        "so_ct": document.group(0) if document else "",
        "ngay_ct": raw_date.group(0) if raw_date else "",
        "ma_gd": transaction.group(1) if transaction else "",
    }


def merge_erp_context(question: str, context: str = "") -> str:
    """Make inherited filters explicit before any deterministic routing."""
    current = (question or "").strip()
    prior = (context or "").strip()
    if not prior:
        return current
    current_entities = extract_erp_entities(current)
    prior_entities = extract_erp_entities(prior)
    inherited = []
    for key in ("ma_vt", "so_ct", "ngay_ct", "ma_gd"):
        if not current_entities[key] and prior_entities[key]:
            inherited.append(prior_entities[key])
    if not inherited:
        return current
    return f"{current}\nĐiều kiện kế thừa từ câu hỏi trước: {' '.join(inherited)}"


def extract_material_name(text: str) -> str:
    """Extract a quoted or display-name material reference, never a guessed code."""
    match = re.search(
        r"(?:vật\s+tư|vat\s+tu)\s+[\"']?(.+?)[\"']?"
        r"(?=\s+(?:có|co|ngày|ngay|vào|vao)\b|,?\s*\d{1,2}/\d{1,2}/\d{4}|$)",
        text or "",
        re.I,
    )
    return match.group(1).strip(" \t\"'") if match else ""


def semantic_tokens(question: str) -> set[str]:
    normalized = normalize_text(question)
    tokens = {token for token in normalized.split() if token not in STOP_WORDS and len(token) > 1}
    compact = normalized.replace(" ", "_")
    for phrase, aliases in SEMANTIC_ALIASES.items():
        if phrase in compact:
            tokens.add(phrase)
            tokens.update(aliases)
    for token in tuple(tokens):
        tokens.update(SEMANTIC_ALIASES.get(token, ()))
    return tokens


def schema_relevance(question: str, table_name: str, columns: str) -> int:
    """Score one table using only schema metadata; no business rows are inspected."""
    terms = semantic_tokens(question)
    haystack = set(normalize_text(table_name + " " + columns).split())
    score = 0
    for term in terms:
        if term in haystack:
            score += 8
        elif any(term in value or value in term for value in haystack if len(value) > 2):
            score += 3
    # ERP schemas often use ma_vt/sl/date0 rather than Vietnamese display names.
    if re.search(r"\b[a-z]{1,5}\d{2,}\b", normalize_text(question)) and {"ma", "vt"}.issubset(haystack):
        score += 6
    if re.search(r"\b\d{1,2}\s+\d{1,2}\s+\d{4}\b", normalize_text(question)) and ({"date0"} & haystack or {"ngay"} & haystack):
        score += 4
    return score


def json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    return value


def format_report_field_value(field: str, value: Any) -> Any:
    """Render numeric report values with the same fixed precision as the ERP UI."""
    if value is None:
        return None
    numeric_fields = {
        "ty_gia", "sl_nhap", "sl_xuat", "gia", "tien_nhap", "tien_xuat",
        "gia_nt", "tien_nhap_nt", "tien_xuat_nt",
    }
    if field not in numeric_fields:
        return value
    try:
        decimal_value = Decimal(str(value))
    except Exception:
        return value
    places = 5 if field == "ty_gia" else 4
    quantum = Decimal("1." + "0" * places)
    return format(decimal_value.quantize(quantum), "f")


def connection_settings() -> dict:
    settings = {
        "host": os.getenv("HTMP_DB_HOST"),
        "port": os.getenv("HTMP_DB_PORT", "5410"),
        "dbname": os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
        "user": os.getenv("HTMP_DB_USER"),
        "password": os.getenv("HTMP_DB_PASSWORD"),
        "connect_timeout": int(os.getenv("HTMP_DB_CONNECT_TIMEOUT_SECONDS", "5")),
    }
    if not settings["host"] or not settings["user"] or not settings["password"]:
        raise RuntimeError("Database connection is not configured")
    return settings


def load_report_config(report_id: str) -> dict[str, Any]:
    """Load a versioned, screen-level ERP report manifest."""
    config = json.loads((ERP_REPORTS_DIR / f"{report_id}.json").read_text())
    if config.get("id") != report_id or not isinstance(config.get("match_phrases"), list):
        raise ValueError("Invalid ERP report manifest")
    return config


def load_report_sql(report: dict[str, Any]) -> str:
    """Load fixed report SQL in either the deployed or repository layout."""
    query_file = report.get("query_file")
    if not isinstance(query_file, str) or not query_file:
        raise ValueError("Report query file is missing")
    candidates = (
        ERP_REPORTS_DIR.parent / "erp-sql" / query_file,
        ERP_REPORTS_DIR.parents[1] / "sql" / "erp-reports" / query_file,
    )
    for path in candidates:
        if path.is_file():
            return path.read_text()
    raise FileNotFoundError(query_file)

def report_column_terms(column: dict[str, Any]) -> tuple[str, ...]:
    """Return normalized UI titles accepted for one report column."""
    values = [column.get("label", ""), *(column.get("aliases") or []), *COMMON_COLUMN_ALIASES.get(column.get("field"), ())]
    return tuple(dict.fromkeys(normalize_text(value) for value in values if value))


def parse_report_request(question: str, report: dict[str, Any]) -> dict[str, Any]:
    """Parse dates, filters and requested UI columns using only a report manifest."""
    normalized = normalize_text(question)
    context_marker = "dieu kien ke thua tu cau hoi truoc"
    selection_text = normalized.split(context_marker, 1)[0].strip()
    raw_dates = re.findall(r"\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b", question)
    dates: list[date] = []
    for raw_date in raw_dates:
        for date_format in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(raw_date, date_format).date()
                if parsed not in dates:
                    dates.append(parsed)
                break
            except ValueError:
                pass

    requested_fields: list[str] = []
    requested_columns: list[dict[str, str]] = []
    candidates: list[tuple[int, str, str, str]] = []
    for column in report.get("columns", []):
        field = column.get("field")
        label = column.get("label")
        if not isinstance(field, str) or not isinstance(label, str):
            continue
        for term in report_column_terms(column):
            candidates.append((len(term), term, field, label))
    occupied: list[tuple[int, int]] = []
    for _, term, field, label in sorted(candidates, reverse=True):
        for match in re.finditer(rf"\b{re.escape(term)}\b", selection_text):
            span = match.span()
            if any(span[0] < end and start < span[1] for start, end in occupied):
                continue
            occupied.append(span)
            if field not in requested_fields:
                requested_fields.append(field)
                requested_columns.append({"field": field, "label": label})
            break

    # A shared quantity qualifier applies to both metrics in phrases such as
    # "số lượng nhập và xuất".  The second metric is intentionally written
    # without repeating "số lượng" in normal Vietnamese.
    if (
        "sl_nhap" in requested_fields
        and re.search(r"\b(?:va|voi)\s+xuat\b", selection_text)
        and "sl_xuat" not in requested_fields
    ):
        requested_fields.append("sl_xuat")
        requested_columns.append({"field": "sl_xuat", "label": "Số lượng xuất"})

    filters: dict[str, str] = {}
    # Codes can have digits in the middle (VGU1A423) and an optional suffix.
    code_text = normalize_code_text(question)
    for item in report.get("inputs", {}).get("filters", []):
        parameter = item.get("parameter")
        if not isinstance(parameter, str) or item.get("value_type") != "code":
            continue
        # Material codes contain digits, while ERP warehouse codes can be
        # alphabetic/hyphenated (for example KHO-LAP-RAP).
        code_pattern = (
            r"([a-z][a-z0-9]*(?:-[a-z0-9]+)*)"
            if parameter == "ma_kho"
            else r"((?=[a-z0-9-]*\d)[a-z0-9]+(?:-[a-z0-9]+)*)"
        )
        aliases = sorted(
            (normalize_text(alias) for alias in item.get("aliases", []) if alias),
            key=len,
            reverse=True,
        )
        for alias in aliases:
            match = re.search(rf"(?:^|\s){re.escape(alias)}\s+(?:(?:la|is)\s+)?{code_pattern}\b", code_text, re.I)
            if match:
                filters[parameter] = match.group(1).upper()
                break

    has_report_name = any(
        normalize_text(phrase) in normalized for phrase in report.get("match_phrases", [])
    )
    return {
        "dates": dates,
        "filters": filters,
        "requested_fields": requested_fields,
        "requested_columns": requested_columns,
        "matches_report": has_report_name or bool(dates and requested_fields),
    }


def merge_report_filters(parsed_filters: dict[str, str], resolved_filters: dict[str, str]) -> dict[str, str]:
    """Keep explicit current-question filters when conversation state is blank."""
    return {
        **parsed_filters,
        **{key: value for key, value in resolved_filters.items() if value},
    }


class Tools:
    def get_erp_schema(self, search: str = "") -> str:
        """Tìm bảng và cột ERP trước khi trả lời câu hỏi tự nhiên.

        Luôn gọi tool này trước khi tạo SQL, nhất là khi chưa chắc tên bảng hoặc
        cột. ``search`` là từ khóa tiếng Việt/tên nghiệp vụ để lọc; để trống sẽ
        lấy danh sách bảng đầu tiên. Không trả dữ liệu nghiệp vụ.
        """
        pattern = "%" + (search or "").strip() + "%"
        sql = """
            SELECT table_schema, table_name,
                   json_agg(json_build_object('name', column_name, 'type', data_type)
                            ORDER BY ordinal_position) AS columns
            FROM information_schema.columns
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
              AND (%s = '%%' OR table_name ILIKE %s OR column_name ILIKE %s)
            GROUP BY table_schema, table_name
            ORDER BY table_schema, table_name
            LIMIT %s
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(sql, (pattern, pattern, pattern, MAX_SCHEMA_TABLES))
                    rows = cursor.fetchall()
        except Exception:
            return "Không thể đọc cấu trúc DB. Kiểm tra cấu hình và quyền SELECT của tài khoản DB."
        return json.dumps(
            [{"schema": schema, "table": table, "columns": columns} for schema, table, columns in rows],
            ensure_ascii=False,
            default=str,
        )


    def _lookup_material_locations(self, value: str, lookup_column: str) -> str:
        """Look up real ERP material/warehouse fields without guessing table names."""
        needle = (value or "").strip()
        if not needle:
            return "Cần cung cấp mã vật tư hoặc mã kho để tra cứu."
        try:
            import psycopg
            from psycopg import sql
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(
                        """
                        SELECT table_schema, table_name
                        FROM information_schema.columns
                        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                          AND column_name IN ('ma_vt', 'ma_kho')
                        GROUP BY table_schema, table_name
                        HAVING count(DISTINCT column_name) = 2
                        ORDER BY
                          CASE table_name
                            WHEN 'cdvt13' THEN 0
                            WHEN 'cdvt' THEN 1
                            WHEN 'cdbsp' THEN 2
                            ELSE 3
                          END,
                          table_schema, table_name
                        LIMIT 12
                        """
                    )
                    tables = cursor.fetchall()
                    matches = []
                    seen = set()
                    for schema, table in tables:
                        query = sql.SQL(
                            "SELECT DISTINCT {warehouse}, {material} FROM {table} "
                            "WHERE upper(trim({lookup})) = upper(trim(%s)) LIMIT %s"
                        ).format(
                            warehouse=sql.Identifier("ma_kho"),
                            material=sql.Identifier("ma_vt"),
                            table=sql.Identifier(schema, table),
                            lookup=sql.Identifier(lookup_column),
                        )
                        cursor.execute(query, (needle, MAX_ROWS + 1))
                        rows = cursor.fetchmany(MAX_ROWS + 1)
                        for warehouse, material in rows[:MAX_ROWS]:
                            key = (warehouse, material)
                            if key in seen:
                                continue
                            seen.add(key)
                            matches.append({"source_table": f"{schema}.{table}", "ma_kho": warehouse, "ma_vt": material})
                            if len(matches) >= MAX_ROWS:
                                break
                        if len(matches) >= MAX_ROWS:
                            break
        except Exception:
            return "Không thể tra cứu cơ sở dữ liệu ERP. Kiểm tra cấu hình và quyền SELECT của tài khoản DB."
        return json.dumps(
            {"lookup": {lookup_column: needle}, "row_count": len(matches), "truncated": len(matches) >= MAX_ROWS, "rows": matches},
            ensure_ascii=False,
            default=str,
        )

    def find_material_by_code(self, ma_vt: str) -> str:
        """Tra kho chứa một mã vật tư ERP bằng cột thật ma_vt và ma_kho.

        Dùng ĐẦU TIÊN cho câu hỏi như "mã này ở kho nào?". Không tự đoán bảng
        hay viết SQL; hàm tự tìm tất cả bảng có đồng thời ma_vt và ma_kho.
        """
        return self._lookup_material_locations(ma_vt, "ma_vt")

    def find_materials_in_warehouse(self, ma_kho: str) -> str:
        """Liệt kê mã vật tư (ma_vt) của một kho ERP bằng cột thật ma_kho.

        Dùng ĐẦU TIÊN cho câu hỏi như "kho X có những mã vật tư nào?". Không tự
        đoán bảng hay viết SQL; hàm tự tìm tất cả bảng có ma_vt và ma_kho.
        """
        return self._lookup_material_locations(ma_kho, "ma_kho")

    def find_material_lots_by_warehouse_date(self, ma_kho: str, ngay: str) -> str:
        """Liệt kê ma_vt và ma_lo của kho tại một ngày theo cột ERP thật.

        Dùng ĐẦU TIÊN khi người dùng hỏi ``ma_vt``, ``ma_lo`` cho một ``ma_kho``
        vào ngày cụ thể. ``ngay`` nhận dd/mm/yyyy hoặc yyyy-mm-dd. Hàm tự tìm
        bảng có ma_kho, ma_vt, ma_lo, date0; không được đoán bảng SQL.
        """
        warehouse = (ma_kho or "").strip()
        raw_date = (ngay or "").strip()
        if not warehouse or not raw_date:
            return "Cần cung cấp cả mã kho và ngày để tra cứu."
        parsed_date = None
        for date_format in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                parsed_date = datetime.strptime(raw_date, date_format).date()
                break
            except ValueError:
                pass
        if parsed_date is None:
            return "Ngày không hợp lệ. Dùng định dạng dd/mm/yyyy hoặc yyyy-mm-dd."
        try:
            import psycopg
            from psycopg import sql
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(
                        """
                        SELECT table_schema, table_name
                        FROM information_schema.columns
                        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                          AND column_name IN ('ma_kho', 'ma_vt', 'ma_lo', 'date0')
                        GROUP BY table_schema, table_name
                        HAVING count(DISTINCT column_name) = 4
                        ORDER BY CASE table_name WHEN 'cdvt13' THEN 0 ELSE 1 END, table_schema, table_name
                        LIMIT 20
                        """
                    )
                    tables = cursor.fetchall()
                    rows_out = []
                    seen = set()
                    for schema, table in tables:
                        query = sql.SQL(
                            "SELECT DISTINCT {material}, {lot} FROM {table} "
                            "WHERE upper(trim({warehouse})) = upper(trim(%s)) "
                            "AND {date0} = %s LIMIT %s"
                        ).format(
                            material=sql.Identifier("ma_vt"),
                            lot=sql.Identifier("ma_lo"),
                            table=sql.Identifier(schema, table),
                            warehouse=sql.Identifier("ma_kho"),
                            date0=sql.Identifier("date0"),
                        )
                        cursor.execute(query, (warehouse, parsed_date, MAX_ROWS + 1))
                        for material, lot in cursor.fetchmany(MAX_ROWS + 1):
                            key = (material, lot)
                            if key in seen:
                                continue
                            seen.add(key)
                            rows_out.append({"source_table": f"{schema}.{table}", "ma_vt": material, "ma_lo": lot})
                            if len(rows_out) >= MAX_ROWS:
                                break
                        if len(rows_out) >= MAX_ROWS:
                            break
        except Exception:
            return "Không thể tra cứu cơ sở dữ liệu ERP. Kiểm tra cấu hình và quyền SELECT của tài khoản DB."
        return json.dumps(
            {"lookup": {"ma_kho": warehouse, "date0": parsed_date.isoformat()}, "row_count": len(rows_out), "truncated": len(rows_out) >= MAX_ROWS, "rows": rows_out},
            ensure_ascii=False,
            default=str,
        )

    def _schema_catalog(self, question: str) -> str:
        """Return only the schema candidates relevant to this question."""
        query = """
            SELECT table_schema, table_name,
                   string_agg(column_name || ':' || data_type, ', ' ORDER BY ordinal_position) AS columns
            FROM information_schema.columns
            WHERE table_schema = 'public'
            GROUP BY table_schema, table_name
            ORDER BY table_name
            LIMIT %s
        """
        import psycopg
        with psycopg.connect(**connection_settings(), autocommit=False) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                cursor.execute(query, (PLANNER_TABLES,))
                tables = cursor.fetchall()
        ranked = sorted(
            tables,
            key=lambda row: (
                -schema_relevance(question, row[1], row[2] or ""),
                row[0],
                row[1],
            ),
        )
        candidates = ranked[:PLANNER_CANDIDATE_TABLES]
        return "\n".join(f"{schema}.{table}({columns})" for schema, table, columns in candidates)

    def _execute_read_query(self, query: str) -> tuple[dict | None, str | None]:
        query = (query or "").strip().removesuffix(";").rstrip()
        if not query or ";" in query or not READ_QUERY.match(query):
            return None, "SQL phải là đúng một câu SELECT hoặc WITH."
        if FORBIDDEN.search(query) or re.search(r"\bselect\b[\s\S]*\binto\b", query, re.I):
            return None, "SQL chứa thao tác không được phép."
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("SELECT * FROM (" + query + ") AS htmp_result LIMIT %s", (MAX_ROWS + 1,))
                    columns = [item.name for item in cursor.description]
                    rows = cursor.fetchmany(MAX_ROWS + 1)
        except Exception as exc:
            # Give the internal planner a concise PostgreSQL error so it can
            # correct its table/column choice; never expose connection details.
            return None, f"PostgreSQL rejected the query: {str(exc)[:500]}"
        result = [dict(zip(columns, (json_value(value) for value in row))) for row in rows[:MAX_ROWS]]
        return {"row_count": len(result), "truncated": len(rows) > MAX_ROWS, "rows": result}, None

    def _supplier_quote_price_after_vat(self, question: str) -> str | None:
        """Resolve a dated supplier-quote price without sending a large catalog to a model.

        ``ctbgncc`` is the detail grid for the 3SERP "Phiếu báo giá nhà cung
        cấp" screen. The UI label "Giá sau VAT" maps to ``gia`` in the base
        currency and to ``gia_nt`` in the document currency.
        """
        normalized = normalize_text(question)
        if "gia sau vat" not in normalized:
            return None
        code_match = re.search(r"\b([a-z]{1,5}\d{2,})\b", question, re.I)
        date_match = re.search(r"\b(\d{1,2}/\d{1,2}/\d{4})\b", question)
        if not code_match or not date_match:
            return None
        try:
            effective_date = datetime.strptime(date_match.group(1), "%d/%m/%Y").date()
        except ValueError:
            return None
        material_code = code_match.group(1).upper()
        query = """
            SELECT ma_vt, dvt,
                   gia AS gia_sau_vat_vnd,
                   gia_nt AS gia_sau_vat_nguyen_te,
                   ma_thue, thue_suat, ngay_bd, ngay_kt, ngay_ct, so_ct,
                   appr_yn AS da_duyet, close_yn AS da_dong
            FROM public.ctbgncc
            WHERE upper(trim(ma_vt)) = %s
              AND ngay_bd <= %s
              AND ngay_kt >= %s
            ORDER BY ngay_ct DESC, so_ct DESC
            LIMIT %s
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (material_code, effective_date, effective_date, MAX_ROWS + 1))
                    columns = [item.name for item in cursor.description]
                    rows = cursor.fetchmany(MAX_ROWS + 1)
        except Exception:
            return "Không thể tra cứu báo giá nhà cung cấp trong ERP. Kiểm tra cấu hình và quyền SELECT của tài khoản DB."
        result = [dict(zip(columns, (json_value(value) for value in row))) for row in rows[:MAX_ROWS]]
        return json.dumps(
            {
                "source": "public.ctbgncc (Phiếu báo giá nhà cung cấp)",
                "lookup": {"ma_vt": material_code, "ngay_hieu_luc": effective_date.isoformat()},
                "row_count": len(result),
                "truncated": len(rows) > MAX_ROWS,
                "rows": result,
            },
            ensure_ascii=False,
            default=str,
        )

    def _purchase_receipt_summary(self, question: str) -> str | None:
        """Summarize purchased receipts for a material code from the 3SERP UI flow."""
        normalized = normalize_text(question)
        if "bao cao" not in normalized or ("nhap mua" not in normalized and "hang nhap" not in normalized):
            return None
        code_match = re.search(r"\b(\d{6,}|[a-z]{1,5}\d{2,})\b", question, re.I)
        if not code_match:
            return "Cần mã vật tư để lập báo cáo tổng hợp hàng nhập mua."
        material_code = code_match.group(1).upper()
        query = """
            SELECT t.ma_vt, max(v.ten_vt) AS ten_vt, max(t.dvt) AS dvt,
                   min(t.ngay_ct) AS tu_ngay, max(t.ngay_ct) AS den_ngay,
                   count(DISTINCT t.so_ct) AS so_chung_tu,
                   sum(t.sl_nhap) AS tong_so_luong_nhap,
                   sum(t.tien_nhap) AS tong_gia_tri_nhap
            FROM public.ct70 AS t
            JOIN public.dmct AS c ON c.ma_ct = t.ma_ct
            LEFT JOIN public.dmvt AS v ON upper(trim(v.ma_vt)) = upper(trim(t.ma_vt))
            WHERE upper(trim(t.ma_vt)) = %s
              AND c.ma_phan_he = 'PO'
              AND c.ct_nxt = 1
              AND coalesce(t.sl_nhap, 0) > 0
            GROUP BY t.ma_vt
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (material_code,))
                    columns = [item.name for item in cursor.description]
                    rows = cursor.fetchall()
        except Exception:
            return "Không thể tổng hợp hàng nhập mua trong ERP. Kiểm tra cấu hình và quyền SELECT của tài khoản DB."
        result = [dict(zip(columns, (json_value(value) for value in row))) for row in rows]
        return json.dumps(
            {
                "source": "public.ct70 + public.dmct (Phiếu nhập hàng mua)",
                "lookup": {"ma_vt": material_code, "khoang_thoi_gian": "toàn bộ dữ liệu"},
                "row_count": len(result),
                "rows": result,
            },
            ensure_ascii=False,
            default=str,
        )

    def _inventory_movement_journal(self, question: str) -> str | None:
        """Execute the manifest-defined Nhật ký nhập xuất tồn report."""
        try:
            report = load_report_config("nhat-ky-nhap-xuat-ton")
            parsed = parse_report_request(question, report)
        except Exception:
            return "Cấu hình báo cáo Nhật ký nhập xuất tồn chưa sẵn sàng."
        if not parsed["matches_report"]:
            return None
        dates = parsed["dates"]
        if not dates:
            return "Cần nêu ngày hoặc khoảng ngày (dd/mm/yyyy) để tra Nhật ký nhập xuất tồn."

        filters = parsed["filters"]
        material_code = filters.get("ma_vt", "")
        warehouse_code = filters.get("ma_kho", "")
        creator_code = filters.get("nguoi_tao", "")
        editor_code = filters.get("nguoi_sua", "")
        try:
            query = load_report_sql(report)
            configured_limit = int(report.get("defaults", {}).get("limit", MAX_ROWS))
            row_limit = min(configured_limit, MAX_ROWS)
        except Exception:
            return "SQL của báo cáo Nhật ký nhập xuất tồn chưa sẵn sàng."
        parameters = (
            min(dates), max(dates), report["defaults"]["ma_dvcs"],
            material_code, material_code, warehouse_code, warehouse_code,
            creator_code, creator_code, editor_code, editor_code, row_limit + 1,
        )
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, parameters)
                    columns = [item.name for item in cursor.description]
                    rows = cursor.fetchmany(row_limit + 1)
        except Exception:
            return "Không thể tra Nhật ký nhập xuất tồn trong ERP."

        full_rows = [
            dict(zip(columns, (json_value(value) for value in row)))
            for row in rows[:row_limit]
        ]
        requested_fields = [
            field for field in parsed["requested_fields"] if field in columns
        ]
        if requested_fields:
            result = []
            seen = set()
            for row in full_rows:
                projected = {field: row.get(field) for field in requested_fields}
                key = tuple(json.dumps(projected.get(field), default=str) for field in requested_fields)
                if key not in seen:
                    seen.add(key)
                    result.append(projected)
        else:
            result = full_rows

        summary = {
            "so_giao_dich_chi_tiet": len(full_rows),
            "tong_sl_nhap": str(sum(
                (Decimal(str(row.get("sl_nhap") or "0")) for row in full_rows),
                Decimal("0"),
            )),
            "tong_sl_xuat": str(sum(
                (Decimal(str(row.get("sl_xuat") or "0")) for row in full_rows),
                Decimal("0"),
            )),
        }
        return json.dumps(
            {
                "report": {"id": report["id"], "title": report["title"]},
                "source": report["sources"],
                "query_scope": "manifest_and_fixed_sql_only",
                "lookup": {
                    "tu_ngay": min(dates).isoformat(),
                    "den_ngay": max(dates).isoformat(),
                    **filters,
                },
                "requested_columns": parsed["requested_columns"],
                "summary": summary,
                "matched_row_count": len(full_rows),
                "row_count": len(result),
                "truncated": len(rows) > row_limit,
                "rows": result,
            },
            ensure_ascii=False,
            default=str,
        )

    def _material_work_code(self, question: str) -> str | None:
        """Look up the master Mã vụ việc associated with a material."""
        normalized = normalize_text(question)
        if "ma vu viec" not in normalized:
            return None
        code_match = re.search(r"\b(\d{6,}|[a-z]{1,5}\d{2,})\b", question, re.I)
        if not code_match:
            return "Cần mã vật tư để tra Mã vụ việc."
        material_code = code_match.group(1).upper()
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT ma_vt, ten_vt, ma_vv FROM public.dmvt WHERE upper(trim(ma_vt)) = %s", (material_code,))
                    columns = [item.name for item in cursor.description]
                    rows = cursor.fetchall()
        except Exception:
            return "Không thể tra Mã vụ việc trong ERP."
        result = [dict(zip(columns, (json_value(value) for value in row))) for row in rows]
        return json.dumps(
            {"source": "public.dmvt (Danh mục vật tư)", "lookup": {"ma_vt": material_code}, "row_count": len(result), "rows": result},
            ensure_ascii=False, default=str,
        )

    def ask_erp(self, question: str, context: str = "", conversation_id: str = "", __chat_id__: str = "") -> str:
        """Resolve a natural-language ERP request through the semantic router first."""
        question = (question or "").strip()
        if not question:
            return "Cần cung cấp câu hỏi ERP để tra cứu."
        active_conversation = conversation_id or __chat_id__ or ""
        filters = ERP_CONVERSATION_STATE.resolve(active_conversation, question, context)
        if not filters.get("ma_vt"):
            material_resolution = self._resolve_material_name(question)
            if isinstance(material_resolution, ERPResult):
                return json.dumps(material_resolution.payload(), ensure_ascii=False, default=str)
            if material_resolution:
                material_code, _material_name = material_resolution
                filters["ma_vt"] = material_code
                ERP_CONVERSATION_STATE.remember(active_conversation, {"ma_vt": material_code})
        semantic_request = build_request(question, filters)
        journal_field_result = self._execute_manifest_journal_field(question, filters)
        if journal_field_result is not None:
            return journal_field_result
        if semantic_request.intent == "transaction_detail":
            return self._execute_transaction_request(semantic_request)
        if semantic_request.intent == "material_document_detail":
            return self._execute_material_document_request(semantic_request)
        if semantic_request.intent == "material_master":
            return self._execute_material_master_request(semantic_request)
        if semantic_request.intent == "inventory_ledger":
            return self._execute_material_date_request(semantic_request)
        question = merge_erp_context(question, " ".join(filters.values()))
        latest_movement_result = self._latest_material_movement(question)
        if latest_movement_result is not None:
            return latest_movement_result
        # A material-code lookup is a master-data read. Resolve it directly
        # instead of asking the planner to infer transaction fields.
        material_details_result = self._material_details(question)
        if material_details_result is not None:
            return material_details_result
        inventory_journal_result = self._inventory_movement_journal(question)
        if inventory_journal_result is not None:
            return inventory_journal_result
        material_work_code_result = self._material_work_code(question)
        if material_work_code_result is not None:
            return material_work_code_result
        supplier_quote_result = self._supplier_quote_price_after_vat(question)
        if supplier_quote_result is not None:
            return supplier_quote_result
        purchase_receipt_result = self._purchase_receipt_summary(question)
        if purchase_receipt_result is not None:
            return purchase_receipt_result
        try:
            catalog = self._schema_catalog(question)
        except Exception:
            return "Không thể đọc catalog ERP. Kiểm tra cấu hình và quyền SELECT của tài khoản DB."

        base_url = (os.getenv("OPENAI_API_BASE_URLS") or "http://vllm:8000/v1").split(",")[0].rstrip("/")
        api_key = os.getenv("OPENAI_API_KEY", "")
        history = ""
        last_error = ""
        for _ in range(PLANNER_ATTEMPTS):
            planner_prompt = f"""Bạn là bộ lập kế hoạch SQL PostgreSQL cho ERP nội bộ. Trả về DUY NHẤT JSON hợp lệ dạng {{"sql": "SELECT ..."}}.

Yêu cầu người dùng: {question}

Catalog ứng viên được chọn tự động từ schema thật dựa trên câu hỏi. Chỉ dùng chính xác tên bảng/cột trong catalog, không bịa tên:
{catalog}

Quy tắc: chỉ một SELECT/WITH; dùng schema public khi cần; tối đa 200 dòng; với ngày dd/mm/yyyy đổi thành DATE 'yyyy-mm-dd'; nếu câu hỏi mơ hồ (ví dụ giao hàng có thể là xuất bán hoặc chuyển kho) hoặc không xác định được bảng/cột, trả {{"sql": null, "reason": "câu hỏi làm rõ ngắn bằng tiếng Việt"}}. Trả SQL chỉ khi đủ chắc chắn. {history}"""
            payload = json.dumps({
                "model": os.getenv("HTMP_DB_PLANNER_MODEL", "qwen2.5-14b"),
                "temperature": 0,
                "max_tokens": 700,
                "messages": [{"role": "system", "content": planner_prompt}],
            }).encode()
            request = urllib.request.Request(
                base_url + "/chat/completions", data=payload,
                headers={"Content-Type": "application/json", **({"Authorization": "Bearer " + api_key} if api_key else {})},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=75) as response:
                    content = json.loads(response.read().decode())["choices"][0]["message"].get("content", "")
                match = re.search(r"\{[\s\S]*\}", content)
                plan = json.loads(match.group(0)) if match else {}
                planned_sql = plan.get("sql")
            except Exception as exc:
                return f"Không thể lập truy vấn ERP nội bộ: {str(exc)[:300]}"
            if not isinstance(planned_sql, str) or not planned_sql.strip():
                reason = str(plan.get("reason") or "Không thể xác định truy vấn an toàn từ catalog ERP.").strip()
                return reason[:500]
            result, error = self._execute_read_query(planned_sql)
            if result is not None:
                if result["row_count"] > 0 or _ == PLANNER_ATTEMPTS - 1:
                    result["planned_sql"] = planned_sql
                    return json.dumps(result, ensure_ascii=False, default=str)
                history = (
                    f"Lần trước SQL trả 0 dòng: {planned_sql}. Không kết luận là không có dữ liệu; "
                    "hãy thử bảng/cột tương đương khác trong catalog, đặc biệt bảng snapshot có hậu tố _YYYYMMDD."
                )
                continue
            last_error = error or "Lỗi SQL không xác định"
            history = f"Lần trước SQL bị lỗi: {last_error}. Hãy sửa bằng catalog thật và chỉ trả JSON mới."
        return f"Không thể chạy truy vấn ERP sau {PLANNER_ATTEMPTS} lần thử: {last_error}"

    def query_erp_database(self, sql: str) -> str:
        """Chạy đúng một SELECT/WITH chỉ đọc trên ERP, tối đa 200 dòng.

        Chỉ gọi sau ``get_erp_schema`` để dùng đúng tên bảng/cột. Tool này được
        model dùng nội bộ để trả lời câu hỏi tiếng Việt; người dùng không cần SQL.
        """
        result, error = self._execute_read_query(sql)
        if result is None:
            return error or "Không thể truy vấn cơ sở dữ liệu ERP."
        return json.dumps(result, ensure_ascii=False, default=str)

    def _execute_transaction_request(self, request: ERPRequest) -> str:
        """Read ERP rows for one explicit transaction code, optionally on one date."""
        transaction = request.filters["ma_gd"]
        where = ["trim(a.ma_gd) = %s"]
        parameters: list[Any] = [transaction]
        raw_date = request.filters.get("ngay_ct", "")
        if raw_date:
            try:
                transaction_date = datetime.strptime(
                    raw_date, "%Y-%m-%d" if "-" in raw_date else "%d/%m/%Y"
                ).date()
            except ValueError:
                return json.dumps(ERPResult(
                    status="invalid_filter", intent=request.intent, filters=request.filters,
                    error_code="INVALID_TRANSACTION_DATE", message="Ngày chứng từ không đúng định dạng."
                ).payload(), ensure_ascii=False, default=str)
            where.append("a.ngay_ct = %s")
            parameters.append(transaction_date)
        parameters.append(MAX_ROWS + 1)
        query = f"""
            SELECT a.ngay_ct, a.so_ct, a.ma_ct, a.ma_gd, a.ma_vt, v.ten_vt,
                   coalesce(v.dvt, a.dvt) AS dvt, a.ma_kho, a.ma_nt,
                   CASE WHEN a.ty_gia = 0 THEN 1 ELSE a.ty_gia END AS ty_gia,
                   coalesce(a.sl_nhap, 0) AS sl_nhap, coalesce(a.sl_xuat, 0) AS sl_xuat,
                   a.gia, a.tien_nhap, a.tien_xuat, a.dien_giai
            FROM public.ct70 AS a
            LEFT JOIN public.dmvt AS v ON upper(trim(v.ma_vt)) = upper(trim(a.ma_vt))
            WHERE {' AND '.join(where)}
            ORDER BY a.ngay_ct, a.stt_rec, a.ma_vt
            LIMIT %s
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, parameters)
                    columns = [item.name for item in cursor.description]
                    raw_rows = cursor.fetchmany(MAX_ROWS + 1)
        except Exception:
            return json.dumps(ERPResult(
                status="db_error", intent=request.intent, filters=request.filters,
                error_code="ERP_QUERY_FAILED", message="Không thể truy vấn giao dịch ERP tại thời điểm này."
            ).payload(), ensure_ascii=False, default=str)
        rows = [dict(zip(columns, (json_value(value) for value in row))) for row in raw_rows[:MAX_ROWS]]
        return json.dumps(ERPResult(
            status="success" if rows else "success_empty", intent=request.intent, filters=request.filters,
            rows=rows, total_rows=len(rows), returned_rows=len(rows), has_more=len(raw_rows) > MAX_ROWS,
            message=None if rows else "Không có giao dịch khớp đúng điều kiện truy vấn.",
        ).payload(), ensure_ascii=False, default=str)

    def _material_details(self, question: str) -> str | None:
        """Return the matching material-master row without relying on chat history."""
        normalized = normalize_text(question)
        if not ("ma vat tu" in normalized or "ma vt" in normalized):
            return None
        if any(term in normalized for term in ("so luong", "sl xuat", "sl nhap", "ty gia", "ti gia")):
            return None
        code_match = re.search(r"\b((?=[a-z0-9-]*\d)[a-z0-9]+(?:-[a-z0-9]+)*)\b", question, re.I)
        if not code_match:
            return "Cần mã vật tư để tra cứu."
        material_code = code_match.group(1).upper()
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT row_to_json(v)
                        FROM public.dmvt AS v
                        WHERE upper(trim(v.ma_vt)) = %s
                    """, (material_code,))
                    row = cursor.fetchone()
        except Exception:
            return "Không thể tra thông tin vật tư trong ERP."
        if not row:
            return f"Không tìm thấy mã vật tư {material_code} trong danh mục ERP."
        return json.dumps(
            {
                "source": "public.dmvt (Danh mục vật tư)",
                "lookup": {"ma_vt": material_code},
                "row_count": 1,
                "rows": [row[0]],
            },
            ensure_ascii=False,
            default=str,
        )

    def _latest_material_movement(self, question: str) -> str | None:
        """Return matching material transactions without arbitrarily picking one row."""
        normalized = normalize_text(question)
        if not any(term in normalized for term in ("ty gia", "ti gia", "so luong xuat", "sl xuat")):
            return None
        code_match = re.search(r"\b((?=[a-z0-9-]*\d)[a-z0-9]+(?:-[a-z0-9]+)*)\b", question, re.I)
        if not code_match:
            return "Cần mã vật tư để tra tỷ giá hoặc số lượng xuất."
        material_code = code_match.group(1).upper()
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT a.ma_vt, v.ten_vt, a.ngay_ct, a.so_ct, a.ma_gd, a.ma_kho,
                               CASE WHEN a.ty_gia = 0 THEN 1 ELSE a.ty_gia END AS ty_gia,
                               a.sl_xuat,
                               sum(coalesce(a.sl_xuat, 0)) OVER () AS tong_sl_xuat
                        FROM public.ct70 AS a
                        LEFT JOIN public.dmvt AS v ON upper(trim(v.ma_vt)) = upper(trim(a.ma_vt))
                        WHERE upper(trim(a.ma_vt)) = %s
                          AND a.ngay_ct = (
                              SELECT max(b.ngay_ct)
                              FROM public.ct70 AS b
                              WHERE upper(trim(b.ma_vt)) = %s
                          )
                        ORDER BY a.ngay_ct DESC, a.stt_rec DESC, a.sl_xuat DESC
                        LIMIT %s
                    """, (material_code, material_code, MAX_ROWS + 1))
                    rows = cursor.fetchmany(MAX_ROWS + 1)
                    columns = [item.name for item in cursor.description]
        except Exception:
            return "Không thể tra tỷ giá và số lượng xuất trong ERP."
        result = [
            dict(zip(columns, (json_value(value) for value in row)))
            for row in rows[:MAX_ROWS]
        ]
        return json.dumps(
            {
                "source": "public.ct70 (Giao dịch vật tư)",
                "lookup": {"ma_vt": material_code},
                "row_count": len(result),
                "truncated": len(rows) > MAX_ROWS,
                "rows": result,
            },
            ensure_ascii=False,
            default=str,
        )
    def _material_document_quantity(self, question: str) -> str | None:
        """Read the exact ERP transaction identified by material and document."""
        normalized = normalize_text(question)
        material_match = re.search(r"\b([a-z]+\d[a-z0-9-]*)\b", question, re.I)
        document_match = re.search(r"\b\d{3}-\d{4}-\d{6}\b", question)
        if not material_match or not document_match:
            return None
        material_code, document_no = material_match.group(1).upper(), document_match.group(0)
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT a.ma_vt, max(v.ten_vt) AS ten_vt, a.so_ct,
                               max(a.ngay_ct) AS ngay_ct, sum(coalesce(a.sl_nhap, 0)) AS sl_nhap, sum(coalesce(a.sl_xuat, 0)) AS sl_xuat
                        FROM public.ct70 AS a
                        LEFT JOIN public.dmvt AS v ON upper(trim(v.ma_vt)) = upper(trim(a.ma_vt))
                        WHERE upper(trim(a.ma_vt)) = %s AND trim(a.so_ct) = %s
                        GROUP BY a.ma_vt, a.so_ct
                    """, (material_code, document_no))
                    row = cursor.fetchone()
        except Exception:
            return "Không thể tra số lượng xuất trong ERP."
        if not row:
            return f"Không tìm thấy giao dịch mã vật tư {material_code}, số chứng từ {document_no}."
        ma_vt, ten_vt, so_ct, ngay_ct, sl_nhap, sl_xuat = (json_value(value) for value in row)
        return f"Mã vật tư {ma_vt} ({ten_vt}), số chứng từ {so_ct}, ngày {ngay_ct}: số lượng nhập là {sl_nhap}; số lượng xuất là {sl_xuat}."
    def _execute_material_document_request(self, request: ERPRequest) -> str:
        """Tier-1 material/document detail query with a validated result contract."""
        material = request.filters["ma_vt"]
        document = request.filters["so_ct"]
        query = """
            SELECT a.ngay_ct, a.so_ct, a.ma_vt, v.ten_vt, a.ma_gd, a.ma_kho,
                   a.ma_nt, CASE WHEN a.ty_gia = 0 THEN 1 ELSE a.ty_gia END AS ty_gia,
                   coalesce(a.sl_nhap, 0) AS sl_nhap, coalesce(a.sl_xuat, 0) AS sl_xuat,
                   a.dvt, a.dien_giai
            FROM public.ct70 AS a
            LEFT JOIN public.dmvt AS v ON upper(trim(v.ma_vt)) = upper(trim(a.ma_vt))
            WHERE upper(trim(a.ma_vt)) = %s AND trim(a.so_ct) = %s
            ORDER BY a.ngay_ct, a.stt_rec, a.ma_vt
            LIMIT %s
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (material, document, MAX_ROWS + 1))
                    columns = [item.name for item in cursor.description]
                    raw_rows = cursor.fetchmany(MAX_ROWS + 1)
        except Exception:
            return json.dumps(ERPResult(
                status="db_error", intent=request.intent, filters=request.filters,
                error_code="ERP_QUERY_FAILED", message="Không thể truy vấn ERP tại thời điểm này."
            ).payload(), ensure_ascii=False, default=str)
        rows = [dict(zip(columns, (json_value(value) for value in row))) for row in raw_rows[:MAX_ROWS]]
        if not rows:
            return json.dumps(ERPResult(
                status="success_empty", intent=request.intent, filters=request.filters,
                message="Không có dữ liệu khớp đúng các điều kiện truy vấn."
            ).payload(), ensure_ascii=False, default=str)
        summary = {
            "sl_nhap": str(sum((Decimal(str(row["sl_nhap"])) for row in rows), Decimal())),
            "sl_xuat": str(sum((Decimal(str(row["sl_xuat"])) for row in rows), Decimal())),
        }
        result = ERPResult(
            status="success", intent=request.intent, filters=request.filters,
            summary=summary, rows=rows, total_rows=len(rows), returned_rows=len(rows),
            has_more=len(raw_rows) > MAX_ROWS,
        )
        result = validate_document_result(result)
        return json.dumps(result.payload(), ensure_ascii=False, default=str)


    def _resolve_material_name(self, question: str) -> tuple[str, str] | ERPResult | None:
        """Resolve an explicit material display name to one ERP code, or fail safely."""
        material_name = extract_material_name(question)
        if not material_name or extract_erp_entities(question)["ma_vt"]:
            return None
        query = """
            SELECT trim(ma_vt) AS ma_vt, trim(ten_vt) AS ten_vt
            FROM public.dmvt
            WHERE upper(trim(ten_vt)) = upper(trim(%s))
            ORDER BY trim(ma_vt)
            LIMIT 2
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (material_name,))
                    rows = cursor.fetchall()
        except Exception:
            return ERPResult(
                status="db_error", intent="material_name_resolution", filters={"ten_vt": material_name},
                error_code="ERP_MATERIAL_LOOKUP_FAILED",
                message="Không thể đối chiếu tên vật tư với danh mục ERP tại thời điểm này.",
            )
        if len(rows) == 1:
            return str(rows[0][0]).strip().upper(), str(rows[0][1]).strip()
        if not rows:
            return ERPResult(
                status="success_empty", intent="material_name_resolution", filters={"ten_vt": material_name},
                message="Không tìm thấy tên vật tư khớp chính xác trong danh mục ERP.",
            )
        return ERPResult(
            status="invalid_filter", intent="material_name_resolution", filters={"ten_vt": material_name},
            error_code="AMBIGUOUS_MATERIAL_NAME",
            message="Tên vật tư khớp nhiều mã; cần cung cấp mã vật tư để chọn đúng bản ghi.",
        )

    def _execute_material_date_request(self, request: ERPRequest) -> str:
        """Tier-1 material/day ledger query, including deterministic in/out aggregates."""
        material = request.filters["ma_vt"]
        raw_date = request.filters["ngay_ct"]
        try:
            transaction_date = datetime.strptime(
                raw_date, "%Y-%m-%d" if "-" in raw_date else "%d/%m/%Y"
            ).date()
        except ValueError:
            return json.dumps(ERPResult(
                status="invalid_filter", intent=request.intent, filters=request.filters,
                error_code="INVALID_TRANSACTION_DATE", message="Ngày chứng từ không đúng định dạng."
            ).payload(), ensure_ascii=False, default=str)
        query = """
            SELECT a.ngay_ct, a.so_ct, a.ma_vt, v.ten_vt, a.ma_gd, a.ma_kho,
                   a.ma_nt, CASE WHEN a.ty_gia = 0 THEN 1 ELSE a.ty_gia END AS ty_gia,
                   coalesce(a.sl_nhap, 0) AS sl_nhap, coalesce(a.sl_xuat, 0) AS sl_xuat,
                   a.dvt, a.dien_giai
            FROM public.ct70 AS a
            LEFT JOIN public.dmvt AS v ON upper(trim(v.ma_vt)) = upper(trim(a.ma_vt))
            WHERE upper(trim(a.ma_vt)) = %s AND a.ngay_ct = %s
            ORDER BY a.so_ct, a.stt_rec, a.ma_vt
            LIMIT %s
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (material, transaction_date, MAX_ROWS + 1))
                    columns = [item.name for item in cursor.description]
                    raw_rows = cursor.fetchmany(MAX_ROWS + 1)
        except Exception:
            return json.dumps(ERPResult(
                status="db_error", intent=request.intent, filters=request.filters,
                error_code="ERP_QUERY_FAILED", message="Không thể truy vấn ERP tại thời điểm này."
            ).payload(), ensure_ascii=False, default=str)
        rows = [dict(zip(columns, (json_value(value) for value in row))) for row in raw_rows[:MAX_ROWS]]
        if not rows:
            return json.dumps(ERPResult(
                status="success_empty", intent=request.intent, filters=request.filters,
                message="Không có dữ liệu khớp đúng các điều kiện truy vấn."
            ).payload(), ensure_ascii=False, default=str)
        summary = {
            "sl_nhap": str(sum((Decimal(str(row["sl_nhap"])) for row in rows), Decimal())),
            "sl_xuat": str(sum((Decimal(str(row["sl_xuat"])) for row in rows), Decimal())),
        }
        return json.dumps(ERPResult(
            status="success", intent=request.intent, filters=request.filters,
            summary=summary, rows=rows, total_rows=len(rows), returned_rows=len(rows),
            has_more=len(raw_rows) > MAX_ROWS,
        ).payload(), ensure_ascii=False, default=str)


    def _execute_material_master_request(self, request: ERPRequest) -> str:
        """Return the full allowed master-data record for one explicit material code."""
        material = request.filters["ma_vt"]
        query = """
            SELECT row_to_json(v)
            FROM public.dmvt AS v
            WHERE upper(trim(v.ma_vt)) = %s
            LIMIT 1
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (material,))
                    row = cursor.fetchone()
        except Exception:
            return json.dumps(ERPResult(
                status="db_error", intent=request.intent, filters=request.filters,
                error_code="ERP_QUERY_FAILED", message="Không thể truy vấn danh mục vật tư tại thời điểm này."
            ).payload(), ensure_ascii=False, default=str)
        if not row:
            return json.dumps(ERPResult(
                status="success_empty", intent=request.intent, filters=request.filters,
                message="Không tìm thấy mã vật tư trong danh mục ERP."
            ).payload(), ensure_ascii=False, default=str)
        record = row[0]
        return json.dumps(ERPResult(
            status="success", intent=request.intent, filters=request.filters,
            rows=[record], total_rows=1, returned_rows=1,
        ).payload(), ensure_ascii=False, default=str)


    def _execute_manifest_journal_field(self, question: str, filters: dict[str, str]) -> str | None:
        """Read a manifest field or aggregate a manifest-defined journal metric."""
        if not filters.get("ma_vt"):
            return None
        try:
            report = load_report_config("nhat-ky-nhap-xuat-ton")
            parsed = parse_report_request(question, report)
        except Exception:
            return None
        filter_fields = {"ma_vt", "so_ct", "ngay_ct", "ma_kho"}
        fields = [field for field in parsed["requested_fields"] if field not in filter_fields]
        if not fields:
            return None
        field = fields[0]
        field_config = next((item for item in report["columns"] if item.get("field") == field), None)
        if not field_config or not re.fullmatch(r"[a-z_]+", field):
            return None
        lookup_source = field_config.get("lookup")
        value_expression = f"a.{field}"
        lookup_join = ""
        # Match the Nhật ký nhập xuất tồn screen: a stored zero exchange rate
        # represents the base-currency rate of one. The other NT fields are
        # display-only computed columns in that same screen.
        computed_expressions = {
            "ty_gia": "CASE WHEN a.ty_gia = 0 THEN 1 ELSE a.ty_gia END",
            "gia_nt": "CASE WHEN a.ty_gia <> 0 THEN a.gia / a.ty_gia ELSE a.gia END",
            "tien_nhap_nt": "CASE WHEN a.ty_gia <> 0 THEN a.tien_nhap / a.ty_gia ELSE a.tien_nhap END",
            "tien_xuat_nt": "CASE WHEN a.ty_gia <> 0 THEN a.tien_xuat / a.ty_gia ELSE a.tien_xuat END",
        }
        value_expression = computed_expressions.get(field, value_expression)
        if lookup_source == "dmvt":
            value_expression = f"v.{field}"
            lookup_join = "LEFT JOIN public.dmvt AS v ON upper(trim(v.ma_vt)) = upper(trim(a.ma_vt))"
        elif lookup_source:
            return None
        report_filters = merge_report_filters(parsed["filters"], filters)
        where = ["upper(trim(a.ma_vt)) = %s"]
        parameters: list[Any] = [report_filters["ma_vt"]]
        if report_filters.get("so_ct"):
            where.append("trim(a.so_ct) = %s")
            parameters.append(report_filters["so_ct"])
        if report_filters.get("ngay_ct"):
            raw_date = report_filters["ngay_ct"]
            try:
                transaction_date = datetime.strptime(
                    raw_date, "%Y-%m-%d" if "-" in raw_date else "%d/%m/%Y"
                ).date()
            except ValueError:
                return json.dumps(ERPResult(
                    status="invalid_request", intent="journal_field_lookup", filters=report_filters,
                    error_code="INVALID_TRANSACTION_DATE", message="Ngày chứng từ không đúng định dạng."
                ).payload(), ensure_ascii=False, default=str)
            where.append("a.ngay_ct = %s")
            parameters.append(transaction_date)
        if report_filters.get("ma_kho"):
            where.append("upper(trim(a.ma_kho)) = %s")
            parameters.append(report_filters["ma_kho"])

        metric_fields = set(report.get("output", {}).get("metrics", []))
        if len(fields) > 1:
            if not all(metric in metric_fields for metric in fields):
                return None
            selections = ", ".join(
                f"coalesce(sum(a.{metric}), 0) AS {metric}" for metric in fields
            )
            query = f"""
                SELECT {selections}
                FROM public.ct70 AS a
                WHERE {' AND '.join(where)}
            """
            try:
                import psycopg
                with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SET TRANSACTION READ ONLY")
                        cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                        cursor.execute(query, parameters)
                        raw_row = cursor.fetchone()
            except Exception:
                return json.dumps(ERPResult(
                    status="db_error", intent="journal_metric_total", filters=filters,
                    error_code="ERP_QUERY_FAILED", message="Không thể truy vấn các cột của Nhật ký nhập xuất tồn."
                ).payload(), ensure_ascii=False, default=str)
            values = {
                metric: format_report_field_value(metric, json_value(raw_row[index]))
                for index, metric in enumerate(fields)
            }
            labels = {item["field"]: item["label"] for item in report["columns"]}
            confirmed = "; ".join(
                f"{labels[metric]}: {values[metric]}" for metric in fields
            )
            return f"KẾT QUẢ ERP ĐÃ XÁC NHẬN — {confirmed}."
        if field in metric_fields:
            query = f"""
                SELECT coalesce(sum({value_expression}), 0) AS value, count(*) AS row_count
                FROM public.ct70 AS a
                {lookup_join}
                WHERE {' AND '.join(where)}
            """
        else:
            query = f"""
                SELECT {value_expression} AS value, count(*) AS row_count
                FROM public.ct70 AS a
                {lookup_join}
                WHERE {' AND '.join(where)}
                GROUP BY {value_expression}
                ORDER BY row_count DESC, value NULLS FIRST
                LIMIT %s
            """
            parameters.append(MAX_ROWS)
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, parameters)
                    columns = [item.name for item in cursor.description]
                    raw_rows = cursor.fetchall()
        except Exception:
            return json.dumps(ERPResult(
                status="db_error", intent="journal_field_lookup", filters=filters,
                error_code="ERP_QUERY_FAILED", message="Không thể truy vấn cột của Nhật ký nhập xuất tồn."
            ).payload(), ensure_ascii=False, default=str)
        rows = [dict(zip(columns, (json_value(value) for value in row))) for row in raw_rows]
        for row in rows:
            row["value"] = format_report_field_value(field, row.get("value"))
        single_value = rows[0]["value"] if len(rows) == 1 else None
        if single_value is not None:
            return f"KẾT QUẢ ERP ĐÃ XÁC NHẬN — {field_config['label']}: {single_value}."
        message = None
        if field in metric_fields and not report_filters.get("ngay_ct") and not report_filters.get("so_ct"):
            message = "Tổng theo toàn bộ giao dịch của mã vật tư."
        return json.dumps(ERPResult(
            status="success" if rows else "success_empty", intent="journal_metric_total" if field in metric_fields else "journal_field_lookup",
            filters={**report_filters, "field": field},
            summary={field: single_value} if single_value is not None else {},
            rows=rows, total_rows=len(rows), returned_rows=len(rows),
            message=message,
        ).payload(), ensure_ascii=False, default=str)
