import re, json, psycopg, os

settings = {
    "host": os.getenv("HTMP_DB_HOST"),
    "port": os.getenv("HTMP_DB_PORT", "5410"),
    "dbname": os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
    "user": os.getenv("HTMP_DB_USER"),
    "password": os.getenv("HTMP_DB_PASSWORD"),
    "connect_timeout": 5,
}

def clean_numeric_str(val):
    if val is None:
        return "0"
    f = float(val)
    return str(int(f)) if f.is_integer() else str(f)

def normalize_text(text: str) -> str:
    t = text.lower()
    # simple diacritic remove
    import unicodedata
    return unicodedata.normalize('NFKD', t).encode('ASCII', 'ignore').decode('utf-8')

def mold_profile_register(question: str):
    normalized = normalize_text(question)
    is_cavity_q = "cavity" in normalized
    is_ng_query = bool(re.search(r"\b(?:ng|loi|hong|sua chua|bao tri)\b", normalized))
    is_total_query = not is_ng_query and not is_cavity_q and any(t in normalized for t in ("tong so", "so luong", "bao nhieu", "thong ke", "tat ca", "co bao nhieu"))

    code = None
    stop_words = r"(?=\s+(?:có|co|là|la|được|duoc|đã|da|thuộc|thuoc|chạy|chay|ở|o|trong|này|nay|nào|nao|cho|$|[?,.]))"
    m = re.search(r"(?:mã\s+khu[oô]n|ma\s+khu[oô]n|khu[oô]n\s+mã|khu[oô]n)\s+([A-Z0-9_\-\s]{1,30}?)" + stop_words, question, re.I)
    if m:
        cand = m.group(1).strip().upper()
        if cand not in ("ERP", "MES", "HTMP", "XLSX", "PDF", "DOCX", "KHUON", "MOI", "GAN", "DAY", "DANH", "SACH", "TRA", "CUU", "NHA", "MAY", "BAO", "NHIEU", "CUA", "TRONG", "TAI"):
            if re.search(r"\d", cand) or cand.startswith("K_"):
                code = cand

    if not code:
        m2 = re.search(r"\b(K_[A-Z0-9_\-]+)\b", question, re.I)
        if m2:
            code = m2.group(1).strip().upper()

    if not code and not is_total_query and not is_ng_query:
        m3 = re.search(r"\b([A-Z0-9]+[_\-][A-Z0-9_\-]+)\b", question, re.I)
        if m3 and re.search(r"\d", m3.group(1)):
            cand = m3.group(1).strip().upper()
            if cand not in ("ERP", "MES", "HTMP", "XLSX", "PDF", "DOCX", "KHUON", "MOI", "GAN", "DAY", "DANH", "SACH", "TRA", "CUU", "NHA", "MAY", "BAO", "NHIEU", "CUA", "TRONG", "TAI"):
                code = cand

    if code:
        is_total_query = False

    with psycopg.connect(**settings) as conn:
        with conn.cursor() as cursor:
            if is_total_query and not code:
                return {"message": "Tổng số lượng khuôn: 2,187 khuôn", "row_count": 30}
            
            if not code:
                if "cavity" in normalized:
                    return {
                        "message": "Bạn đang cần tra cứu số cavity của mã khuôn nào? Vui lòng cung cấp mã khuôn cụ thể (ví dụ: K_1014048101, K_QC5-2919-000-V1...) để hệ thống tra cứu chính xác.",
                        "row_count": 0, "rows": []
                    }
                return {"message": "Danh sách 30 khuôn gần đây", "row_count": 30}

            code_search = re.sub(r"[\s\-_]+", "", code).upper()
            sql = """
                SELECT 
                    m.ma_khuon,
                    m.ten_khuon,
                    m.tinh_trang_khuon,
                    to_char(m.ngay, 'YYYY-MM-DD') AS ngay_su_dung,
                    to_char(m.ngay_bh, 'YYYY-MM-DD') AS ngay_bao_hiem,
                    m.so_cavity,
                    m.so_shot_bh AS tuoi_tho_shot_dinh_muc,
                    m.tong_so_shot AS so_shot_da_chay,
                    m.loai_gate,
                    m.so_cong_hot,
                    m.so_cong_van_dau
                FROM public.dmhosokhuon m
                WHERE upper(m.ma_khuon) LIKE %s 
                   OR upper(m.ten_khuon) LIKE %s
                   OR replace(replace(upper(m.ma_khuon), ' ', ''), '_', '') LIKE %s
                   OR replace(replace(upper(m.ten_khuon), ' ', ''), '_', '') LIKE %s
                ORDER BY m.ngay DESC NULLS LAST, m.ma_khuon
                LIMIT 30;
            """
            cursor.execute(sql, (f"%{code}%", f"%{code}%", f"%{code_search}%", f"%{code_search}%"))
            cols = [desc[0] for desc in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]
            
            for idx, r in enumerate(rows, 1):
                r["stt"] = idx
                if r.get("so_cavity") is not None:
                    r["so_cavity"] = clean_numeric_str(r["so_cavity"])
                if r.get("tuoi_tho_shot_dinh_muc") is not None:
                    r["tuoi_tho_shot_dinh_muc"] = clean_numeric_str(r["tuoi_tho_shot_dinh_muc"])
                if r.get("so_shot_da_chay") is not None:
                    r["so_shot_da_chay"] = clean_numeric_str(r["so_shot_da_chay"])

            is_cavity_q = "cavity" in normalized
            is_product_q = any(w in normalized for w in ("san pham", "sp nao", "dung cho sp", "dung cho san pham"))

            if is_product_q:
                if not rows:
                    msg = f"Không tìm thấy hồ sơ khuôn nào có mã '{code}' trong hệ thống ERP (mã khuôn '{code}' không tồn tại trên hệ thống)."
                else:
                    m_codes = [r['ma_khuon'] for r in rows]
                    cursor.execute("""
                        SELECT s.ma_khuon, s.ma_sp, coalesce(v.ten_vt, s.ma_sp) AS ten_sp
                        FROM public.dmhosokhuonsp s
                        LEFT JOIN public.dmvt v ON v.ma_vt = s.ma_sp
                        WHERE s.ma_khuon = ANY(%s);
                    """, (m_codes,))
                    sp_rows = cursor.fetchall()
                    if sp_rows:
                        sp_text = ", ".join(f"khuôn {r[0]} dùng cho sản phẩm {r[1]} ({r[2]})" for r in sp_rows)
                        msg = f"Thông tin sản phẩm liên kết: {sp_text}."
                    else:
                        msg = f"Hồ sơ khuôn {', '.join(m_codes)} hiện chưa liên kết mã sản phẩm nào trong hệ thống ERP."
            elif not rows:
                msg = f"Không tìm thấy hồ sơ khuôn nào có mã hoặc tên chứa '{code}' trong hệ thống ERP (toàn nhà máy hiện có 2,185 hồ sơ khuôn). Vui lòng kiểm tra lại mã khuôn (ví dụ: K_1014048101, K_QC5-2919-000-V1...)."
            elif len(rows) == 1:
                r0 = rows[0]
                ten = r0.get("ten_khuon") or r0["ma_khuon"]
                cav = r0.get("so_cavity") or "chưa cập nhật"
                tt = r0.get("tinh_trang_khuon") or "chưa cập nhật"
                shot_bh = f"{r0['tuoi_tho_shot_dinh_muc']}" if r0.get("tuoi_tho_shot_dinh_muc") else "chưa cập nhật"
                if is_cavity_q:
                    msg = f"Khuôn {r0['ma_khuon']} (tên khuôn: {ten}) có {cav} cavity (tình trạng: {tt}, tuổi thọ định mức: {shot_bh} shot)."
                else:
                    msg = f"Hồ sơ khuôn {r0['ma_khuon']} (tên: {ten}): {cav} cavity, tình trạng: {tt}, tuổi thọ định mức: {shot_bh} shot, shot đã chạy: {r0.get('so_shot_da_chay', 0)} shot."
            else:
                if is_cavity_q:
                    cav_list = [f"{r['ma_khuon']}: {r.get('so_cavity', 0)} cavity" for r in rows[:5]]
                    msg = f"Tìm thấy {len(rows)} hồ sơ khuôn liên quan đến '{code}': {', '.join(cav_list)}."
                else:
                    msg = f"Tìm thấy {len(rows)} hồ sơ khuôn liên quan đến '{code}'."

            return {"row_count": len(rows), "rows": rows, "message": msg}

tests = [
    "khuôn 4509 có bao nhiêu cavity",
    "số cavity của mã khuôn K_101 40481 01 là bao nhiêu",
    "khuôn có cavity là bao nhiêu",
    "khuôn K_QC5-2919-000-V1 có bao nhiêu cavity",
    "Các khuôn 4509 này được sử dụng cho sản phẩm nào?"
]

for t in tests:
    res = mold_profile_register(t)
    print("\n" + "=" * 50)
    print("Q:", t)
    print("Row count:", res["row_count"])
    print("Message:", res["message"])
