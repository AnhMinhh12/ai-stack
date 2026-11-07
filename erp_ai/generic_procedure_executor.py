"""Generic Procedure Executor for ERP 3S & MES.

Eliminates patchwork regex handlers by executing standardized stored procedures
and catalog-driven contracts with safe PostgreSQL read-only transactions,
parameter validation, and natural Vietnamese formatting.
"""

import json
import logging
import re
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from erp_ai.native_tools import (
    ERPNativeTools,
    clean_numeric_str,
    connection_settings,
    resolve_date_range,
)
from erp_ai.procedure_catalog import REPORT_CATALOG, find_report_in_catalog

logger = logging.getLogger("htmp.procedure_executor")
TIMEOUT_MS = 15000


def format_number(val: Any) -> str:
    """Format numbers into readable strings with thousand separators."""
    if val is None or val == "":
        return "-"
    if isinstance(val, (int, float, Decimal)):
        # If integer or float with no fractional part
        if float(val) == int(float(val)):
            return f"{int(float(val)):,}"
        return f"{float(val):,.2f}"
    return str(val)


class GenericProcedureExecutor:
    """Universal executor for ERP stored procedures and data contracts."""

    def __init__(self):
        self.native_tools = ERPNativeTools()

    def execute_db_procedure(self, proc_name: str, search_dynamic: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """Safely execute an ERP stored procedure inside a read transaction."""
        import psycopg
        from psycopg.rows import dict_row

        payload = json.dumps({
            "JSON": {
                "user_id": "1",
                "searchDynamic": search_dynamic
            }
        })

        with psycopg.connect(**connection_settings(), autocommit=False) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                sql = f"SELECT * FROM public.{proc_name}(%s)"
                if limit and limit > 0:
                    sql += f" LIMIT {int(limit)}"
                
                try:
                    cursor.execute(sql, (payload,))
                    rows = cursor.fetchall()
                    return [dict(r) for r in rows]
                finally:
                    conn.rollback()

    def extract_entities_from_text(self, text: str) -> Dict[str, str]:
        """Extract business entities (material code, customer/supplier code, warehouse) from text."""
        entities = {
            "item_code": "",
            "partner_code": "",
            "warehouse_code": "",
            "order_code": "",
            "account_code": ""
        }
        if not text:
            return entities

        # 1. Partner code (KHxxxx, NCCxxxx)
        m_kh = re.search(r"\b(KH\d{4,5})\b", text, re.I)
        if m_kh:
            entities["partner_code"] = m_kh.group(1).upper()
        m_ncc = re.search(r"\b(NCC\d{4,5})\b", text, re.I)
        if m_ncc:
            entities["partner_code"] = m_ncc.group(1).upper()

        # 2. Account code (131, 331, 152, 156, etc.)
        m_acc = re.search(r"\b(?:tk|tai khoan)?\s*(131|331|152|155|156)\b", text, re.I)
        if m_acc:
            entities["account_code"] = m_acc.group(1)

        # 3. Warehouse code (KHO_TP, KHO_NVL, KHO_THI_TRUONG, etc.)
        m_kho = re.search(r"\b(KHO[A-Z0-9_-]+)\b", text, re.I)
        if m_kho:
            entities["warehouse_code"] = m_kho.group(1).upper()

        # 4. Order code (SO, PO, CT) - exclude report procedure names
        # Standard ERP voucher formats: 001-2610-000830 or SO-xxxx, PO-xxxx
        m_order = re.search(r"\b(\d{3}-\d{4}-\d{6}|(?:SO|PO|HDA|PNF|PXB|CT)[-_]?\d+[\w-]*)\b", text, re.I)
        if m_order:
            code = m_order.group(1).upper()
            if not code.lower().startswith("pobk") and not code.lower().startswith("sobk"):
                entities["order_code"] = code

        # 5. Item / material code
        # Look for patterns like 003-M69-101-2, TPE11DS, TPUD318, POMP801
        m_item = re.search(r"\b([A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+(?:-[A-Z0-9]+)?|[A-Z]{3,}[0-9]{2,}[A-Z0-9]*)\b", text)
        if m_item:
            code = m_item.group(1).upper()
            if not code.startswith("KHO") and not code.startswith("NCC") and not code.startswith("KH"):
                entities["item_code"] = code

        return entities

    def query_report(
        self,
        report_type: str = "",
        query: str = "",
        date_from: str = "",
        date_to: str = "",
        item_code: str = "",
        partner_code: str = "",
        warehouse_code: str = "",
        account_code: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """Universal entry point to execute and format any ERP 3S / MES business report."""
        combined_text = f"{report_type} {query}".strip()
        report_meta = find_report_in_catalog(report_type) or find_report_in_catalog(combined_text)

        if not report_meta:
            return {
                "success": False,
                "message": f"Không tìm thấy mẫu báo cáo phù hợp cho yêu cầu: '{combined_text}'. Các báo cáo hỗ trợ gồm: Tồn kho, Nhập xuất tồn, Thẻ kho, Đơn hàng bán, Đơn mua hàng, Tiến độ giao hàng, Lịch sử giá, Sổ công nợ (131/331), Chất lượng IQC, Số shot khuôn, Dừng máy, Định mức BOM, Quy cách đóng gói."
            }

        report_id = report_meta["id"]
        title = report_meta["title"]
        domain = report_meta["domain"]

        # Extract dates
        d_from, d_to = resolve_date_range(date_from=date_from, date_to=date_to, query_hint=combined_text)

        # Extract entities from query text if not explicitly provided
        entity_source_text = query if query.strip() else combined_text
        extracted = self.extract_entities_from_text(entity_source_text)
        c_item = (item_code or extracted["item_code"]).strip().upper()
        c_partner = (partner_code or extracted["partner_code"]).strip().upper()
        c_warehouse = (warehouse_code or extracted["warehouse_code"]).strip().upper()
        c_order = kwargs.get("order_code") or extracted["order_code"]
        c_acc = account_code or extracted["account_code"] or ("331" if "331" in combined_text or "ncc" in combined_text.lower() else "131")

        # ---------------------------------------------------------
        # Branch A: Reports handled by ERPNativeTools specialized methods
        # ---------------------------------------------------------
        if report_id == "inso1":
            raw_text = self.native_tools.lookup_stock_card(
                material_code=c_item,
                warehouse_code=c_warehouse,
                date_from=d_from,
                date_to=d_to,
                query_hint=combined_text
            )
            return {"success": True, "report_id": report_id, "title": title, "formatted_text": raw_text}

        if report_id == "lookup_incoming_quality":
            raw_text = self.native_tools.lookup_incoming_quality(
                date_from=d_from,
                date_to=d_to,
                supplier_code=c_partner,
                query_hint=combined_text
            )
            return {"success": True, "report_id": report_id, "title": title, "formatted_text": raw_text}

        if report_id == "lookup_mold_and_mes":
            raw_text = self.native_tools.lookup_mold_and_mes(
                mold_code=kwargs.get("mold_code", ""),
                material_code=c_item,
                query_hint=combined_text
            )
            return {"success": True, "report_id": report_id, "title": title, "formatted_text": raw_text}

        if report_id == "lookup_bom":
            raw_text = self.native_tools.lookup_bom(
                product_code=c_item or kwargs.get("product_code", ""),
                material_code=kwargs.get("sub_material_code", ""),
                query_hint=combined_text
            )
            return {"success": True, "report_id": report_id, "title": title, "formatted_text": raw_text}

        if report_id == "lookup_mes_downtime":
            raw_text = self.native_tools.lookup_mes_downtime(
                date_from=d_from,
                date_to=d_to,
                machine_code=kwargs.get("machine_code", ""),
                query_hint=combined_text
            )
            return {"success": True, "report_id": report_id, "title": title, "formatted_text": raw_text}

        if report_id == "lookup_general_catalog":
            cat = "quy_cach" if any(w in combined_text.lower() for w in ("quy cach", "dong goi", "thung", "khay")) else "employee"
            raw_text = self.native_tools.lookup_general_catalog(
                category=cat,
                keyword=c_item or c_partner or combined_text
            )
            return {"success": True, "report_id": report_id, "title": title, "formatted_text": raw_text}

        # ---------------------------------------------------------
        # Branch B: Standard Stored Procedure Execution
        # ---------------------------------------------------------
        proc_name = report_meta.get("procedure_name")
        if not proc_name:
            return {"success": False, "message": f"Báo cáo '{report_id}' chưa được cấu hình procedure."}

        # Prepare parameters
        search_dynamic = dict(report_meta.get("default_params", {}))
        search_dynamic.update({
            "dfrom": d_from,
            "dto": d_to,
            "cma_vt": c_item,
            "cma_kh": c_partner,
            "cma_kho": c_warehouse,
            "cso_ct1": c_order,
            "cma_dvcs": "001",
            "culture": "vi-VN"
        })

        if proc_name == "sosoctcongno1kh":
            search_dynamic["ccust"] = c_partner
            search_dynamic["caccount"] = c_acc
            search_dynamic["cbranch"] = "001"
            search_dynamic["isdetail"] = 1

        elif proc_name == "inbctonkho":
            search_dynamic["dto"] = d_to or d_from

        try:
            raw_rows = self.execute_db_procedure(proc_name, search_dynamic, limit=50)
        except Exception as e:
            logger.exception("Failed to execute stored procedure %s: %s", proc_name, e)
            msg = f"Báo cáo ERP ({proc_name}) xử lý quá thời gian cho phép (timeout 15s). Vui lòng giới hạn khoảng thời gian hoặc lọc theo mã vật tư/kho." if "timeout" in str(e).lower() else f"Lỗi khi thực thi báo cáo ERP ({proc_name}): {str(e)}"
            return {
                "success": False,
                "report_id": report_id,
                "title": title,
                "message": msg,
                "formatted_text": f"### {title}\n- **Thông báo:** {msg}"
            }

        if not raw_rows:
            return {
                "success": True,
                "report_id": report_id,
                "title": title,
                "date_range": f"{d_from} đến {d_to}",
                "formatted_text": f"### {title}\n- **Khoảng thời gian:** {d_from} đến {d_to}\n- **Kết quả:** Không có dữ liệu phát sinh trong kỳ tra cứu."
            }

        # Format rows into Markdown presentation
        col_labels = report_meta.get("column_labels", {})
        formatted_output = self._format_procedure_result(
            title=title,
            d_from=d_from,
            d_to=d_to,
            raw_rows=raw_rows,
            col_labels=col_labels,
            summary_fields=report_meta.get("summary_fields", [])
        )

        return {
            "success": True,
            "report_id": report_id,
            "title": title,
            "row_count": len(raw_rows),
            "formatted_text": formatted_output
        }

    def _format_procedure_result(
        self,
        title: str,
        d_from: str,
        d_to: str,
        raw_rows: List[Dict[str, Any]],
        col_labels: Dict[str, str],
        summary_fields: List[str]
    ) -> str:
        """Render raw procedure rows into structured Vietnamese Markdown."""
        summary_row = None
        detail_rows = []

        for r in raw_rows:
            # Check for total / summary row
            is_summary = (
                r.get("systotal") == 1 or
                r.get("sysorder") == 1 or
                str(r.get("ten_vt", "")).strip().upper() == "TỔNG CỘNG" or
                str(r.get("dien_giai", "")).strip().upper() == "TỔNG CỘNG"
            )
            if is_summary and summary_row is None:
                summary_row = r
            else:
                detail_rows.append(r)

        # Build output markdown
        lines = [f"### {title}"]
        if d_from and d_to:
            lines.append(f"- **Khoảng thời gian:** {d_from} đến {d_to}")

        # Summary box if available
        if summary_row and summary_fields:
            summary_parts = []
            for sf in summary_fields:
                val = summary_row.get(sf)
                if val is not None:
                    label = col_labels.get(sf, sf)
                    summary_parts.append(f"**{label}:** {format_number(val)}")
            if summary_parts:
                lines.append(f"- **Tổng hợp chung:** " + " | ".join(summary_parts))

        lines.append("")

        # Identify which columns to display
        display_cols = [c for c in col_labels.keys() if any(c in r for r in detail_rows)]
        if not display_cols:
            display_cols = list(col_labels.keys())[:6]

        # Markdown Table Header
        header = "| " + " | ".join(col_labels.get(c, c) for c in display_cols) + " |"
        separator = "| " + " | ".join("---" for _ in display_cols) + " |"
        lines.append(header)
        lines.append(separator)

        for row in detail_rows[:30]:
            row_vals = []
            for c in display_cols:
                v = row.get(c)
                if v is None:
                    row_vals.append("-")
                elif isinstance(v, (int, float, Decimal)):
                    row_vals.append(format_number(v))
                else:
                    row_vals.append(str(v).strip())
            lines.append("| " + " | ".join(row_vals) + " |")

        if len(detail_rows) > 30:
            lines.append(f"\n*(Đã hiển thị 30 / {len(detail_rows)} dòng dữ liệu)*")

        return "\n".join(lines)
