import re
import psycopg
from psycopg.rows import dict_row
from functions.htmp_postgres_query import connection_settings, clean_numeric_str, normalize_text, TIMEOUT_MS

KNOWN_WAREHOUSES = frozenset({
    "KHOTP00", "KHOTP01", "KHOTP02", "KHOTP03", "KHOLK00", "KHOLK01", "KHOLKSX",
    "KHONMD", "KHONVL00", "KHONVL01", "KHONVLSX", "KHOQA", "KHOQC", "KHOQC01", "KHOQC02",
    "KHOTESTITG", "KHOTNHH", "KHOVT00", "KHOVT01", "KHOVT02", "KHOVT03", "KHO25",
    "KHOBD01", "KHO-IN", "KHO-CXL", "KHO-LAP-RAP", "KHO-XHTL", "KHO-TAI-MAY",
    "KHO-SORTING", "KHO-HANG-LE", "KHO-HOALAC", "KHO-HOT", "KHO-HTSS", "KHO-GCN",
    "KHO-GBNG", "KHO-CHUYENTHUNG", "KHO-MAU-QC", "KHO-NG", "KHO-QVFLOT1", "KHO-QVFLOT2",
    "KHO-XHLOT2", "KHO-XHLOT3", "KHO_TAIMAY", "MOLD01", "VATTU_THIETBI", "CHUYENNGOAI"
})

def mock_sales_price(question, active_conv_code=None):
    clean_question = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s+\d{1,2}\s+thg\s+\d{1,2}(?:\s+\d{4})?)?\b", "", question, flags=re.I)
    normalized = normalize_text(clean_question)
    keywords = (
        "gia ban", "bang gia ban", "danh muc bang gia", "chinh sach gia", 
        "gia ban san pham", "tra cuu gia ban", "don gia ban", "gia niem yet",
        "gia cua ma hang", "gia cua ma", "gia ban cua ma hang", "gia ban cua ma",
        "gia dang bao nhieu", "gia ban la bao nhieu", "ban bao nhieu", "gia ban hien tai",
        "gia xuat ban", "gia san pham"
    )
    if not any(kw in normalized for kw in keywords):
        return None
    code_match = re.search(r"\b((?=[a-z0-9/.-]*\d)[a-z0-9]+(?:[-/.][a-z0-9]+)*)\b", clean_question, re.I)
    code = code_match.group(1).upper() if code_match else None
    if not code or (code.isdigit() and len(code) < 6):
        num_match = re.search(r"\b(\d{6,})\b", clean_question)
        code = num_match.group(1) if num_match else None
    if not code and active_conv_code:
        code = active_conv_code
    if code in ("ERP", "MES", "HTMP", "XLSX", "PDF", "DOCX", "GIA"):
        code = None

    with psycopg.connect(**connection_settings(), autocommit=False) as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            rows = []
            if code:
                sql = """
                    SELECT 
                        b.ma_bang_gia,
                        b.ten_bang_gia,
                        trim(c.ma_vt) AS ma_vt,
                        coalesce(v.ten_vt, c.ma_vt) AS ten_vt,
                        coalesce(v.dvt, c.dvt, 'PCS') AS dvt,
                        trim(c.ma_kh) AS ma_kh,
                        coalesce(k.ten_kh, c.ma_kh) AS ten_kh,
                        c.gia AS don_gia_ban,
                        coalesce(c.ma_nt, 'VND') AS ma_nt,
                        coalesce(c.sl_min, 0) AS sl_min,
                        to_char(c.ngay_bd, 'YYYY-MM-DD') AS ngay_bd,
                        to_char(c.ngay_kt, 'YYYY-MM-DD') AS ngay_kt
                    FROM public.dmbanggiact c
                    JOIN public.dmbanggia b ON b.ma_bang_gia = c.ma_bang_gia
                    LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(c.ma_vt))
                    LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(c.ma_kh))
                    WHERE upper(trim(c.ma_vt)) = %s 
                       OR upper(trim(b.ma_bang_gia)) = %s 
                       OR upper(trim(c.ma_kh)) = %s
                    ORDER BY c.ngay_bd DESC, c.ma_bang_gia
                    LIMIT 10;
                """
                cursor.execute(sql, (code, code, code))
                rows = cursor.fetchall()
                if not rows:
                    sql_issue = """
                        SELECT 
                            'PXK' AS ma_bang_gia,
                            'Phiếu xuất kho bán hàng' AS ten_bang_gia,
                            trim(c.ma_vt) AS ma_vt,
                            coalesce(v.ten_vt, c.ma_vt) AS ten_vt,
                            coalesce(v.dvt, c.dvt, 'PCS') AS dvt,
                            trim(h.ma_kh) AS ma_kh,
                            coalesce(k.ten_kh, h.ma_kh) AS ten_kh,
                            c.gia2 AS don_gia_ban,
                            coalesce(c.ma_nt, 'VND') AS ma_nt,
                            0 AS sl_min,
                            to_char(c.ngay_ct, 'YYYY-MM-DD') AS ngay_bd,
                            to_char(c.ngay_ct, 'YYYY-MM-DD') AS ngay_kt
                        FROM public.ct81 c
                        JOIN public.ph81 h ON h.stt_rec = c.stt_rec
                        LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(c.ma_vt))
                        LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(h.ma_kh))
                        WHERE upper(trim(c.ma_vt)) = %s AND c.gia2 > 0
                        ORDER BY c.ngay_ct DESC
                        LIMIT 5;
                    """
                    cursor.execute(sql_issue, (code,))
                    rows = cursor.fetchall()

    if rows and code:
        first = rows[0]
        ten = first.get("ten_vt", code)
        raw_gia = float(first.get("don_gia_ban") or 0)
        gia_str = f"{int(raw_gia):,}" if raw_gia.is_integer() else f"{raw_gia:g}"
        nt = first.get("ma_nt", "VND")
        dvt = first.get("dvt", "PCS")
        kh = first.get("ten_kh", first.get("ma_kh", ""))
        bd = first.get("ngay_bd", "")
        kt = first.get("ngay_kt", "")
        bg = first.get("ten_bang_gia", first.get("ma_bang_gia", ""))
        msg = f"Giá bán của mã hàng {code} ({ten}) là {gia_str} {nt}/{dvt}"
        if kh:
            msg += f" (khách hàng: {kh})"
        if bd and kt:
            msg += f", hiệu lực: {bd} đến {kt}"
        if bg:
            msg += f" [{bg}]."
        else:
            msg += "."
        return msg
    return f"Không tìm thấy giá bán cho mã {code}"

