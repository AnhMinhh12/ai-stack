#!/usr/bin/env python3
import json
import psycopg
from psycopg.rows import dict_row

CONN_PARAMS = {
    "host": "10.0.6.2",
    "port": 5410,
    "dbname": "3SERP_HTMP_DATA",
    "user": "read_htmp",
    "password": "P@ss@Htmp@W0rd!2025",
    "connect_timeout": 5
}

def query(sql, params=None):
    with psycopg.connect(**CONN_PARAMS, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def main():
    print("=== Q17: Khách hàng 'Canon... Thăng Long' ===")
    res_kh = query("SELECT ma_kh, ten_kh, dia_chi FROM dmkh WHERE ten_kh ILIKE %s OR ma_kh ILIKE %s", ['%Canon%', '%KH0015%'])
    print(json.dumps(res_kh, ensure_ascii=False, indent=2, default=str))

    print("\n=== Q5: Mã hàng QC7-5146-000 thuộc khách hàng nào? ===")
    res_vt = query("""
        SELECT * FROM dmvt WHERE ma_vt ILIKE %s
    """, ['%QC7-5146-000%'])
    print("In dmvt:")
    for r in res_vt:
        for k, v in r.items():
            if v is not None and v != "":
                print(f"  {k}: {v}")

    # Also check other tables referencing QC7-5146-000
    res_vt_kh = query("""
        SELECT DISTINCT ma_kh FROM ph64 h JOIN ct64 d USING(stt_rec) WHERE d.ma_vt ILIKE %s
    """, ['%QC7-5146-000%'])
    print("In ph64/ct64 customers:", res_vt_kh)

    print("\n=== Q1: Cấu trúc sản phẩm / Loại nhựa cho QC7-5146-000 ===")
    # Check tables with 'bom' or 'dinh_muc' or 'mfbom'
    tables_bom = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND (table_name ILIKE '%bom%' OR table_name ILIKE '%dinhmuc%' OR table_name ILIKE '%cau_truc%')
    """)
    print("BOM tables:", [t['table_name'] for t in tables_bom])
    
    for t in [tb['table_name'] for tb in tables_bom]:
        try:
            r = query(f"SELECT * FROM {t} WHERE ma_vt ILIKE %s LIMIT 5", ['%QC7-5146-000%'])
            if r:
                print(f"Found in {t}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception as e:
            pass

    # Check dmvt description / quy cach / ghi chu / nhom
    res_vt_detail = query("SELECT * FROM dmvt WHERE ma_vt ILIKE %s", ['%QC7-5146-000%'])
    print("Full dmvt columns:", json.dumps(res_vt_detail, ensure_ascii=False, indent=2, default=str))

    print("\n=== Q2: MOQ & Giá của QC7-5146-000 ===")
    # Search dmbanggia & dmbanggiact
    res_bg = query("""
        SELECT c.*, b.ten_bang_gia, b.ngay_hl, b.ngay_hh, b.ma_nt
        FROM dmbanggiact c
        JOIN dmbanggia b ON c.ma_bang_gia = b.ma_bang_gia
        WHERE c.ma_vt ILIKE %s
    """, ['%QC7-5146-000%'])
    print("dmbanggiact:", json.dumps(res_bg, ensure_ascii=False, indent=2, default=str))

    # Also check other price tables
    tables_gia = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name ILIKE '%gia%'
    """)
    print("Gia tables:", [t['table_name'] for t in tables_gia])

    print("\n=== Q3 & Q4: Xuất bán QC7-5146-000 ===")
    # Check ct81/ph81
    res_xuat = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.gia2, d.tien2, d.ma_lo, d.so_po, d.so_so
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt ILIKE %s AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC
        LIMIT 10
    """, ['%QC7-5146-000%'])
    print("Recent shipments (up to 2026-10-20):", json.dumps(res_xuat, ensure_ascii=False, indent=2, default=str))

    # Q4: From 2026-10-01 to 2026-10-20
    res_q4 = query("""
        SELECT COUNT(*) as so_dong, SUM(d.so_luong) as tong_sl, SUM(d.tien2) as tong_tien2, h.ma_nt
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt ILIKE %s AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        GROUP BY h.ma_nt
    """, ['%QC7-5146-000%'])
    print("Q4 Aggregate (01/10/2026 - 20/10/2026):", json.dumps(res_q4, ensure_ascii=False, indent=2, default=str))

if __name__ == '__main__':
    main()
