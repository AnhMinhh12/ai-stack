"""Deterministic extraction of stable ERP identifiers."""

import re
from typing import Mapping


DOCUMENT = re.compile(r"\b\d{3}-\d{4}-\d{6}\b")
MATERIAL = re.compile(r"\b[a-z]+\d[a-z0-9-]*\b", re.I)
NUMERIC_MATERIAL = re.compile(
    r"(?:mã\s*(?:vật\s*tư|vt)|ma\s*(?:vat\s*tu|vt))\s*[:#-]?\s*(\d{6,})\b"
    r"|\b(\d{6,})\b(?=\s+(?:mã\s*)?(?:vật\s*tư|vt)\b)",
    re.I,
)
DATE = re.compile(r"\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b")
TRANSACTION = re.compile(
    r"(?:mã\s*giao\s*dịch|ma\s*giao\s*dich|mã\s*gd|ma\s*gd)\s*[:#-]?\s*(\d{4,})",
    re.I,
)


def extract_entities(text: str) -> dict[str, str]:
    """Return explicit identifiers; never infer values from similar records."""
    value = text or ""
    document = DOCUMENT.search(value)
    material = MATERIAL.search(value)
    numeric_material = NUMERIC_MATERIAL.search(value)
    date = DATE.search(value)
    transaction = TRANSACTION.search(value)
    return {
        "ma_vt": (
            material.group(0).upper()
            if material
            else next((group for group in (numeric_material.groups() if numeric_material else ()) if group), "")
        ),
        "so_ct": document.group(0) if document else "",
        "ngay_ct": date.group(0) if date else "",
        "ma_gd": transaction.group(1) if transaction else "",
    }


def merge_filters(current: Mapping[str, str], previous: Mapping[str, str]) -> dict[str, str]:
    """Current-turn explicit values override state; missing values inherit state."""
    return {
        key: current.get(key) or previous.get(key) or ""
        for key in ("ma_vt", "so_ct", "ngay_ct", "ma_gd")
    }
