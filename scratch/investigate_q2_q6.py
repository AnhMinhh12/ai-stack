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
    # Q2: MOQ & Bảng giá
    # ----------------------------------------------------
    print_section("CÂU 2: MOQ báo giá hiện tại & Giá áp dụng")
    res_bg = query("""
        SELECT c.*, b.ten_bang_gia, b.ngay_bd, b.ngay_kt, c.ma_nt, b.status
        FROM dmbanggiact c
        JOIN dmbanggia b ON c.ma_bang_gia = b.ma_bang_gia
        WHERE c.ma_vt = 'QC7-5146-000'
        ORDER BY b.ngay_bd DESC
    """)
    print("dmbanggiact:", json.dumps(res_bg, ensure_ascii=False, indent=2, default=str))

    # Also check dmgiamua / dmgia / sys_banggia or other price tables
    tables_bg = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%%gia%%'
    """)
    for t in [tb['table_name'] for tb in tables_bg]:
        try:
            r = query(f"SELECT * FROM {t} WHERE ma_vt = 'QC7-5146-000' LIMIT 5")
            if r:
                print(f"Table {t}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception:
            pass

    # Check moq in dmvt
    res_vt_moq = query("SELECT ma_vt, moq, min_stock, max_stock, gia_ton FROM dmvt WHERE ma_vt = 'QC7-5146-000'")
    print("dmvt MOQ:", res_vt_moq)

    # ----------------------------------------------------
    # Q3: Lot gần nhất xuất giao tính đến ngày 20/10/2026
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
    print("Xuất giao HDA:", json.dumps(res_q3, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q4: Từ 01/10/2026 đến hết 20/10/2026: Tổng SL xuất bán & Doanh thu
    # ----------------------------------------------------
    print_section("CÂU 4: Tổng SL xuất bán & doanh thu (01/10/2026 - 20/10/2026)")
    res_q4_detail = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.so_luong, d.gia2, d.tien2, h.ma_nt
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct ASC, h.so_ct ASC
    """)
    print("Chi tiết xuất bán:", json.dumps(res_q4_detail, ensure_ascii=False, indent=2, default=str))
    res_q4_sum = query("""
        SELECT h.ma_nt, COUNT(DISTINCT h.so_ct) as so_phieu, SUM(d.so_luong) as tong_so_luong, SUM(d.tien2) as tong_tien2
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        GROUP BY h.ma_nt
    """)
    print("Tổng cộng:", json.dumps(res_q4_sum, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q6: Nhập kho QC7-5146-000 (01/10/2026 - 20/10/2026)
    # ----------------------------------------------------
    print_section("CÂU 6: Nhập kho QC7-5146-000 (01/10/2026 - 20/10/2026)")
    # Check all internal transactions ph74/ct74 or ph71/ct71
    res_q6_74 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_ct, h.user_id0, h.user_id2,
               d.ma_vt, d.so_luong, d.ma_kho, d.ma_khon, d.ma_lo, u.user_name as creator_name
        FROM ph74 h
        JOIN ct74 d USING(stt_rec)
        LEFT JOIN sys_userinfo u ON h.user_id0 = u.user_id
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct ASC
    """)
    print("Trong ph74/ct74:", json.dumps(res_q6_74, ensure_ascii=False, indent=2, default=str))

    # Check ct70 (thẻ kho) for any other receipts (ma_ct = 'PND', 'PN1', etc.)
    res_q6_ct70 = query("""
        SELECT ngay_ct, so_ct, ma_ct, sl_nhap, sl_xuat, ma_kho, ma_khon, ma_lo, user_id0
        FROM ct70
        WHERE ma_vt = 'QC7-5146-000' AND ngay_ct >= '2026-10-01' AND ngay_ct <= '2026-10-20' AND sl_nhap > 0
        ORDER BY ngay_ct ASC
    """)
    print("Trong ct70 nhập:", json.dumps(res_q6_ct70, ensure_ascii=False, indent=2, default=str))

if __name__ == '__main__':
    main()
