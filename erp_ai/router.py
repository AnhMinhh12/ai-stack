"""Map normalized ERP requests to business intents using semantic concept routing."""

import re
import unicodedata

from .contracts import ERPRequest


def _normalized_text(value: str) -> str:
    """Compare Vietnamese request semantics without depending on accents."""
    folded = unicodedata.normalize("NFD", value or "")
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    return re.sub(r"\s+", " ", folded.replace("đ", "d").replace("Đ", "d").lower()).strip()


def _has_concept(norm_text: str, concepts: tuple[str, ...]) -> bool:
    """Match whole concept words/phrases to prevent partial substring collisions."""
    for c in concepts:
        if re.search(rf"(?<![a-z0-9]){re.escape(c)}(?![a-z0-9])", norm_text):
            return True
    return False


# Semantic concept vocabularies (domain concept stems in factory ERP/MES)
DELIVERY_CONCEPTS = (
    "xuat", "giao", "ban hang", "phieu xuat", "chung tu xuat",
    "don giao", "dot xuat", "lo xuat", "lot xuat", "chuyen hang",
    "xuat kho", "giao hang", "xuat ban", "do_no"
)

PURCHASE_CONCEPTS = (
    "mua", "nhap mua", "don mua", "dat hang", "da dat", "da mua",
    "bao nhieu lan", "lich su don hang", "lich su dat hang", "po1",
    "ncc", "nha cung cap"
)

INVENTORY_CONCEPTS = (
    "ton", "ton kho", "con hang", "con lai", "trong kho",
    "so luong ton", "so kho", "the kho", "ton tai kho", "vi tri"
)

BOM_CONCEPTS = (
    "bom", "dinh muc", "cau truc", "cau thanh", "nguyen lieu",
    "hat nhua", "thanh phan", "ti le nhua", "nvl"
)

MOLD_CONCEPTS = (
    "khuon", "shot", "tuoi tho", "bao hanh", "cavity", "die",
    "so shot", "khuon duc"
)

QC_CONCEPTS = (
    "qc", "kiem tra", "iqc", "oqc", "tem", "chat luong",
    "dat", "ng", "loi", "status_qc"
)

PRICE_CONCEPTS = (
    "bang gia", "moq", "don gia", "gia ban", "gia niem yet",
    "gia chuan", "bao gia", "gia"
)

RECENCY_CONCEPTS = (
    "gan nhat", "moi nhat", "cuoi cung", "vua roi", "lan nhat",
    "lan cuoi", "moi day", "vua xong", "gan day", "cuoi"
)


def build_request(question: str, filters: dict[str, str]) -> ERPRequest:
    """Route semantic entities to business intents using concept classification."""
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

    has_delivery = _has_concept(normalized, DELIVERY_CONCEPTS)
    has_purchase = _has_concept(normalized, PURCHASE_CONCEPTS)
    has_stock = _has_concept(normalized, INVENTORY_CONCEPTS)
    has_recency = _has_concept(normalized, RECENCY_CONCEPTS)
    has_bom = _has_concept(normalized, BOM_CONCEPTS)
    has_mold = _has_concept(normalized, MOLD_CONCEPTS)
    has_qc = _has_concept(normalized, QC_CONCEPTS)
    has_price = _has_concept(normalized, PRICE_CONCEPTS)

    if active.get("ma_vt"):
        # 1. Delivery / Shipment intent (priority when delivery concepts present)
        if has_delivery and not has_purchase:
            if has_recency:
                return ERPRequest(
                    intent="latest_sales_delivery",
                    filters=active,
                    source="semantic_router",
                )
            return ERPRequest(
                intent="sales_shipment",
                filters=active,
                source="semantic_router",
            )

        # 2. Purchase history intent
        if has_purchase:
            return ERPRequest(
                intent="purchase_order_history",
                filters=active,
                metrics=("so_lan_dat",),
                source="semantic_router",
            )

        # 3. Inventory stock intent
        if has_stock:
            if active.get("ngay_ct"):
                return ERPRequest(
                    intent="inventory_ledger",
                    filters=active,
                    metrics=("sl_nhap", "sl_xuat"),
                    source="semantic_router",
                )
            return ERPRequest(
                intent="inventory_balance",
                filters=active,
                metrics=("so_luong_ton",),
                source="semantic_router",
            )

        # 4. BOM / Material structure
        if has_bom:
            return ERPRequest(
                intent="material_bom",
                filters=active,
                source="semantic_router",
            )

        # 5. Mold profile
        if has_mold:
            return ERPRequest(
                intent="mold_profile",
                filters=active,
                source="semantic_router",
            )

        # 6. QC quality inspection
        if has_qc:
            return ERPRequest(
                intent="qc_inspection",
                filters=active,
                source="semantic_router",
            )

        # 7. Price / MOQ
        if has_price:
            return ERPRequest(
                intent="sales_price",
                filters=active,
                source="semantic_router",
            )

        # 8. Pure master-data read (NO action concepts)
        if not (has_delivery or has_purchase or has_stock or has_bom or has_mold or has_qc or has_price):
            return ERPRequest(
                intent="material_master",
                filters=active,
                source="semantic_router",
            )

    if active.get("ma_vt") and active.get("ngay_ct"):
        return ERPRequest(
            intent="inventory_ledger",
            filters=active,
            metrics=("sl_nhap", "sl_xuat"),
            source="semantic_router",
        )

    return ERPRequest(intent="unsupported", filters=active, source="router_no_match")
