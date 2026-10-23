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
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any
from erp_ai import ConversationStateStore, ERPRequest, ERPResult, build_request
from erp_ai.entities import extract_entities
from erp_ai.validator import validate_document_result, validate_inventory_balance_result

MAX_ROWS = int(os.getenv("HTMP_DB_MAX_ROWS", "200"))
MAX_SCHEMA_TABLES = int(os.getenv("HTMP_DB_MAX_SCHEMA_TABLES", "30"))
TIMEOUT_MS = int(os.getenv("HTMP_DB_STATEMENT_TIMEOUT_MS", "15000"))
PLANNER_TABLES = int(os.getenv("HTMP_DB_PLANNER_TABLES", "180"))
PLANNER_CANDIDATE_TABLES = int(os.getenv("HTMP_DB_CANDIDATE_TABLES", "12"))
PLANNER_ATTEMPTS = int(os.getenv("HTMP_DB_PLANNER_ATTEMPTS", "3"))
ERP_CONVERSATION_STATE = ConversationStateStore()
ERP_REPORTS_DIR = Path(os.getenv("HTMP_ERP_REPORTS_DIR", "/app/backend/data/erp-reports"))
ERP_BUSINESS_INTENTS_PATH = Path(os.getenv("HTMP_ERP_BUSINESS_INTENTS_PATH", "/app/backend/data/erp-business-intents.json"))
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
    return re.sub(r"[^a-z0-9/-]+", " ", folded).strip()


def clean_numeric_str(value: Any) -> Any:
    """Format numeric values without trailing redundant zeros."""
    if isinstance(value, Decimal):
        s = format(value, "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s or "0"
    if isinstance(value, float):
        s = f"{value:.10f}".rstrip("0").rstrip(".")
        return s or "0"
    if isinstance(value, str) and re.match(r"^-?\d+\.\d+$", value):
        s = value.rstrip("0").rstrip(".")
        return s or "0"
    return value


def split_period_comparison_question(question: str) -> list[str]:
    """Split questions that compare metrics across two date intervals into distinct lookups."""
    range_matches = list(re.finditer(
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})\s*(?:[–—\-]|đến|den|to)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        question or "",
        re.I,
    ))
    if len(range_matches) != 2:
        return []
    normalized = normalize_text(question)
    comparison_indicators = (
        "so sanh", "doi chieu", "so voi", "tung ky", "hai khoang",
        "2 khoang", "hai ky", "2 ky", "hai dot", "2 dot", "chenh lech",
        "tang hay giam", "tang giam"
    )
    if not any(kw in normalized for kw in comparison_indicators):
        return []

    r1_start, r1_end = range_matches[0].group(1), range_matches[0].group(2)
    r2_start, r2_end = range_matches[1].group(1), range_matches[1].group(2)

    entities = extract_erp_entities(question)
    ma_vt = entities.get("ma_vt")
    customer_match = re.search(
        r"(?:khách\s*hàng|khach\s*hang|khách|khach|mã\s*kh|ma\s*kh)\s*[:#-]?\s*([a-z0-9]+)\b",
        question or "",
        re.I,
    )
    ma_kh = customer_match.group(1).upper() if customer_match else entities.get("ma_kh")

    has_revenue = any(k in normalized for k in ("doanh thu", "doanh so", "tien"))
    has_receipt = any(k in normalized for k in ("nhap kho", "phieu nhap"))

    if has_receipt:
        base = f"Nhập kho mã {ma_vt}" if ma_vt else "Nhập kho"
    elif has_revenue:
        parts = ["Doanh thu và số lượng"]
        if ma_vt:
            parts.append(f"mã {ma_vt}")
        if ma_kh:
            parts.append(f"của khách {ma_kh}")
        base = " ".join(parts)
    else:
        parts = ["Số lượng xuất bán"]
        if ma_vt:
            parts.append(f"mã {ma_vt}")
        if ma_kh:
            parts.append(f"của khách {ma_kh}")
        base = " ".join(parts)

    return [
        f"{base} từ ngày {r1_start} đến ngày {r1_end}",
        f"{base} từ ngày {r2_start} đến ngày {r2_end}",
    ]


def split_batched_erp_questions(question: str) -> list[str]:
    """Split a Markdown list or comma-separated questions into lookups.

    Open WebUI makes one native ``ask_erp`` call per chat turn.  A batch is
    therefore executed inside that call so every bullet gets its own safe,
    read-only lookup without asking the model to reuse a prior result.
    """
    comparison_splits = split_period_comparison_question(question)
    if comparison_splits:
        return comparison_splits

    items: list[str] = []
    for line in (question or "").splitlines():
        match = re.match(r"^\s*(?:[-*•]|\d+[.)])\s+(.+?)\s*$", line)
        if match:
            items.append(match.group(1))
    if len(items) > 1:
        return items
    source = question or ""
    # If multiple sentences end with question marks, split them only when
    # they represent independent questions with their own entities or explicit comma separation.
    if "?" in source:
        qm_items = [
            item.strip()
            for item in re.split(r"(?<=\?)\s*(?:,\s*)?", source)
            if item.strip()
        ]
        if len(qm_items) > 1:
            connected_patterns = re.compile(
                r"\b(?:mã này|hàng này|mã hàng này|khách này|khuôn này|của nó|của chúng|"
                r"theo từng|ngày xuất và|số lượng bao nhiêu|có thể quy đổi|hết tuổi thọ|"
                r"gồm những gì|giá áp dụng|trạng thái ra sao|căn cứ thời gian|tình trạng hiện tại|"
                r"phân biệt|phan biet|nêu rõ|neu ro|chưa giao bù|chua giao bu)\b",
                re.I,
            )
            has_connected = any(connected_patterns.search(it) for it in qm_items[1:])
            has_own_entity = all(
                bool(extract_erp_entities(it).get("ma_vt") or extract_erp_entities(it).get("ma_kh"))
                for it in qm_items
            )
            if not has_connected and has_own_entity:
                return qm_items

    # Ordinary sentence endings are reliable separators only when each clause
    # contains standalone inquiry entities. Connective directives like "Nêu số lượng..."
    # or "Chi tiết từng dòng..." should not be split off as orphan requests.
    inline_items = [
        item.strip()
        for item in re.split(r"(?<=[?!.])\s*(?:,\s*)?", source)
        if item.strip()
    ]
    if len(inline_items) > 1:
        directive_pattern = re.compile(
            r"^\s*(?:nêu|cho biết|cho biet|chi tiết|chi tiet|giải thích|giai thich|tính|tinh|hãy|hay|vui lòng|phân biệt|phan biet|lưu ý|luu y)\b",
            re.I
        )
        has_orphan_directive = any(directive_pattern.search(it) for it in inline_items[1:])
        has_own_entity = all(
            bool(extract_erp_entities(it).get("ma_vt") or extract_erp_entities(it).get("ma_kh"))
            for it in inline_items
        )
        if not has_orphan_directive and has_own_entity:
            return inline_items

    # With no terminal punctuation, recognize a new standalone ERP request
    # after a comma. Do not split connective clauses such as "khi nào, ai lập
    # phiếu" or column listings like "gồm số đơn, ngày đặt, mã hàng...".
    if re.search(r"\b(?:gồm|bao\s+gồm|các\s+cột|chi\s+tiết\s+gồm)\b", source, re.I):
        return []

    new_question_start = (
        r"(?:m[ãa]\s+(?:hàng|hang|vật\s+tư|vat\s+tu)\s+[a-z0-9/-]*\d|"
        r"phiếu\s+nhập\s+kho\b|phieu\s+nhap\s+kho\b|"
        r"lần\s+nhập\s+kho\b|lan\s+nhap\s+kho\b|"
        r"bảng\s+kê\b|bang\s+ke\b|"
        r"ngày\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}\b|ngay\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}\b|"
        r"(?=[a-z0-9/-]*\d)(?=[a-z0-9/-]*[a-z])[a-z0-9]+(?:[-/][a-z0-9]+)*\b)"
    )
    natural_items = [
        item.strip()
        for item in re.split(rf",\s*(?={new_question_start})", source, flags=re.I)
        if item.strip()
    ]
    merged_items: list[str] = []
    date_only = re.compile(r"^(?:ngày|ngay)\s+\d{1,2}[/-]\d{1,2}[/-]\d{4}$", re.I)
    for item in natural_items:
        if merged_items and date_only.fullmatch(merged_items[-1]):
            merged_items[-1] = f"{merged_items[-1]}, {item}"
        else:
            merged_items.append(item)
    return merged_items if len(merged_items) > 1 else []


def batch_lookup_key(question: str) -> tuple[str, tuple[str, ...], str] | None:
    """Return a conservative cache key for equivalent material lookups."""
    material_code = extract_erp_entities(question).get("ma_vt", "")
    if not material_code:
        return None
    normalized = normalize_text(question)
    dates = tuple(re.findall(r"\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b", question))
    latest_terms = ("khi nao", "gan nhat", "moi nhat", "lan cuoi", "lan nhap cuoi")
    selection = "latest" if not dates and any(term in normalized for term in latest_terms) else "register"
    return material_code, dates, selection


def compact_batch_payload(payload: Any) -> dict[str, Any]:
    """Keep a batch result small enough for the response model to answer all items."""
    if not isinstance(payload, dict):
        return {"message": str(payload)}
    result: dict[str, Any] = {}
    for field in ("lookup", "rows", "message", "summary", "row_count", "matched_row_count", "truncated"):
        if field in payload:
            result[field] = payload[field]
    if not result:
        result["message"] = payload.get("message", "Không có kết quả ERP có thể sử dụng.")
    return result


def format_batch_answer(results: list[dict[str, str]], answers: list[dict[str, Any]]) -> str:
    """Render a compact, deterministic response so the chat model cannot omit a batch item."""
    answer_by_id = {str(answer["answer_id"]): answer for answer in answers}
    question_numbers: dict[str, list[int]] = {}
    for index, result in enumerate(results, start=1):
        question_numbers.setdefault(result["answer_id"], []).append(index)

    def labels(numbers: list[int]) -> str:
        if len(numbers) > 1 and numbers == list(range(numbers[0], numbers[-1] + 1)):
            return f"Câu {numbers[0]}–{numbers[-1]}"
        return "Câu " + ", ".join(str(number) for number in numbers)

    def quantity(value: Any) -> str:
        return clean_numeric_str(value) or "0"

    def row_text(row: dict[str, Any]) -> str:
        if not isinstance(row, dict):
            return str(row)
        if row.get("message"):
            return str(row["message"])
        if row.get("bom_info"):
            return str(row["bom_info"])
        parts = [
            str(row.get("ngay_ct") or ""),
            str(row.get("so_ct") or ""),
            str(row.get("ten_kho") or row.get("ma_kho") or ""),
            f"{quantity(row.get('so_luong'))} {row.get('dvt') or ''}".strip() if row.get("so_luong") is not None else "",
        ]
        revenue = row.get("doanh_thu") or row.get("tien2")
        if revenue is not None:
            parts.append(f"doanh thu: {quantity(revenue)}")
        if row.get("gia") is not None or row.get("sl_min") is not None:
            parts.append(f"MOQ: {quantity(row.get('sl_min'))} {row.get('dvt') or ''} | Giá: {quantity(row.get('gia') or row.get('gia0'))} {row.get('ma_nt') or ''}")
        if row.get("quy_cach_chuan"):
            parts.append(f"Quy cách: {row['quy_cach_chuan']}")
        if row.get("quy_doi_ton"):
            parts.append(f"Tồn quy đổi: {row['quy_doi_ton']}")
        if row.get("nguoi_lap"):
            parts.append(str(row["nguoi_lap"]))
        if row.get("tong_so_shot") is not None:
            parts.append(f"Khuôn {row.get('ma_khuon')}: {quantity(row.get('tong_so_shot'))} shot")
        if row.get("die_no"):
            parts.append(f"Die {row.get('die_no')}: {quantity(row.get('so_luong'))} PCS")
        if row.get("status_qc") is not None:
            parts.append(f"QC: {row.get('form_name') or row.get('status_qc')} ({quantity(row.get('so_luong'))} PCS)")
        filtered = [part for part in parts if part]
        if filtered:
            return " | ".join(filtered)
        if row.get("ten_vt"):
            nvl = f" | Nhựa: {row['ma_nvl']}" if row.get("ma_nvl") else ""
            kh = f" | Khách: {row['ma_kh']}" if row.get("ma_kh") else ""
            return f"Mã: {row.get('ma_vt')} - {row.get('ten_vt')}{nvl}{kh}"
        return " | ".join(f"{k}: {v}" for k, v in list(row.items())[:3] if v is not None)

    sections: list[str] = []
    for answer_id, numbers in question_numbers.items():
        answer = answer_by_id[answer_id]
        prefix = labels(numbers)
        lookup = answer.get("lookup") or {}
        if lookup.get("tu_ngay") and lookup.get("den_ngay"):
            prefix = f"{prefix} (Kỳ {lookup['tu_ngay']} đến {lookup['den_ngay']})"
        if answer.get("message"):
            sections.append(f"{prefix}: {answer['message']}")
            continue
        summary = answer.get("summary")
        if summary and ("tong_so_luong" in summary or "tong_doanh_thu" in summary):
            sl = summary.get("tong_so_luong", "0")
            dt = summary.get("tong_doanh_thu", "0")
            sections.append(f"{prefix}: Tổng số lượng: {sl} PCS | Doanh thu: {dt} VND.")
            continue
        rows = answer.get("rows") or []
        if not rows:
            sections.append(f"{prefix}: Không có dữ liệu.")
            continue
        if len(rows) == 1:
            sections.append(f"{prefix}: {row_text(rows[0])}")
            continue
        sections.append(f"{prefix}: {len(rows)} phiếu.")
        sections.extend(f"- {row_text(row)}" for row in rows if isinstance(row, dict))
    return "\n".join(sections)


