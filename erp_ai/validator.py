"""Business-result validation before an LLM can describe ERP data."""

from decimal import Decimal
from .contracts import ERPResult


def validate_document_result(result: ERPResult) -> ERPResult:
    """Ensure all returned rows honour the material/document filters and totals."""
    if result.status != "success":
        return result
    material = result.filters.get("ma_vt", "")
    document = result.filters.get("so_ct", "")
    if any(row.get("ma_vt") != material or row.get("so_ct") != document for row in result.rows):
        result.status = "query_validation_failed"
        result.error_code = "FILTER_MISMATCH"
        result.message = "Kết quả không khớp điều kiện truy vấn."
        return result
    in_total = sum((Decimal(str(row.get("sl_nhap") or 0)) for row in result.rows), Decimal())
    out_total = sum((Decimal(str(row.get("sl_xuat") or 0)) for row in result.rows), Decimal())
    if Decimal(str(result.summary.get("sl_nhap") or 0)) != in_total or Decimal(str(result.summary.get("sl_xuat") or 0)) != out_total:
        result.status = "query_validation_failed"
        result.error_code = "AGGREGATE_MISMATCH"
        result.message = "Tổng hợp không khớp các dòng chi tiết."
    return result
