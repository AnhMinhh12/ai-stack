"""Deterministic extraction of stable ERP identifiers."""

import re
from typing import Mapping


DOCUMENT = re.compile(r"\b\d{3}-\d{4}-\d{6}\b")
# Some ERP material codes use a revision suffix, e.g. PNKV1260WA1K115/V1.
# Treat slash-delimited segments as part of the identifier rather than text
# separators; otherwise a lookup silently queries a different material.
MATERIAL = re.compile(
    r"\b(?=[a-z0-9/-]*\d)(?=[a-z0-9/-]*[a-z])[a-z0-9]+(?:[-/][a-z0-9]+)*\b",
    re.I,
)
NUMERIC_MATERIAL = re.compile(
    # Users commonly shorten "mã vật tư" to just "mã" or use "mã hàng", "mã sản phẩm".
    r"(?:mã|ma)(?:\s*(?:vật\s*tư|vat\s*tu|vt|hàng|hang|sản\s*phẩm|san\s*pham|sp))?\s*[:#-]?\s*(\d{6,})\b"
    r"|\b(\d{6,})\b(?=\s+(?:mã\s*)?(?:vật\s*tư|vt|hàng|hang|sản\s*phẩm|san\s*pham|sp)\b)",
    re.I,
)
STANDALONE_NUMERIC_MATERIAL = re.compile(r"^\s*(\d{6,})\s*(?:[?!.…]+)?\s*$")
# A material code made solely of letters may be safely recognized only when it
# is explicitly labelled, and must contain a separator so ordinary phrases
# such as "mã này" are not mistaken for a code.
LABELLED_HYPHENATED_MATERIAL = re.compile(
    r"(?:mã|ma)(?:\s*(?:vật\s*tư|vat\s*tu|vt|hàng|hang|sản\s*phẩm|san\s*pham))?\s*[:#-]?\s*"
    r"([a-z0-9][a-z0-9]*(?:[-/][a-z0-9]+)+)\b",
    re.I,
)
DATE = re.compile(r"\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b")
TRANSACTION = re.compile(
    r"(?:mã\s*giao\s*dịch|ma\s*giao\s*dich|mã\s*gd|ma\s*gd)\s*[:#-]?\s*(\d{4,})",
    re.I,
)
CUSTOMER = re.compile(
    r"(?:khách\s*hàng|khach\s*hang|khách|khach|mã\s*kh|ma\s*kh)\s*[:#-]?\s*([a-z0-9]+)\b|\b(KH\d+|NCC\d+)\b",
    re.I,
)


KNOWN_WAREHOUSES = frozenset({
    "KHOTP00", "KHOTP01", "KHOTP02", "KHOTP03", "KHOLK00", "KHOLK01", "KHOLKSX",
    "KHONMD", "KHONVL00", "KHONVL01", "KHONVLSX", "KHOQA", "KHOQC", "KHOQC01", "KHOQC02",
    "KHOTESTITG", "KHOTNHH", "KHOVT00", "KHOVT01", "KHOVT02", "KHOVT03", "KHO25",
    "KHOBD01", "KHO-IN", "KHO-CXL", "KHO-LAP-RAP", "KHO-XHTL", "KHO-TAI-MAY",
    "KHO-SORTING", "KHO-HANG-LE", "KHO-HOALAC", "KHO-HOT", "KHO-HTSS", "KHO-GCN",
    "KHO-GBNG", "KHO-CHUYENTHUNG", "KHO-MAU-QC", "KHO-NG", "KHO-QVFLOT1", "KHO-QVFLOT2",
    "KHO-XHLOT2", "KHO-XHLOT3", "KHO_TAIMAY", "MOLD01", "VATTU_THIETBI", "CHUYENNGOAI"
})


def extract_entities(text: str) -> dict[str, str]:
    """Return explicit identifiers; never infer values from similar records."""
    value = text or ""
    document = DOCUMENT.search(value)
    customer = CUSTOMER.search(value)
    customer_code = (customer.group(1) or customer.group(2)).upper() if customer else ""

    warehouse_code = ""
    material = None
    for m in MATERIAL.finditer(value):
        candidate = m.group(0).upper()
        if customer_code and candidate == customer_code:
            continue
        # Warehouse check: if code starts with KHO or is a known warehouse code, it is ma_kho
        if candidate.startswith("KHO") or candidate in KNOWN_WAREHOUSES or re.search(r"\b(?:kho|o\s*kho|ở\s*kho|tai\s*kho|tại\s*kho|ở|tai|tại)\s*[:#-]?\s*$", value[:m.start()], re.I):
            if candidate.startswith("KHO") or candidate in KNOWN_WAREHOUSES:
                if not warehouse_code:
                    warehouse_code = candidate
                continue
        material = m
        break

    if not warehouse_code:
        for wh in KNOWN_WAREHOUSES:
            if re.search(rf"\b{re.escape(wh)}\b", value, re.I):
                warehouse_code = wh
                break

    numeric_material = NUMERIC_MATERIAL.search(value)
    standalone_numeric_material = STANDALONE_NUMERIC_MATERIAL.match(value)
    labelled_hyphenated_material = LABELLED_HYPHENATED_MATERIAL.search(value)
    date = DATE.search(value)
    transaction = TRANSACTION.search(value)
    matched_ma_vt = (
        material.group(0).upper()
        if material
        else (
            labelled_hyphenated_material.group(1).upper()
            if labelled_hyphenated_material
            else next((
                group
                for group in (numeric_material.groups() if numeric_material else ())
                if group
            ), standalone_numeric_material.group(1) if standalone_numeric_material else "")
        )
    )
    if not matched_ma_vt:
        clean_val = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s+\d{1,2}\s+thg\s+\d{1,2}(?:\s+\d{4})?)?\b", "", value, flags=re.I)
        clean_val = re.sub(r"\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b", "", clean_val)
        num_search = re.search(r"\b(\d{6,})\b", clean_val)
        if num_search:
            matched_ma_vt = num_search.group(1)

    return {
        "ma_vt": matched_ma_vt,
        "ma_kh": customer_code,
        "ma_kho": warehouse_code,
        "so_ct": document.group(0) if document else "",
        "ngay_ct": date.group(0) if date else "",
        "ma_gd": transaction.group(1) if transaction else "",
    }


def merge_filters(current: Mapping[str, str], previous: Mapping[str, str]) -> dict[str, str]:
    """Current-turn explicit values override state; missing values inherit state."""
    return {
        key: current.get(key) or previous.get(key) or ""
        for key in ("ma_vt", "ma_kh", "ma_kho", "so_ct", "ngay_ct", "ma_gd")
    }
