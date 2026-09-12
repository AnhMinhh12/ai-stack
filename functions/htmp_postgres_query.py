"""
title: Tra cứu PostgreSQL ERP
author: HTMP Platform
version: 1.2.0
required_open_webui_version: 0.6.0
"""

"""Global Open WebUI tools for natural-language, read-only ERP lookup."""

import json
import os
import re
import urllib.error
import urllib.request
from datetime import date, datetime
from decimal import Decimal
from typing import Any

MAX_ROWS = int(os.getenv("HTMP_DB_MAX_ROWS", "200"))
MAX_SCHEMA_TABLES = int(os.getenv("HTMP_DB_MAX_SCHEMA_TABLES", "30"))
TIMEOUT_MS = int(os.getenv("HTMP_DB_STATEMENT_TIMEOUT_MS", "15000"))
PLANNER_TABLES = int(os.getenv("HTMP_DB_PLANNER_TABLES", "180"))
PLANNER_ATTEMPTS = int(os.getenv("HTMP_DB_PLANNER_ATTEMPTS", "3"))
READ_QUERY = re.compile(r"^\s*(?:select|with)\b", re.I | re.S)
FORBIDDEN = re.compile(r"\b(?:insert|update|delete|merge|alter|drop|create|grant|revoke|copy|call|do|vacuum|analyze|truncate|listen|notify|execute|prepare|deallocate|set|show|reset|discard|lock)\b", re.I)


def json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    return value


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

    def _schema_catalog(self) -> str:
        """Return a compact, data-free catalog for the internal SQL planner."""
        query = """
            SELECT table_schema, table_name,
                   string_agg(column_name || ':' || data_type, ', ' ORDER BY ordinal_position) AS columns
            FROM information_schema.columns
            WHERE table_schema = 'public'
            GROUP BY table_schema, table_name
            ORDER BY CASE table_name
                WHEN 'cdvt13' THEN 0 WHEN 'cdvt' THEN 1 WHEN 'cdbsp' THEN 2 ELSE 3 END,
                table_name
            LIMIT %s
        """
        import psycopg
        with psycopg.connect(**connection_settings(), autocommit=False) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                cursor.execute(query, (PLANNER_TABLES,))
                return "\n".join(f"{schema}.{table}({columns})" for schema, table, columns in cursor.fetchall())

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

    def ask_erp(self, question: str) -> str:
        """Trả lời câu hỏi ERP bất kỳ bằng tiếng Việt, không cần người dùng biết SQL.

        Dùng ĐẦU TIÊN cho câu ERP chưa có hàm chuyên biệt. Hàm tự đọc catalog
        bảng/cột, nhờ model nội bộ lập SELECT an toàn, chạy truy vấn chỉ đọc và
        tự sửa SQL tối đa ba lần khi tên bảng/cột chưa đúng.
        """
        question = (question or "").strip()
        if not question:
            return "Cần cung cấp câu hỏi ERP để tra cứu."
        try:
            catalog = self._schema_catalog()
        except Exception:
            return "Không thể đọc catalog ERP. Kiểm tra cấu hình và quyền SELECT của tài khoản DB."

        base_url = (os.getenv("OPENAI_API_BASE_URLS") or "http://vllm:8000/v1").split(",")[0].rstrip("/")
        api_key = os.getenv("OPENAI_API_KEY", "")
        history = ""
        last_error = ""
        for _ in range(PLANNER_ATTEMPTS):
            planner_prompt = f"""Bạn là bộ lập kế hoạch SQL PostgreSQL cho ERP nội bộ. Trả về DUY NHẤT JSON hợp lệ dạng {{"sql": "SELECT ..."}}.

Yêu cầu người dùng: {question}

Catalog thật (chỉ dùng chính xác tên bảng/cột trong catalog, không bịa tên):
{catalog}

Quy tắc: chỉ một SELECT/WITH; dùng schema public khi cần; tối đa 200 dòng; với ngày dd/mm/yyyy đổi thành DATE 'yyyy-mm-dd'; nếu câu hỏi cần dữ liệu mà không xác định được bảng/cột, trả {{"sql": null, "reason": "..."}}. {history}"""
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
                return "Không thể xác định truy vấn an toàn từ catalog ERP. Hãy nêu rõ thêm trường hoặc điều kiện cần xem."
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
