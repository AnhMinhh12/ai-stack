"""Business-result validation before an LLM can describe ERP data."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation


def validate_inventory_balance_result(material: str, rows: list[dict]) -> str | None:
    """Return an error code unless one row confirms the requested stock quantity."""
    if len(rows) != 1:
        return "INVENTORY_ROW_COUNT_INVALID"
    row = rows[0]
    if str(row.get("ma_vt") or "").strip().upper() != material.strip().upper():
        return "INVENTORY_MATERIAL_MISMATCH"
    value = row.get("so_luong_ton")
    if value is None or isinstance(value, bool):
        return "INVENTORY_QUANTITY_MISSING"
    try:
        quantity = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "INVENTORY_QUANTITY_INVALID"
    if not quantity.is_finite():
        return "INVENTORY_QUANTITY_INVALID"
    return None