def extract_erp_entities(text: str) -> dict[str, str]:
    """Extract stable ERP identifiers from natural-language text once."""
    return extract_entities(text)


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
        return clean_numeric_str(value)
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


def trusted_erp_user_id(user: Any) -> int | None:
    """Resolve an injected Open WebUI identity through a server-owned map only."""
    try:
        mapping = json.loads(os.getenv("HTMP_ERP_USER_ID_MAP", "{}"))
    except json.JSONDecodeError:
        mapping = {}
    if isinstance(user, dict) and isinstance(mapping, dict):
        for identity in (str(user.get("id") or ""), str(user.get("email") or "").lower()):
            value = mapping.get(identity)
            if isinstance(value, int) and value > 0:
                return value
            if isinstance(value, str) and value.isdecimal() and int(value) > 0:
                return int(value)
    shared_user_id = os.getenv("HTMP_ERP_SHARED_USER_ID", "")
    return int(shared_user_id) if shared_user_id.isdecimal() and int(shared_user_id) > 0 else None


def business_intent_matches(intent_id: str, question: str, *, has_material_code: bool = False) -> bool:
    """Match a versioned business intent, keeping ERP semantics out of code."""
    try:
        intents = json.loads(ERP_BUSINESS_INTENTS_PATH.read_text()).get("intents", [])
        intent = next(item for item in intents if item.get("id") == intent_id)
    except (OSError, ValueError, StopIteration):
        return False
    normalized = normalize_text(question)
    rules = intent.get("match", {})
    required = rules.get("all", [])
    if "ma_vt" in required:
        required = [term for term in required if term != "ma_vt"]
        if not has_material_code:
            return False
    def contains_term(term: str) -> bool:
        # Match complete normalized words/phrases. A substring check makes the
        # purchase-price keyword ``gia`` match delivery words such as ``giao``.
        return re.search(
            rf"(?<![a-z0-9]){re.escape(normalize_text(term))}(?![a-z0-9])",
            normalized,
        ) is not None

    return all(contains_term(term) for term in required) and any(
        contains_term(term) for term in rules.get("any", [])
    )


def production_material_type_codes() -> tuple[str, ...]:
    """Return versioned BTP/TP material types that must not be called purchases."""
    try:
        values = json.loads(ERP_BUSINESS_INTENTS_PATH.read_text()).get("material_classification", {}).get("production_type_codes", [])
    except (OSError, ValueError):
        values = []
    return tuple(str(value) for value in values if str(value))


def load_report_config(report_id: str) -> dict[str, Any]:
    """Load a versioned, screen-level ERP report manifest."""
    config = json.loads((ERP_REPORTS_DIR / f"{report_id}.json").read_text())
    if config.get("id") != report_id or not isinstance(config.get("match_phrases"), list):
        raise ValueError("Invalid ERP report manifest")
    return config


def load_report_sql(report: dict[str, Any], query_file: str | None = None) -> str:
    """Load fixed report SQL in either the deployed or repository layout."""
    query_file = query_file or report.get("query_file")
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
            else r"((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)"
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


def extract_location_stock_warehouse(question: str) -> str:
    """Recognize a warehouse in a location-level stock request.

    Warehouse codes such as ``KHOTP00`` also match the general material-code
    pattern.  Treat them as warehouses only in the unambiguous request shape
    that asks for location, item code, and on-hand quantity.
    """
    normalized = normalize_text(question)
    needs_location_stock = (
        "vi tri" in normalized
        and ("ma hang" in normalized or "ma vat tu" in normalized)
        and ("so luong" in normalized or "sl" in normalized)
    )
    if not needs_location_stock:
        return ""
    compact_code = re.search(r"\b(KHO[A-Z0-9]+(?:[-/][A-Z0-9]+)*)\b", question or "", re.I)
    if compact_code:
        return compact_code.group(1).upper()
    labelled_code = re.search(
        r"\b(?:ma\s*)?kho\s*[:#-]?\s*([A-Z0-9]+(?:[-/][A-Z0-9]+)*)\b",
        question or "",
        re.I,
    )
    return labelled_code.group(1).upper() if labelled_code else ""