def mock_wh_stock(question, active_conv_code=None):
    clean_question = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s+\d{1,2}\s+thg\s+\d{1,2}(?:\s+\d{4})?)?\b", "", question, flags=re.I)
    normalized = normalize_text(clean_question)
    
    # 1. Target warehouse detection
    target_warehouse = None
    for wh in KNOWN_WAREHOUSES:
        if re.search(rf"\b{re.escape(wh)}\b", clean_question, re.I):
            target_warehouse = wh.upper()
            break
            
    wh_keywords = (
        "o tung kho", "tung kho", "cac kho", "theo kho", "nhung kho", "kho nao", "ton o kho", "tat ca cac kho",
        "ton o", "ton tai", "ton kho tai", "ton kho o", "ton chi tiet cac kho", "ton chi tiet"
    )
    if not any(k in normalized for k in wh_keywords) and not target_warehouse:
        return None
        
    # 2. Material code detection
    code_match = re.search(r"\b([a-zA-Z0-9]+(?:[-/][a-zA-Z0-9]+)+|[a-zA-Z]{2,}\d+|\d+[a-zA-Z]+\d*)\b", clean_question, re.I)
    material_code = None
    if code_match:
        c = code_match.group(1).upper()
        if c not in KNOWN_WAREHOUSES and not c.startswith("KHO") and not (c.isdigit() and len(c) < 6):
            material_code = c
    if not material_code:
        num_match = re.search(r"\b(\d{6,})\b", clean_question)
        if num_match:
            material_code = num_match.group(1)
    if not material_code and active_conv_code:
        material_code = active_conv_code
        
    with psycopg.connect(**connection_settings(), autocommit=False) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SELECT public.sys_getstartdate(CURRENT_DATE)")
            start_date = cursor.fetchone()[0]
            
            if material_code:
                cursor.execute("""
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
                          AND c.ngay_ct >= %s
                        GROUP BY c.ma_kho
                    ),
                    combined AS (
                        SELECT ma_kho, qty FROM opening
                        UNION ALL
                        SELECT ma_kho, qty FROM movements
                    )
                    SELECT ma_kho, sum(qty) AS ton_kho
                    FROM combined
                    GROUP BY ma_kho
                    HAVING sum(qty) > 0
                    ORDER BY ton_kho DESC;
                """, (start_date, material_code, material_code, start_date))
                rows = cursor.fetchall()
                
                cursor.execute("SELECT coalesce(dvt, 'PCS') FROM public.dmvt WHERE upper(trim(ma_vt)) = %s", (material_code,))
                r_dvt = cursor.fetchone()
                dvt = str(r_dvt[0]).strip() if r_dvt and r_dvt[0] else "PCS"
                
                parts = [f"{r[0]}: {int(r[1]):,} {dvt}" for r in rows]
                total = sum(int(r[1]) for r in rows)
                
                if target_warehouse:
                    wh_match = [r for r in rows if r[0].upper() == target_warehouse]
                    wh_qty = int(wh_match[0][1]) if wh_match else 0
                    msg = f"Tồn kho của mã {material_code} tại kho {target_warehouse} hiện tại là {wh_qty:,} {dvt}"
                    if total > 0:
                        msg += f" (Tổng tồn toàn bộ các kho: {total:,} {dvt} gồm {'; '.join(parts)})."
                    else:
                        msg += f" (Mã {material_code} hiện tại không còn tồn ở kho nào khác)."
                    return msg
                else:
                    return f"Tồn kho hiện tại của mã {material_code} ở từng kho: " + "; ".join(parts) + f" (Tổng cộng: {total:,} {dvt})."
            elif target_warehouse:
                cursor.execute("""
                    SELECT coalesce(k.ten_kho, %s), sum(b.so_luong_ton) AS tong_ton
                    FROM (
                        SELECT sum(ton00) AS so_luong_ton
                        FROM public.cdvt
                        WHERE nam = extract(year FROM %s::date)::smallint AND upper(trim(ma_kho)) = %s
                        UNION ALL
                        SELECT sum(sl_nhap - sl_xuat) AS so_luong_ton
                        FROM public.ct70
                        WHERE ngay_ct >= %s AND upper(trim(ma_kho)) = %s
                    ) b
                    LEFT JOIN public.dmkho k ON upper(trim(k.ma_kho)) = %s
                    GROUP BY k.ten_kho;
                """, (target_warehouse, start_date, target_warehouse, start_date, target_warehouse, target_warehouse))
                r = cursor.fetchone()
                ten_kho = r[0] if r else target_warehouse
                total_wh = int(r[1]) if r and r[1] else 0
                return f"Tổng số lượng tồn kho tại kho {target_warehouse} ({ten_kho}) hiện tại là {total_wh:,} PCS."

print("=" * 80)
print("TEST 1: Incident 29: check cho chị giá bán của mã hàng 156279430 15:49 6 thg 11")
print(mock_sales_price("check cho chị giá bán của mã hàng 156279430 15:49 6 thg 11"))

print("\n" + "=" * 80)
print("TEST 2: Incident 28: check cho chị giá bán của mã hàng T1015910DA này đang bao nhiêu 15:47 6 thg 11")
print(mock_sales_price("check cho chị giá bán của mã hàng T1015910DA này đang bao nhiêu 15:47 6 thg 11"))

print("\n" + "=" * 80)
print("TEST 3: Incident 27: cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11 (with prior material 1014084300)")
print(mock_wh_stock("cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11", active_conv_code="1014084300"))

print("\n" + "=" * 80)
print("TEST 4: Incident 27 variant: cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11 (no prior material)")
print(mock_wh_stock("cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11"))
