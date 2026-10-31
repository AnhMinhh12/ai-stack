import psycopg, re, json, os

settings = {
    "host": os.getenv("HTMP_DB_HOST"),
    "port": os.getenv("HTMP_DB_PORT", "5410"),
    "dbname": os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
    "user": os.getenv("HTMP_DB_USER"),
    "password": os.getenv("HTMP_DB_PASSWORD"),
    "connect_timeout": 5,
}

def query_mold(code_input, is_cavity_question=True):
    code = code_input.strip()
    code_search = re.sub(r"[\s\-_]+", "", code).upper()
    with psycopg.connect(**settings) as conn:
        with conn.cursor() as cursor:
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
                   OR replace(replace(upper(m.ma_khuon), ' ', ''), '-', '') LIKE %s
                   OR replace(replace(upper(m.ten_khuon), ' ', ''), '-', '') LIKE %s
                ORDER BY m.ngay DESC NULLS LAST, m.ma_khuon
                LIMIT 30;
            """
            cursor.execute(sql, (f"%{code}%", f"%{code}%", f"%{code_search}%", f"%{code_search}%"))
            cols = [desc[0] for desc in cursor.description]
            raw_rows = cursor.fetchall()
            rows = [dict(zip(cols, r)) for r in raw_rows]
            
            for idx, r in enumerate(rows, 1):
                r["stt"] = idx
                if r.get("so_cavity") is not None:
                    c_val = float(r["so_cavity"])
                    r["so_cavity"] = int(c_val) if c_val.is_integer() else c_val
                if r.get("tuoi_tho_shot_dinh_muc") is not None:
                    r["tuoi_tho_shot_dinh_muc"] = int(float(r["tuoi_tho_shot_dinh_muc"]))
                if r.get("so_shot_da_chay") is not None:
                    r["so_shot_da_chay"] = int(float(r["so_shot_da_chay"]))
            
            if not rows:
                msg = f"Không tìm thấy hồ sơ khuôn nào có mã hoặc tên chứa '{code}' trong hệ thống ERP (toàn nhà máy hiện có 2,185 hồ sơ khuôn). Vui lòng kiểm tra lại mã khuôn."
                return {"row_count": 0, "rows": [], "message": msg}
            
            if len(rows) == 1:
                r0 = rows[0]
                ten = r0["ten_khuon"] or r0["ma_khuon"]
                cav = r0.get("so_cavity", "chưa cập nhật")
                tt = r0.get("tinh_trang_khuon") or "chưa cập nhật"
                shot_bh = f"{r0['tuoi_tho_shot_dinh_muc']:,}" if r0.get("tuoi_tho_shot_dinh_muc") else "chưa cập nhật"
                if is_cavity_question:
                    msg = f"Khuôn {r0['ma_khuon']} (tên khuôn: {ten}) có {cav} cavity (tình trạng: {tt}, tuổi thọ định mức: {shot_bh} shot)."
                else:
                    msg = f"Hồ sơ khuôn {r0['ma_khuon']} (tên: {ten}): {cav} cavity, tình trạng: {tt}, định mức: {shot_bh} shot, đã chạy: {r0.get('so_shot_da_chay', 0):,} shot."
            else:
                cav_list = [f"{r['ma_khuon']} ({r.get('so_cavity', 0)} cavity)" for r in rows[:5]]
                msg = f"Tìm thấy {len(rows)} hồ sơ khuôn liên quan đến '{code}': {', '.join(cav_list)}."
            
            return {"row_count": len(rows), "rows": rows, "message": msg}

print("Test 1: '4509'")
print(query_mold("4509")["message"])

print("\nTest 2: 'K_101 40481 01'")
print(query_mold("K_101 40481 01")["message"])

print("\nTest 3: 'K_QC5-2919-000-V1'")
print(query_mold("K_QC5-2919-000-V1")["message"])
