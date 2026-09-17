"""Map normalized ERP requests to deterministic business intents."""

from .contracts import ERPRequest


def build_request(question: str, filters: dict[str, str]) -> ERPRequest:
    """Route only from explicit semantic entities, never from generated SQL."""
    normalized = (question or "").lower()
    active = {key: value for key, value in filters.items() if value}
    if active.get("ma_gd"):
        return ERPRequest(
            intent="transaction_detail",
            filters=active,
            source="deterministic_router",
        )
    if active.get("ma_vt") and active.get("so_ct"):
        return ERPRequest(
            intent="material_document_detail",
            filters=active,
            metrics=("sl_nhap", "sl_xuat", "ty_gia"),
            source="deterministic_router",
        )
    if active.get("ma_vt") and not active.get("so_ct") and not active.get("ngay_ct"):
        return ERPRequest(
            intent="material_master",
            filters=active,
            source="deterministic_router",
        )
    if active.get("ma_vt") and active.get("ngay_ct"):
        return ERPRequest(
            intent="inventory_ledger",
            filters=active,
            metrics=("sl_nhap", "sl_xuat"),
            source="deterministic_router",
        )
    return ERPRequest(intent="unsupported", filters=active, source="router_no_match")
