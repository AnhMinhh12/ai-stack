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
    # Users commonly shorten "mã vật tư" to just "mã" in follow-up
    # questions, e.g. "mã 3003541 thì sao?".
    r"(?:mã|ma)(?:\s*(?:vật\s*tư|vat\s*tu|vt))?\s*[:#-]?\s*(\d{6,})\b"
    r"|\b(\d{6,})\b(?=\s+(?:mã\s*)?(?:vật\s*tư|vt)\b)",
    re.I,
)
STANDALONE_NUMERIC_MATERIAL = re.compile(r"^\s*(\d{6,})\s*(?:[?!.…]+)?\s*$")
# A material code made solely of letters may be safely recognized only when it
# is explicitly labelled, and must contain a separator so ordinary phrases
# such as "mã này" are not mistaken for a code.
LABELLED_HYPHENATED_MATERIAL = re.compile(
    r"(?:mã|ma)(?:\s*(?:vật\s*tư|vat\s*tu|vt))?\s*[:#-]?\s*"
    r"([a-z][a-z0-9]*(?:[-/][a-z0-9]+)+)\b",
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
    standalone_numeric_material = STANDALONE_NUMERIC_MATERIAL.match(value)
    labelled_hyphenated_material = LABELLED_HYPHENATED_MATERIAL.search(value)
    date = DATE.search(value)
    transaction = TRANSACTION.search(value)
    return {
        "ma_vt": (
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
