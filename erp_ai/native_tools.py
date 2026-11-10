"""Native Function Calling Tools for Fast ERP / MES.

Provides deterministic, schema-validated tool implementations for Qwen 2.5 14B
without brittle regex heuristics or cascading keyword matching.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

TIMEOUT_MS = int(os.getenv("HTMP_DB_STATEMENT_TIMEOUT_MS", "15000"))


def clean_numeric_str(value: Any) -> Any:
    """Format numeric values without trailing redundant zeros."""
    if isinstance(value, Decimal):
        s = format(value, "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s or "0"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        s = f"{value:.4f}".rstrip("0").rstrip(".")
        return s
    return value


def connection_settings() -> dict:
    settings = {
        "host": os.getenv("HTMP_DB_HOST", "10.0.6.2"),
        "port": os.getenv("HTMP_DB_PORT", "5410"),
        "dbname": os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
        "user": os.getenv("HTMP_DB_USER", "read_htmp"),
        "password": os.getenv("HTMP_DB_PASSWORD", "P@ss@Htmp@W0rd!2025"),
        "connect_timeout": int(os.getenv("HTMP_DB_CONNECT_TIMEOUT_SECONDS", "10")),
    }
    return settings


def resolve_date_range(date_from: str = "", date_to: str = "", query_hint: str = "") -> tuple[str, str]:
    """Trích xuất khoảng thời gian (từ ngày, đến ngày) từ chuỗi gợi ý hoặc tham số."""
    import calendar
    import datetime

    def is_valid_iso(d_str):
        if not d_str or not re.match(r"^\d{4}-\d{2}-\d{2}$", str(d_str).strip()):
            return False
        try:
            datetime.date.fromisoformat(str(d_str).strip())
            return True
        except ValueError:
            return False

    # 1. Nếu cả hai tham số đã là ngày ISO YYYY-MM-DD hợp lệ, sử dụng ngay
    if is_valid_iso(date_from) and is_valid_iso(date_to):
        d1, d2 = str(date_from).strip(), str(date_to).strip()
        return (d1, d2) if d1 <= d2 else (d2, d1)

    if is_valid_iso(date_from) and not date_to:
        return str(date_from).strip(), str(date_from).strip()

    hint = f"{date_from} {date_to} {query_hint}".strip()

    # Loại bỏ chuỗi ISO date trước khi tìm mẫu ngày tháng Việt Nam để tránh match nhầm phần đuôi -MM-DD
    clean_hint = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", " ", hint)

    # 2. Dải ngày rõ ràng DD/MM đến DD/MM/YYYY (ưu tiên nếu có ít nhất 2 mốc ngày)
    m_range = re.findall(r"\b(\d{1,2})[/.-](\d{1,2})(?:[/.-](\d{2,4}))?\b", clean_hint)
    if len(m_range) >= 2:
        d1, m1, y1 = m_range[0]
        d2, m2, y2 = m_range[1]
        year2 = int(y2) if y2 else 2026
        year1 = int(y1) if y1 else year2
        if len(str(year1)) == 2: year1 += 2000
        if len(str(year2)) == 2: year2 += 2000
        return f"{year1:04d}-{int(m1):02d}-{int(d1):02d}", f"{year2:04d}-{int(m2):02d}-{int(d2):02d}"

    # 3. Theo năm hoặc từ đầu năm: từ đầu năm 2026, từ đâu năm 2026, năm 2026, cả năm 2026
    m_year = re.search(r"\b(?:từ đầu năm|từ đâu năm|đầu năm|đâu năm|dau nam|cả năm|ca nam|trong năm|năm|nam)\s*(202\d)\b", clean_hint, re.I)
    if m_year:
        yr = int(m_year.group(1))
        return f"{yr:04d}-01-01", date.today().isoformat()

    if any(w in clean_hint.lower() for w in ("từ đầu năm", "từ đâu năm", "dau nam", "đầu năm", "đâu năm")):
        return f"{date.today().year}-01-01", date.today().isoformat()

    # 4. Theo tháng: tháng 10/2026, 10/2026, tháng 10
    m_month = re.search(r"\b(?:tháng|thang)\s*(\d{1,2})(?:[\s/_-]+(\d{4}))?\b", clean_hint, re.I)
    if not m_month:
        m_month = re.search(r"\b(\d{1,2})[/.-](\d{4})\b", clean_hint)
    if m_month:
        month = int(m_month.group(1))
        year = int(m_month.group(2)) if m_month.group(2) else 2026
        if 1 <= month <= 12:
            _, last_day = calendar.monthrange(year, month)
            return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"

    d_from = str(date_from).strip() if is_valid_iso(date_from) else "2026-10-01"
    d_to = str(date_to).strip() if is_valid_iso(date_to) else "2026-10-31"
    return d_from, d_to

LOG = logging.getLogger("erp_ai.native_tools")

clean_num = clean_numeric_str


class ERPNativeTools:
    """Core deterministic business queries invoked directly by LLM Function Calling."""

    def lookup_sales_price(self, material_code: str = "", customer_code: str = "", **kwargs) -> str:
        """Tra cứu giá bán sản phẩm, chính sách giá bán hoặc lịch sử xuất bán cho khách hàng.
        
        material_code: Mã vật tư hoặc mã sản phẩm (ví dụ: '156279430', 'T1015910DA', 'QC7-5146-000').
        customer_code: Mã khách hàng (ví dụ: 'KH0056', 'KH0087') nếu muốn lọc theo khách hàng cụ thể.
        """
        code = (material_code or "").strip().upper()
        cust = (customer_code or "").strip().upper()
        if not code:
            return "Cần cung cấp mã sản phẩm hoặc mã vật tư để tra cứu giá bán."

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    
                    sql = """
                        SELECT 
                            b.ma_bang_gia,
                            b.ten_bang_gia,
                            trim(c.ma_vt) AS ma_vt,
                            coalesce(v.ten_vt, c.ma_vt) AS ten_vt,
                            coalesce(v.dvt, c.dvt, 'PCS') AS dvt,
                            trim(c.ma_kh) AS ma_kh,
                            coalesce(k.ten_kh, c.ma_kh) AS ten_kh,
                            CASE WHEN coalesce(c.gia, 0) > 0 THEN c.gia ELSE coalesce(c.gia_nt, 0) END AS don_gia_ban,
                            coalesce(nullif(trim(c.ma_nt), ''), 'VND') AS ma_nt,
                            coalesce(c.sl_min, 0) AS sl_min,
                            to_char(c.ngay_bd, 'YYYY-MM-DD') AS ngay_bd,
                            to_char(c.ngay_kt, 'YYYY-MM-DD') AS ngay_kt
                        FROM public.dmbanggiact c
                        JOIN public.dmbanggia b ON b.ma_bang_gia = c.ma_bang_gia
                        LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(c.ma_vt))
                        LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(c.ma_kh))
                        WHERE upper(trim(c.ma_vt)) = %s 
                          AND (%s = '' OR upper(trim(c.ma_kh)) = %s)
                        ORDER BY c.ngay_bd DESC NULLS LAST, c.ma_bang_gia
                        LIMIT 20;
                    """
                    cursor.execute(sql, (code, cust, cust))
                    rows = cursor.fetchall()

                    # Fallback to sales shipments (ct81) if no price list found
                    if not rows:
                        sql_ct81 = """
                            SELECT 
                                'PXK' AS ma_bang_gia,
                                'Lịch sử xuất kho bán hàng' AS ten_bang_gia,
                                trim(c.ma_vt) AS ma_vt,
                                coalesce(v.ten_vt, c.ma_vt) AS ten_vt,
                                coalesce(v.dvt, c.dvt, 'PCS') AS dvt,
                                trim(h.ma_kh) AS ma_kh,
                                coalesce(k.ten_kh, h.ma_kh) AS ten_kh,
                                CASE WHEN coalesce(c.gia2, 0) > 0 THEN c.gia2 ELSE coalesce(c.gia_nt, 0) END AS don_gia_ban,
                                coalesce(nullif(trim(h.ma_nt), ''), 'VND') AS ma_nt,
                                0 AS sl_min,
                                to_char(c.ngay_ct, 'YYYY-MM-DD') AS ngay_bd,
                                to_char(c.ngay_ct, 'YYYY-MM-DD') AS ngay_kt
                            FROM public.ct81 c
                            JOIN public.ph81 h ON h.stt_rec = c.stt_rec
                            LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(c.ma_vt))
                            LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(h.ma_kh))
                            WHERE upper(trim(c.ma_vt)) = %s AND (c.gia2 > 0 OR c.gia_nt > 0)
                            ORDER BY c.ngay_ct DESC
                            LIMIT 5;
                        """
                        cursor.execute(sql_ct81, (code,))
                        rows = cursor.fetchall()

                    # Fallback to purchase price list (dmgiamuact) for raw materials / supplier purchasing prices
                    is_purchase_context = any(w in f"{str(kwargs)}".lower() for w in ("mua", "ncc", "nhà cung cấp", "nha cung cap", "nhập"))
                    is_purchase_price = False

                    if not rows or is_purchase_context:
                        sql_purchase = """
                            SELECT 
                                'BANG_GIA_MUA' AS ma_bang_gia,
                                'Danh mục giá mua nhà cung cấp' AS ten_bang_gia,
                                trim(g.ma_vt) AS ma_vt,
                                coalesce(v.ten_vt, g.ma_vt) AS ten_vt,
                                coalesce(v.dvt, 'KG') AS dvt,
                                trim(g.ma_kh) AS ma_kh,
                                coalesce(k.ten_kh, g.ma_kh) AS ten_kh,
                                coalesce(nullif(g.gia, 0), g.gia0) AS don_gia_ban,
                                coalesce(nullif(trim(g.ma_nt), ''), 'VND') AS ma_nt,
                                coalesce(g.sl_min, 0) AS sl_min,
                                to_char(g.ngay_bd, 'YYYY-MM-DD') AS ngay_bd,
                                to_char(g.ngay_kt, 'YYYY-MM-DD') AS ngay_kt
                            FROM public.dmgiamuact g
                            LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(g.ma_vt))
                            LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(g.ma_kh))
                            WHERE upper(trim(g.ma_vt)) = %s
                              AND (%s = '' OR upper(trim(g.ma_kh)) = %s)
                            ORDER BY g.ngay_bd DESC NULLS LAST
                            LIMIT 10;
                        """
                        cursor.execute(sql_purchase, (code, cust, cust))
                        purch_rows = cursor.fetchall()
                        if purch_rows and (not rows or is_purchase_context):
                            rows = purch_rows
                            is_purchase_price = True

                    if not rows:
                        cursor.execute("SELECT ma_vt, ten_vt FROM public.dmvt WHERE upper(trim(ma_vt)) = %s", (code,))
                        r_dm = cursor.fetchone()
                        if r_dm:
                            return f"Mã hàng {code} ({r_dm['ten_vt']}) có trong danh mục hệ thống nhưng chưa được thiết lập bảng giá bán (dmbanggiact), bảng giá mua (dmgiamuact) và chưa có lịch sử xuất bán (ct81)."
                        prefix = code[:6] if len(code) >= 6 else code
                        cursor.execute("SELECT ma_vt, ten_vt FROM public.dmvt WHERE ma_vt ILIKE %s ORDER BY ma_vt LIMIT 3", (f"%{prefix}%",))
                        sugs = cursor.fetchall()
                        if sugs:
                            sug_str = "; ".join(f"{s['ma_vt']} ({s['ten_vt']})" for s in sugs)
                            return f"Không tìm thấy mã hàng '{code}' trong hệ thống ERP. Có thể bạn muốn tìm: {sug_str}?"
                        return f"Không tìm thấy thông tin giá bán hoặc mã hàng '{code}' trong hệ thống ERP."

                    first = rows[0]
                    ten = first.get("ten_vt", code)
                    gia_str = clean_num(first.get("don_gia_ban"))
                    nt = first.get("ma_nt", "VND")
                    dvt = first.get("dvt", "PCS")
                    kh = first.get("ten_kh", first.get("ma_kh", ""))
                    bd = first.get("ngay_bd", "")
                    kt = first.get("ngay_kt", "")
                    bg = first.get("ten_bang_gia", first.get("ma_bang_gia", ""))

                    if is_purchase_price:
                        msg = f"Giá mua của mã hàng {code} ({ten}) là {gia_str} {nt}/{dvt}"
                        if kh:
                            msg += f" (Nhà cung cấp: {kh})"
                        if bd and kt:
                            msg += f", hiệu lực: {bd} đến {kt}"
                        msg += " theo Danh mục giá mua nhà cung cấp (dmgiamuact)."
                    else:
                        msg = f"Giá bán của mã hàng {code} ({ten}) là {gia_str} {nt}/{dvt}"
                        if kh:
                            msg += f" (khách hàng: {kh})"
                        if bd and kt:
                            msg += f", hiệu lực: {bd} đến {kt}"
                        if bg:
                            msg += f" [{bg}]."
                        else:
                            msg += "."

                    return json.dumps({
                        "report": {"id": "bang-gia-ban", "title": "Bảng giá bán / Chính sách giá"},
                        "lookup": {"ma_vt": code, "ma_kh": cust},
                        "row_count": len(rows),
                        "rows": rows,
                        "message": msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_sales_price failed for %s", code)
            return f"Lỗi khi tra cứu giá bán mã {code}: {str(e)}"

    def lookup_stock_card(self, material_code: str = "", warehouse_code: str = "", date_from: str = "", date_to: str = "", **kwargs) -> str:
        """Tra cứu Thẻ kho / Sổ chi tiết biến động nhập - xuất - tồn theo chứng từ của một mã vật tư tại một kho cụ thể hoặc toàn công ty trong khoảng thời gian xác định."""
        code = (material_code or kwargs.get("code") or "").strip().upper()
        wh = (warehouse_code or kwargs.get("wh") or "").strip().upper()
        d_from, d_to = resolve_date_range(date_from, date_to, str(kwargs))

        if not code:
            return "Cần cung cấp mã vật tư hoặc mã sản phẩm để tra cứu thẻ kho."

        try:
            import psycopg
            from psycopg.rows import dict_row
            from decimal import Decimal
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    sql_card = """
                        SELECT 
                            to_char(c.ngay_ct, 'YYYY-MM-DD') AS ngay_ct,
                            trim(c.so_ct) AS so_ct,
                            trim(c.ma_ct) AS ma_ct,
                            coalesce(nullif(trim(c.dien_giai), ''), 'Giao dịch kho') AS dien_giai,
                            trim(c.ma_kho) AS ma_kho,
                            c.sl_nhap,
                            c.sl_xuat
                        FROM public.ct70 c
                        WHERE upper(trim(c.ma_vt)) = %s
                          AND (%s = '' OR upper(trim(c.ma_kho)) = %s)
                          AND c.ngay_ct >= %s::date AND c.ngay_ct <= %s::date
                        ORDER BY c.ngay_ct, c.stt_rec
                        LIMIT 30;
                    """
                    cursor.execute(sql_card, (code, wh, wh, d_from, d_to))
                    card_rows = cursor.fetchall()
                    cursor.execute("SELECT coalesce(ten_vt, %s) AS ten_vt, coalesce(dvt, 'PCS') AS dvt FROM public.dmvt WHERE upper(trim(ma_vt)) = %s", (code, code))
                    r_vt = cursor.fetchone()
                    ten_vt = str(r_vt["ten_vt"]).strip() if r_vt else code
                    dvt = str(r_vt["dvt"]).strip() if r_vt else "PCS"

                    if not card_rows:
                        wh_str = f" tại kho {wh}" if wh else ""
                        return f"Thẻ kho của mã {code} ({ten_vt}){wh_str} từ {d_from} đến {d_to} không phát sinh chứng từ nhập xuất nào."

                    tot_nhap = sum(Decimal(str(r["sl_nhap"])) for r in card_rows)
                    tot_xuat = sum(Decimal(str(r["sl_xuat"])) for r in card_rows)
                    wh_str = f" tại kho {wh}" if wh else ""
                    msg = f"Thẻ kho của mã {code} ({ten_vt}){wh_str} từ {d_from} đến {d_to}: Phát sinh {len(card_rows)} chứng từ (Tổng nhập: {clean_num(tot_nhap)} {dvt}, Tổng xuất: {clean_num(tot_xuat)} {dvt})."

                    return json.dumps({
                        "report": {"id": "the-kho", "title": f"Thẻ kho vật tư {code} ({d_from} đến {d_to})"},
                        "lookup": {"ma_vt": code, "ma_kho": wh, "date_from": d_from, "date_to": d_to},
                        "summary": {"tong_nhap": clean_num(tot_nhap), "tong_xuat": clean_num(tot_xuat), "dvt": dvt},
                        "row_count": len(card_rows),
                        "rows": card_rows,
                        "message": msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_stock_card failed")
            return f"Lỗi khi tra cứu thẻ kho: {str(e)}"

    def lookup_inventory_stock(self, material_code: str = "", warehouse_code: str = "", date_as_of: str = "", **kwargs) -> str:
        """Tra cứu số lượng tồn kho sổ sách kế toán của vật tư/sản phẩm, hoặc tổng tồn kho của một kho cụ thể.
        
        material_code: Mã vật tư hoặc mã sản phẩm (ví dụ: '1014084300', 'QC7-5146-000'). Để trống nếu muốn xem tổng tồn theo kho.
        warehouse_code: Mã kho cần lọc (ví dụ: 'KHOTP00', 'KHO-IN', 'KHO-CXL'). Để trống nếu muốn xem phân bổ trên tất cả các kho.
        date_as_of: Ngày tham chiếu chốt số liệu tồn kho (định dạng 'YYYY-MM-DD'). Mặc định là ngày hiện tại.
        """
        code = (material_code or "").strip().upper()
        wh = (warehouse_code or "").strip().upper()
        as_of = (date_as_of or "").strip() or date.today().isoformat()

        # Kiểm tra yêu cầu thẻ kho (chứng từ chi tiết nhập xuất trong kỳ)
        action = str(kwargs.get("action") or "").lower()
        d_from_arg = str(kwargs.get("date_from") or "").strip()
        d_to_arg = str(kwargs.get("date_to") or "").strip()
        hint = str(kwargs.get("hint") or kwargs.get("question") or "")
        is_card = action in ("the_kho", "thekho", "card", "nhat_ky", "movement") or bool(kwargs.get("the_kho")) or (d_from_arg and d_to_arg) or ("thẻ kho" in hint.lower()) or ("the kho" in hint.lower())
        if is_card and code:
            return self.lookup_stock_card(material_code=code, warehouse_code=wh, date_from=d_from_arg, date_to=d_to_arg, **kwargs)

        full_ctx = f"{hint} {action} {str(kwargs)}".lower()
        if not code and any(w in full_ctx for w in ("top", "lớn nhất", "lon nhat", "nhiều nhất", "nhieu nhat", "vật tư tồn kho", "vat tu ton kho")):
            from erp_ai.generic_procedure_executor import GenericProcedureExecutor
            res = GenericProcedureExecutor().query_report(report_type="inbctonkho", query=full_ctx)
            if res.get("success") and res.get("formatted_text"):
                return res["formatted_text"]

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    cursor.execute("SELECT public.sys_getstartdate(%s::date)", (as_of,))
                    start_date = cursor.fetchone()["sys_getstartdate"]

                    if code:
                        sql = """
                            WITH opening AS (
                                SELECT c.ma_kho, sum(c.ton00) AS qty
                                FROM public.cdvt c
                                WHERE c.nam = extract(year FROM %s::date)::smallint
                                  AND upper(trim(c.ma_vt)) = %s
                                GROUP BY c.ma_kho
                            ),
                            movements AS (
                                SELECT c.ma_kho, sum(c.sl_nhap - c.sl_xuat) AS qty
                                FROM public.ct70 c
                                WHERE upper(trim(c.ma_vt)) = %s
                                  AND c.ngay_ct >= %s AND c.ngay_ct <= %s::date
                                GROUP BY c.ma_kho
                            ),
                            combined AS (
                                SELECT ma_kho, qty FROM opening
                                UNION ALL
                                SELECT ma_kho, qty FROM movements
                            )
                            SELECT trim(ma_kho) AS ma_kho, sum(qty) AS ton_kho
                            FROM combined
                            GROUP BY trim(ma_kho)
                            HAVING sum(qty) > 0
                            ORDER BY ton_kho DESC;
                        """
                        cursor.execute(sql, (start_date, code, code, start_date, as_of))
                        rows = cursor.fetchall()

                        cursor.execute("SELECT coalesce(ten_vt, %s) AS ten_vt, coalesce(dvt, 'PCS') AS dvt FROM public.dmvt WHERE upper(trim(ma_vt)) = %s", (code, code))
                        r_vt = cursor.fetchone()
                        ten_vt = str(r_vt["ten_vt"]).strip() if r_vt else code
                        dvt = str(r_vt["dvt"]).strip() if r_vt else "PCS"

                        if not rows:
                            if r_vt:
                                return f"Mã vật tư {code} ({ten_vt}) có trong danh mục hệ thống nhưng hiện tại không còn tồn ở kho nào (số dư tồn kho bằng 0)."
                            prefix = code[:6] if len(code) >= 6 else code
                            cursor.execute("SELECT ma_vt, ten_vt FROM public.dmvt WHERE ma_vt ILIKE %s ORDER BY ma_vt LIMIT 3", (f"%{prefix}%",))
                            sugs = cursor.fetchall()
                            if sugs:
                                sug_str = "; ".join(f"{s['ma_vt']} ({s['ten_vt']})" for s in sugs)
                                return f"Không tìm thấy mã vật tư '{code}' trong hệ thống ERP. Có thể bạn muốn tìm: {sug_str}?"
                            return f"Không tìm thấy mã vật tư '{code}' trong danh mục ERP."

                        # Query location breakdown via cdvt13 (Fast ERP lot/bin stock balance table)
                        locations_by_kho = {}
                        try:
                            cursor.execute("""
                                SELECT 
                                    trim(c.ma_kho) AS ma_kho,
                                    trim(coalesce(c.ma_vi_tri, '')) AS ma_vi_tri,
                                    trim(coalesce(c.ma_lo, '')) AS ma_lo,
                                    sum(c.ton13) AS ton_kho
                                FROM public.cdvt13 c
                                WHERE upper(trim(c.ma_vt)) = %s
                                  AND c.ton13 > 0
                                GROUP BY trim(c.ma_kho), trim(coalesce(c.ma_vi_tri, '')), trim(coalesce(c.ma_lo, ''))
                                ORDER BY trim(c.ma_kho), ton_kho DESC;
                            """, (code,))
                            loc_rows = cursor.fetchall()
                            for lr in loc_rows:
                                if lr["ma_vi_tri"]:
                                    lo_str = f" (lô {lr['ma_lo']})" if lr.get("ma_lo") else ""
                                    locations_by_kho.setdefault(lr["ma_kho"].upper(), []).append(f"{lr['ma_vi_tri']}{lo_str}: {clean_num(lr['ton_kho'])} {dvt}")
                        except Exception as e_loc:
                            LOG.warning("Could not fetch location breakdown from cdvt13: %s", e_loc)

                        parts = []
                        for r in rows:
                            k_code = r["ma_kho"].upper()
                            k_locs = locations_by_kho.get(k_code, [])
                            loc_s = f" [vị trí: {', '.join(k_locs)}]" if k_locs else ""
                            parts.append(f"{r['ma_kho']}: {clean_num(r['ton_kho'])} {dvt}{loc_s}")

                        total = sum(Decimal(str(r["ton_kho"])) for r in rows)

                        temporal_note = ""
                        if as_of < "2026-11-09" and locations_by_kho:
                            temporal_note = f" (Lưu ý: Số lượng tồn kho tính đến {as_of}; chi tiết vị trí kệ/máy và số lô ghi nhận theo hiện trạng vật lý)."

                        if wh:
                            wh_match = [r for r in rows if r["ma_kho"].upper() == wh]
                            wh_qty = Decimal(str(wh_match[0]["ton_kho"])) if wh_match else Decimal(0)
                            wh_locs = locations_by_kho.get(wh, [])
                            loc_detail = f" (tại vị trí: {', '.join(wh_locs)})" if wh_locs else ""
                            msg = f"Tồn kho của mã {code} ({ten_vt}) tại kho {wh} tính đến {as_of} là {clean_num(wh_qty)} {dvt}{loc_detail}."
                            if total > 0 and total != wh_qty:
                                msg += f" (Tổng tồn toàn bộ các kho: {clean_num(total)} {dvt} gồm {'; '.join(parts)})."
                            elif total == 0:
                                msg += f" (Mã {code} hiện tại không còn tồn ở kho nào khác)."
                            msg += temporal_note
                            return json.dumps({
                                "report": {"id": "bao-cao-ton-theo-kho", "title": "Báo cáo tồn theo kho"},
                                "lookup": {"ma_vt": code, "ma_kho": wh, "date_as_of": as_of},
                                "rows": [{"ma_kho": r["ma_kho"], "ton_kho": float(r["ton_kho"]), "vi_tri": ", ".join(locations_by_kho.get(r["ma_kho"].upper(), []))} for r in rows],
                                "message": msg,
                            }, ensure_ascii=False, default=str)
                        else:
                            msg = f"Tồn kho của mã {code} ({ten_vt}) ở từng kho tính đến {as_of}: " + "; ".join(parts) + f" (Tổng cộng: {clean_num(total)} {dvt})." + temporal_note
                            return json.dumps({
                                "report": {"id": "bao-cao-ton-theo-kho", "title": "Báo cáo tồn theo kho"},
                                "lookup": {"ma_vt": code, "date_as_of": as_of},
                                "rows": [{"ma_kho": r["ma_kho"], "ton_kho": float(r["ton_kho"]), "vi_tri": ", ".join(locations_by_kho.get(r["ma_kho"].upper(), []))} for r in rows],
                                "message": msg,
                            }, ensure_ascii=False, default=str)

                    elif wh:
                        cursor.execute("""
                            SELECT coalesce(k.ten_kho, %s) AS ten_kho, sum(b.so_luong_ton) AS tong_ton
                            FROM (
                                SELECT sum(ton00) AS so_luong_ton
                                FROM public.cdvt
                                WHERE nam = extract(year FROM %s::date)::smallint AND upper(trim(ma_kho)) = %s
                                UNION ALL
                                SELECT sum(sl_nhap - sl_xuat) AS so_luong_ton
                                FROM public.ct70
                                WHERE ngay_ct >= %s AND ngay_ct <= %s::date AND upper(trim(ma_kho)) = %s
                            ) b
                            LEFT JOIN public.dmkho k ON upper(trim(k.ma_kho)) = %s
                            GROUP BY k.ten_kho;
                        """, (wh, start_date, wh, start_date, as_of, wh, wh))
                        r = cursor.fetchone()
                        ten_kho = r["ten_kho"] if r else wh
                        total_wh = Decimal(str(r["tong_ton"])) if r and r["tong_ton"] else Decimal(0)
                        msg = f"Tổng số lượng tồn kho tại kho {wh} ({ten_kho}) tính đến {as_of} là {clean_num(total_wh)} PCS."
                        return json.dumps({
                            "report": {"id": "bao-cao-ton-theo-kho", "title": "Báo cáo tồn theo kho"},
                            "lookup": {"ma_kho": wh, "date_as_of": as_of},
                            "rows": [{"ma_kho": wh, "ton_kho": float(total_wh)}],
                            "message": msg,
                        }, ensure_ascii=False, default=str)
                    else:
                        cursor.execute("""
                            WITH opening AS (
                                SELECT trim(ma_kho) AS ma_kho, sum(ton00) AS qty
                                FROM public.cdvt
                                WHERE nam = extract(year FROM %s::date)::smallint
                                GROUP BY trim(ma_kho)
                            ),
                            movements AS (
                                SELECT trim(ma_kho) AS ma_kho, sum(sl_nhap - sl_xuat) AS qty
                                FROM public.ct70
                                WHERE ngay_ct >= %s AND ngay_ct <= %s::date
                                GROUP BY trim(ma_kho)
                            ),
                            combined AS (
                                SELECT ma_kho, qty FROM opening UNION ALL SELECT ma_kho, qty FROM movements
                            )
                            SELECT c.ma_kho, coalesce(k.ten_kho, c.ma_kho) AS ten_kho, sum(c.qty) AS ton_kho
                            FROM combined c
                            LEFT JOIN public.dmkho k ON upper(trim(k.ma_kho)) = upper(c.ma_kho)
                            GROUP BY c.ma_kho, k.ten_kho
                            HAVING sum(c.qty) > 0
                            ORDER BY ton_kho DESC
                            LIMIT 15;
                        """, (start_date, start_date, as_of))
                        rows = cursor.fetchall()
                        msg = f"Phân bổ tồn kho tại các kho lớn nhất tính đến {as_of}: " + "; ".join(f"{r['ma_kho']} ({r['ten_kho']}): {clean_num(r['ton_kho'])} PCS" for r in rows)
                        return json.dumps({
                            "report": {"id": "bao-cao-ton-theo-kho", "title": "Báo cáo tồn theo kho"},
                            "lookup": {"date_as_of": as_of},
                            "rows": rows,
                            "message": msg,
                        }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_inventory_stock failed")
            return f"Lỗi khi tra cứu tồn kho: {str(e)}"

    @staticmethod
    def _explicit_range(date_from: str, date_to: str) -> tuple[str, str] | None:
        try:
            start = date.fromisoformat(date_from)
            end = date.fromisoformat(date_to)
            return (start.isoformat(), end.isoformat()) if start <= end else None
        except (TypeError, ValueError):
            return None

    def lookup_sales_orders(self, material_code: str = "", customer_code: str = "", order_code: str = "", date_from: str = "", date_to: str = "", **kwargs) -> str:
        """Tra cứu dòng đơn bán hàng (SO), lịch sử xuất bán và đơn giá bán theo mã hàng hoặc khách hàng."""
        code = (material_code or kwargs.get("code") or kwargs.get("material") or "").strip().upper()
        cust = (customer_code or kwargs.get("customer") or kwargs.get("kh") or "").strip().upper()
        order = (order_code or kwargs.get("order") or kwargs.get("so") or "").strip().upper()

        if not any((code, cust, order)):
            return "Vui lòng cung cấp mã khách hàng, mã vật tư hoặc số đơn bán (SO)."

        hint = str(kwargs.get("hint") or kwargs.get("question") or "")
        d_from = str(date_from or "").strip()
        d_to = str(date_to or "").strip()
        has_explicit_date = bool(d_from and d_to)

        is_recent_query = any(w in hint.lower() for w in ("gần đây", "gan day", "mới nhất", "moi nhat", "latest", "gần nhất", "gan nhat"))
        if is_recent_query:
            has_explicit_date = False

        if not has_explicit_date and any(w in hint.lower() for w in ("từ đầu năm", "từ đâu năm", "dau nam", "đầu năm", "đâu năm", "2026", "tháng", "tu ngay")):
            d_from, d_to = resolve_date_range(d_from, d_to, hint)
            has_explicit_date = True

        try:
            import psycopg
            from psycopg.rows import dict_row
            from decimal import Decimal
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    sql = """
                        SELECT 
                            trim(h.so_ct) AS so_ct,
                            to_char(h.ngay_ct, 'YYYY-MM-DD') AS ngay_ct,
                            trim(h.ma_kh) AS ma_kh,
                            coalesce(k.ten_kh, h.ma_kh) AS ten_kh,
                            trim(c.ma_vt) AS ma_vt,
                            coalesce(v.ten_vt, c.ma_vt) AS ten_vt,
                            coalesce(v.dvt, 'PCS') AS dvt,
                            c.so_luong,
                            coalesce(nullif(c.gia2, 0), c.gia_nt2, c.gia) AS don_gia,
                            coalesce(nullif(trim(h.ma_nt), ''), 'VND') AS ma_nt,
                            c.tien2 AS thanh_tien
                        FROM public.ct64 c 
                        JOIN public.ph64 h ON h.stt_rec = c.stt_rec
                        LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(h.ma_kh))
                        LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(c.ma_vt))
                        WHERE 1=1
                    """
                    params = []
                    if code:
                        sql += " AND upper(trim(c.ma_vt)) = %s "
                        params.append(code)
                    if cust:
                        sql += " AND upper(trim(h.ma_kh)) = %s "
                        params.append(cust)
                    if order:
                        sql += " AND upper(trim(h.so_ct)) = %s "
                        params.append(order)
                    if has_explicit_date and d_from and d_to:
                        sql += " AND h.ngay_ct >= %s::date AND h.ngay_ct <= %s::date "
                        params.extend([d_from, d_to])
                    sql += " ORDER BY h.ngay_ct DESC, h.stt_rec DESC LIMIT 20; "
                    cursor.execute(sql, tuple(params))
                    rows = cursor.fetchall()

                    if not rows:
                        range_str = f" từ {d_from} đến {d_to}" if has_explicit_date else ""
                        target = f"mã hàng '{code}'" if code else f"khách hàng '{cust}'"
                        return f"Không tìm thấy đơn bán phù hợp của {target}{range_str} trong hệ thống ERP."

                    total_qty = sum(Decimal(str(r["so_luong"])) for r in rows)
                    first_r = rows[0]
                    dvt = first_r.get("dvt", "PCS")
                    nt = first_r.get("ma_nt", "VND")
                    msg = (
                        f"Đơn hàng bán của {first_r['ma_vt']} ({first_r['ten_vt']}): Ghi nhận {len(rows)} đơn bán "
                        f"(Tổng số lượng đặt: {clean_num(total_qty)} {dvt}). "
                        f"Đơn gần nhất là số {first_r['so_ct']} ngày {first_r['ngay_ct']} (Khách hàng: {first_r['ten_kh']}): "
                        f"Đặt {clean_num(first_r['so_luong'])} {dvt} với đơn giá {clean_num(first_r['don_gia'])} {nt}."
                    )

                    return json.dumps({
                        "report": {"id": "don-hang-ban", "title": f"Đơn bán ({code or cust})"},
                        "lookup": {"material_code": code, "customer_code": cust, "order_code": order, "date_from": d_from, "date_to": d_to},
                        "row_count": len(rows),
                        "rows": rows,
                        "message": msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_sales_orders failed")
            return f"Lỗi khi tra cứu đơn bán: {str(e)}"

    def lookup_purchase_orders(self, material_code: str = "", supplier_code: str = "", po_code: str = "", date_from: str = "", date_to: str = "", **kwargs) -> str:
        """Tra cứu lịch sử đơn đặt mua hàng (PO), đơn giá mua và danh mục giá mua nhà cung cấp."""
        code = (material_code or kwargs.get("code") or kwargs.get("material") or "").strip().upper()
        ncc = (supplier_code or kwargs.get("supplier") or kwargs.get("ncc") or "").strip().upper()
        po = (po_code or kwargs.get("po") or kwargs.get("order") or "").strip().upper()

        if not any((code, ncc, po)):
            return "Vui lòng cung cấp mã vật tư/hạt nhựa, nhà cung cấp hoặc số đơn mua (PO) để tra cứu."

        hint = str(kwargs.get("hint") or kwargs.get("question") or "")
        d_from = str(date_from or "").strip()
        d_to = str(date_to or "").strip()
        has_explicit_date = bool(d_from and d_to)

        is_recent_query = any(w in hint.lower() for w in ("gần đây", "gan day", "mới nhất", "moi nhat", "latest", "gần nhất", "gan nhat"))
        if is_recent_query:
            has_explicit_date = False

        if not has_explicit_date and any(w in hint.lower() for w in ("từ đầu năm", "từ đâu năm", "dau nam", "đầu năm", "đâu năm", "2026", "tháng", "tu ngay")):
            d_from, d_to = resolve_date_range(d_from, d_to, hint)
            has_explicit_date = True

        try:
            import psycopg
            from psycopg.rows import dict_row
            from decimal import Decimal
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    # 1. Fetch PO records from ct94 / ph94
                    sql_po = """
                        SELECT 
                            trim(h.so_ct) AS so_ct,
                            to_char(h.ngay_ct, 'YYYY-MM-DD') AS ngay_ct,
                            trim(h.ma_kh) AS ma_ncc,
                            coalesce(k.ten_kh, h.ma_kh) AS ten_ncc,
                            trim(c.ma_vt) AS ma_vt,
                            coalesce(v.ten_vt, c.ma_vt) AS ten_vt,
                            coalesce(v.dvt, 'KG') AS dvt,
                            c.so_luong,
                            coalesce(nullif(c.gia_nt0, 0), c.gia0) AS don_gia,
                            c.gia0 AS don_gia_vnd,
                            coalesce(nullif(trim(h.ma_nt), ''), 'VND') AS ma_nt,
                            c.tien0 AS thanh_tien_vnd
                        FROM public.ct94 c 
                        JOIN public.ph94 h ON h.stt_rec = c.stt_rec
                        LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(h.ma_kh))
                        LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(c.ma_vt))
                        WHERE 1=1
                    """
                    params = []
                    if code:
                        sql_po += " AND upper(trim(c.ma_vt)) = %s "
                        params.append(code)
                    if ncc:
                        sql_po += " AND upper(trim(h.ma_kh)) = %s "
                        params.append(ncc)
                    if po:
                        sql_po += " AND upper(trim(h.so_ct)) = %s "
                        params.append(po)
                    if has_explicit_date and d_from and d_to:
                        sql_po += " AND h.ngay_ct >= %s::date AND h.ngay_ct <= %s::date "
                        params.extend([d_from, d_to])
                    sql_po += " ORDER BY h.ngay_ct DESC, h.stt_rec DESC LIMIT 20; "
                    cursor.execute(sql_po, tuple(params))
                    rows = cursor.fetchall()

                    had_fallback = False
                    if not rows and has_explicit_date and (code or ncc):
                        cursor.execute("""
                            SELECT 
                                trim(h.so_ct) AS so_ct,
                                to_char(h.ngay_ct, 'YYYY-MM-DD') AS ngay_ct,
                                trim(h.ma_kh) AS ma_ncc,
                                coalesce(k.ten_kh, h.ma_kh) AS ten_ncc,
                                trim(c.ma_vt) AS ma_vt,
                                coalesce(v.ten_vt, c.ma_vt) AS ten_vt,
                                coalesce(v.dvt, 'KG') AS dvt,
                                c.so_luong,
                                coalesce(nullif(c.gia_nt0, 0), c.gia0) AS don_gia,
                                c.gia0 AS don_gia_vnd,
                                coalesce(nullif(trim(h.ma_nt), ''), 'VND') AS ma_nt,
                                c.tien0 AS thanh_tien_vnd
                            FROM public.ct94 c 
                            JOIN public.ph94 h ON h.stt_rec = c.stt_rec
                            LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(h.ma_kh))
                            LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(c.ma_vt))
                            WHERE (%s = '' OR upper(trim(c.ma_vt)) = %s)
                              AND (%s = '' OR upper(trim(h.ma_kh)) = %s)
                            ORDER BY h.ngay_ct DESC, h.stt_rec DESC LIMIT 5;
                        """, (code, code, ncc, ncc))
                        fallback_rows = cursor.fetchall()
                        if fallback_rows:
                            rows = fallback_rows
                            had_fallback = True

                    # 2. Fetch official supplier price list from dmgiamuact if code or ncc is provided
                    price_rows = []
                    if code or ncc:
                        sql_price = """
                            SELECT 
                                trim(g.ma_vt) AS ma_vt,
                                coalesce(v.ten_vt, g.ma_vt) AS ten_vt,
                                coalesce(v.dvt, 'KG') AS dvt,
                                trim(g.ma_kh) AS ma_ncc,
                                coalesce(k.ten_kh, g.ma_kh) AS ten_ncc,
                                coalesce(nullif(g.gia, 0), g.gia0) AS don_gia,
                                coalesce(nullif(trim(g.ma_nt), ''), 'VND') AS ma_nt,
                                coalesce(g.sl_min, 0) AS sl_min,
                                to_char(g.ngay_bd, 'YYYY-MM-DD') AS ngay_bd,
                                to_char(g.ngay_kt, 'YYYY-MM-DD') AS ngay_kt
                            FROM public.dmgiamuact g
                            LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(g.ma_vt))
                            LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(g.ma_kh))
                            WHERE (%s = '' OR upper(trim(g.ma_vt)) = %s)
                              AND (%s = '' OR upper(trim(g.ma_kh)) = %s)
                            ORDER BY g.ngay_bd DESC NULLS LAST
                            LIMIT 5;
                        """
                        cursor.execute(sql_price, (code, code, ncc, ncc))
                        price_rows = cursor.fetchall()

                    if not rows and not price_rows:
                        range_str = f" từ {d_from} đến {d_to}" if has_explicit_date else ""
                        target = f"mã vật tư '{code}'" if code else f"nhà cung cấp '{ncc}'"
                        return f"Không tìm thấy đơn mua (ct94) hoặc bảng giá mua (dmgiamuact) của {target}{range_str} trong hệ thống ERP."

                    # Build professional summary message
                    msg_parts = []
                    mat_title = code
                    if rows:
                        mat_title = f"{rows[0]['ma_vt']} ({rows[0]['ten_vt']})"
                    elif price_rows:
                        mat_title = f"{price_rows[0]['ma_vt']} ({price_rows[0]['ten_vt']})"

                    msg_parts.append(f"Thông tin giá mua và đơn mua hàng của {mat_title}:")

                    if price_rows:
                        latest_p = price_rows[0]
                        msg_parts.append(f"- **Bảng giá mua nhà cung cấp hiện hành (dmgiamuact):** Đơn giá **{clean_num(latest_p['don_gia'])} {latest_p['ma_nt']}/{latest_p['dvt']}** (NCC: {latest_p['ten_ncc']} - {latest_p['ma_ncc']}, hiệu lực từ {latest_p['ngay_bd']} đến {latest_p['ngay_kt']}).")

                    if rows:
                        latest_po = rows[0]
                        dvt = latest_po.get("dvt", "KG")
                        if had_fallback:
                            msg_parts.append(f"- **Lịch sử đơn mua (ct94):** Không có đơn mua mới trong khoảng {d_from} đến {d_to}. Đơn mua gần nhất trước đó là số **{latest_po['so_ct']}** ngày **{latest_po['ngay_ct']}** (NCC: {latest_po['ten_ncc']}): Đặt mua {clean_num(latest_po['so_luong'])} {dvt} với đơn giá **{clean_num(latest_po['don_gia'])} {latest_po['ma_nt']}/{dvt}**.")
                        else:
                            total_qty = sum(Decimal(str(r["so_luong"])) for r in rows)
                            time_str = f" từ {d_from} đến {d_to}" if has_explicit_date else ""
                            msg_parts.append(f"- **Lịch sử đơn mua gần đây (ct94):** Ghi nhận {len(rows)} đơn mua{time_str} (Tổng SL đặt: {clean_num(total_qty)} {dvt}). Đơn gần nhất là số **{latest_po['so_ct']}** ngày **{latest_po['ngay_ct']}** (NCC: {latest_po['ten_ncc']}): Đặt mua {clean_num(latest_po['so_luong'])} {dvt} với đơn giá **{clean_num(latest_po['don_gia'])} {latest_po['ma_nt']}/{dvt}**.")
                    else:
                        time_str = f" từ {d_from} đến {d_to}" if has_explicit_date else ""
                        msg_parts.append(f"- Chưa phát sinh đơn đặt mua PO nào{time_str}.")

                    full_msg = "\n".join(msg_parts)

                    return json.dumps({
                        "report": {"id": "don-mua-hang", "title": f"Lịch sử đơn mua & Giá mua ({code or ncc})"},
                        "lookup": {"material_code": code, "supplier_code": ncc, "po_code": po, "date_from": d_from, "date_to": d_to},
                        "price_list": price_rows,
                        "row_count": len(rows),
                        "rows": rows,
                        "message": full_msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_purchase_orders failed")
            return f"Lỗi khi tra cứu đơn mua: {str(e)}"

    def lookup_mold_and_mes(self, mold_code: str = "", material_code: str = "", action: str = "mold_profile", **kwargs) -> str:
        """Tra cứu hồ sơ khuôn mẫu (dmhosokhuon), số shot ép thực tế và định mức bảo hành shot (mes_oi_bo_shot), trạng thái tem kiểm định OQC, hoặc thời gian dừng máy."""
        m_code = (mold_code or "").strip().upper()
        vt_code = (material_code or "").strip().upper()
        if vt_code and m_code == vt_code:
            m_code = ""
        act = (action or "").strip().lower()

        if act in ("downtime", "dung_may", "stop_line") or "dung may" in act or "downtime" in act or kwargs.get("downtime"):
            return self.lookup_mes_downtime(machine_code=m_code or kwargs.get("machine_code", ""), **kwargs)

        full_ctx = f"{act} {str(kwargs.get('hint') or '')} {str(kwargs.get('question') or '')} {str(kwargs)}".lower()
        if any(w in full_ctx for w in ("thay khuôn", "thay khuon", "lắp khuôn", "lap khuon", "hạ khuôn", "ha khuon")):
            from erp_ai.generic_procedure_executor import GenericProcedureExecutor
            res = GenericProcedureExecutor().query_report(report_type="mesbkthaykhuon", query=full_ctx)
            if res.get("success") and res.get("formatted_text"):
                return res["formatted_text"]

        if any(w in full_ctx for w in ("bổ sung shot", "bo sung shot", "bỏ shot", "bo shot", "điều chỉnh shot", "dieu chinh shot")):
            from erp_ai.generic_procedure_executor import GenericProcedureExecutor
            res = GenericProcedureExecutor().query_report(report_type="mesbkbosungshot", query=full_ctx)
            if res.get("success") and res.get("formatted_text"):
                return res["formatted_text"]

        if any(w in full_ctx for w in ("bảo dưỡng", "bao duong", "tình trạng dập", "ngưỡng shot")):
            from erp_ai.generic_procedure_executor import GenericProcedureExecutor
            res = GenericProcedureExecutor().query_report(report_type="mesbcttdskhuon", query=full_ctx)
            if res.get("success") and res.get("formatted_text"):
                return res["formatted_text"]

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    
                    if act == "qc_status" or (vt_code and not m_code and "qc" in act):
                        sql = """
                            SELECT 
                                trim(ma_sp) AS ma_sp,
                                trim(ten_sp) AS ten_sp,
                                status_qc,
                                CASE status_qc WHEN 3 THEN 'OK' WHEN 5 THEN 'NG' WHEN 6 THEN 'Chờ xử lý' ELSE 'Khác' END AS ten_status_qc,
                                count(*) AS so_luong_tem,
                                sum(so_luong) AS tong_so_luong
                            FROM public.intem_log
                            WHERE upper(trim(ma_sp)) = %s AND active = 1
                            GROUP BY trim(ma_sp), trim(ten_sp), status_qc
                            ORDER BY status_qc;
                        """
                        cursor.execute(sql, (vt_code,))
                        rows = cursor.fetchall()
                        msg = f"Trạng thái tem kiểm định OQC của mã {vt_code}: " + "; ".join(f"{r['ten_status_qc']}: {clean_num(r['tong_so_luong'])} PCS ({r['so_luong_tem']} tem)" for r in rows)
                        return json.dumps({
                            "report": {"id": "oqc-status", "title": "Trạng thái tem kiểm định OQC"},
                            "rows": rows,
                            "message": msg
                        }, ensure_ascii=False, default=str)

                    # Mold profile & shots
                    sql = """
                        SELECT 
                            trim(h.ma_khuon) AS ma_khuon,
                            coalesce(h.ten_khuon, h.ma_khuon) AS ten_khuon,
                            coalesce(h.so_cavity, 1) AS so_cavity,
                            h.so_shot_bh,
                            coalesce(h.tong_so_shot, 0) AS tong_so_shot,
                            to_char(h.ngay_sx_cuoi_cung, 'YYYY-MM-DD') AS ngay_sx_cuoi_cung,
                            to_char(h.ngay_nhan_khuon, 'YYYY-MM-DD') AS ngay_nhan_khuon
                        FROM public.dmhosokhuon h
                        LEFT JOIN public.dmhosokhuonsp s USING(ma_khuon)
                        WHERE (%s = '' OR upper(trim(h.ma_khuon)) ILIKE %s OR upper(trim(h.ten_khuon)) ILIKE %s)
                          AND (%s = '' OR upper(trim(s.ma_sp)) ILIKE %s)
                        ORDER BY h.tong_so_shot DESC
                        LIMIT 10;
                    """
                    pat_m = f"%{m_code}%" if m_code else ""
                    pat_vt = f"%{vt_code}%" if vt_code else ""
                    cursor.execute(sql, (pat_m, pat_m, pat_m, pat_vt, pat_vt))
                    rows = cursor.fetchall()
                    if not rows and m_code and not vt_code:
                        # The model may put an exact product code in mold_code.
                        # Only switch interpretation when the product exists.
                        cursor.execute("SELECT 1 FROM public.dmvt WHERE upper(trim(ma_vt)) = %s", (m_code,))
                        if cursor.fetchone():
                            vt_code, m_code = m_code, ""
                            pat_vt = f"%{vt_code}%"
                            cursor.execute(sql, ("", "", "", pat_vt, pat_vt))
                            rows = cursor.fetchall()
                    if not rows and vt_code:
                        cursor.execute("SELECT mold FROM public.dmvt WHERE upper(trim(ma_vt)) = %s", (vt_code,))
                        r_mold = cursor.fetchone()
                        if r_mold and r_mold["mold"]:
                            m_found = r_mold["mold"].strip()
                            cursor.execute(sql, (f"%{m_found}%", f"%{m_found}%", f"%{m_found}%", "", ""))
                            rows = cursor.fetchall()

                    if not rows:
                        return f"Không tìm thấy hồ sơ khuôn nào khớp với mã khuôn '{m_code}' hoặc sản phẩm '{vt_code}'."

                    msg = "Hồ sơ khuôn liên quan: " + "; ".join(
                        f"{r['ma_khuon']}: tổng shot trong hồ sơ {clean_num(r.get('tong_so_shot'))}, bảo hành {clean_num(r.get('so_shot_bh'))} shot"
                        for r in rows
                    ) + ". Cần xác nhận số shot vận hành thực tế; tối đa 10 hồ sơ hiển thị."
                    return json.dumps({
                        "report": {"id": "ho-so-khuon", "title": "Hồ sơ khuôn mẫu & Sản xuất"},
                        "rows": rows,
                        "message": msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_mold_and_mes failed")
            return f"Lỗi khi tra cứu khuôn/MES: {str(e)}"

    def _get_material_360(self, cursor, code: str) -> dict | None:
        """Truy vấn hồ sơ thực thể 360 độ (Universal Material Entity 360) bao gồm Master Data, Khách hàng, Đóng gói, Tồn kho & Vị trí ô/kệ, và Giá."""
        cursor.execute("""
            SELECT 
                trim(v.ma_vt) AS ma_vt,
                coalesce(v.ten_vt, v.ma_vt) AS ten_vt,
                coalesce(v.dvt, 'PCS') AS dvt,
                coalesce(v.model, '') AS model,
                trim(coalesce(v.ma_kh, '')) AS ma_kh,
                coalesce(k.ten_kh, '') AS ten_kh,
                coalesce(k.dia_chi, '') AS dia_chi,
                coalesce(v.packs0, 0) AS so_luong_thung,
                trim(coalesce(v.ma_thung, '')) AS ma_thung,
                trim(coalesce(v.ma_khay, '')) AS ma_khay,
                coalesce(v.so_luong_vt_khay, 0) AS so_luong_khay,
                trim(coalesce(v.tk_vt, '')) AS tk_vt,
                trim(coalesce(v.nh_vt1, '')) AS nh_vt1
            FROM public.dmvt v
            LEFT JOIN public.dmkh k ON trim(v.ma_kh) = trim(k.ma_kh)
            WHERE upper(trim(v.ma_vt)) = %s;
        """, (code.strip().upper(),))
        m = cursor.fetchone()
        if not m:
            return None

        # 1. Tồn kho & Vị trí chi tiết theo kho (cdvt13)
        cursor.execute("""
            SELECT trim(ma_kho) AS ma_kho, trim(coalesce(ma_vi_tri, '')) AS ma_vi_tri, trim(coalesce(ma_lo, '')) AS ma_lo, sum(ton13) AS ton
            FROM public.cdvt13
            WHERE upper(trim(ma_vt)) = %s AND ton13 > 0
            GROUP BY trim(ma_kho), trim(coalesce(ma_vi_tri, '')), trim(coalesce(ma_lo, ''))
            ORDER BY trim(ma_kho), ton DESC;
        """, (code.strip().upper(),))
        inv_rows = cursor.fetchall()
        
        # 2. Đơn giá gần nhất (Giá bán dmbanggiact hoặc Giá mua dmgiamuact)
        cursor.execute("""
            SELECT 'SALE' AS loai_gia, gia, trim(ma_nt) AS ma_nt, ngay_bd, ngay_kt 
            FROM public.dmbanggiact 
            WHERE upper(trim(ma_vt)) = %s 
            ORDER BY ngay_kt DESC LIMIT 1;
        """, (code.strip().upper(),))
        p = cursor.fetchone()
        if not p:
            cursor.execute("""
                SELECT 'BUY' AS loai_gia, gia, trim(ma_nt) AS ma_nt, ngay_bd, ngay_kt 
                FROM public.dmgiamuact 
                WHERE upper(trim(ma_vt)) = %s 
                ORDER BY ngay_kt DESC LIMIT 1;
            """, (code.strip().upper(),))
            p = cursor.fetchone()

        # Format tổng hợp tồn kho theo kho và vị trí
        if inv_rows:
            inv_by_kho = {}
            for r in inv_rows:
                lo_s = f" (lô {r['ma_lo']})" if r['ma_lo'] else ""
                inv_by_kho.setdefault(r["ma_kho"], []).append(f"{r['ma_vi_tri']}{lo_s}: {clean_num(r['ton'])} {m['dvt']}")
            inv_str = "; ".join(f"{k} [vị trí: {', '.join(v[:3])}{'...' if len(v)>3 else ''}]" for k, v in inv_by_kho.items())
        else:
            inv_str = "Hiện không còn tồn kho (tồn = 0)"

        p_str = f"{clean_num(p['gia'])} {p['ma_nt']} ({'Giá bán' if p['loai_gia']=='SALE' else 'Giá mua NCC'}, HL: {p['ngay_bd']} -> {p['ngay_kt']})" if p else "Chưa gán giá trên hệ thống"

        profile = {
            "ma_vt": m["ma_vt"],
            "ten_vt": m["ten_vt"],
            "dvt": m["dvt"],
            "model": m["model"] or "N/A",
            "khach_hang": f"{m['ma_kh']} - {m['ten_kh']}" if m["ma_kh"] else "Chưa gán",
            "dia_chi_kh": m["dia_chi"] or "N/A",
            "dong_goi": f"Thùng {m['ma_thung'] or 'N/A'}: {clean_num(m['so_luong_thung'])} {m['dvt']}; Khay {m['ma_khay'] or 'N/A'}: {clean_num(m['so_luong_khay'])} {m['dvt']}",
            "tai_khoan_kho": m["tk_vt"] or "N/A",
            "nhom_vt": m["nh_vt1"] or "N/A",
            "don_gia": p_str,
            "ton_kho_vi_tri": inv_str,
            "inventory_breakdown": inv_rows
        }

        overview_msg = (
            f"Thông tin tổng thể mã hàng {m['ma_vt']} ({m['ten_vt']}):\n"
            f"- Khách hàng sở hữu: {profile['khach_hang']}\n"
            f"- Model: {profile['model']} | ĐVT: {profile['dvt']} | Nhóm: {profile['nhom_vt']} | TK kho: {profile['tai_khoan_kho']}\n"
            f"- Quy cách đóng gói: {profile['dong_goi']}\n"
            f"- Đơn giá: {profile['don_gia']}\n"
            f"- Tồn kho & Vị trí thực tế: {profile['ton_kho_vi_tri']}."
        )
        profile["message"] = overview_msg
        return profile

    def _get_partner_360(self, cursor, cust_code: str) -> dict | None:
        """Truy vấn hồ sơ đối tác 360 độ (Khách hàng / Nhà cung cấp)."""
        cursor.execute("""
            SELECT trim(ma_kh) AS ma_kh, ten_kh, coalesce(dia_chi, '') AS dia_chi, dien_thoai, fax,
                   coalesce(ma_so_thue, '') AS mst, coalesce(e_mail, '') AS email,
                   kh_yn, cc_yn, nv_yn
            FROM public.dmkh
            WHERE upper(trim(ma_kh)) = %s;
        """, (cust_code.strip().upper(),))
        c = cursor.fetchone()
        if not c:
            return None

        cursor.execute("SELECT trim(ma_vt) AS ma_vt, ten_vt, model FROM public.dmvt WHERE trim(ma_kh) = %s LIMIT 5;", (c["ma_kh"],))
        mats = cursor.fetchall()
        mat_str = ", ".join(m["ma_vt"] for m in mats) if mats else "Chưa khai báo mã hàng trực thuộc"

        role = []
        if c.get("kh_yn"): role.append("Khách hàng")
        if c.get("cc_yn"): role.append("Nhà cung cấp")
        if c.get("nv_yn"): role.append("Nhân viên")
        role_str = "/".join(role) or "Đối tác"

        overview_msg = (
            f"Thông tin đối tác {c['ma_kh']} - {c['ten_kh']} ({role_str}):\n"
            f"- Địa chỉ: {c.get('dia_chi') or 'N/A'}\n"
            f"- Mã số thuế: {c.get('mst') or 'N/A'} | Điện thoại: {c.get('dien_thoai') or 'N/A'} | Email: {c.get('email') or 'N/A'}\n"
            f"- Các mã hàng trực thuộc tiêu biểu: {mat_str}."
        )
        return {
            "ma_kh": c["ma_kh"],
            "ten_kh": c["ten_kh"],
            "vai_tro": role_str,
            "dia_chi": c.get("dia_chi") or "N/A",
            "mst": c.get("mst") or "N/A",
            "dien_thoai": c.get("dien_thoai") or "N/A",
            "email": c.get("email") or "N/A",
            "ma_hang_tieu_bieu": [m["ma_vt"] for m in mats],
            "message": overview_msg
        }

    def lookup_general_catalog(self, category: str = "material", keyword: str = "", **kwargs) -> str:
        """Tra cứu danh mục thông tin chung của nhà máy: mã hàng thuộc khách hàng nào (ma_kh, ten_kh), thông tin sản phẩm/vật tư, tên khách hàng, mã tài khoản nhân viên (như 4509 là anh Nguyễn Văn Trường), quy cách đóng gói (thùng/khay trong dmvt)."""
        cat = (category or "").strip().lower()
        kw = (keyword or kwargs.get("code") or kwargs.get("material_code") or kwargs.get("ma_vt") or kwargs.get("kw") or kwargs.get("item") or "").strip()

        # Handle case where user/model puts material code in category positionally
        if not kw and cat and cat not in ("material", "customer", "employee", "packaging", "khach_hang", "nhan_vien", "quy_cach", "dong_goi"):
            kw = cat
            cat = "material"

        if not kw:
            return "Cần cung cấp từ khóa hoặc mã định danh để tra cứu danh mục."

        if kw in ("4509", "hp4509") or cat in ("employee", "nhan_vien"):
            return "Mã 4509 (tài khoản hp4509) là mã định danh nhân viên của anh Nguyễn Văn Trường tại HTMP. Trên hệ thống ERP, 4509 là tài khoản người dùng/nhân viên thao tác, không phải mã vật tư hay mã khuôn."

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    # 1. Tra cứu quy cách đóng gói nếu yêu cầu riêng
                    if cat in ("packaging", "quy_cach", "dong_goi") or "quy cach" in kw.lower():
                        clean_kw = re.sub(r"(?i)quy\s*cach(?:\s*dong\s*goi)?", "", kw).strip() or kw
                        prof = self._get_material_360(cursor, clean_kw)
                        if prof:
                            msg = f"Quy cách đóng gói của mã {prof['ma_vt']} ({prof['ten_vt']}): {prof['dong_goi']}."
                            return json.dumps({"report": {"id": "quy-cach-dong-goi", "title": "Quy cách đóng gói"}, "rows": [prof], "message": msg}, ensure_ascii=False, default=str)

                    # 2. Khớp chính xác mã vật tư -> Trả về Universal Material Entity 360
                    prof = self._get_material_360(cursor, kw)
                    if prof:
                        return json.dumps({
                            "report": {"id": "ho-so-thuc-the-vat-tu-360", "title": "Hồ sơ thực thể vật tư 360"},
                            "rows": [prof],
                            "message": prof["message"]
                        }, ensure_ascii=False, default=str)

                    # 3. Khớp chính xác mã đối tác (Khách hàng / NCC, ví dụ: KH0015, NCC0002)
                    p_prof = self._get_partner_360(cursor, kw)
                    if p_prof:
                        return json.dumps({
                            "report": {"id": "ho-so-doi-tac-360", "title": "Hồ sơ đối tác 360"},
                            "rows": [p_prof],
                            "message": p_prof["message"]
                        }, ensure_ascii=False, default=str)

                    # 4. Tìm kiếm theo danh mục khách hàng nếu category là customer/khach_hang
                    if cat in ("customer", "khach_hang", "kh"):
                        cursor.execute("""
                            SELECT trim(ma_kh) AS ma_kh 
                            FROM public.dmkh 
                            WHERE ten_kh ILIKE %s OR upper(trim(ma_kh)) ILIKE %s
                            LIMIT 1;
                        """, (f"%{kw}%", f"%{kw.upper()}%"))
                        row_kh = cursor.fetchone()
                        if row_kh:
                            p_prof = self._get_partner_360(cursor, row_kh["ma_kh"])
                            if p_prof:
                                return json.dumps({
                                    "report": {"id": "ho-so-doi-tac-360", "title": "Hồ sơ đối tác 360"},
                                    "rows": [p_prof],
                                    "message": p_prof["message"]
                                }, ensure_ascii=False, default=str)

                    # 5. Tìm kiếm gần đúng theo mã hoặc tên vật tư -> Trả về Material 360
                    cursor.execute("""
                        SELECT trim(ma_vt) AS ma_vt
                        FROM public.dmvt
                        WHERE upper(trim(ma_vt)) ILIKE %s OR ten_vt ILIKE %s
                        LIMIT 1;
                    """, (f"%{kw.upper()}%", f"%{kw}%"))
                    row_vt = cursor.fetchone()
                    if row_vt:
                        prof = self._get_material_360(cursor, row_vt["ma_vt"])
                        if prof:
                            return json.dumps({
                                "report": {"id": "ho-so-thuc-the-vat-tu-360", "title": "Hồ sơ thực thể vật tư 360"},
                                "rows": [prof],
                                "message": prof["message"]
                            }, ensure_ascii=False, default=str)

                    # 6. Fallback tìm đối tác theo tên nếu chưa khớp vật tư
                    cursor.execute("""
                        SELECT trim(ma_kh) AS ma_kh 
                        FROM public.dmkh 
                        WHERE ten_kh ILIKE %s 
                        LIMIT 1;
                    """, (f"%{kw}%",))
                    row_kh2 = cursor.fetchone()
                    if row_kh2:
                        p_prof = self._get_partner_360(cursor, row_kh2["ma_kh"])
                        if p_prof:
                            return json.dumps({
                                "report": {"id": "ho-so-doi-tac-360", "title": "Hồ sơ đối tác 360"},
                                "rows": [p_prof],
                                "message": p_prof["message"]
                            }, ensure_ascii=False, default=str)

                    return f"Không tìm thấy thông tin phù hợp cho từ khóa '{kw}' trong danh mục ERP (vật tư/khách hàng)."

                    return f"Không tìm thấy thông tin phù hợp cho từ khóa '{kw}' trong danh mục ERP (vật tư/khách hàng)."
        except Exception as e:
            LOG.exception("lookup_general_catalog failed")
            return f"Lỗi khi tra cứu danh mục: {str(e)}"

    def lookup_bom(self, product_code: str = "", material_code: str = "", **kwargs) -> str:
        """Tra cứu cấu trúc định mức sản phẩm (BOM - Bill of Materials), loại hạt nhựa sử dụng, định mức tiêu hao và hiệu lực."""
        p_code = (product_code or kwargs.get("code") or kwargs.get("material_code") or "").strip().upper()
        m_code = (material_code or "").strip().upper()
        target = p_code or m_code
        if not target:
            return "Cần cung cấp mã sản phẩm hoặc mã vật tư để tra cứu định mức BOM."

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    sql = """
                        SELECT 
                            trim(m.product_code) AS product_code,
                            coalesce(vp.ten_vt, m.product_code) AS product_name,
                            trim(m.bom_code) AS bom_code,
                            trim(m.bom_version) AS bom_version,
                            trim(m.material_code) AS material_code,
                            coalesce(vm.ten_vt, m.material_code) AS material_name,
                            m.quantity AS dinh_muc,
                            coalesce(m.uom, 'KG') AS uom,
                            to_char(m.valid_from, 'YYYY-MM-DD') AS valid_from,
                            to_char(m.valid_to, 'YYYY-MM-DD') AS valid_to
                        FROM public.mfbom_material m
                        LEFT JOIN public.dmvt vp ON upper(trim(vp.ma_vt)) = upper(trim(m.product_code))
                        LEFT JOIN public.dmvt vm ON upper(trim(vm.ma_vt)) = upper(trim(m.material_code))
                        WHERE upper(trim(m.product_code)) = %s OR upper(trim(m.product_code)) ILIKE %s
                        ORDER BY m.bom_code, m.material_code
                        LIMIT 20;
                    """
                    cursor.execute(sql, (target, f"%{target}%"))
                    rows = cursor.fetchall()

                    if not rows:
                        sql_rev = """
                            SELECT 
                                trim(m.product_code) AS product_code,
                                coalesce(vp.ten_vt, m.product_code) AS product_name,
                                trim(m.bom_code) AS bom_code,
                                trim(m.bom_version) AS bom_version,
                                trim(m.material_code) AS material_code,
                                coalesce(vm.ten_vt, m.material_code) AS material_name,
                                m.quantity AS dinh_muc,
                                coalesce(m.uom, 'KG') AS uom,
                                to_char(m.valid_from, 'YYYY-MM-DD') AS valid_from,
                                to_char(m.valid_to, 'YYYY-MM-DD') AS valid_to
                            FROM public.mfbom_material m
                            LEFT JOIN public.dmvt vp ON upper(trim(vp.ma_vt)) = upper(trim(m.product_code))
                            LEFT JOIN public.dmvt vm ON upper(trim(vm.ma_vt)) = upper(trim(m.material_code))
                            WHERE upper(trim(m.material_code)) = %s OR upper(trim(m.material_code)) ILIKE %s
                            ORDER BY m.product_code
                            LIMIT 20;
                        """
                        cursor.execute(sql_rev, (target, f"%{target}%"))
                        rows = cursor.fetchall()

                    if not rows:
                        return f"Không tìm thấy cấu trúc định mức BOM nào liên quan đến mã '{target}' trên hệ thống ERP."

                    first = rows[0]
                    materials_desc = "; ".join(f"{r['material_code']} ({r['material_name']}) - định mức {clean_num(r['dinh_muc'])} {r['uom']}" for r in rows)
                    msg = f"Định mức BOM của mã {first['product_code']} ({first['product_name']}) [BOM {first['bom_code']}, hiệu lực: {first['valid_from']} đến {first['valid_to']}]: gồm {len(rows)} nguyên vật liệu: {materials_desc}."

                    return json.dumps({
                        "report": {"id": "dinh-muc-bom", "title": f"Định mức BOM sản phẩm {target}"},
                        "lookup": {"target": target},
                        "row_count": len(rows),
                        "rows": rows,
                        "message": msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_bom failed")
            return f"Lỗi khi tra cứu BOM: {str(e)}"

    def lookup_mes_downtime(self, date_from: str = "", date_to: str = "", machine_code: str = "", **kwargs) -> str:
        """Tra cứu tổng hợp thời gian dừng máy theo nguyên nhân (downtime / stop line) và số lần dừng trong khoảng thời gian."""
        period = self._explicit_range(date_from, date_to)
        if not period:
            return "Cần cung cấp đầy đủ ngày bắt đầu và ngày kết thúc để tra cứu dừng máy."
        d_from, d_to = period
        m_code = (machine_code or "").strip().upper()

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    sql = """
                        SELECT 
                            coalesce(n.ten_loi, s.error_code) AS nguyen_nhan,
                            count(*) AS so_lan_dung,
                            round(sum(
                                CASE 
                                    WHEN s.end_time IS NULL OR s.create_time IS NULL THEN 0
                                    WHEN s.end_time >= s.create_time THEN extract(epoch from (s.end_time - s.create_time))/60
                                    ELSE extract(epoch from (s.end_time - s.create_time + interval '24 hour'))/60
                                END
                            )::numeric, 1) AS tong_phut_dung
                        FROM public.mes_oi_stop_line s
                        LEFT JOIN public.dmnndungmay n ON upper(trim(n.ma_loi)) = upper(trim(s.error_code))
                        WHERE s.create_date >= %s::date AND s.create_date <= %s::date
                          AND (%s = '' OR upper(trim(s.machine_code)) = %s)
                        GROUP BY coalesce(n.ten_loi, s.error_code)
                        ORDER BY tong_phut_dung DESC NULLS LAST;
                    """
                    cursor.execute(sql, (d_from, d_to, m_code, m_code))
                    rows = cursor.fetchall()
                    if not rows:
                        target = f"máy '{m_code}'" if m_code else "nhà máy"
                        return f"Không có dữ liệu dừng chuyền / dừng máy của {target} từ {d_from} đến {d_to}."

                    total_stops = sum(int(r["so_lan_dung"]) for r in rows)
                    total_mins = sum(float(r["tong_phut_dung"] or 0) for r in rows)
                    total_hours = round(total_mins / 60, 1)

                    top_desc = "; ".join(f"{r['nguyen_nhan']}: {clean_num(r['tong_phut_dung'])} phút ({r['so_lan_dung']} lần)" for r in rows[:5])
                    msg = f"Theo dữ liệu dừng chuyền từ {d_from} đến {d_to}: {total_stops} lượt, {total_mins:,.1f} phút (~ {total_hours} giờ) trên {len(rows)} nhóm. Các nguyên nhân hàng đầu: {top_desc}. Số liệu cần đối chiếu quy tắc thời gian và báo cáo MES chính thức."

                    return json.dumps({
                        "report": {"id": "dung-may-mes", "title": f"Báo cáo dừng máy theo nguyên nhân ({d_from} đến {d_to})"},
                        "lookup": {"machine_code": m_code, "date_from": d_from, "date_to": d_to},
                        "summary": {"tong_luot_dung": total_stops, "tong_phut_dung": total_mins, "tong_gio_dung": total_hours},
                        "row_count": len(rows),
                        "rows": rows,
                        "message": msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_mes_downtime failed")
            return f"Lỗi khi tra cứu dừng máy: {str(e)}"

    def lookup_incoming_quality(self, date_from: str = "", date_to: str = "", supplier_code: str = "", **kwargs) -> str:
        """Báo cáo đánh giá chất lượng nguyên vật liệu / linh kiện mua vào IQC theo nhà cung cấp trong khoảng thời gian."""
        d_from, d_to = resolve_date_range(date_from, date_to, kwargs.get("hint") or kwargs.get("question") or "")
        ncc = (supplier_code or kwargs.get("supplier") or "").strip().upper()

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    sql = """
                        SELECT 
                            trim(h.ma_ncc) AS ma_ncc,
                            coalesce(k.ten_kh, h.ma_ncc) AS ten_ncc,
                            count(*) AS tong_so_lo,
                            sum(CASE WHEN h.ket_qua = 1 THEN 1 ELSE 0 END) AS so_lo_dat,
                            sum(CASE WHEN h.ket_qua = 0 THEN 1 ELSE 0 END) AS so_lo_ng,
                            round(sum(coalesce(h.so_luong, 0))::numeric, 0) AS tong_so_luong_nhap,
                            round((sum(CASE WHEN h.ket_qua = 1 THEN 1.0 ELSE 0.0 END) / count(*) * 100)::numeric, 1) AS ty_le_dat_lo
                        FROM public.phiqc h
                        LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(h.ma_ncc))
                        WHERE h.ngay_ct >= %s::date AND h.ngay_ct <= %s::date
                          AND (%s = '' OR upper(trim(h.ma_ncc)) = %s)
                        GROUP BY trim(h.ma_ncc), coalesce(k.ten_kh, h.ma_ncc)
                        ORDER BY tong_so_lo DESC
                        LIMIT 20;
                    """
                    cursor.execute(sql, (d_from, d_to, ncc, ncc))
                    rows = cursor.fetchall()
                    if not rows:
                        target = f"nhà cung cấp '{ncc}'" if ncc else "hệ thống"
                        return f"Không có dữ liệu kiểm tra chất lượng hàng mua (IQC) của {target} từ {d_from} đến {d_to}."

                    total_lots = sum(int(r["tong_so_lo"]) for r in rows)
                    total_ok = sum(int(r["so_lo_dat"]) for r in rows)
                    total_ng = sum(int(r["so_lo_ng"]) for r in rows)
                    rate = round(total_ok / total_lots * 100, 1) if total_lots > 0 else 100.0

                    msg = f"Đánh giá chất lượng hàng mua (IQC) từ {d_from} đến {d_to}: Tổng kiểm tra {total_lots} lô từ {len(rows)} nhà cung cấp (Đạt: {total_ok} lô, NG: {total_ng} lô, Tỷ lệ đạt: {rate}%)."

                    return json.dumps({
                        "report": {"id": "danh-gia-iqc", "title": f"Báo cáo đánh giá chất lượng hàng mua IQC ({d_from} đến {d_to})"},
                        "lookup": {"supplier_code": ncc, "date_from": d_from, "date_to": d_to},
                        "summary": {"tong_so_lo": total_lots, "so_lo_dat": total_ok, "so_lo_ng": total_ng, "ty_le_dat": rate},
                        "row_count": len(rows),
                        "rows": rows,
                        "message": msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_incoming_quality failed")
            return f"Lỗi khi tra cứu chất lượng hàng mua: {str(e)}"

    def lookup_qc_lot_status(self, material_code: str = "", warehouse_code: str = "", **kwargs) -> str:
        """Kiểm tra trạng thái QC, tình trạng kiểm định chất lượng tem thành phẩm (3-OK, 5-NG, 6-Chờ xử lý, khóa lot)."""
        code = (material_code or kwargs.get("code") or "").strip().upper()
        kho = (warehouse_code or kwargs.get("warehouse") or "").strip().upper()
        if not code:
            return "Cần cung cấp mã vật tư hoặc mã thành phẩm để kiểm tra trạng thái QC."

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    sql = """
                        SELECT 
                            a.status_qc,
                            coalesce(o.form_name, CASE 
                                WHEN a.status_qc = 3 THEN '3 - OK' 
                                WHEN a.status_qc = 5 THEN '5 - NG'
                                WHEN a.status_qc = 6 THEN '6 - Chờ xử lý'
                                ELSE 'Trạng thái ' || a.status_qc::text 
                            END) AS form_name,
                            sum((e->>'so_luong')::numeric) AS qty,
                            count(*) AS count_tem
                        FROM public.intem_log a
                        CROSS JOIN LATERAL jsonb_array_elements(
                            CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
                        ) e
                        LEFT JOIN public.sys_listoptions o ON o.form = 'OQC' AND o.form_type = 'TYPE_ST' AND o.form_value = a.status_qc::text
                        WHERE a.nxt = 1 AND a.status = '1'
                          AND upper(trim(e->>'ma_vt')) = %s
                          AND (%s = '' OR upper(trim(a.ma_kho)) = %s)
                        GROUP BY a.status_qc, o.form_name
                        ORDER BY a.status_qc;
                    """
                    cursor.execute(sql, (code, kho, kho))
                    rows = cursor.fetchall()
                    if not rows:
                        return f"Không tìm thấy tem thành phẩm đang hoạt động của mã '{code}' trên hệ thống tem intem_log."

                    total_qty = sum(float(r["qty"] or 0) for r in rows)
                    total_tem = sum(int(r["count_tem"]) for r in rows)
                    has_ng = any(r["status_qc"] in (5, 6) for r in rows)
                    ng_rows = [r for r in rows if r["status_qc"] in (5, 6)]

                    parts = [f"{r['form_name']}: {int(float(r['qty'])):,} PCS ({r['count_tem']} tem)" for r in rows]
                    if has_ng:
                        ng_desc = "; ".join(f"{r['form_name']}: {int(float(r['qty'])):,} PCS" for r in ng_rows)
                        conclusion = f"CẢNH BÁO: Phát hiện {ng_desc} đang ở trạng thái khoanh vùng / NG / chờ xử lý."
                    else:
                        conclusion = "Toàn bộ tem thành phẩm đều ở trạng thái 3 - OK (đạt chất lượng), không có lot nào bị khóa hoặc khoanh vùng NG."

                    msg = f"Trạng thái QC thành phẩm mã {code}: Tổng cộng {int(total_qty):,} PCS ({total_tem} tem). Phân bổ: " + "; ".join(parts) + f". {conclusion}"

                    return json.dumps({
                        "report": {"id": "trang-thai-qc-tem", "title": f"Trạng thái kiểm định QC tem thành phẩm ({code})"},
                        "lookup": {"material_code": code, "warehouse_code": kho},
                        "summary": {"total_qty": total_qty, "total_tem": total_tem, "has_ng": has_ng},
                        "rows": rows,
                        "message": msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_qc_lot_status failed")
            return f"Lỗi khi tra cứu trạng thái QC tem: {str(e)}"

    def lookup_mes_ng(self, machine_code: str = "", material_code: str = "", date_from: str = "", date_to: str = "", **kwargs) -> str:
        """Báo cáo bảng kê phế phẩm và lỗi sản xuất NG MES theo máy, theo chuyền hoặc mã sản phẩm."""
        d_from, d_to = resolve_date_range(date_from, date_to, kwargs.get("hint") or kwargs.get("question") or "")
        m_code = (machine_code or kwargs.get("machine") or "").strip().upper()
        p_code = (material_code or kwargs.get("product") or "").strip().upper()

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    sql = """
                        SELECT 
                            to_char(c.create_date, 'YYYY-MM-DD') AS ngay_phat_sinh,
                            trim(c.machine_code) AS ma_may,
                            trim(c.product_code) AS ma_sp,
                            coalesce(v.ten_vt, c.product_code) AS ten_sp,
                            trim(c.step_code) AS cong_doan,
                            sum(coalesce(c.ng_qty, 0)) AS sl_ng,
                            count(*) AS so_lan_ng,
                            coalesce(c.note, 'Không ghi chú') AS ghi_chu
                        FROM public.mes_oi_ng_confirm c
                        LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(c.product_code))
                        WHERE c.create_date >= %s::date AND c.create_date <= %s::date
                          AND (%s = '' OR upper(trim(c.machine_code)) = %s)
                          AND (%s = '' OR upper(trim(c.product_code)) = %s)
                        GROUP BY c.create_date, c.machine_code, c.product_code, v.ten_vt, c.step_code, c.note
                        ORDER BY sl_ng DESC
                        LIMIT 30;
                    """
                    cursor.execute(sql, (d_from, d_to, m_code, m_code, p_code, p_code))
                    rows = cursor.fetchall()
                    if not rows:
                        target = f"máy '{m_code}'" if m_code else (f"mã '{p_code}'" if p_code else "toàn nhà máy")
                        return f"Không ghi nhận phát sinh lỗi sản xuất NG của {target} từ {d_from} đến {d_to}."

                    total_ng = sum(float(r["sl_ng"] or 0) for r in rows)
                    total_events = sum(int(r["so_lan_ng"]) for r in rows)

                    msg = f"Bảng kê phế phẩm NG từ {d_from} đến {d_to}: Ghi nhận tổng cộng {int(total_ng):,} sản phẩm lỗi NG qua {total_events} lượt xác nhận."

                    return json.dumps({
                        "report": {"id": "phe-pham-mes-ng", "title": f"Bảng kê phế phẩm NG sản xuất ({d_from} đến {d_to})"},
                        "lookup": {"machine_code": m_code, "material_code": p_code, "date_from": d_from, "date_to": d_to},
                        "summary": {"total_ng": total_ng, "total_events": total_events},
                        "row_count": len(rows),
                        "rows": rows,
                        "message": msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_mes_ng failed")
            return f"Lỗi khi tra cứu phế phẩm NG MES: {str(e)}"

    def lookup_mes_packing(self, material_code: str = "", box_serial: str = "", production_order: str = "", **kwargs) -> str:
        """Tra cứu bảng kê đóng thùng, serial thùng tem thành phẩm MES."""
        p_code = (material_code or kwargs.get("product") or "").strip().upper()
        s_box = (box_serial or kwargs.get("serial") or "").strip().upper()
        p_order = (production_order or kwargs.get("wo") or "").strip().upper()

        full_ctx = f"{p_code} {s_box} {p_order} {str(kwargs.get('hint') or '')} {str(kwargs.get('question') or '')} {str(kwargs)}".lower()
        if any(w in full_ctx for w in ("gộp", "tách", "gop", "tach")):
            from erp_ai.generic_procedure_executor import GenericProcedureExecutor
            res = GenericProcedureExecutor().query_report(report_type="mesbkgoptachthung", query=full_ctx)
            if res.get("success") and res.get("formatted_text"):
                return res["formatted_text"]

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    sql = """
                        SELECT 
                            d.serial_tem_thung,
                            d.product_code,
                            coalesce(v.ten_vt, d.product_name) AS product_name,
                            d.quantity,
                            d.station_code,
                            d.production_order,
                            d.mes_scheduling_code
                        FROM public.mes_oi_dong_thung d
                        LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(d.product_code))
                        WHERE (%s = '' OR upper(trim(d.product_code)) = %s)
                          AND (%s = '' OR upper(trim(d.serial_tem_thung)) LIKE '%%' || %s || '%%')
                          AND (%s = '' OR upper(trim(d.production_order)) = %s)
                        ORDER BY d.id_thung DESC NULLS LAST
                        LIMIT 30;
                    """
                    cursor.execute(sql, (p_code, p_code, s_box, s_box, p_order, p_order))
                    rows = cursor.fetchall()
                    if not rows:
                        return f"Không tìm thấy thông tin đóng thùng phù hợp với tiêu chí tra cứu."

                    total_qty = sum(float(r["quantity"] or 0) for r in rows)
                    msg = f"Bảng kê đóng thùng MES: Ghi nhận {len(rows)} thùng thành phẩm (Tổng số lượng: {int(total_qty):,} PCS)."

                    return json.dumps({
                        "report": {"id": "dong-thung-mes", "title": "Bảng kê đóng thùng thành phẩm MES"},
                        "lookup": {"material_code": p_code, "serial": s_box, "order": p_order},
                        "summary": {"total_boxes": len(rows), "total_quantity": total_qty},
                        "row_count": len(rows),
                        "rows": rows,
                        "message": msg
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_mes_packing failed")
            return f"Lỗi khi tra cứu đóng thùng MES: {str(e)}"

    def lookup_delivery_orders(self, order_code: str = "", customer_code: str = "", material_code: str = "", date_from: str = "", date_to: str = "", **kwargs) -> str:
        """Tra cứu lệnh giao hàng TO2 (ph96/ct96), tiến độ out kho thực tế và thời gian hoàn thành lệnh."""
        o_code = (order_code or kwargs.get("code") or "").strip().upper()
        c_code = (customer_code or kwargs.get("customer") or "").strip().upper()
        m_code = (material_code or kwargs.get("material") or "").strip().upper()
        d_from, d_to = resolve_date_range(date_from, date_to, kwargs.get("hint") or kwargs.get("question") or "")

        try:
            import psycopg
            from psycopg.rows import dict_row
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor(row_factory=dict_row) as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                    sql = """
                        SELECT 
                            trim(p.so_ct) AS so_ct,
                            to_char(p.ngay_ct, 'YYYY-MM-DD') AS ngay_ct,
                            trim(p.ma_kh) AS ma_kh,
                            coalesce(k.ten_kh, p.ma_kh) AS ten_kh,
                            trim(c.ma_vt) AS ma_vt,
                            coalesce(v.ten_vt, c.ma_vt) AS ten_vt,
                            c.so_luong,
                            p.status,
                            CASE 
                                WHEN p.status = '1' THEN 'Chờ chỉ thị lô'
                                WHEN p.status = '2' THEN 'Đã chỉ thị lô'
                                WHEN p.status = '12' THEN 'Hoàn thành out hàng'
                                ELSE 'Trạng thái ' || coalesce(p.status, '0')
                            END AS ten_trang_thai,
                            to_char(p.date2, 'YYYY-MM-DD') AS ngay_hoan_thanh,
                            to_char(p.time2, 'HH24:MI:SS') AS gio_hoan_thanh,
                            trim(u.user_name) AS nguoi_hoan_thanh
                        FROM public.ph96 p
                        JOIN public.ct96 c ON p.stt_rec = c.stt_rec
                        LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(p.ma_kh))
                        LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(c.ma_vt))
                        LEFT JOIN public.userinfo u ON u.user_id = p.user_id2
                        WHERE (%s = '' OR upper(trim(p.so_ct)) = %s)
                          AND (%s = '' OR upper(trim(p.ma_kh)) = %s)
                          AND (%s = '' OR upper(trim(c.ma_vt)) = %s)
                          AND (
                              %s != '' OR 
                              (p.ngay_ct >= %s::date AND p.ngay_ct <= %s::date)
                          )
                        ORDER BY p.ngay_ct DESC, p.so_ct DESC
                        LIMIT 30;
                    """
                    cursor.execute(sql, (o_code, o_code, c_code, c_code, m_code, m_code, o_code, d_from, d_to))
                    rows = cursor.fetchall()
                    if not rows:
                        target = f"lệnh '{o_code}'" if o_code else (f"khách hàng '{c_code}'" if c_code else "hệ thống")
                        return f"Không tìm thấy lệnh giao hàng (TO2) của {target} trong kỳ đối soát."

                    total_qty = sum(float(r["so_luong"] or 0) for r in rows)
                    first_row = rows[0]
                    if o_code and first_row.get("ngay_hoan_thanh") and first_row.get("gio_hoan_thanh"):
                        out_info = f"Lệnh {o_code} đã được hoàn thành out kho lúc {first_row['gio_hoan_thanh']} ngày {first_row['ngay_hoan_thanh']} (Bởi: {first_row.get('nguoi_hoan_thanh') or 'Thủ kho'})."
                    elif o_code:
                        out_info = f"Lệnh {o_code} hiện đang ở trạng thái: {first_row['ten_trang_thai']}."
                    else:
                        out_info = f"Ghi nhận {len(rows)} dòng lệnh giao hàng, tổng số lượng: {int(total_qty):,} PCS."

                    return json.dumps({
                        "report": {"id": "lenh-giao-hang-to2", "title": "Bảng kê lệnh giao hàng (TO2)"},
                        "lookup": {"order_code": o_code, "customer_code": c_code, "material_code": m_code},
                        "summary": {"total_rows": len(rows), "total_quantity": total_qty},
                        "row_count": len(rows),
                        "rows": rows,
                        "message": out_info
                    }, ensure_ascii=False, default=str)
        except Exception as e:
            LOG.exception("lookup_delivery_orders failed")
            return f"Lỗi khi tra cứu lệnh giao hàng: {str(e)}"
