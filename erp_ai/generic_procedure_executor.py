"""Generic Procedure Executor for ERP 3S & MES.

Eliminates patchwork regex handlers by executing standardized stored procedures
and catalog-driven contracts with safe PostgreSQL read-only transactions,
parameter validation, and natural Vietnamese formatting across all 8 functional
departments (IN, SO, PO, GL, MES, MF, QC, VS).
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

    def _execute_direct_sql(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Safely execute a direct SQL query inside an uncommitted transaction with 15s timeout."""
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(**connection_settings(), autocommit=False) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                try:
                    cursor.execute(sql, params)
                    return [dict(r) for r in cursor.fetchall()]
                finally:
                    conn.rollback()

    def extract_entities_from_text(self, text: str) -> Dict[str, str]:
        """Extract business entities (material code, customer/supplier code, warehouse, machine, mold) from text."""
        entities = {
            "item_code": "",
            "partner_code": "",
            "warehouse_code": "",
            "order_code": "",
            "account_code": "",
            "machine_code": "",
            "mold_code": ""
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

        # 2. Account code (111, 112, 131, 152, 1521, 154, 155, 156, 331, 511, 621, 622, 627, 632, 641, 642)
        m_acc = re.search(r"\b(?:tk|tai khoan)?\s*([1-9]\d{2,4})\b", text, re.I)
        if m_acc:
            acc_cand = m_acc.group(1)
            if any(acc_cand.startswith(p) for p in ("111", "112", "131", "152", "154", "155", "156", "331", "511", "621", "622", "627", "632", "641", "642")):
                entities["account_code"] = acc_cand

        # 3. Warehouse code (KHO_TP, KHO_NVL, KHO_THI_TRUONG, etc.)
        m_kho = re.search(r"\b(KHO[A-Z0-9_-]+)\b", text, re.I)
        if m_kho:
            entities["warehouse_code"] = m_kho.group(1).upper()

        # 4. Machine code (DUC-xxxx, DC_IN-xxxx, DC-xxxx, DC_SXLT_xxxx)
        m_machine = re.search(r"\b((?:DUC|DC|MAY)[-_][A-Z0-9_-]+)\b", text, re.I)
        if m_machine:
            entities["machine_code"] = m_machine.group(1).upper()

        # 5. Mold code (K_xxxx, xxHIxxx)
        m_mold = re.search(r"\b(K_[A-Z0-9_-]+|\d{2}[A-Z]{2}\d{3})\b", text, re.I)
        if m_mold:
            entities["mold_code"] = m_mold.group(1).upper()

        # 6. Order code (SO, PO, CT, WO) - exclude report procedure names
        m_order = re.search(r"\b(\d{3}-\d{4}-\d{6}|(?:SO|PO|HDA|PNF|PXB|CT|WO)[-_]?\d+[\w-]*)\b", text, re.I)
        if m_order:
            code = m_order.group(1).upper()
            if not code.lower().startswith("pobk") and not code.lower().startswith("sobk") and not code.lower().startswith("mesbk"):
                entities["order_code"] = code

        # 7. Item / material code
        m_item = re.search(r"\b([A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+(?:-[A-Z0-9]+)?|[A-Z]{3,}[0-9]{2,}[A-Z0-9]*)\b", text)
        if m_item:
            code = m_item.group(1).upper()
            if (not code.startswith("KHO") and not code.startswith("NCC") and not code.startswith("KH") 
                and not code.startswith("DUC") and not code.startswith("DC_") and not code.startswith("K_")
                and code != entities.get("order_code", "")):
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
        report_meta = None
        if query.strip():
            report_meta = find_report_in_catalog(query.strip())
        if not report_meta:
            report_meta = find_report_in_catalog(report_type) or find_report_in_catalog(combined_text)

        if not report_meta:
            return {
                "success": False,
                "message": f"Không tìm thấy mẫu báo cáo phù hợp cho yêu cầu: '{combined_text}'. Các báo cáo hỗ trợ gồm 8 phân hệ: KHO, BÁN HÀNG, MUA HÀNG, KẾ TOÁN (Sổ cái/Cân đối/Quỹ/Chi phí), SẢN XUẤT MES (OEE/Dừng máy/Đóng thùng/Shot), KẾ HOẠCH MF (Lệnh SX/BOM/Tiêu hao NVL/NXT công đoạn), CHẤT LƯỢNG QC (IQC/IPQC/Lỗi NVL), KHUÔN MẪU VS (Hồ sơ/Bảo trì)."
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
        c_machine = kwargs.get("machine_code") or extracted.get("machine_code", "")
        c_mold = kwargs.get("mold_code") or extracted.get("mold_code", "")
        c_order = kwargs.get("order_code") or extracted["order_code"]
        c_acc = account_code or extracted["account_code"]
        if not c_acc:
            if "331" in combined_text or "ncc" in combined_text.lower() or "nha cung cap" in combined_text.lower():
                c_acc = "331"
            elif "131" in combined_text or "khach hang" in combined_text.lower():
                c_acc = "131"
            else:
                c_acc = ""

        # ---------------------------------------------------------
        # Branch A: Specialized Native & Direct Database Handlers
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

        if report_id == "lookup_qc_lot_status":
            raw_text = self.native_tools.lookup_qc_lot_status(
                material_code=c_item,
                warehouse_code=c_warehouse,
                query_hint=combined_text
            )
            return {"success": True, "report_id": report_id, "title": title, "formatted_text": raw_text}

        if report_id == "lookup_mes_ng":
            raw_text = self.native_tools.lookup_mes_ng(
                machine_code=c_machine,
                material_code=c_item,
                date_from=d_from,
                date_to=d_to,
                query_hint=combined_text
            )
            return {"success": True, "report_id": report_id, "title": title, "formatted_text": raw_text}

        if report_id == "mesbkdongthung":
            raw_text = self.native_tools.lookup_mes_packing(
                material_code=c_item,
                production_order=c_order,
                query_hint=combined_text
            )
            return {"success": True, "report_id": report_id, "title": title, "formatted_text": raw_text}

        if report_id == "sobklenhgiaohang":
            raw_text = self.native_tools.lookup_delivery_orders(
                order_code=c_order,
                customer_code=c_partner,
                material_code=c_item,
                date_from=d_from,
                date_to=d_to,
                query_hint=combined_text
            )
            return {"success": True, "report_id": report_id, "title": title, "formatted_text": raw_text}

        if report_id == "lookup_mold_and_mes":
            raw_text = self.native_tools.lookup_mold_and_mes(
                mold_code=c_mold or kwargs.get("mold_code", ""),
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
                machine_code=c_machine or kwargs.get("machine_code", ""),
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
        # Branch A2: Kế toán Tổng hợp (GL) Direct Query Handlers
        # ---------------------------------------------------------
        if report_id == "glso1":
            acc_pattern = f"{c_acc}%" if c_acc else "%"
            tot_sql = """
                SELECT count(*) as total_count, COALESCE(SUM(c.ps_no), 0) as tot_no, COALESCE(SUM(c.ps_co), 0) as tot_co
                FROM public.ct00 c
                WHERE c.tk LIKE %s AND c.ngay_ct BETWEEN %s AND %s;
            """
            tot_rows = self._execute_direct_sql(tot_sql, (acc_pattern, d_from, d_to))
            total_count = int(tot_rows[0].get("total_count") or 0) if tot_rows else 0
            db_tot_no = Decimal(str(tot_rows[0].get("tot_no") or 0)) if tot_rows else Decimal(0)
            db_tot_co = Decimal(str(tot_rows[0].get("tot_co") or 0)) if tot_rows else Decimal(0)

            sql = """
                SELECT c.ngay_ct, c.so_ct, COALESCE(c.dien_giai, '') as dien_giai, 
                       c.tk, c.tk_du, c.ps_no, c.ps_co, COALESCE(c.ma_kh, '') as ma_kh
                FROM public.ct00 c
                WHERE c.tk LIKE %s AND c.ngay_ct BETWEEN %s AND %s
                ORDER BY c.ngay_ct DESC, c.so_ct DESC
                LIMIT 10;
            """
            rows = self._execute_direct_sql(sql, (acc_pattern, d_from, d_to))
            if rows:
                rows.append({"systotal": 1, "ps_no": db_tot_no, "ps_co": db_tot_co})
            formatted_text = self._format_procedure_result(
                title=f"{title} (TK {c_acc})" if c_acc else title,
                d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            notice = (
                f"\n\n> [!NOTE]\n"
                f"> **Tổng hợp toàn bộ kỳ từ CSDL ({total_count:,} chứng từ phát sinh):**\n"
                f"> - **Tổng phát sinh Nợ:** {db_tot_no:,.2f} VND\n"
                f"> - **Tổng phát sinh Có:** {db_tot_co:,.2f} VND\n"
                f"> *(Bảng dữ liệu trên đang hiển thị {len(rows)-1 if rows else 0} / {total_count:,} dòng chi tiết gần nhất)*"
            )
            formatted_text += notice
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "glbccdsp":
            sql = """
                SELECT c.tk, COALESCE(t.ten_tk, '') as ten_tk, 
                       SUM(c.ps_no) as tong_no, SUM(c.ps_co) as tong_co
                FROM public.ct00 c
                LEFT JOIN public.dmtk0 t ON c.tk = t.tk
                WHERE c.ngay_ct BETWEEN %s AND %s
                GROUP BY c.tk, t.ten_tk
                ORDER BY c.tk
                LIMIT 50;
            """
            rows = self._execute_direct_sql(sql, (d_from, d_to))
            tot_no = sum(Decimal(str(r.get("tong_no") or 0)) for r in rows)
            tot_co = sum(Decimal(str(r.get("tong_co") or 0)) for r in rows)
            if rows:
                rows.append({"systotal": 1, "tong_no": tot_no, "tong_co": tot_co})
            formatted_text = self._format_procedure_result(
                title=title, d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "glsoctthuchi":
            sql = """
                SELECT c.ngay_ct, c.so_ct, COALESCE(c.dien_giai, '') as dien_giai, 
                       c.tk, c.tk_du, c.ps_no as thu, c.ps_co as chi
                FROM public.ct00 c
                WHERE (c.tk LIKE '111%' OR c.tk LIKE '112%')
                  AND c.ngay_ct BETWEEN %s AND %s
                ORDER BY c.ngay_ct DESC, c.so_ct DESC
                LIMIT 10;
            """
            rows = self._execute_direct_sql(sql, (d_from, d_to))
            tot_thu = sum(Decimal(str(r.get("thu") or 0)) for r in rows)
            tot_chi = sum(Decimal(str(r.get("chi") or 0)) for r in rows)
            if rows:
                rows.append({"systotal": 1, "thu": tot_thu, "chi": tot_chi})
            formatted_text = self._format_procedure_result(
                title=title, d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "glbcchiphi":
            sql = """
                SELECT c.tk, COALESCE(t.ten_tk, '') as ten_tk, SUM(c.ps_no) as chi_phi
                FROM public.ct00 c
                LEFT JOIN public.dmtk0 t ON c.tk = t.tk
                WHERE (c.tk LIKE '154%%' OR c.tk LIKE '621%%' OR c.tk LIKE '622%%' OR c.tk LIKE '627%%' OR c.tk LIKE '641%%' OR c.tk LIKE '642%%')
                  AND c.ngay_ct BETWEEN %s AND %s
                GROUP BY c.tk, t.ten_tk
                ORDER BY c.tk;
            """
            rows = self._execute_direct_sql(sql, (d_from, d_to))
            tot_cp = sum(Decimal(str(r.get("chi_phi") or 0)) for r in rows)
            if rows:
                rows.append({"systotal": 1, "chi_phi": tot_cp})
            formatted_text = self._format_procedure_result(
                title=title, d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        # ---------------------------------------------------------
        # Branch A3: Kế hoạch Sản xuất MF Direct Query Handlers
        # ---------------------------------------------------------
        if report_id == "mfbklsx":
            sql = """
                SELECT a.so_ct, a.ngay_ct, a.ma_vt, COALESCE(v.ten_vt, '') as ten_vt, 
                       a.dvt, a.so_luong, COALESCE(b.so_dh, '') as so_dh, 
                       COALESCE(b.ma_kh, '') as ma_kh, COALESCE(b.status, '') as status
                FROM public.ctlsx a
                JOIN public.phlsx b ON a.stt_rec = b.stt_rec
                LEFT JOIN public.dmvt v ON a.ma_vt = v.ma_vt
                WHERE a.ngay_ct BETWEEN %s AND %s
                  AND (%s = '' OR a.ma_vt ILIKE %s)
                  AND (%s = '' OR a.so_ct ILIKE %s)
                ORDER BY a.ngay_ct DESC, a.so_ct DESC
                LIMIT 50;
            """
            item_pat = f"%{c_item}%" if c_item else ""
            order_pat = f"%{c_order}%" if c_order else ""
            rows = self._execute_direct_sql(sql, (d_from, d_to, c_item, item_pat, c_order, order_pat))
            tot_sl = sum(Decimal(str(r.get("so_luong") or 0)) for r in rows)
            if rows:
                rows.append({"systotal": 1, "so_luong": tot_sl})
            formatted_text = self._format_procedure_result(
                title=title, d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        # ---------------------------------------------------------
        # Branch A4: Bảng giá bán & Bảng giá mua NCC Direct Handlers
        # ---------------------------------------------------------
        if report_id == "dmbanggiact":
            sql = """
                SELECT b.ma_vt, COALESCE(v.ten_vt, '') as ten_vt, 
                       b.ma_kh, COALESCE(k.ten_kh, '') as ten_kh, 
                       b.gia_nt, b.ngay_bd, b.ngay_kt, b.ma_nt
                FROM public.dmbanggiact b
                LEFT JOIN public.dmvt v ON b.ma_vt = v.ma_vt
                LEFT JOIN public.dmkh k ON b.ma_kh = k.ma_kh
                WHERE (%s = '' OR b.ma_vt ILIKE %s)
                  AND (%s = '' OR b.ma_kh ILIKE %s)
                ORDER BY b.ngay_bd DESC
                LIMIT 50;
            """
            item_pat = f"%{c_item}%" if c_item else ""
            part_pat = f"%{c_partner}%" if c_partner else ""
            rows = self._execute_direct_sql(sql, (c_item, item_pat, c_partner, part_pat))
            formatted_text = self._format_procedure_result(
                title=title, d_from="", d_to="", raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "dmgiamuact":
            sql = """
                SELECT b.ma_vt, COALESCE(v.ten_vt, '') as ten_vt, 
                       b.ma_kh as ma_ncc, COALESCE(k.ten_kh, '') as ten_ncc, 
                       b.gia, b.ngay_bd, b.ngay_kt, b.ma_nt
                FROM public.dmgiamuact b
                LEFT JOIN public.dmvt v ON b.ma_vt = v.ma_vt
                LEFT JOIN public.dmkh k ON b.ma_kh = k.ma_kh
                WHERE (%s = '' OR b.ma_vt ILIKE %s)
                  AND (%s = '' OR b.ma_kh ILIKE %s)
                ORDER BY b.ngay_bd DESC
                LIMIT 50;
            """
            item_pat = f"%{c_item}%" if c_item else ""
            part_pat = f"%{c_partner}%" if c_partner else ""
            rows = self._execute_direct_sql(sql, (c_item, item_pat, c_partner, part_pat))
            formatted_text = self._format_procedure_result(
                title=title, d_from="", d_to="", raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        # ---------------------------------------------------------
        # Branch A5: Chất lượng QC IQC/IPQC Direct Handlers
        # ---------------------------------------------------------
        if report_id == "qcbkiqcipqc":
            sql = """
                SELECT p.so_ct, p.ngay_ct, p.ma_vt, COALESCE(v.ten_vt, '') as ten_vt, 
                       p.ma_ncc, p.so_luong as so_luong_lo, p.so_luong_ok as sl_ok, p.so_luong_ng as sl_ng,
                       CASE WHEN p.status = '1' THEN 'Đạt (OK)' ELSE 'Không đạt (NG)' END as ket_luan
                FROM public.phiqc p
                LEFT JOIN public.dmvt v ON p.ma_vt = v.ma_vt
                WHERE p.ngay_ct BETWEEN %s AND %s
                  AND (%s = '' OR p.ma_vt ILIKE %s)
                  AND (%s = '' OR p.ma_ncc ILIKE %s)
                ORDER BY p.ngay_ct DESC, p.so_ct DESC
                LIMIT 50;
            """
            item_pat = f"%{c_item}%" if c_item else ""
            part_pat = f"%{c_partner}%" if c_partner else ""
            rows = self._execute_direct_sql(sql, (d_from, d_to, c_item, item_pat, c_partner, part_pat))
            tot_lo = sum(Decimal(str(r.get("so_luong_lo") or 0)) for r in rows)
            tot_ok = sum(Decimal(str(r.get("sl_ok") or 0)) for r in rows)
            tot_ng = sum(Decimal(str(r.get("sl_ng") or 0)) for r in rows)
            if rows:
                rows.append({"systotal": 1, "so_luong_lo": tot_lo, "sl_ok": tot_ok, "sl_ng": tot_ng})
            formatted_text = self._format_procedure_result(
                title=title, d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        # ---------------------------------------------------------
        # Branch A6: Khuôn mẫu & Thiết bị (VS) Direct Handlers
        # ---------------------------------------------------------
        if report_id == "dmhosokhuon":
            sql = """
                SELECT k.ma_khuon, k.ten_khuon, k.so_cavity, k.tong_so_shot, 
                       k.so_shot_baotri, COALESCE(k.vi_tri_khuon, '') as vi_tri_khuon, 
                       COALESCE(k.status, '') as status
                FROM public.dmhosokhuon k
                WHERE (%s = '' OR k.ma_khuon ILIKE %s OR k.ten_khuon ILIKE %s)
                ORDER BY k.ma_khuon
                LIMIT 50;
            """
            m_pat = f"%{c_mold}%" if c_mold else ""
            rows = self._execute_direct_sql(sql, (c_mold, m_pat, m_pat))
            formatted_text = self._format_procedure_result(
                title=title, d_from="", d_to="", raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "dmhosokhuonsc":
            sql = """
                SELECT s.ma_khuon, s.ngay_nhan_yc, COALESCE(s.loai::text, '') as loai, 
                       COALESCE(s.noi_dung, '') as noi_dung, COALESCE(s.noi_sua::text, '') as noi_sua, 
                       COALESCE(s.trang_thai::text, '') as trang_thai
                FROM public.dmhosokhuonsc s
                WHERE (%s = '' OR s.ma_khuon ILIKE %s)
                ORDER BY s.ngay_nhan_yc DESC
                LIMIT 50;
            """
            m_pat = f"%{c_mold}%" if c_mold else ""
            rows = self._execute_direct_sql(sql, (c_mold, m_pat))
            formatted_text = self._format_procedure_result(
                title=title, d_from="", d_to="", raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "mesbcttdskhuon":
            sql = """
                SELECT k.ma_khuon, k.ten_khuon, k.tong_so_shot, k.so_shot_baotri,
                       (k.so_shot_baotri - k.tong_so_shot) as chenh_lech,
                       CASE WHEN k.so_shot_baotri > 0 AND k.tong_so_shot >= k.so_shot_baotri THEN 'CẦN BẢO DƯỠNG NGAY'
                            WHEN k.so_shot_baotri > 0 AND k.tong_so_shot >= k.so_shot_baotri * 0.8 THEN 'SẮP ĐẾN HẠN BẢO TRÌ'
                            ELSE 'BÌNH THƯỜNG' END as khuyen_nghi
                FROM public.dmhosokhuon k
                WHERE k.so_shot_baotri > 0
                ORDER BY (k.so_shot_baotri - k.tong_so_shot) ASC
                LIMIT 50;
            """
            rows = self._execute_direct_sql(sql)
            formatted_text = self._format_procedure_result(
                title=title, d_from="", d_to="", raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "so-sanh-do-fcst":
            from erp_ai.native_tools import connection_settings
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT DISTINCT id, date0
                        FROM public.mfkhsx_po_fc
                        ORDER BY id DESC LIMIT 2
                    """)
                    snapshots = cursor.fetchall()
                    if not snapshots:
                        return {"success": False, "formatted_text": "Không tìm thấy dữ liệu phiên bản cập nhật kế hoạch trong mfkhsx_po_fc."}
                    id1, d1 = snapshots[0]
                    id2 = snapshots[1][0] if len(snapshots) >= 2 else id1
                    d2 = snapshots[1][1] if len(snapshots) >= 2 else d1

                    cursor.execute("""
                        SELECT id, nguon_du_lieu, coalesce(sum(so_luong), 0)
                        FROM public.mfkhsx_po_fc
                        WHERE (%s = '' OR upper(trim(ma_vt)) = %s) AND id IN (%s, %s)
                        GROUP BY id, nguon_du_lieu
                        ORDER BY id DESC, nguon_du_lieu
                    """, (c_item, c_item, id1, id2))
                    demand_rows = cursor.fetchall()

                    cur_do, cur_fc = 0, 0
                    prev_do, prev_fc = 0, 0
                    for r in demand_rows:
                        snap_id, src, qty = r[0], str(r[1]).upper(), int(r[2])
                        if snap_id == id1:
                            if src in ("SO", "PO"):
                                cur_do += qty
                            elif src == "FC":
                                cur_fc += qty
                        elif snap_id == id2:
                            if src in ("SO", "PO"):
                                prev_do += qty
                            elif src == "FC":
                                prev_fc += qty

            diff_do = cur_do - prev_do
            pct_do = (diff_do / prev_do * 100) if prev_do > 0 else 0
            diff_fc = cur_fc - prev_fc
            pct_fc = (diff_fc / prev_fc * 100) if prev_fc > 0 else 0

            do_trend = f"tăng {diff_do:+,} PCS ({pct_do:+.2f}%)" if diff_do != 0 else "không đổi (0 PCS)"
            fc_trend = f"tăng {diff_fc:+,} PCS ({pct_fc:+.2f}%)" if diff_fc != 0 else "không đổi (0 PCS)"

            vt_title = f" — MÃ **{c_item}**" if c_item else ""
            msg = (
                f"### So sánh Biến động Demand (DO & FCST) giữa 2 Lần Cập nhật Kế hoạch{vt_title}\n\n"
                f"- **Lần cập nhật mới nhất (`{id1}` — ngày {d1})**:\n"
                f"  + Nhu cầu giao hàng DO (SO Demand): **{cur_do:,} PCS**\n"
                f"  + Dự báo nhu cầu FCST (FC Demand): **{cur_fc:,} PCS**\n\n"
                f"- **Lần cập nhật trước đó (`{id2}` — ngày {d2})**:\n"
                f"  + Nhu cầu giao hàng DO (SO Demand): **{prev_do:,} PCS**\n"
                f"  + Dự báo nhu cầu FCST (FC Demand): **{prev_fc:,} PCS**\n\n"
                f"| Chỉ tiêu Demand | Bản mới nhất ({id1}) | Bản trước ({id2}) | Chênh lệch (PCS) | Tỷ lệ biến động |\n"
                f"| :--- | :--- | :--- | :--- | :--- |\n"
                f"| **Nhu cầu giao hàng DO (SO Demand)** | {cur_do:,} PCS | {prev_do:,} PCS | {diff_do:+,} PCS | **{pct_do:+.2f}%** ({do_trend}) |\n"
                f"| **Dự báo nhu cầu FCST (FC Demand)** | {cur_fc:,} PCS | {prev_fc:,} PCS | {diff_fc:+,} PCS | **{pct_fc:+.2f}%** ({fc_trend}) |\n\n"
                f"*(Căn cứ nghiệp vụ: Hệ thống đối soát biến động demand trên cùng dải kế hoạch giữa 2 phiên bản nhập snapshot dữ liệu kế hoạch sản xuất theo chuẩn MRP/Demand Planning từ bảng `mfkhsx_po_fc`).*"
            )
            return {
                "success": True,
                "report_id": "so-sanh-do-fcst",
                "title": "So sánh biến động Demand giữa 2 lần cập nhật kế hoạch",
                "row_count": 2,
                "formatted_text": msg
            }

        if report_id == "sobkdubaotieuthu":
            sql = """
                SELECT f1.ma_fc, f1.ma_kh, f1.ma_vt, f1.ngay_ct1 as ngay_nhu_cau, f1.so_luong
                FROM public.mfdmfc1 f1
                WHERE (%s = '' OR f1.ma_kh ILIKE %s)
                  AND (%s = '' OR f1.ma_vt ILIKE %s)
                LIMIT 50;
            """
            part_pat = f"%{c_partner}%" if c_partner else ""
            item_pat = f"%{c_item}%" if c_item else ""
            rows = self._execute_direct_sql(sql, (c_partner, part_pat, c_item, item_pat))
            tot_sl = sum(Decimal(str(r.get("so_luong") or 0)) for r in rows)
            if rows:
                rows.append({"systotal": 1, "so_luong": tot_sl})
            formatted_text = self._format_procedure_result(
                title=title, d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "inbctrangthaikho":
            sql = """
                SELECT k.ma_kho, k.ten_kho, b.ma_vi_tri, b.ma_vt, b.ton00 as so_luong, 0 as suc_chua
                FROM public.cdbsp b
                JOIN public.dmkho k ON b.ma_kho = k.ma_kho
                WHERE (%s = '' OR b.ma_kho ILIKE %s)
                  AND (%s = '' OR b.ma_vt ILIKE %s)
                ORDER BY b.ma_kho, b.ma_vi_tri
                LIMIT 50;
            """
            wh_pat = f"%{c_warehouse}%" if c_warehouse else ""
            item_pat = f"%{c_item}%" if c_item else ""
            rows = self._execute_direct_sql(sql, (c_warehouse, wh_pat, c_item, item_pat))
            tot_sl = sum(Decimal(str(r.get("so_luong") or 0)) for r in rows)
            if rows:
                rows.append({"systotal": 1, "so_luong": tot_sl})
            formatted_text = self._format_procedure_result(
                title=title, d_from="", d_to="", raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id in ("inbctonkho", "inbctontheokho"):
            if any(w in combined_text.lower() for w in ("top", "lon nhat", "nhieu nhat")):
                sql = """
                    SELECT trim(b.ma_vt) as ma_vt, COALESCE(trim(v.ten_vt), '') as ten_vt, 
                           COALESCE(trim(v.dvt), 'PCS') as dvt, SUM(b.ton00) as so_luong
                    FROM public.cdbsp b
                    LEFT JOIN public.dmvt v ON trim(b.ma_vt) = trim(v.ma_vt)
                    GROUP BY trim(b.ma_vt), trim(v.ten_vt), trim(v.dvt)
                    HAVING SUM(b.ton00) > 0
                    ORDER BY so_luong DESC
                    LIMIT 10;
                """
                rows = self._execute_direct_sql(sql)
                tot_sl = sum(Decimal(str(r.get("so_luong") or 0)) for r in rows)
                if rows:
                    rows.append({"systotal": 1, "so_luong": tot_sl})
                formatted_text = self._format_procedure_result(
                    title="Báo cáo Top 10 Vật tư có Số lượng Tồn kho Lớn nhất Hiện tại",
                    d_from="", d_to="", raw_rows=rows,
                    col_labels={"ma_vt": "Mã vật tư", "ten_vt": "Tên vật tư", "dvt": "ĐVT", "so_luong": "Tồn kho"},
                    summary_fields=["so_luong"]
                )
                return {"success": True, "report_id": report_id, "title": "Top 10 Tồn kho", "row_count": len(rows), "formatted_text": formatted_text}

            if not c_item and (not c_warehouse or any(w in combined_text.lower() for w in ("theo tung kho", "phan bo", "tat ca kho", "cac kho"))):
                sql = """
                    SELECT trim(b.ma_kho) as ma_kho, COALESCE(trim(k.ten_kho), '') as ten_kho, 
                           SUM(b.ton00) as so_luong
                    FROM public.cdbsp b
                    LEFT JOIN public.dmkho k ON trim(b.ma_kho) = trim(k.ma_kho)
                    GROUP BY trim(b.ma_kho), trim(k.ten_kho)
                    HAVING SUM(b.ton00) > 0
                    ORDER BY so_luong DESC;
                """
                rows = self._execute_direct_sql(sql)
                tot_sl = sum(Decimal(str(r.get("so_luong") or 0)) for r in rows)
                if rows:
                    rows.append({"systotal": 1, "so_luong": tot_sl})
                formatted_text = self._format_procedure_result(
                    title="Báo cáo Tổng hợp Số lượng Tồn kho Phân bổ theo Từng Kho Hàng",
                    d_from="", d_to="", raw_rows=rows,
                    col_labels={"ma_kho": "Mã kho", "ten_kho": "Tên kho hàng", "so_luong": "Tổng tồn kho"},
                    summary_fields=["so_luong"]
                )
                return {"success": True, "report_id": report_id, "title": "Tồn kho theo Kho", "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "inbckstonkholo":
            sql = """
                SELECT c.ma_kho, COALESCE(k.ten_kho, '') as ten_kho, c.ma_vt, COALESCE(v.ten_vt, '') as ten_vt, 
                       c.ma_lo, c.ma_vi_tri, c.ton13 as so_luong
                FROM public.cdvt13 c
                LEFT JOIN public.dmvt v ON trim(c.ma_vt) = trim(v.ma_vt)
                LEFT JOIN public.dmkho k ON trim(c.ma_kho) = trim(k.ma_kho)
                WHERE c.ton13 > 0
                  AND (%s = '' OR c.ma_vt ILIKE %s)
                  AND (%s = '' OR c.ma_kho ILIKE %s)
                ORDER BY c.ton13 DESC
                LIMIT 50;
            """
            item_pat = f"%{c_item}%" if c_item else ""
            wh_pat = f"%{c_warehouse}%" if c_warehouse else ""
            rows = self._execute_direct_sql(sql, (c_item, item_pat, c_warehouse, wh_pat))
            tot_sl = sum(Decimal(str(r.get("so_luong") or 0)) for r in rows)
            if rows:
                rows.append({"systotal": 1, "so_luong": tot_sl})
            formatted_text = self._format_procedure_result(
                title=f"{title} ({c_item})" if c_item else title,
                d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels=report_meta.get("column_labels", {}),
                summary_fields=report_meta.get("summary_fields", [])
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "mesbkthaykhuon":
            sql = """
                SELECT v.create_date as ngay_thay, v.create_time as gio_thay, 
                       v.machine_code as ma_may, 
                       COALESCE(v.ma_khuon_xuong, '') as khuon_ha, 
                       COALESCE(v.ma_khuon_len, '') as khuon_len, 
                       COALESCE(v.employee_code, '') as ma_nv
                FROM public.mes_oi_van_hanh_khuon v
                WHERE v.create_date BETWEEN %s AND %s
                  AND (%s = '' OR v.machine_code ILIKE %s)
                  AND (%s = '' OR v.ma_khuon_xuong ILIKE %s OR v.ma_khuon_len ILIKE %s)
                ORDER BY v.create_date DESC, v.create_time DESC
                LIMIT 50;
            """
            m_pat = f"%{c_machine}%" if c_machine else ""
            mold_pat = f"%{c_mold}%" if c_mold else ""
            rows = self._execute_direct_sql(sql, (d_from, d_to, c_machine, m_pat, c_mold, mold_pat, mold_pat))
            formatted_text = self._format_procedure_result(
                title=title, d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels={"ngay_thay": "Ngày thay", "gio_thay": "Giờ thay", "ma_may": "Mã máy", "khuon_ha": "Khuôn hạ", "khuon_len": "Khuôn lắp", "ma_nv": "Nhân viên"},
                summary_fields=[]
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "mesbkbosungshot":
            sql = """
                SELECT b.date0 as ngay, b.time0 as gio, b.machine_code as ma_may, 
                       b.product_code as ma_sp, b.quantity as so_shot_bo, 
                       b.quantity_product as sl_sp_bo, COALESCE(b.production_order, '') as so_lsx
                FROM public.mes_oi_bo_shot b
                WHERE b.date0 BETWEEN %s AND %s
                  AND (%s = '' OR b.machine_code ILIKE %s)
                  AND (%s = '' OR b.product_code ILIKE %s)
                ORDER BY b.date0 DESC, b.time0 DESC
                LIMIT 50;
            """
            m_pat = f"%{c_machine}%" if c_machine else ""
            item_pat = f"%{c_item}%" if c_item else ""
            rows = self._execute_direct_sql(sql, (d_from, d_to, c_machine, m_pat, c_item, item_pat))
            tot_shot = sum(Decimal(str(r.get("so_shot_bo") or 0)) for r in rows)
            tot_sp = sum(Decimal(str(r.get("sl_sp_bo") or 0)) for r in rows)
            if rows:
                rows.append({"systotal": 1, "so_shot_bo": tot_shot, "sl_sp_bo": tot_sp})
            formatted_text = self._format_procedure_result(
                title=title, d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels={"ngay": "Ngày", "gio": "Giờ", "ma_may": "Mã máy", "ma_sp": "Mã SP", "so_shot_bo": "Shot điều chỉnh", "sl_sp_bo": "SL SP điều chỉnh", "so_lsx": "Lệnh SX"},
                summary_fields=["so_shot_bo", "sl_sp_bo"]
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

        if report_id == "mesbkgoptachthung":
            sql = """
                SELECT l.date0 as ngay, l.time0 as gio, 
                       l.id_carton as ma_thung_cu, l.id_carton_new as ma_thung_moi
                FROM public.intem_carton_log l
                WHERE l.date0 BETWEEN %s AND %s
                  AND (%s = '' OR l.id_carton ILIKE %s OR l.id_carton_new ILIKE %s)
                ORDER BY l.date0 DESC, l.time0 DESC
                LIMIT 50;
            """
            c_pat = f"%{c_order}%" if c_order else ""
            rows = self._execute_direct_sql(sql, (d_from, d_to, c_order, c_pat, c_pat))
            formatted_text = self._format_procedure_result(
                title=title, d_from=d_from, d_to=d_to, raw_rows=rows,
                col_labels={"ngay": "Ngày thao tác", "gio": "Giờ", "ma_thung_cu": "Thùng ban đầu", "ma_thung_moi": "Thùng sau gộp/tách"},
                summary_fields=[]
            )
            return {"success": True, "report_id": report_id, "title": title, "row_count": len(rows), "formatted_text": formatted_text}

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

        # Ensure type-safe defaults for numeric and time fields in Fast ERP
        search_dynamic.setdefault("limit", 50)
        search_dynamic.setdefault("offset", 0)
        search_dynamic.setdefault("index", 0)
        search_dynamic.setdefault("time_from", "00:00")
        search_dynamic.setdefault("time_to", "23:59")
        search_dynamic.setdefault("cgroup_yn", "1")
        search_dynamic.setdefault("mau_bc", "001")
        search_dynamic.setdefault("cky_bc", 1)
        search_dynamic.setdefault("ctype", "3")
        search_dynamic.setdefault("gridid", "SOBCTongHopBH001" if proc_name == "sobctonghopbh" else "ReportGrid")

        if proc_name in ("sosoctcongno1kh", "posoctcongno1ncc"):
            search_dynamic["ccust"] = c_partner
            search_dynamic["caccount"] = "331" if proc_name == "posoctcongno1ncc" else (c_acc or "131")
            search_dynamic["cbranch"] = "001"
            search_dynamic["isdetail"] = 1

        elif proc_name in ("inbctonkho", "inbctontheokho"):
            search_dynamic["dto"] = d_to or d_from

        # Guard against unindexed full-history scans on multi-million row lot tables
        if proc_name in ("bccanhbaohsd", "inbctuoithotheolo") and not c_item:
            return {
                "success": True,
                "report_id": report_id,
                "title": title,
                "rows": [],
                "row_count": 0,
                "message": f"Báo cáo '{title}' yêu cầu chỉ định mã vật tư cụ thể để tra cứu hạn sử dụng hoặc tuổi hàng theo lô.",
                "formatted_text": (
                    f"### {title}\n"
                    f"- **Yêu cầu tham số:** Vui lòng chỉ định **mã sản phẩm hoặc vật tư cụ thể** "
                    f"(ví dụ: `QC7-5146-000` hoặc `75577-BZ010`) để hệ thống tra cứu chính xác số dư và hạn sử dụng/tuổi hàng theo từng lô."
                )
            }

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
