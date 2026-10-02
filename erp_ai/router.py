"""Map normalized ERP requests to deterministic business intents."""

import re
import unicodedata

from .contracts import ERPRequest


def _normalized_text(value: str) -> str:
    """Compare Vietnamese request semantics without depending on accents."""
    folded = unicodedata.normalize("NFD", value or "")
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", folded.replace("đ", "d").replace("Đ", "d").lower()).strip()


def build_request(question: str, filters: dict[str, str]) -> ERPRequest:
    """Route only from explicit semantic entities, never from generated SQL."""
    normalized = _normalized_text(question)
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
    # Questions about whether/how often an item was ordered refer to purchase
    # documents, not the material master. This stays generic across wording.
    order_history_terms = ("da dat", "da mua", "bao nhieu lan", "lich su don hang", "lich su dat hang", "lan mua gan nhat")
    if active.get("ma_vt") and any(term in normalized for term in order_history_terms):
        return ERPRequest(
            intent="purchase_order_history",
            filters=active,
            metrics=("so_lan_dat",),
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
