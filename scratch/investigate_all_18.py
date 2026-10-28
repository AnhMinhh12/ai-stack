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

def print_section(title):
    print(f"\n{'='*20} {title} {'='*20}")

def main():
    # ----------------------------------------------------
    # Q1: Loại nhựa & Cấu trúc sản phẩm (BOM)
    # ----------------------------------------------------
    print_section("CÂU 1: Loại nhựa & Cấu trúc sản phẩm của QC7-5146-000")
    # Check dmvt NVL & BOM
    res_vt = query("""
        SELECT ma_vt, ten_vt, ten_vt2, model, ma_kh, ma_nvl, weight, weight_runner, cavity, die_no,
               ma_thung, ma_khay, so_luong_vt_khay, packs0, ma_vt_c1, sl_sp_ma_vt_c1, sl_ma_vt_c1_thung
        FROM dmvt WHERE ma_vt = 'QC7-5146-000'
    """)
    print("Thông tin vật tư dmvt:", json.dumps(res_vt, ensure_ascii=False, indent=2, default=str))

    # Check BOM tables in system
    bom_tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%%bom%%'
    """)
    print("Các bảng BOM trong DB:", [t['table_name'] for t in bom_tables])
    for tb in [t['table_name'] for t in bom_tables]:
        try:
            r = query(f"SELECT * FROM {tb} WHERE ma_vt = 'QC7-5146-000' OR ma_sp = 'QC7-5146-000' LIMIT 5")
            if r:
                print(f"Dữ liệu trong {tb}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception:
            pass

    # Check routing tables
    routing_tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%%routing%%'
    """)
    print("Các bảng Routing:", [t['table_name'] for t in routing_tables])
    for tb in [t['table_name'] for t in routing_tables]:
        try:
            r = query(f"SELECT * FROM {tb} WHERE ma_vt = 'QC7-5146-000' OR ma_sp = 'QC7-5146-000' LIMIT 5")
            if r:
                print(f"Dữ liệu trong {tb}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception:
            pass

    # ----------------------------------------------------
    # Q2: MOQ báo giá hiện tại & Giá áp dụng theo từng mức MOQ
    # ----------------------------------------------------
    print_section("CÂU 2: MOQ báo giá hiện tại & Giá áp dụng theo MOQ")
    res_bg = query("""
        SELECT c.*, b.ten_bang_gia, b.ngay_hl, b.ngay_hh, b.ma_nt, b.status
        FROM dmbanggiact c
        JOIN dmbanggia b ON c.ma_bang_gia = b.ma_bang_gia
        WHERE c.ma_vt = 'QC7-5146-000'
        ORDER BY b.ngay_hl DESC
    """)
    print("Trong dmbanggiact:", json.dumps(res_bg, ensure_ascii=False, indent=2, default=str))

    # Also search any other table with 'gia' and 'QC7-5146-000'
    gia_tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%%gia%%' AND table_name NOT LIKE '%%banggia%%'
    """)
    print("Bảng giá khác:", [t['table_name'] for t in gia_tables])
    for tb in [t['table_name'] for t in gia_tables]:
        try:
            r = query(f"SELECT * FROM {tb} WHERE ma_vt = 'QC7-5146-000' LIMIT 5")
            if r:
                print(f"Dữ liệu trong {tb}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception:
            pass

    # ----------------------------------------------------
    # Q3: Lot gần nhất xuất giao tính đến 20/10/2026
    # ----------------------------------------------------
    print_section("CÂU 3: Lot gần nhất xuất giao tính đến 20/10/2026")
    res_q3 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.ma_lo, d.so_po, d.so_so, d.gia2, d.tien2
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC
        LIMIT 5
    """)
    print("Xuất giao HDA (ph81/ct81):", json.dumps(res_q3, ensure_ascii=False, indent=2, default=str))

    # Also check MES shipment / xuất hàng if any
    mes_ship = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%%xuat%%'
    """)
    print("Bảng xuất khác:", [t['table_name'] for t in mes_ship])

    # ----------------------------------------------------
    # Q4: Từ 01/10/2026 đến hết 20/10/2026: Tổng SL xuất bán & doanh thu
    # ----------------------------------------------------
    print_section("CÂU 4: Tổng SL xuất bán & doanh thu (01/10/2026 - 20/10/2026)")
    res_q4_detail = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_kh, d.so_luong, d.gia2, d.tien2, h.ma_nt, h.ty_gia
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct ASC
    """)
    print("Chi tiết từng phiếu xuất:", json.dumps(res_q4_detail, ensure_ascii=False, indent=2, default=str))
    res_q4_sum = query("""
        SELECT COUNT(*) as so_dong, COUNT(DISTINCT h.so_ct) as so_phieu,
               SUM(d.so_luong) as tong_so_luong, SUM(d.tien2) as tong_tien2, h.ma_nt
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        GROUP BY h.ma_nt
    """)
    print("Tổng cộng:", json.dumps(res_q4_sum, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q5 & Q17: Khách hàng của QC7-5146-000 & Mã KH của Canon Thăng Long
    # ----------------------------------------------------
    print_section("CÂU 5 & 17: Khách hàng")
    print("Mã KH trong dmvt của QC7-5146-000:", res_vt[0].get('ma_kh') if res_vt else None)
    res_canon = query("SELECT ma_kh, ten_kh, dia_chi FROM dmkh WHERE ten_kh ILIKE '%%Canon%%Thăng Long%%'")
    print("Khách hàng Canon Thăng Long:", json.dumps(res_canon, ensure_ascii=False, indent=2, default=str))

if __name__ == '__main__':
    main()