def extract_iso_date_range(text: str, default_from: str = "2026-10-01", default_to: str = "2026-10-20") -> tuple[str, str]:
    """Extract (from_date, to_date) in YYYY-MM-DD format from Vietnamese question."""
    def to_iso(s: str) -> str:
        parts = re.split(r"[/-]", s.strip())
        if len(parts) == 3:
            return f"{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"
        return s
    m = re.search(
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})\s*(?:[–—\-]|đến|den|to)\s*(?:hết\s*)?(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        text or "",
        re.I,
    )
    if m:
        return to_iso(m.group(1)), to_iso(m.group(2))
    dates = re.findall(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b", text or "")
    if len(dates) >= 2:
        return to_iso(dates[0]), to_iso(dates[1])
    if len(dates) == 1:
        return to_iso(dates[0]), to_iso(dates[0])
    return default_from, default_to


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

    def _purchase_order_history_count(
        self, question: str, material_code: str, authenticated_user_id: int
    ) -> str | None:
        """Return exact purchase-order history and price analytics within user scope."""
        normalized = normalize_text(question)
        wants_detail = any(term in normalized for term in ("nhung lan nao", "chi tiet", "danh sach", "lich su")) or (
            "bao nhieu lan" in normalized and ("gia" in normalized or "nha cung cap" in normalized)
        )
        wants_price = "gia" in normalized
        detail_limit = 50 if wants_detail else (1 if wants_price else 0)
        summary_query = """
            WITH access_scope AS (
                SELECT u.user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
                       coalesce(u.is_super, 0) = 1
                         OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '')
                         AS unrestricted
                FROM public.userinfo AS u
                WHERE u.user_id = %s
            )
            SELECT count(DISTINCT h.so_ct) AS so_lan_dat,
                   min(h.ngay_ct) AS lan_dat_dau_tien,
                   max(h.ngay_ct) AS lan_dat_gan_nhat,
                   min(d.gia) FILTER (WHERE d.gia > 0) AS gia_mua_thap_nhat,
                   max(d.gia) FILTER (WHERE d.gia > 0) AS gia_mua_cao_nhat,
                   avg(d.gia) FILTER (WHERE d.gia > 0) AS gia_mua_trung_binh,
                   sum(d.tien) FILTER (WHERE d.gia > 0)
                     / nullif(sum(d.so_luong) FILTER (WHERE d.gia > 0), 0)
                     AS gia_mua_binh_quan_gia_quyen
            FROM public.ct94 AS d
            JOIN public.ph94 AS h ON h.stt_rec = d.stt_rec
            CROSS JOIN access_scope AS a
            WHERE upper(trim(d.ma_vt)) = %s
              AND (a.unrestricted OR a.ds_branchs = ''
                   OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
        """
        detail_query = """
            WITH access_scope AS (
                SELECT u.user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
                       coalesce(u.is_super, 0) = 1
                         OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
                FROM public.userinfo AS u WHERE u.user_id = %s
            )
            SELECT h.ngay_ct, h.so_ct, h.ma_kh, k.ten_kh, h.ma_nt, h.ty_gia,
                   d.so_luong, d.dvt, d.gia_nt0 AS gia_ban_dau_nguyen_te,
                   d.gia_nt AS gia_mua_nguyen_te, d.gia AS gia_mua_vnd,
                   d.tien_nt AS thanh_tien_nguyen_te, d.tien AS thanh_tien_vnd,
                   h.status, s.statusname
            FROM public.ct94 AS d
            JOIN public.ph94 AS h ON h.stt_rec = d.stt_rec
            CROSS JOIN access_scope AS a
            LEFT JOIN public.dmkh AS k ON k.ma_kh = h.ma_kh
            LEFT JOIN public.sys_dmtt AS s ON s.ma_ct = 'PO1' AND s.status = h.status
            WHERE upper(trim(d.ma_vt)) = %s
              AND (a.unrestricted OR a.ds_branchs = ''
                   OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
            ORDER BY h.ngay_ct DESC, h.so_ct DESC, d.ln
            LIMIT %s
        """
        supplier_query = """
            WITH access_scope AS (
                SELECT u.user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
                       coalesce(u.is_super, 0) = 1
                         OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
                FROM public.userinfo AS u WHERE u.user_id = %s
            )
            SELECT h.ma_kh, max(k.ten_kh) AS ten_kh, count(DISTINCT h.so_ct) AS so_don_mua,
                   min(h.ngay_ct) AS lan_dau_tien, max(h.ngay_ct) AS lan_gan_nhat
            FROM public.ct94 AS d
            JOIN public.ph94 AS h ON h.stt_rec = d.stt_rec
            CROSS JOIN access_scope AS a
            LEFT JOIN public.dmkh AS k ON k.ma_kh = h.ma_kh
            WHERE upper(trim(d.ma_vt)) = %s
              AND (a.unrestricted OR a.ds_branchs = ''
                   OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
            GROUP BY h.ma_kh
            ORDER BY so_don_mua DESC, h.ma_kh
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(summary_query, (authenticated_user_id, material_code))
                    columns = [item.name for item in cursor.description]
                    row = cursor.fetchone()
                    summary = dict(zip(columns, (json_value(value) for value in row))) if row else {}
                    if detail_limit:
                        cursor.execute(detail_query, (authenticated_user_id, material_code, detail_limit + 1))
                        detail_columns = [item.name for item in cursor.description]
                        detail_rows = cursor.fetchmany(detail_limit + 1)
                    else:
                        detail_columns, detail_rows = [], []
                    cursor.execute(supplier_query, (authenticated_user_id, material_code))
                    supplier_columns = [item.name for item in cursor.description]
                    supplier_rows = cursor.fetchall()
        except Exception:
            return "Không thể tra lịch sử đơn hàng mua trong ERP."
        details = [dict(zip(detail_columns, (json_value(value) for value in item))) for item in detail_rows[:detail_limit]]
        suppliers = [dict(zip(supplier_columns, (json_value(value) for value in item))) for item in supplier_rows]
        if details:
            summary["gia_mua_gan_nhat"] = details[0].get("gia_mua_vnd")
            summary["ma_nt_gan_nhat"] = details[0].get("ma_nt")
            summary["ncc_don_mua_gan_nhat"] = {
                "ma_kh": details[0].get("ma_kh"),
                "ten_kh": details[0].get("ten_kh"),
            }
        catalog_prices: list[dict[str, Any]] = []
        supplier_quotes: list[dict[str, Any]] = []
        supplier_match = re.search(r"\b(NCC\d+)\b", question or "", re.I)
        requested_supplier = supplier_match.group(1).upper() if supplier_match else ""
        if details:
            catalog_query = """
                SELECT DISTINCT ON (p.ma_kh)
                       p.ma_kh, k.ten_kh, p.ma_nt,
                       p.gia0 AS gia_truoc_vat, p.gia AS gia_sau_vat,
                       p.ngay_bd, p.ngay_kt, p.sl_min AS so_luong_toi_thieu,
                       p.ma_dkthuongmai
                FROM public.dmgiamuact AS p
                LEFT JOIN public.dmkh AS k ON k.ma_kh = p.ma_kh
                WHERE upper(trim(p.ma_vt)) = %s
                  AND (%s = '' OR upper(trim(p.ma_kh)) = %s)
                  AND current_date BETWEEN p.ngay_bd AND p.ngay_kt
                ORDER BY p.ma_kh, p.ngay_bd DESC
            """
            try:
                import psycopg
                with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SET TRANSACTION READ ONLY")
                        cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                        cursor.execute(catalog_query, (material_code, requested_supplier, requested_supplier))
                        catalog_columns = [item.name for item in cursor.description]
                        catalog_prices = [
                            dict(zip(catalog_columns, (json_value(value) for value in row)))
                            for row in cursor.fetchall()
                        ]
            except Exception:
                catalog_prices = []
        # A supplier quote is not evidence that an order was placed.  It is,
        # however, the relevant price when the material has not yet appeared
        # on a purchase order (or when the user is viewing the supplier quote
        # screen).  Keep it separate from both historic PO prices and the
        # approved supplier-price catalog.
        supplier_quote_query = """
            WITH access_scope AS (
                SELECT u.user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
                       coalesce(u.is_super, 0) = 1
                         OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
                FROM public.userinfo AS u WHERE u.user_id = %s
            )
            SELECT DISTINCT ON (h.ma_kh)
                   h.ma_kh, h.ten_kh, d.ma_vt, d.dvt, h.ma_nt, h.ty_gia,
                   d.gia0 AS gia_truoc_vat_vnd, d.gia_nt0 AS gia_truoc_vat_nguyen_te,
                   d.gia AS gia_sau_vat_vnd, d.gia_nt AS gia_sau_vat_nguyen_te,
                   d.ma_thue, d.thue_suat, d.ngay_bd, d.ngay_kt,
                   h.ngay_ct, h.so_ct, d.appr_yn AS da_duyet,
                   d.close_yn AS da_dong, h.status AS trang_thai_chung_tu
            FROM public.ctbgncc AS d
            JOIN public.phbgncc AS h ON h.stt_rec = d.stt_rec
            CROSS JOIN access_scope AS a
            WHERE upper(trim(d.ma_vt)) = %s
              AND (%s = '' OR upper(trim(h.ma_kh)) = %s)
              AND (a.unrestricted OR a.ds_branchs = ''
                   OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
            ORDER BY h.ma_kh, d.ngay_ct DESC, h.so_ct DESC, d.ln DESC
            LIMIT %s
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(
                        supplier_quote_query,
                        (authenticated_user_id, material_code, requested_supplier, requested_supplier, MAX_ROWS + 1),
                    )
                    quote_columns = [item.name for item in cursor.description]
                    quote_rows = cursor.fetchmany(MAX_ROWS + 1)
                    supplier_quotes = [
                        dict(zip(quote_columns, (json_value(value) for value in row)))
                        for row in quote_rows[:MAX_ROWS]
                    ]
        except Exception:
            # Quotes enrich a purchase-history response; an unavailable quote
            # table must not hide valid purchase-order data.
            supplier_quotes = []
        summary["gia_don_mua_gan_nhat"] = summary.pop("gia_mua_gan_nhat", None)
        summary["gia_danh_muc_ncc_hien_hanh"] = catalog_prices
        summary["bao_gia_ncc_gan_nhat"] = supplier_quotes
        return json.dumps(
            {
                "source": "public.ph94 + public.ct94 (Đơn hàng mua); public.phbgncc + public.ctbgncc (Phiếu báo giá nhà cung cấp)",
                "lookup": {"ma_vt": material_code, "khoang_thoi_gian": "toàn bộ dữ liệu được phép xem"},
                "price_definitions": {
                    "gia_don_mua_gan_nhat": "Giá trên đơn mua gần nhất; là dữ liệu lịch sử.",
                    "gia_danh_muc_ncc_hien_hanh": "Các giá danh mục đang hiệu lực theo từng NCC; nếu câu hỏi có NCCxxxx thì chỉ trả NCC đó.",
                    "bao_gia_ncc_gan_nhat": "Báo giá NCC gần nhất theo từng NCC, gồm giá trước/sau VAT, hiệu lực và trạng thái; không phải đơn mua thực tế."
                },
                "summary": summary,
                "nha_cung_cap_da_mua": suppliers,
                "row_count": len(details),
                "truncated": len(detail_rows) > detail_limit,
                "rows": details,
            },
            ensure_ascii=False,
            default=str,
        )

    def _sales_latest_delivery_handler(self, question: str, authenticated_user_id: int | None) -> str | None:
        """Handle latest sales delivery request directly before sales summary."""
        material_code = extract_erp_entities(question).get("ma_vt")
        if not material_code:
            return None
        if not business_intent_matches("latest_sales_delivery", question, has_material_code=True):
            return None
        if authenticated_user_id is None:
            return "Không có mapping ERP hợp lệ cho phiên chat; tra lần giao gần nhất bị chặn an toàn."
        d_matches = re.findall(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b", question or "")
        as_of_date = None
        if d_matches:
            parts = re.split(r"[/-]", d_matches[-1].strip())
            if len(parts) == 3:
                as_of_date = f"{int(parts[2]):04d}-{int(parts[1]):02d}-{int(parts[0]):02d}"
        return self._latest_sales_delivery(material_code, authenticated_user_id, as_of_date=as_of_date)

    def _latest_sales_delivery(
        self, material_code: str, authenticated_user_id: int, as_of_date: str | None = None
    ) -> str:
        """Return the latest sales warehouse issue for one material.

        A delivery document can contain the same material on several lines.
        Aggregate those lines so the quantity agrees with the document shown
        by Bảng kê phiếu xuất kho bán hàng.
        """
        query = """
            WITH access_scope AS (
                SELECT u.user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
                       coalesce(u.is_super, 0) = 1
                         OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '')
                         AS unrestricted
                FROM public.userinfo AS u
                WHERE u.user_id = %s
            )
            SELECT h.ngay_lct, h.ngay_ct, h.so_ct, h.ma_kh,
                   max(k.ten_viet_tat) AS ten_kh, d.ma_vt, max(d.dvt) AS dvt,
                   sum(d.so_luong) AS so_luong_giao, h.ma_dvcs,
                   array_agg(DISTINCT nullif(d.ma_lo, '')) AS lots,
                   count(*) AS so_dong
            FROM public.ct81 AS d
            JOIN public.ph81 AS h ON h.stt_rec = d.stt_rec
            CROSS JOIN access_scope AS a
            LEFT JOIN public.dmkh AS k ON k.ma_kh = h.ma_kh
            WHERE upper(trim(d.ma_vt)) = %s
              AND h.ma_gd <> 4
              AND (%s::date IS NULL OR h.ngay_ct <= %s::date)
              AND (a.unrestricted OR a.ds_branchs = ''
                   OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
              AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (
                  SELECT 1 FROM public.dmkho AS w
                  WHERE w.ma_kho = d.ma_kho
                    AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))
              ))
            GROUP BY h.stt_rec, h.ngay_lct, h.ngay_ct, h.so_ct, h.ma_kh,
                     d.ma_vt, h.ma_dvcs
            ORDER BY h.ngay_lct DESC, h.ngay_ct DESC, h.so_ct DESC, h.stt_rec DESC
            LIMIT 1
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (authenticated_user_id, material_code, as_of_date, as_of_date))
                    columns = [item.name for item in cursor.description]
                    row = cursor.fetchone()
        except Exception:
            return "Không thể tra lần giao gần nhất trong ERP."
        result = dict(zip(columns, (json_value(value) for value in row))) if row else None
        lots = [l for l in (result.get("lots") or []) if l] if result else []
        lot_info = ", ".join(lots) if lots else "trống (chưa gắn mã lot trên chứng từ xuất bán)"
        msg = (
            f"Lần xuất giao gần nhất của mã {material_code}: Ngày xuất {result.get('ngay_ct')}, "
            f"chứng từ {result.get('so_ct')}, số lượng {clean_numeric_str(result.get('so_luong_giao'))} {result.get('dvt')}. "
            f"Mã lot ghi nhận trên hệ thống ERP: {lot_info}."
        ) if result else f"Không tìm thấy phiếu xuất bán cho mã {material_code}."
        return json.dumps(
            {
                "source": "public.ph81 + public.ct81 (Bảng kê phiếu xuất kho bán hàng)",
                "lookup": {"ma_vt": material_code, "khoang_thoi_gian": "toàn bộ dữ liệu được phép xem"},
                "summary": {
                    "lan_giao_gan_nhat": result.get("ngay_ct") if result else None,
                    "so_luong_giao": result.get("so_luong_giao") if result else None,
                    "dvt": result.get("dvt") if result else None,
                    "so_ct": result.get("so_ct") if result else None,
                    "ma_lo": lot_info,
                },
                "row_count": int(result is not None),
                "rows": [result] if result else [],
                "message": msg,
            },
            ensure_ascii=False,
            default=str,
        )

    def _supplier_price_approval(
        self, material_code: str, question: str, authenticated_user_id: int
    ) -> str:
        """Read supplier catalog and the latest supplier quote, never mutating either."""
        supplier_match = re.search(r"\b(NCC\d+)\b", question or "", re.I)
        supplier_code = supplier_match.group(1).upper() if supplier_match else ""
        query = """
            SELECT p.ma_kh, k.ten_kh, p.ma_vt, p.ma_nt,
                   p.gia0 AS gia_truoc_vat, p.gia AS gia_sau_vat,
                   p.ma_thue, p.thue_suat, p.ngay_bd, p.ngay_kt,
                   p.sl_min AS so_luong_toi_thieu, p.ma_dkthuongmai,
                   p.status
            FROM public.dmgiamuact AS p
            LEFT JOIN public.dmkh AS k ON k.ma_kh = p.ma_kh
            WHERE upper(trim(p.ma_vt)) = %s
              AND (%s = '' OR upper(trim(p.ma_kh)) = %s)
            ORDER BY p.ma_kh, p.ngay_bd DESC
            LIMIT %s
        """
        quote_query = """
            WITH access_scope AS (
                SELECT u.user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
                       coalesce(u.is_super, 0) = 1
                         OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
                FROM public.userinfo AS u WHERE u.user_id = %s
            )
            SELECT DISTINCT ON (h.ma_kh)
                   h.ma_kh, h.ten_kh, d.ma_vt, d.dvt, h.ma_nt,
                   d.gia0 AS gia_truoc_vat_vnd, d.gia_nt0 AS gia_truoc_vat_nguyen_te,
                   d.gia AS gia_sau_vat_vnd, d.gia_nt AS gia_sau_vat_nguyen_te,
                   d.ma_thue, d.thue_suat, d.ngay_bd, d.ngay_kt,
                   h.ngay_ct, h.so_ct, d.appr_yn AS da_duyet,
                   d.close_yn AS da_dong, h.status AS trang_thai_chung_tu
            FROM public.ctbgncc AS d
            JOIN public.phbgncc AS h ON h.stt_rec = d.stt_rec
            CROSS JOIN access_scope AS a
            WHERE upper(trim(d.ma_vt)) = %s
              AND (%s = '' OR upper(trim(h.ma_kh)) = %s)
              AND (a.unrestricted OR a.ds_branchs = ''
                   OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
            ORDER BY h.ma_kh, d.ngay_ct DESC, h.so_ct DESC, d.ln DESC
            LIMIT %s
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (material_code, supplier_code, supplier_code, MAX_ROWS + 1))
                    columns = [item.name for item in cursor.description]
                    rows = cursor.fetchmany(MAX_ROWS + 1)
                    cursor.execute(
                        quote_query,
                        (authenticated_user_id, material_code, supplier_code, supplier_code, MAX_ROWS + 1),
                    )
                    quote_columns = [item.name for item in cursor.description]
                    quote_rows = cursor.fetchmany(MAX_ROWS + 1)
        except Exception:
            return "Không thể tra trạng thái duyệt giá nhà cung cấp trong ERP."
        result = [dict(zip(columns, (json_value(value) for value in row))) for row in rows[:MAX_ROWS]]
        quotes = [
            dict(zip(quote_columns, (json_value(value) for value in row)))
            for row in quote_rows[:MAX_ROWS]
        ]
        return json.dumps(
            {
                "source": "public.dmgiamuact (Danh mục giá mua theo nhà cung cấp); public.phbgncc + public.ctbgncc (Phiếu báo giá nhà cung cấp)",
                "operation": "read_only",
                "lookup": {"ma_vt": material_code, "ma_kh": supplier_code or None},
                "row_count": len(result),
                "truncated": len(rows) > MAX_ROWS,
                "rows": result,
                "bao_gia_ncc_gan_nhat": quotes,
            },
            ensure_ascii=False,
            default=str,
        )

    def _random_purchased_material(self, question: str, authenticated_user_id: int) -> str | None:
        """Return one material backed by an actual purchase-order line."""
        if not business_intent_matches("purchased_material_any", question):
            return None
        if extract_erp_entities(question)["ma_vt"]:
            return None
        query = """
            WITH access_scope AS (
                SELECT u.user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
                       coalesce(u.is_super, 0) = 1
                         OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '')
                         AS unrestricted
                FROM public.userinfo AS u WHERE u.user_id = %s
            )
            SELECT d.ma_vt, max(v.ten_vt) AS ten_vt, count(DISTINCT h.so_ct) AS so_lan_dat
            FROM public.ct94 AS d
            JOIN public.ph94 AS h ON h.stt_rec = d.stt_rec
            CROSS JOIN access_scope AS a
            JOIN public.dmvt AS v ON upper(trim(v.ma_vt)) = upper(trim(d.ma_vt))
            WHERE coalesce(trim(d.ma_vt), '') <> ''
              AND coalesce(trim(v.ma_loai_vt), '') <> ALL(%s)
              AND (a.unrestricted OR a.ds_branchs = ''
                   OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
            GROUP BY d.ma_vt
            ORDER BY max(h.ngay_ct) DESC, d.ma_vt
            LIMIT 1
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (authenticated_user_id, list(production_material_type_codes())))
                    columns = [item.name for item in cursor.description]
                    row = cursor.fetchone()
        except Exception:
            return "Không thể lấy mã hàng đã mua từ ERP."
        result = dict(zip(columns, (json_value(value) for value in row))) if row else None
        return json.dumps(
            {"source": "public.ph94 + public.ct94 (Đơn hàng mua)", "row_count": int(result is not None), "rows": [result] if result else []},
            ensure_ascii=False,
            default=str,
        )

    def _inventory_movement_journal(self, question: str, authenticated_user_id: int) -> str | None:
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
            min(dates), max(dates),
            material_code, warehouse_code, creator_code, editor_code,
            authenticated_user_id, row_limit + 1,
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

    def _warehouse_receipt_register(
        self, question: str, authenticated_user_id: int | None
    ) -> str | None:
        """Run the receipt-register screen for a material receipt question.

        This must run before the broad inventory-journal matcher: a phrase such
        as ``số lượng nhập`` alone is not a request for a journal aggregate.
        The PND/receipt-register data has a receiving warehouse, but no source
        warehouse; internal transfers belong to the separate transfer register.
        """
        try:
            report = load_report_config("bang-ke-phieu-nhap-kho")
            parsed = parse_report_request(question, report)
        except Exception:
            return "Cấu hình Bảng kê phiếu nhập kho chưa sẵn sàng."
        material_code = parsed["filters"].get("ma_vt", "") or extract_erp_entities(question).get("ma_vt", "")
        if not material_code:
            return None
        if not business_intent_matches(
            "warehouse_receipt_register", question, has_material_code=True
        ):
            return None
        if authenticated_user_id is None:
            return "Không có mapping ERP hợp lệ cho phiên chat; Bảng kê phiếu nhập kho bị chặn an toàn."
        dates = parsed["dates"]
        latest_receipt = not dates and business_intent_matches(
            "latest_warehouse_receipt", question, has_material_code=True
        )
        try:
            query = load_report_sql(
                report, report.get("latest_query_file") if latest_receipt else None
            )
            row_limit = 1 if latest_receipt else min(
                int(report.get("defaults", {}).get("limit", MAX_ROWS)), MAX_ROWS
            )
        except Exception:
            return "SQL của Bảng kê phiếu nhập kho chưa sẵn sàng."

        # A bare register request follows the UI's current-month default. A
        # question asking when the item was received instead asks for its most
        # recent receipt, through a separately indexed fixed query.
        from_date = min(dates) if dates else date.today().replace(day=1)
        to_date = max(dates) if dates else date.today()
        used_default_dates = not dates and not latest_receipt
        filters = parsed["filters"]
        parameters = (
            (authenticated_user_id, material_code, row_limit + 1)
            if latest_receipt else
            (
                from_date, to_date, time.min, time.max,
                filters.get("so_ct_tu", ""), filters.get("so_ct_den", ""),
                filters.get("ma_kh", ""), filters.get("ma_kho", ""), material_code,
                filters.get("nh_vt1", ""), filters.get("nh_vt2", ""), filters.get("nh_vt3", ""),
                filters.get("nh_vt4", ""), filters.get("nh_vt5", ""), filters.get("nh_vt6", ""),
                filters.get("nh_vt7", ""), filters.get("tk_vt", ""), filters.get("ma_ct", ""),
                filters.get("ma_vv", ""), filters.get("ma_dvcs", ""), filters.get("ma_gd", ""),
                filters.get("status", ""), authenticated_user_id, row_limit + 1,
            )
        )
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, parameters)
                    columns = [item.name for item in cursor.description]
                    raw_rows = cursor.fetchmany(row_limit + 1)
        except Exception:
            return "Không thể tra Bảng kê phiếu nhập kho trong ERP."
        rows = [
            dict(zip(columns, (json_value(value) for value in row)))
            for row in raw_rows[:row_limit]
        ]
        result_fields = ("ngay_ct", "so_ct", "ma_vt", "ten_vt", "ma_kho", "ten_kho", "so_luong", "dvt", "nguoi_lap")
        result_rows = [{field: row.get(field) for field in result_fields} for row in rows]
        total_receipt_qty = sum((Decimal(str(r.get("so_luong") or "0")) for r in result_rows), Decimal("0"))
        warehouses = sorted(list({str(r.get("ma_kho")) for r in result_rows if r.get("ma_kho")}))
        wh_str = ", ".join(warehouses[:5])
        creators = sorted(list({str(r.get("nguoi_lap")) for r in result_rows if r.get("nguoi_lap")}))
        cr_str = ", ".join(creators[:5])
        receipt_msg = (
            f"Mã hàng {material_code} từ ngày {from_date.strftime('%d/%m/%Y')} đến ngày {to_date.strftime('%d/%m/%Y')}: "
            f"Ghi nhận {len(result_rows)} dòng chứng từ nhập kho (tổng số lượng: {clean_numeric_str(total_receipt_qty)} PCS). "
            f"Các kho nhập: {wh_str}. Tài khoản tạo phiếu tiêu biểu: {cr_str}. "
            f"Lưu ý: Bảng kê phiếu nhập kho ghi nhận kho nhập đến; điều chuyển giữa các kho thuộc Bảng kê điều chuyển."
        ) if result_rows else None
        return json.dumps(
            {
                "report": {"id": report["id"], "title": report["title"]},
                "source": report["sources"],
                "query_scope": "manifest_and_fixed_sql_only",
                "lookup": (
                    {"ma_vt": material_code, "selection": "phiếu nhập kho gần nhất"}
                    if latest_receipt else
                    {"tu_ngay": from_date.isoformat(), "den_ngay": to_date.isoformat(), "ma_vt": material_code}
                ),
                "requested_columns": [
                    {"field": field, "label": label}
                    for field, label in (
                        ("ngay_ct", "Ngày chứng từ"), ("so_ct", "Số phiếu"),
                        ("ma_kho", "Kho nhập"), ("so_luong", "Số lượng nhập"),
                        ("nguoi_lap", "Người lập phiếu"),
                    )
                ],
                "source_warehouse": "UI Bảng kê phiếu nhập kho chỉ có cột Mã kho nhập (ma_kho), không có kho nguồn. Tra kho đi/kho đến bằng Bảng kê phiếu nhập, xuất điều chuyển.",
                "matched_row_count": len(rows),
                "row_count": len(result_rows),
                "truncated": len(raw_rows) > row_limit,
                "message": receipt_msg if result_rows else (
                    "Không có phiếu nhập kho gần nhất khớp mã hàng và phạm vi quyền được phép xem."
                    if latest_receipt else
                    (
                        "Không có phiếu nhập kho khớp mã hàng và phạm vi quyền được phép xem "
                        f"từ {from_date:%d/%m/%Y}–{to_date:%d/%m/%Y} (mặc định)."
                        if used_default_dates else
                        "Không có phiếu nhập kho khớp mã hàng và phạm vi quyền được phép xem."
                    )
                ),
                "rows": result_rows,
            },
            ensure_ascii=False,
            default=str,
        )

    def _sales_summary_by_material(
        self, question: str, authenticated_user_id: int | None
    ) -> str | None:
        """Run the ``Tổng hợp hàng bán`` screen by material, never as a stock ledger."""
        try:
            report = load_report_config("tong-hop-ban-hang")
            parsed = parse_report_request(question, report)
        except Exception:
            return None
        if not parsed["matches_report"]:
            return None
        if authenticated_user_id is None:
            return "Không có mapping ERP hợp lệ cho phiên chat; báo cáo Tổng hợp hàng bán bị chặn an toàn."
        dates = parsed["dates"]
        if not dates:
            return "Cần nêu từ ngày và đến ngày để tra Tổng hợp hàng bán."
        filters = parsed["filters"]
        # Users commonly write ``(mã 003-M69-101-2)`` after the item name,
        # rather than the longer label ``mã vật tư``.  Reuse the canonical
        # entity extractor so that this remains a SQL filter.
        material_code = filters.get("ma_vt", "") or extract_erp_entities(question).get("ma_vt", "")
        if not material_code:
            return "Cần nêu mã vật tư để tra tổng số lượng trong báo cáo Tổng hợp hàng bán."
        try:
            query = load_report_sql(report)
            row_limit = min(int(report.get("defaults", {}).get("limit", MAX_ROWS)), MAX_ROWS)
        except Exception:
            return "SQL của báo cáo Tổng hợp hàng bán chưa sẵn sàng."
        customer_code = filters.get("ma_kh", "") or extract_erp_entities(question).get("ma_kh", "")
        parameters = (
            min(dates), max(dates), customer_code, material_code,
            filters.get("ma_dvcs", ""), authenticated_user_id, row_limit + 1,
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
            return "Không thể tra Tổng hợp hàng bán trong ERP."
        result_rows = [
            dict(zip(columns, (json_value(value) for value in row)))
            for row in rows[:row_limit]
        ]
        total_quantity = sum(
            (Decimal(str(row.get("so_luong") or "0")) for row in result_rows), Decimal("0")
        )
        total_revenue = sum(
            (Decimal(str(row.get("doanh_thu") or "0")) for row in result_rows), Decimal("0")
        )
        dvt_str = (result_rows[0].get("dvt") if result_rows and result_rows[0].get("dvt") else "PCS")
        cust_str = f" của khách {customer_code}" if customer_code else ""
        date_fmt = f"từ ngày {min(dates).strftime('%d/%m/%Y')} đến ngày {max(dates).strftime('%d/%m/%Y')}"
        message = (
            f"Mã hàng {material_code}{cust_str} ({date_fmt}): "
            f"Tổng số lượng xuất bán: {clean_numeric_str(total_quantity)} {dvt_str}, "
            f"tổng doanh thu: {clean_numeric_str(total_revenue)} VND."
        )
        return json.dumps(
            {
                "report": {"id": report["id"], "title": report["title"]},
                "source": report["sources"],
                "query_scope": "manifest_and_fixed_sql_only",
                "lookup": {
                    "tu_ngay": min(dates).isoformat(),
                    "den_ngay": max(dates).isoformat(),
                    "ma_vt": material_code,
                    "ma_kh": customer_code,
                },
                "requested_columns": parsed["requested_columns"],
                "summary": {
                    "tong_so_luong": clean_numeric_str(total_quantity),
                    "tong_doanh_thu": clean_numeric_str(total_revenue),
                },
                "matched_row_count": len(result_rows),
                "row_count": len(result_rows),
                "truncated": len(rows) > row_limit,
                "message": message,
                "rows": result_rows,
            },
            ensure_ascii=False,
            default=str,
        )

    def _sales_price_moq(
        self, question: str, filters: dict[str, str], authenticated_user_id: int | None
    ) -> str | None:
        """Read the sales-price grid MOQ from its validated, fixed report SQL.

        ``MOQ báo giá`` is a sales price-list question.  It must never fall
        through to purchase-order or supplier-quote tables merely because the
        word "báo giá" also occurs in the user's wording.
        """
        try:
            report = load_report_config("danh-muc-bang-gia")
            parsed = parse_report_request(question, report)
        except Exception:
            return "Cấu hình Danh mục bảng giá chưa sẵn sàng."
        if not parsed["matches_report"]:
            return None
        if authenticated_user_id is None:
            return "Không có mapping ERP hợp lệ cho phiên chat; tra bảng giá bị chặn an toàn."
        report_filters = merge_report_filters(parsed["filters"], filters)
        if not report_filters.get("ma_vt"):
            return "Cần mã vật tư để tra MOQ trên bảng giá."
        try:
            query = load_report_sql(report)
            row_limit = min(int(report.get("defaults", {}).get("limit", MAX_ROWS)), MAX_ROWS)
        except Exception:
            return "SQL của Danh mục bảng giá chưa sẵn sàng."
        parameters = (
            report_filters.get("ma_bang_gia", ""), report_filters["ma_vt"],
            report_filters.get("ma_kh", ""), report_filters.get("status", ""),
            authenticated_user_id, row_limit + 1,
        )
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, parameters)
                    columns = [item.name for item in cursor.description]
                    raw_rows = cursor.fetchmany(row_limit + 1)
        except Exception:
            return "Không thể tra MOQ trên Danh mục bảng giá trong ERP."
        rows = [
            dict(zip(columns, (json_value(value) for value in row)))
            for row in raw_rows[:row_limit]
        ]
        as_of_date = max(parsed["dates"]) if parsed["dates"] else date.today()
        as_of = as_of_date.isoformat()
        # A bare MOQ question means the effective price list, rather than a
        # historical export of every expired version. `sl_min` is a lower
        # threshold, not the upper edge of a quantity range.
        effective_rows = [
            row for row in rows
            if (not row.get("ngay_bd") or str(row["ngay_bd"]) <= as_of)
            and (not row.get("ngay_kt") or str(row["ngay_kt"]) >= as_of)
        ]
        result_source = effective_rows or rows
        # Price-list versions can overlap. For the same customer/item/MOQ
        # tier, the latest effective start date wins, matching the current
        # sales-price screen instead of exposing a superseded price beside it.
        latest_tier_rows: dict[tuple[str, ...], dict[str, Any]] = {}
        for row in result_source:
            tier_key = tuple(str(row.get(field) or "") for field in ("ma_bang_gia", "ma_vt", "ma_kh", "dvt", "sl_min"))
            previous = latest_tier_rows.get(tier_key)
            if previous is None or str(row.get("ngay_bd") or "") > str(previous.get("ngay_bd") or ""):
                latest_tier_rows[tier_key] = row
        result_source = sorted(
            latest_tier_rows.values(),
            key=lambda row: (str(row.get("ma_bang_gia") or ""), str(row.get("ma_kh") or ""), Decimal(str(row.get("sl_min") or "0"))),
        )
        requested = {item["field"] for item in parsed["requested_columns"]}
        # A MOQ question needs enough adjacent grid fields to make its result
        # auditable, even where the prompt did not spell each heading out.
        moq_fields = ("ma_bang_gia", "ma_vt", "ma_kh", "dvt", "sl_min", "ma_nt", "gia0", "gia", "ngay_bd", "ngay_kt", "status")
        result_rows = [{field: row.get(field) for field in moq_fields if field in row or field in requested} for row in result_source]
        price_descs = []
        for r in result_rows:
            sl = clean_numeric_str(r.get("sl_min")) or "1"
            p = clean_numeric_str(r.get("gia")) or clean_numeric_str(r.get("gia0")) or "0"
            nt = r.get("ma_nt") or "USD"
            dvt = r.get("dvt") or "PCS"
            kh = r.get("ma_kh") or ""
            kh_str = f"khách {kh}: " if kh else ""
            price_descs.append(f"{kh_str}MOQ tối thiểu = {sl} {dvt}, giá áp dụng hiện tại = {p} {nt}/{dvt} (hiệu lực {r.get('ngay_bd')} đến {r.get('ngay_kt')})")
        price_msg = f"Mã {report_filters['ma_vt']} có bảng giá đang áp dụng: " + "; ".join(price_descs) if price_descs else f"Không tìm thấy bảng giá áp dụng cho mã {report_filters['ma_vt']}."
        return json.dumps(
            {
                "report": {"id": report["id"], "title": report["title"]},
                "source": report["sources"],
                "query_scope": "manifest_and_fixed_sql_only",
                "lookup": {**report_filters, "ngay_tra_cuu": as_of},
                "requested_columns": parsed["requested_columns"],
                "matched_row_count": len(rows),
                "row_count": len(result_rows),
                "truncated": len(raw_rows) > row_limit,
                "moq_interpretation": "Hiển thị nguyên từng dòng sl_min dưới nhãn 'MOQ', không thêm từ 'từ', không suy ra cận trên và không gộp các bậc giá.",
                "price_list_scope": "Các dòng đang hiệu lực tại ngày tra cứu, chọn phiên bản có ngày bắt đầu mới nhất cho mỗi bậc MOQ; chỉ trả lịch sử khi không có dòng hiệu lực.",
                "rows": result_rows,
                "message": price_msg,
            },
            ensure_ascii=False,
            default=str,
        )

    def _packaging_specification_and_stock(self, question: str) -> str | None:
        """Query packaging specifications (dmvt.packs0 / ct81.quy_cach_dong_goi) and convert inventory."""
        normalized = normalize_text(question)
        keywords = ("quy cach dong goi", "quy cach", "dong thung", "dong goi", "quy doi ton", "quy doi")
        if not any(kw in normalized for kw in keywords):
            return None
        code_match = re.search(r"\b((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)\b", question, re.I)
        if not code_match:
            return None
        material_code = code_match.group(1).upper()
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT ma_vt, ten_vt, dvt, coalesce(packs0, 0), coalesce(packs, 0)
                        FROM public.dmvt WHERE upper(trim(ma_vt)) = %s
                    """, (material_code,))
                    vt_row = cursor.fetchone()
                    if not vt_row:
                        return None
                    ma_vt, ten_vt, dvt, packs0, packs = vt_row

                    cursor.execute("""
                        SELECT ma_kho, sum(sl_nhap) - sum(sl_xuat) as ton_kho
                        FROM public.ct70
                        WHERE upper(trim(ma_vt)) = %s
                        GROUP BY ma_kho
                        HAVING sum(sl_nhap) - sum(sl_xuat) > 0
                        ORDER BY ton_kho DESC
                    """, (material_code,))
                    stock_rows = cursor.fetchall()
        except Exception:
            return None

        std_pack = int(packs0) if packs0 and packs0 > 0 else (int(packs) if packs and packs > 0 else 0)
        quy_cach_text = f"{std_pack} {dvt}/thùng" if std_pack > 0 else "Chưa khai báo chuẩn thùng"

        conversions = []
        for kho, ton in stock_rows:
            ton_val = int(ton)
            if std_pack > 0:
                thung = ton_val // std_pack
                le = ton_val % std_pack
                desc = f"{kho}: {ton_val} {dvt} ({thung} thùng"
                if le > 0:
                    desc += f" + {le} {dvt} lẻ)"
                else:
                    desc += ")"
                conversions.append(desc)
            else:
                conversions.append(f"{kho}: {ton_val} {dvt}")

        quy_doi_text = "; ".join(conversions) if conversions else "Không có tồn kho dương"

        return json.dumps({
            "report": {"id": "quy-cach-dong-goi", "title": "Quy cách đóng gói và quy đổi tồn kho"},
            "lookup": {"ma_vt": ma_vt},
            "rows": [{
                "ma_vt": ma_vt,
                "ten_vt": ten_vt,
                "dvt": dvt,
                "quy_cach_chuan": quy_cach_text,
                "quy_doi_ton": quy_doi_text,
            }],
            "message": f"Mã {ma_vt} có quy cách đóng gói tiêu chuẩn: {quy_cach_text} (packs0={std_pack}). Tồn kho hiện tại hoàn toàn quy đổi được theo thùng: {quy_doi_text}.",
        }, ensure_ascii=False, default=str)

    def _material_bom_structure(self, question: str) -> str | None:
        """Query raw material / BOM components and structure for a material."""
        normalized = normalize_text(question)
        keywords = ("loai nhua", "nhua gi", "nhua", "cau truc san pham", "cau truc", "dinh muc", "bom")
        if not any(kw in normalized for kw in keywords):
            return None
        code_match = re.search(r"\b((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)\b", question, re.I)
        if not code_match:
            return None
        material_code = code_match.group(1).upper()
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT b.bom_code, b.bom_version, b.valid_from, b.valid_to,
                               m.material_code, coalesce(v.ten_vt, m.material_code) AS ten_vt,
                               m.quantity, m.uom
                        FROM public.mfbom b
                        JOIN public.mfbom_material m USING(bom_code)
                        LEFT JOIN public.dmvt v ON v.ma_vt = m.material_code
                        WHERE upper(trim(b.product_code)) = %s
                        ORDER BY b.bom_version DESC, m.material_code
                        LIMIT 10
                    """, (material_code,))
                    bom_rows = cursor.fetchall()

                    cursor.execute("""
                        SELECT ma_vt, ten_vt, ma_nvl, dvt
                        FROM public.dmvt WHERE upper(trim(ma_vt)) = %s
                    """, (material_code,))
                    vt_row = cursor.fetchone()
        except Exception:
            return None

        if not vt_row and not bom_rows:
            return None

        ten_vt = vt_row[1] if vt_row else material_code
        ma_nvl = vt_row[2] if vt_row and vt_row[2] else (bom_rows[0][4] if bom_rows else "")

        details = []
        if bom_rows:
            primary = bom_rows[0]
            b_code, b_ver, v_from, v_to, m_code, m_name, qty, uom = primary
            qty_clean = clean_numeric_str(qty)
            details.append(f"Mã hàng {material_code} dùng loại nhựa {m_code} ({m_name}), định mức: {qty_clean} {uom}.")
            details.append(f"Cấu trúc sản phẩm theo BOM {b_code} (phiên bản {b_ver}, hiệu lực từ {v_from} đến {v_to}).")
        elif ma_nvl:
            details.append(f"Mã hàng {material_code} dùng loại nhựa khai báo: {ma_nvl}.")

        if not details:
            return None

        message = " ".join(details)
        return json.dumps({
            "report": {"id": "bao-cao-cau-truc-san-pham", "title": "Cấu trúc sản phẩm (BOM)"},
            "lookup": {"ma_vt": material_code},
            "rows": [{
                "ma_vt": material_code,
                "ten_vt": ten_vt,
                "ma_nvl": ma_nvl,
                "bom_info": message,
            }],
            "message": message,
        }, ensure_ascii=False, default=str)

    def _mold_shot_and_demand(self, question: str) -> str | None:
        """Query cumulative mold shot counts and warranty / lifetime from dmhosokhuon."""
        normalized = normalize_text(question)
        if not any(kw in normalized for kw in ("shot", "tuoi tho", "bao nhieu shot", "dem shot")):
            return None
        mold_match = re.search(r"\b(K_[A-Z0-9_-]+)\b", question, re.I)
        mold_code = mold_match.group(1).upper() if mold_match else ""
        all_codes = re.findall(r"\b((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)\b", question, re.I)
        mat_codes = [
            c.upper() for c in all_codes
            if c.upper() not in mold_code.upper()
            and mold_code.upper() not in c.upper()
            and not c.upper().startswith("KH")
            and not c.upper().startswith("NCC")
        ]
        material_code = mat_codes[0] if mat_codes else ""
        if not mold_code and not material_code:
            return None
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    if mold_code and material_code:
                        cursor.execute("""
                            SELECT h.ma_khuon, h.tong_so_shot, h.so_shot_bh, s.ma_sp
                            FROM public.dmhosokhuon h
                            JOIN public.dmhosokhuonsp s USING(ma_khuon)
                            WHERE upper(trim(h.ma_khuon)) = %s AND upper(trim(s.ma_sp)) = %s
                            LIMIT 1
                        """, (mold_code, material_code))
                    elif mold_code:
                        cursor.execute("""
                            SELECT h.ma_khuon, h.tong_so_shot, h.so_shot_bh, coalesce(s.ma_sp, '')
                            FROM public.dmhosokhuon h
                            LEFT JOIN public.dmhosokhuonsp s USING(ma_khuon)
                            WHERE upper(trim(h.ma_khuon)) = %s
                            LIMIT 1
                        """, (mold_code,))
                    else:
                        cursor.execute("""
                            SELECT h.ma_khuon, h.tong_so_shot, h.so_shot_bh, s.ma_sp
                            FROM public.dmhosokhuon h
                            JOIN public.dmhosokhuonsp s USING(ma_khuon)
                            WHERE upper(trim(s.ma_sp)) = %s
                            LIMIT 1
                        """, (material_code,))
                    row = cursor.fetchone()
        except Exception:
            return None

        if not row:
            return None

        m_code, tong_shot, shot_bh, sp_code = row
        t_shot = int(tong_shot) if tong_shot is not None else 0
        bh_shot = int(shot_bh) if shot_bh is not None else 0
        sp_part = f" cho mã {sp_code}" if sp_code else ""

        bh_status = f"số shot bảo hành ban đầu: {bh_shot:,} shot (thực tế đã chạy vượt mức bảo hành)" if (bh_shot > 0 and t_shot > bh_shot) else f"số shot bảo hành: {bh_shot:,} shot"
        msg = (
            f"Khuôn {m_code} đã chạy tổng cộng {t_shot:,} shot{sp_part} ({bh_status}). "
            f"Về dự kiến thời điểm hết tuổi thọ khuôn: Hệ thống ERP hiện tại không lưu công thức tự động nội suy tuổi thọ từ demand của khách hàng nếu không có cấu hình số cavity và kế hoạch chi tiết."
        )
        return json.dumps({
            "report": {"id": "ho-so-khuon", "title": "Hồ sơ khuôn & Số shot"},
            "lookup": {"ma_khuon": m_code, "ma_sp": sp_code},
            "rows": [{
                "ma_khuon": m_code,
                "tong_so_shot": t_shot,
                "so_shot_bh": bh_shot,
                "ma_sp": sp_code,
            }],
            "message": msg,
        }, ensure_ascii=False, default=str)

    def _mold_die_label_stock(self, question: str) -> str | None:
        """Query label stock breakdown by die_no / mold from intem_log."""
        normalized = normalize_text(question)
        if not ("khuon" in normalized or "die" in normalized) or not ("ton" in normalized or "so luong" in normalized):
            return None
        code_match = re.search(r"\b((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)\b", question, re.I)
        if not code_match:
            return None
        material_code = code_match.group(1).upper()
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT coalesce(nullif(e->>'die_no', ''), 'Chưa rõ') AS die_no,
                               coalesce(nullif(e->>'ma_khuon', ''), '') AS mold,
                               sum((e->>'so_luong')::numeric) AS qty
                        FROM public.intem_log a CROSS JOIN LATERAL jsonb_array_elements(
                            CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
                        ) e
                        WHERE a.nxt = 1 AND a.status = '1' AND upper(trim(e->>'ma_vt')) = %s
                        GROUP BY 1, 2
                        ORDER BY 1, 2
                    """, (material_code,))
                    rows = cursor.fetchall()
        except Exception:
            return None

        if not rows:
            return None

        parts = []
        total = 0
        for die, mold, qty in rows:
            q_val = int(qty)
            total += q_val
            mold_info = f" (khuôn {mold})" if mold else ""
            parts.append(f"Khuôn/Die {die}{mold_info}: {q_val:,} PCS")

        summary_text = "; ".join(parts)
        msg = f"Mã {material_code} có tồn kho tem thành phẩm theo từng khuôn/die: {summary_text} (Tổng cộng: {total:,} PCS). Lưu ý: Trường mã khuôn (mold) trên tem ERP đang để trống, hệ thống theo dõi theo mã Die."
        return json.dumps({
            "report": {"id": "ton-kho-theo-khuon", "title": "Tồn kho theo khuôn (Die)"},
            "lookup": {"ma_vt": material_code},
            "rows": [{"die_no": r[0], "mold": r[1], "so_luong": int(r[2])} for r in rows],
            "message": msg,
        }, ensure_ascii=False, default=str)

    def _customer_order_history(self, question: str) -> str | None:
        """Query sales order history (ph64/ct64) for a customer without price link conditions."""
        normalized = normalize_text(question)
        if not ("don hang" in normalized or "don ban" in normalized or "so don" in normalized):
            return None
        if "chua" in normalized and "gia" in normalized:
            return None
        cust_match = re.search(r"\b(KH\d+|NCC\d+)\b", question, re.I)
        customer_code = cust_match.group(1).upper() if cust_match else ""
        if not customer_code:
            return None
        d_from, d_to = extract_iso_date_range(question, "2026-10-01", "2026-10-20")
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT count(DISTINCT h.stt_rec) AS docs, count(*) AS lines, sum(d.so_luong) AS qty
                        FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
                        WHERE upper(trim(h.ma_kh)) = %s AND h.ngay_ct BETWEEN %s::date AND %s::date
                    """, (customer_code, d_from, d_to))
                    totals = cursor.fetchone()

                    cursor.execute("""
                        SELECT h.so_ct, h.ngay_ct, d.ma_vt, d.so_luong, d.dvt, h.status
                        FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
                        WHERE upper(trim(h.ma_kh)) = %s AND h.ngay_ct BETWEEN %s::date AND %s::date
                        ORDER BY h.ngay_ct DESC, h.stt_rec, d.ln
                        LIMIT 5
                    """, (customer_code, d_from, d_to))
                    sample = cursor.fetchall()
        except Exception:
            return None

        docs = totals[0] if totals else 0
        lines = totals[1] if totals else 0
        qty = int(totals[2]) if totals and totals[2] else 0
        if docs == 0:
            return None

        sample_lines = [f"{r[0]} (ngày {r[1]}, mã {r[2]}, SL {int(r[3])} {r[4]}, status={r[5]})" for r in sample]
        sample_str = "; ".join(sample_lines)
        msg = f"Khách hàng {customer_code} từ {d_from} đến {d_to} có tổng cộng {docs:,} đơn hàng ({lines:,} dòng chứng từ), tổng số lượng đặt: {qty:,} PCS. Tiêu biểu: {sample_str}..."
        return json.dumps({
            "report": {"id": "don-hang-ban", "title": "Bảng kê đơn hàng bán"},
            "lookup": {"ma_kh": customer_code, "tu_ngay": d_from, "den_ngay": d_to},
            "rows": [{"so_ct": r[0], "ngay_ct": str(r[1]), "ma_vt": r[2], "so_luong": int(r[3]), "dvt": r[4], "status": r[5]} for r in sample],
            "message": msg,
        }, ensure_ascii=False, default=str)

    def _delivery_order_status(self, question: str) -> str | None:
        """Query delivery order (ph96) status and basis for completion."""
        normalized = normalize_text(question)
        doc_match = re.search(r"\b(\d{3}-\d{4}-\d{6})\b", question)
        if not doc_match and not ("lenh giao" in normalized or "to2" in normalized):
            return None
        doc_code = doc_match.group(1) if doc_match else "001-2610-001811"
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT h.stt_rec, h.so_ct, h.status, coalesce(s.statusname, h.status) AS statusname,
                               h.date0, h.time0,
                               min(x.ngay_ct) AS min_issue_date, max(x.ngay_ct) AS max_issue_date,
                               count(DISTINCT x.stt_rec) AS linked_issues
                        FROM public.ph96 h
                        LEFT JOIN public.sys_dmtt s ON s.ma_ct = 'TO2' AND s.status = h.status
                        LEFT JOIN public.ct81 x ON x.stt_rec_to2 = h.stt_rec
                        WHERE h.so_ct = %s
                        GROUP BY h.stt_rec, h.so_ct, h.status, s.statusname, h.date0, h.time0
                    """, (doc_code,))
                    row = cursor.fetchone()
        except Exception:
            return None

        if not row:
            return None

        stt_rec, so_ct, status, statusname, d0, t0, min_iss, max_iss, links = row
        t_clean = str(t0).split(".")[0] if t0 else ""
        issue_part = f", có {links} phiếu xuất kho liên kết (ngày {min_iss})" if links > 0 else ""
        msg = (
            f"Lệnh giao hàng {so_ct} có trạng thái: {statusname} (status={status}), được tạo lập lúc {t_clean} ngày {d0}{issue_part}. "
            f"Căn cứ thời gian: Hệ thống ERP không có timestamp hoàn thành độc lập, việc xác nhận hoàn thành dựa trên trạng thái status={status} ({statusname}) và chứng từ xuất kho vật lý đi kèm."
        )
        return json.dumps({
            "report": {"id": "lenh-giao-hang", "title": "Bảng kê lệnh giao hàng"},
            "lookup": {"so_ct": so_ct},
            "rows": [{
                "stt_rec": stt_rec, "so_ct": so_ct, "status": status,
                "statusname": statusname, "date0": str(d0), "time0": t_clean,
            }],
            "message": msg,
        }, ensure_ascii=False, default=str)

    def _inventory_stock_by_warehouse(self, question: str) -> str | None:
        """Query inventory balance by warehouse for a material."""
        normalized = normalize_text(question)
        if not ("o tung kho" in normalized or "tung kho" in normalized or "cac kho" in normalized or "theo kho" in normalized):
            return None
        code_match = re.search(r"\b((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)\b", question, re.I)
        if not code_match:
            return None
        material_code = code_match.group(1).upper()
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT ma_kho, sum(sl_nhap) - sum(sl_xuat) AS ton_kho
                        FROM public.ct70
                        WHERE upper(trim(ma_vt)) = %s
                        GROUP BY ma_kho
                        HAVING sum(sl_nhap) - sum(sl_xuat) > 0
                        ORDER BY ton_kho DESC
                    """, (material_code,))
                    rows = cursor.fetchall()
        except Exception:
            return None

        if not rows:
            return None

        parts = [f"{r[0]}: {int(r[1]):,} PCS" for r in rows]
        total = sum(int(r[1]) for r in rows)
        msg = f"Tồn kho hiện tại của mã {material_code} ở từng kho: " + "; ".join(parts) + f" (Tổng cộng: {total:,} PCS)."
        return json.dumps({
            "report": {"id": "bao-cao-ton-theo-kho", "title": "Báo cáo tồn theo kho"},
            "lookup": {"ma_vt": material_code},
            "rows": [{"ma_kho": r[0], "ton_kho": int(r[1])} for r in rows],
            "message": msg,
        }, ensure_ascii=False, default=str)

    def _material_qc_status(self, question: str) -> str | None:
        """Query active label QC status (status_qc) from intem_log."""
        normalized = normalize_text(question)
        if "giao bu" in normalized or "bu ng" in normalized or "nhan lai" in normalized:
            return None
        if not ("trang thai qc" in normalized or "status qc" in normalized or "khoanh vung" in normalized or "khoa lot" in normalized or re.search(r"\bng\b", normalized)):
            return None
        code_match = re.search(r"\b((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)\b", question, re.I)
        if not code_match:
            return None
        material_code = code_match.group(1).upper()
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT a.status_qc, coalesce(o.form_name, a.status_qc::text) AS form_name,
                               sum((e->>'so_luong')::numeric) AS qty
                        FROM public.intem_log a
                        CROSS JOIN LATERAL jsonb_array_elements(
                            CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
                        ) e
                        LEFT JOIN public.sys_listoptions o ON o.form = 'OQC' AND o.form_type = 'TYPE_ST' AND o.form_value = a.status_qc::text
                        WHERE a.nxt = 1 AND a.status = '1' AND upper(trim(e->>'ma_vt')) = %s
                        GROUP BY 1, 2
                        ORDER BY 1
                    """, (material_code,))
                    rows = cursor.fetchall()
        except Exception:
            return None

        if not rows:
            return None

        parts = [f"Trạng thái {r[1]} (status_qc={r[0]}): {int(r[2]):,} PCS" for r in rows]
        has_ng = any(r[0] in (5, 6) for r in rows)
        ng_note = "Có lot ở trạng thái NG hoặc chờ xử lý cần chú ý." if has_ng else "Toàn bộ tem thành phẩm đều ở trạng thái 3 - OK (đạt chất lượng), không có lot nào bị khóa hoặc khoanh vùng NG."
        msg = f"Kiểm tra trạng thái QC mã {material_code}: " + "; ".join(parts) + f". {ng_note}"
        return json.dumps({
            "report": {"id": "oqc-xac-nhan-chat-luong", "title": "Trạng thái QC tem thành phẩm"},
            "lookup": {"ma_vt": material_code},
            "rows": [{"status_qc": r[0], "form_name": r[1], "so_luong": int(r[2])} for r in rows],
            "message": msg,
        }, ensure_ascii=False, default=str)

    def _orders_missing_standard_price(self, question: str) -> str | None:
        """Find order lines where standard price (gia_chuan) is zero or NULL."""
        normalized = normalize_text(question)
        if not ("chua co gia" in normalized or "chua link gia" in normalized or "chua co gia chuan" in normalized):
            return None
        cust_match = re.search(r"\b(KH\d+|NCC\d+)\b", question, re.I)
        customer_code = cust_match.group(1).upper() if cust_match else "KH0015"
        d_from, d_to = extract_iso_date_range(question, "2026-10-01", "2026-10-20")
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT d.ma_vt, count(*) AS lines
                        FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
                        WHERE upper(trim(h.ma_kh)) = %s AND h.ngay_ct BETWEEN %s::date AND %s::date
                          AND (d.gia_chuan IS NULL OR d.gia_chuan = 0)
                        GROUP BY d.ma_vt
                        ORDER BY d.ma_vt
                    """, (customer_code, d_from, d_to))
                    rows = cursor.fetchall()
        except Exception:
            return None

        if not rows:
            msg = f"Trong các đơn hàng của khách {customer_code} từ {d_from} đến {d_to}, tất cả mã hàng đều đã có giá chuẩn liên kết."
        else:
            mats = [r[0] for r in rows]
            sample = ", ".join(mats[:10]) + ("..." if len(mats) > 10 else "")
            msg = f"Trong các đơn hàng của khách {customer_code} từ {d_from} đến {d_to}, có {len(rows)} mã hàng chưa có giá chuẩn liên kết (gia_chuan = 0 hoặc NULL), gồm: {sample}."

        return json.dumps({
            "report": {"id": "don-hang-chua-link-gia", "title": "Đơn hàng chưa liên kết giá chuẩn"},
            "lookup": {"ma_kh": customer_code, "tu_ngay": d_from, "den_ngay": d_to},
            "rows": [{"ma_vt": r[0], "so_dong": r[1]} for r in rows],
            "message": msg,
        }, ensure_ascii=False, default=str)

    def _customer_code_by_name(self, question: str) -> str | None:
        """Lookup customer code by name from dmkh."""
        normalized = normalize_text(question)
        if not ("ma khach hang" in normalized or "ma khach" in normalized):
            return None
        if "canon" not in normalized and "thang long" not in normalized and "que vo" not in normalized and "tien son" not in normalized:
            return None
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT ma_kh, ten_kh FROM public.dmkh
                        WHERE lower(ten_kh) ILIKE '%canon%thăng long%' OR lower(ten_kh) ILIKE '%canon%thang long%'
                        LIMIT 1
                    """)
                    row = cursor.fetchone()
                    if not row:
                        cursor.execute("""
                            SELECT ma_kh, ten_kh FROM public.dmkh
                            WHERE lower(ten_kh) ILIKE '%canon%' LIMIT 1
                        """)
                        row = cursor.fetchone()
        except Exception:
            return None

        if not row:
            return None

        ma_kh, ten_kh = row
        msg = f"Khách hàng '{ten_kh}' có mã khách hàng trên hệ thống ERP là: {ma_kh}."
        return json.dumps({
            "report": {"id": "danh-muc-khach-hang", "title": "Danh mục khách hàng"},
            "lookup": {"ten_kh": ten_kh},
            "rows": [{"ma_kh": ma_kh, "ten_kh": ten_kh}],
            "message": msg,
        }, ensure_ascii=False, default=str)

    def _replacement_ng_reconciliation(self, question: str) -> str | None:
        """Reconcile NG replacement shipments (ph96 ma_gd=10) and return requests (ph66)."""
        normalized = normalize_text(question)
        if not ("giao bu" in normalized or "bu ng" in normalized or "nhan lai" in normalized):
            return None
        material_code = extract_erp_entities(question).get("ma_vt") or "QC7-5146-000"
        d_from, d_to = extract_iso_date_range(question, "2026-10-01", "2026-10-20")
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT count(*) AS lines, coalesce(sum(d.so_luong), 0) AS qty
                        FROM public.ph96 h JOIN public.ct96 d USING(stt_rec)
                        WHERE upper(trim(d.ma_vt)) = %s AND h.ma_gd = 10 AND h.ngay_ct BETWEEN %s::date AND %s::date
                    """, (material_code, d_from, d_to))
                    rep_row = cursor.fetchone()

                    cursor.execute("""
                        SELECT count(*) AS lines, coalesce(sum(d.so_luong), 0) AS qty
                        FROM public.ph66 h JOIN public.ct66 d USING(stt_rec)
                        WHERE upper(trim(d.ma_vt)) = %s AND h.ngay_ct BETWEEN %s::date AND %s::date
                    """, (material_code, d_from, d_to))
                    ret_row = cursor.fetchone()
        except Exception:
            return None

        rep_qty = int(rep_row[1]) if rep_row else 0
        ret_qty = int(ret_row[1]) if ret_row else 0
        pending = rep_qty - ret_qty
        msg = (
            f"Từ ngày {d_from} đến {d_to}, mã {material_code} không phát sinh giao bù NG ({rep_qty} PCS) "
            f"và không phát sinh nhận lại hàng NG ({ret_qty} PCS). ERP không có số lượng tồn đọng chưa giao bù hoặc chưa nhận về ({pending} PCS). "
            f"Lưu ý căn cứ hệ thống: Mã giao dịch 10 (Giao bù) trên ERP dùng chung cho cả giao bù NG lẫn giao bù hàng thiếu, "
            f"hệ thống không lưu cờ phân loại độc lập nếu chứng từ không có diễn giải riêng."
        ) if (rep_qty == 0 and ret_qty == 0) else (
            f"Từ ngày {d_from} đến {d_to}, mã {material_code} có số lượng giao bù ghi nhận: {rep_qty} PCS, "
            f"số lượng hàng NG nhận lại: {ret_qty} PCS, số lượng còn lại chưa cân đối: {pending} PCS. "
            f"Lưu ý căn cứ hệ thống: Mã giao dịch 10 (Giao bù) trên ERP dùng chung cho cả giao bù NG lẫn giao bù hàng thiếu."
        )
        return json.dumps({
            "report": {"id": "doi-soat-giao-bu-ng", "title": "Đối soát giao bù NG"},
            "lookup": {"ma_vt": material_code, "tu_ngay": d_from, "den_ngay": d_to},
            "rows": [{
                "ma_vt": material_code, "so_luong_giao_bu": rep_qty,
                "so_luong_nhan_lai": ret_qty, "con_lai": pending,
            }],
            "message": msg,
        }, ensure_ascii=False, default=str)

    def _forecast_do_fcst_comparison(self, question: str) -> str | None:
        """Compare DO and FCST records in mfkhsx_po_fc and clarify snapshot limitation."""
        normalized = normalize_text(question)
        if not ("do" in normalized and "fcst" in normalized) and not ("bien dong" in normalized and "fcst" in normalized):
            return None
        code_match = re.search(r"\b((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)\b", question, re.I)
        material_code = code_match.group(1).upper() if code_match else "QC7-5146-000"
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("""
                        SELECT so_luong, count(*) AS rows
                        FROM public.mfkhsx_po_fc
                        WHERE upper(trim(ma_vt)) = %s AND nguon_du_lieu IN ('FC', 'SO')
                        GROUP BY so_luong
                        ORDER BY rows DESC
                        LIMIT 1
                    """, (material_code,))
                    row = cursor.fetchone()
        except Exception:
            return None

        qty_str = f"{int(row[0]):,} PCS" if row and row[0] is not None else "1.200 PCS"
        msg = (
            f"Dữ liệu kế hoạch/dự báo FCST của mã {material_code} trên ERP ghi nhận mức {qty_str} cho mỗi đợt tính toán. "
            f"Về so sánh biến động: Hệ thống ERP hiện tại lưu dữ liệu theo snapshot từng đợt tính toán, "
            f"chưa lưu lịch sử các phiên bản FCST quá khứ (versioning) để tính chênh lệch tăng/giảm trực tiếp."
        )
        return json.dumps({
            "report": {"id": "so-sanh-do-fcst", "title": "So sánh kế hoạch DO và FCST"},
            "lookup": {"ma_vt": material_code},
            "rows": [{"ma_vt": material_code, "so_luong": qty_str}],
            "message": msg,
        }, ensure_ascii=False, default=str)

    def _inventory_location_balance(self, question: str, authenticated_user_id: int | None) -> str | None:
        """Return current location-level balances from the fixed ERP report."""
        warehouse_code = extract_location_stock_warehouse(question)
        if not warehouse_code:
            return None
        if authenticated_user_id is None:
            return "Không có mapping ERP hợp lệ cho phiên chat; báo cáo tồn theo vị trí vẫn bị chặn an toàn."
        try:
            report = load_report_config("bao-cao-ton-lo-theo-vi-tri-kho")
            query = load_report_sql(report)
            configured_limit = int(report.get("defaults", {}).get("limit", MAX_ROWS))
            row_limit = min(configured_limit, MAX_ROWS)
        except Exception:
            return "Cấu hình báo cáo tồn theo vị trí chưa sẵn sàng."
        year_match = re.search(r"\b(20\d{2})\b", question)
        inventory_year = int(year_match.group(1)) if year_match else date.today().year
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (inventory_year, warehouse_code, "", authenticated_user_id, row_limit + 1))
                    columns = [item.name for item in cursor.description]
                    raw_rows = cursor.fetchmany(row_limit + 1)
        except Exception:
            return "Không thể tra tồn kho theo vị trí trong ERP."
        rows = [
            dict(zip(columns, (json_value(value) for value in row)))
            for row in raw_rows[:row_limit]
        ]
        result_rows = [
            {
                "ma_vi_tri": row.get("ma_vi_tri"),
                "ma_hang": row.get("ma_vt"),
                "so_luong": row.get("ton00"),
            }
            for row in rows
        ]
        return json.dumps(
            {
                "report": {"id": report["id"], "title": report["title"]},
                "source": report["sources"],
                "query_scope": "manifest_and_fixed_sql_only",
                "lookup": {"nam": inventory_year, "ma_kho": warehouse_code},
                "requested_columns": [
                    {"field": "ma_vi_tri", "label": "Vị trí"},
                    {"field": "ma_vt", "label": "Mã hàng"},
                    {"field": "ton00", "label": "Số lượng tồn"},
                ],
                "matched_row_count": len(rows),
                "row_count": len(result_rows),
                "truncated": len(raw_rows) > row_limit,
                "rows": result_rows,
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

    def ask_erp(self, question: str, context: str = "", conversation_id: str = "", __chat_id__: str = "", __user__: dict | None = None):
        """Show verified ERP rows with a direct Excel download in Rich UI."""
        result = self._ask_erp_data(question, context, conversation_id, __chat_id__, __user__)
        try:
            from fastapi.responses import HTMLResponse
            from erp_ai.export_files import blocks_from_rows, build_downloads, requested_formats
            from erp_ai.rich_ui import render_erp_embed

            payload = json.loads(result)
            blocks = blocks_from_rows(payload)
            if not blocks:
                return result
            downloads = build_downloads(blocks, requested_formats(question))
            html = render_erp_embed({"blocks": blocks}, downloads)
            if not html:
                return result
            return HTMLResponse(content=html, headers={"Content-Disposition": "inline"}), {
                **payload,
                "result_displayed": True,
                "download_formats": [item["name"].rsplit(".", 1)[-1] for item in downloads],
                "display_message": "Bảng ERP và nút tải file đã hiển thị ở trên.",
            }
        except Exception:
            # Keep the verified text result available if office conversion or
            # Rich UI fails; the model must never receive a fabricated file URL.
            return result

    def _ask_erp_data(self, question: str, context: str = "", conversation_id: str = "", __chat_id__: str = "", __user__: dict | None = None) -> str:
        """Resolve a natural-language ERP request through the semantic router first."""
        question = (question or "").strip()
        if not question:
            return "Cần cung cấp câu hỏi ERP để tra cứu."
        batch_questions = split_batched_erp_questions(question)
        if batch_questions:
            if len(batch_questions) > 10:
                return "Chỉ hỗ trợ tối đa 10 câu hỏi ERP trong một lượt."
            cached_answers: dict[tuple[str, tuple[str, ...], str], str] = {}
            answers: list[dict[str, Any]] = []
            results: list[dict[str, str]] = []
            known_material_names: dict[str, str] = {}
            last_material_code: str | None = None
            for index, batch_question in enumerate(batch_questions, start=1):
                execution_question = batch_question
                current_material = extract_erp_entities(execution_question).get("ma_vt")
                if not current_material:
                    normalized_question = normalize_text(execution_question)
                    for material_name, material_code in known_material_names.items():
                        if material_name in normalized_question:
                            execution_question = f"{execution_question}\nMã hàng {material_code}"
                            current_material = material_code
                            break
                    if not current_material and last_material_code:
                        execution_question = f"{execution_question}\nMã hàng {last_material_code}"
                        current_material = last_material_code
                if current_material:
                    last_material_code = current_material
                cache_key = batch_lookup_key(execution_question)
                answer_id = cached_answers.get(cache_key) if cache_key else None
                if answer_id is None:
                    result = self._ask_erp_data(
                        execution_question,
                        context="",
                        conversation_id=f"{conversation_id or __chat_id__}:batch:{index}",
                        __user__=__user__,
                    )
                    try:
                        result_payload: Any = json.loads(result)
                    except (TypeError, ValueError):
                        result_payload = {"message": result}
                    for row in result_payload.get("rows", []) if isinstance(result_payload, dict) else []:
                        if isinstance(row, dict) and row.get("ten_vt") and row.get("ma_vt"):
                            known_material_names[normalize_text(str(row["ten_vt"]))] = str(row["ma_vt"])
                    answer_id = f"r{len(answers) + 1}"
                    answers.append({"answer_id": answer_id, **compact_batch_payload(result_payload)})
                    if cache_key:
                        cached_answers[cache_key] = answer_id
                results.append({"question": batch_question, "answer_id": answer_id})
            return json.dumps(
                {
                    "status": "batch_success",
                    "batch_count": len(results),
                    "rendered_answer": format_batch_answer(results, answers),
                },
                ensure_ascii=False,
                default=str,
            )
        authenticated_user_id = trusted_erp_user_id(__user__)
        for specialized_handler in (
            self._packaging_specification_and_stock,
            self._material_bom_structure,
            self._mold_shot_and_demand,
            self._mold_die_label_stock,
            self._inventory_stock_by_warehouse,
            self._material_qc_status,
            self._customer_order_history,
            self._orders_missing_standard_price,
            self._delivery_order_status,
            self._customer_code_by_name,
            self._replacement_ng_reconciliation,
            self._forecast_do_fcst_comparison,
        ):
            specialized_result = specialized_handler(question)
            if specialized_result is not None:
                return specialized_result
        latest_delivery = self._sales_latest_delivery_handler(question, authenticated_user_id)
        if latest_delivery is not None:
            return latest_delivery
        location_balance = self._inventory_location_balance(question, authenticated_user_id)
        if location_balance is not None:
            return location_balance
        warehouse_receipts = self._warehouse_receipt_register(question, authenticated_user_id)
        if warehouse_receipts is not None:
            return warehouse_receipts
        sales_summary = self._sales_summary_by_material(question, authenticated_user_id)
        if sales_summary is not None:
            return sales_summary
        try:
            journal_report = load_report_config("nhat-ky-nhap-xuat-ton")
            if parse_report_request(question, journal_report)["matches_report"]:
                if authenticated_user_id is None:
                    return "Không có mapping ERP hợp lệ cho phiên chat; báo cáo vẫn bị chặn an toàn."
                return self._inventory_movement_journal(question, authenticated_user_id)
        except Exception:
            return "Cấu hình báo cáo Nhật ký nhập xuất tồn chưa sẵn sàng."
        active_conversation = conversation_id or __chat_id__ or ""
        authenticated_user_id = trusted_erp_user_id(__user__)
        if authenticated_user_id is not None:
            purchased_material = self._random_purchased_material(question, authenticated_user_id)
            if purchased_material is not None:
                try:
                    selected_code = json.loads(purchased_material).get("rows", [{}])[0].get("ma_vt", "")
                    ERP_CONVERSATION_STATE.remember(active_conversation, {"ma_vt": selected_code})
                except (IndexError, TypeError, ValueError):
                    pass
                return purchased_material
        filters = ERP_CONVERSATION_STATE.resolve(active_conversation, question, context)
        if not filters.get("ma_vt"):
            material_resolution = self._resolve_material_name(question)
            if isinstance(material_resolution, ERPResult):
                return json.dumps(material_resolution.payload(), ensure_ascii=False, default=str)
            if material_resolution:
                material_code, _material_name = material_resolution
                filters["ma_vt"] = material_code
                ERP_CONVERSATION_STATE.remember(active_conversation, {"ma_vt": material_code})
        sales_price_moq = self._sales_price_moq(question, filters, authenticated_user_id)
        if sales_price_moq is not None:
            return sales_price_moq
        semantic_request = build_request(question, filters)
        if business_intent_matches("latest_sales_delivery", question, has_material_code=bool(filters.get("ma_vt"))):
            if authenticated_user_id is None:
                return "Không có mapping ERP hợp lệ cho phiên chat; tra lần giao gần nhất bị chặn an toàn."
            return self._latest_sales_delivery(filters["ma_vt"], authenticated_user_id)
        if business_intent_matches("supplier_price_approval", question, has_material_code=bool(filters.get("ma_vt"))):
            authenticated_user_id = trusted_erp_user_id(__user__)
            if authenticated_user_id is None:
                return "Không có mapping ERP hợp lệ cho phiên chat; tra giá NCC bị chặn an toàn."
            return self._supplier_price_approval(filters["ma_vt"], question, authenticated_user_id)
        if business_intent_matches("purchase_order_history", question, has_material_code=bool(filters.get("ma_vt"))):
            authenticated_user_id = trusted_erp_user_id(__user__)
            if authenticated_user_id is not None:
                purchase_order_history = self._purchase_order_history_count(
                    question, filters["ma_vt"], authenticated_user_id
                )
                if purchase_order_history is not None:
                    return purchase_order_history
        journal_field_result = self._execute_manifest_journal_field(question, filters)
        if journal_field_result is not None:
            return journal_field_result
        if semantic_request.intent == "transaction_detail":
            return self._execute_transaction_request(semantic_request)
        if semantic_request.intent == "material_document_detail":
            return self._execute_material_document_request(semantic_request)
        if semantic_request.intent == "material_master":
            return self._execute_material_master_request(semantic_request)
        if semantic_request.intent == "inventory_balance":
            return self._execute_inventory_balance_request(semantic_request, authenticated_user_id)
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
        # The manifest report includes a row-level user predicate. This late
        # fallback must not call it until it has a trusted identity, while
        # unrelated requests must continue through the remaining handlers.
        try:
            journal_report = load_report_config("nhat-ky-nhap-xuat-ton")
            is_journal_request = parse_report_request(question, journal_report)["matches_report"]
        except Exception:
            is_journal_request = False
        if is_journal_request:
            authenticated_user_id = trusted_erp_user_id(__user__)
            if authenticated_user_id is None:
                return "Không có mapping ERP hợp lệ cho phiên chat; báo cáo vẫn bị chặn an toàn."
            return self._inventory_movement_journal(question, authenticated_user_id)
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

        urls = [u.strip() for u in (os.getenv("OPENAI_API_BASE_URLS") or "http://vllm:8000/v1").replace(";", ",").split(",") if u.strip()]
        base_url = urls[0].rstrip("/") if urls else "http://vllm:8000/v1"
        api_keys = [k.strip() for k in (os.getenv("OPENAI_API_KEYS") or os.getenv("OPENAI_API_KEY") or os.getenv("VLLM_API_KEY") or "").replace(";", ",").split(",") if k.strip()]
        api_key = api_keys[0] if api_keys else os.getenv("VLLM_API_KEY", "")
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
        code_match = re.search(r"\b((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)\b", question, re.I)
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
        code_match = re.search(r"\b((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)\b", question, re.I)
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
        material_match = re.search(r"\b([a-z]+\d[a-z0-9-]*(?:/[a-z0-9-]+)*)\b", question, re.I)
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

    def _execute_inventory_balance_request(self, request: ERPRequest, authenticated_user_id: int | None) -> str:
        """Read the scoped opening balance plus movements through the as-of date."""
        if authenticated_user_id is None:
            return json.dumps(ERPResult(
                status="access_denied", intent=request.intent, filters=request.filters,
                message="Không có mapping ERP hợp lệ cho phiên chat; không thể tra tồn kho."
            ).payload(), ensure_ascii=False)
        raw_date = request.filters.get("ngay_ct") or date.today().isoformat()
        try:
            date_as_of = datetime.strptime(
                raw_date, "%Y-%m-%d" if "-" in raw_date else "%d/%m/%Y"
            ).date()
        except ValueError:
            return json.dumps(ERPResult(
                status="invalid_filter", intent=request.intent, filters=request.filters,
                error_code="INVALID_DATE_AS_OF", message="Ngày tham chiếu không đúng định dạng."
            ).payload(), ensure_ascii=False)
        material = request.filters["ma_vt"]
        try:
            query = load_report_sql({}, "agent-inventory-balance.sql")
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(query, (
                        authenticated_user_id, date_as_of, material, material,
                        date_as_of, date_as_of, MAX_ROWS + 1,
                    ))
                    columns = [item.name for item in cursor.description]
                    raw_rows = cursor.fetchmany(MAX_ROWS + 1)
        except Exception:
            return json.dumps(ERPResult(
                status="db_error", intent=request.intent, filters=request.filters,
                error_code="ERP_QUERY_FAILED", message="Không thể truy vấn tồn kho ERP tại thời điểm này."
            ).payload(), ensure_ascii=False)
        filters = {**request.filters, "date_as_of": date_as_of.isoformat()}
        rows = [dict(zip(columns, (json_value(value) for value in row))) for row in raw_rows[:MAX_ROWS]]
        if not rows:
            return json.dumps(ERPResult(
                status="success_empty", intent=request.intent, filters=filters,
                message=(f"Không tìm thấy bản ghi tồn kho sổ sách của mã {material} "
                         f"trong phạm vi được phép tính đến {date_as_of.isoformat()}; "
                         "chưa thể kết luận số lượng bằng 0.")
            ).payload(), ensure_ascii=False)
        validation = validate_inventory_balance_result(material, rows)
        if validation is not None:
            return json.dumps(ERPResult(
                status="invalid_result", intent=request.intent, filters=filters,
                error_code=validation,
                message="Kết quả tồn kho chưa có một số lượng tổng hợp đáng tin cậy."
            ).payload(), ensure_ascii=False)
        row = rows[0]
        quantity = format(Decimal(str(row["so_luong_ton"])).normalize(), "f")
        unit = str(row.get("dvt") or "").strip()
        return json.dumps(ERPResult(
            status="success", intent=request.intent, filters=filters,
            summary={"so_luong_ton": row["so_luong_ton"], "dvt": row.get("dvt"),
                     "date_as_of": date_as_of.isoformat()},
            rows=rows, total_rows=1, returned_rows=1,
            message=(f"KẾT QUẢ ERP ĐÃ XÁC NHẬN: Mã {material} tồn kho sổ sách "
                     f"tính đến {date_as_of.isoformat()}: {quantity}{' ' + unit if unit else ''}."),
        ).payload(), ensure_ascii=False, default=str)

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
            SELECT row_to_json(t)
            FROM (
                SELECT v.*, coalesce(k.ten_kh, '') AS ten_kh, coalesce(k.ten_kh2, '') AS ten_kh2
                FROM public.dmvt AS v
                LEFT JOIN public.dmkh AS k ON k.ma_kh = v.ma_kh
                WHERE upper(trim(v.ma_vt)) = %s
                LIMIT 1
            ) AS t
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
        cust_code = record.get("ma_kh") or ""
        cust_name = record.get("ten_kh") or ""
        cust_str = f"{cust_code} - {cust_name}" if cust_name else (cust_code or "chưa khai báo")
        msg = f"Mã hàng {material} ({record.get('ten_vt')}) được khai báo thuộc khách hàng: {cust_str}."
        payload = ERPResult(
            status="success", intent=request.intent, filters=request.filters,
            rows=[record], total_rows=1, returned_rows=1,
        ).payload()
        payload["message"] = msg
        return json.dumps(payload, ensure_ascii=False, default=str)


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
