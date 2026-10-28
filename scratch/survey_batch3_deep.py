#!/usr/bin/env python3
import psycopg
import time
import json

def main():
    conn = psycopg.connect(
        host='10.0.6.2',
        port=5410,
        dbname='3SERP_HTMP_DATA',
        user='read_htmp',
        password='P@ss@Htmp@W0rd!2025',
        connect_timeout=3
    )
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '3s'")
    
    print("=" * 80)
    print("KHẢO SÁT CHI TIẾT NGHIỆP VỤ ĐỢT 3 (BÁN HÀNG, MUA HÀNG, KHO VẬN, KHUÔN)")
    print("=" * 80)

    # 1. BÁN HÀNG: SO1 (ph64/ct64)
    print("\n1. BÁN HÀNG - ĐƠN HÀNG BÁN / HỢP ĐỒNG (SO1: ph64 & ct64):")
    cur.execute("""
        SELECT so_ct, ngay_ct, ma_kh, ten_kh, so_po, t_so_luong, t_tien, status
        FROM ph64
        WHERE ma_ct = 'SO1'
        ORDER BY ngay_ct DESC
        LIMIT 3;
    """)
    rows = cur.fetchall()
    for r in rows:
        print(f"  Header SO: {r[0]} | Ngày: {r[1]} | KH: {r[2]} ({r[3]}) | PO_KH: {r[4]} | Tổng SL: {r[5]:,.0f} | Tổng tiền: {r[6]:,.0f} | Status: {r[7]}")
    
    # 2. BÁN HÀNG: XUẤT BÁN / HÓA ĐƠN (HDA: ph81 & ct81)
    print("\n2. BÁN HÀNG - PHIẾU XUẤT BÁN / HÓA ĐƠN BÁN HÀNG (ph81 & ct81):")
    cur.execute("""
        SELECT so_ct, ngay_ct, ma_ct, ma_kh, ten_kh, t_so_luong, t_tien, so_ct_so1, status
        FROM ph81
        ORDER BY ngay_ct DESC
        LIMIT 3;
    """)
    for r in cur.fetchall():
        print(f"  Header PXK Bán: {r[0]} | Ngày: {r[1]} | Loại CT: {r[2]} | KH: {r[3]} ({r[4]}) | Tổng SL: {r[5]:,.0f} | Tiền: {r[6]:,.0f} | Ref SO: {r[7]} | Status: {r[8]}")

    # 3. MUA HÀNG: ĐƠN HÀNG MUA PO (ph94 & ct94)
    print("\n3. MUA HÀNG - ĐƠN HÀNG MUA (PO: ph94 & ct94):")
    cur.execute("""
        SELECT so_ct, ngay_ct, ma_ct, ma_kh, ten_kh, t_so_luong, t_tien, status
        FROM ph94
        ORDER BY ngay_ct DESC
        LIMIT 3;
    """)
    for r in cur.fetchall():
        print(f"  Header PO: {r[0]} | Ngày: {r[1]} | Loại CT: {r[2]} | NCC: {r[3]} ({r[4]}) | Tổng SL: {r[5]:,.0f} | Tiền: {r[6]:,.0f} | Status: {r[7]}")

    # 4. KHO VẬN: PHIẾU NHẬP / XUẤT KHO KHÁC (ph74 / ct74)
    print("\n4. KHO VẬN - PHIẾU NHẬP/XUẤT KHO NỘI BỘ (ph74 & ct74):")
    cur.execute("""
        SELECT so_ct, ngay_ct, ma_ct, t_so_luong, dien_giai, status
        FROM ph74
        ORDER BY ngay_ct DESC
        LIMIT 3;
    """)
    for r in cur.fetchall():
        print(f"  Header Kho 74: {r[0]} | Ngày: {r[1]} | Loại CT: {r[2]} | SL: {r[3]:,.0f} | Diễn giải: {r[4]} | Status: {r[5]}")

    # 5. KHO VẬN: SỔ CHI TIẾT VẬT TƯ (ct70) & TỒN KHO (cdvt)
    print("\n5. KHO VẬN - SỔ CHI TIẾT NHẬP XUẤT TỒN (ct70):")
    cur.execute("""
        SELECT ngay_ct, so_ct, ma_ct, ma_vt, ma_kho, ma_nx, sl_nhap, sl_xuat
        FROM ct70
        ORDER BY ngay_ct DESC
        LIMIT 3;
    """)
    for r in cur.fetchall():
        print(f"  Log ct70: Ngày {r[0]} | CT: {r[1]} ({r[2]}) | VT: {r[3]} | Kho: {r[4]} | Nhập/Xuất: {r[5]} | SL Nhập: {r[6]} | SL Xuất: {r[7]}")

    # 6. BẢNG GIÁ (dmbanggia & dmbanggiact)
    print("\n6. BẢNG GIÁ - DANH MỤC & CHI TIẾT (dmbanggia & dmbanggiact):")
    cur.execute("""
        SELECT b.ma_bang_gia, b.ten_bang_gia, c.ma_vt, c.ma_kh, c.gia, c.ma_nt, c.sl_min
        FROM dmbanggia b
        JOIN dmbanggiact c ON b.ma_bang_gia = c.ma_bang_gia
        LIMIT 3;
    """)
    for r in cur.fetchall():
        print(f"  Bảng giá {r[0]} ({r[1]}): VT {r[2]} | KH: {r[3]} | Giá: {r[4]:,.2f} {r[5]} | Min: {r[6]}")

    # 7. HỒ SƠ KHUÔN (dmhosokhuon)
    print("\n7. HỒ SƠ KHUÔN - QUẢN LÝ TÀI SẢN KHUÔN (dmhosokhuon):")
    cur.execute("""
        SELECT ma_khuon, ten_khuon, so_cavity, so_shot_bh, ngay_bh
        FROM dmhosokhuon
        ORDER BY ma_khuon
        LIMIT 3;
    """)
    for r in cur.fetchall():
        print(f"  Khuôn: {r[0]} | Tên: {r[1]} | Cavity: {r[2]} | Shot bảo hiểm/tuổi thọ: {r[3]:,.0f} | Ngày BH: {r[4]}")

    # 8. DANH MỤC TRẠNG THÁI (sys_dmtt)
    print("\n8. GIẢI MÃ TRẠNG THÁI CHỨNG TỪ (sys_dmtt):")
    cur.execute("""
        SELECT ma_ct, status, statusname
        FROM sys_dmtt
        WHERE ma_ct IN ('SO1', 'PO1', 'HDA', 'PXK', 'PNK', 'PXD')
        ORDER BY ma_ct, status;
    """)
    for r in cur.fetchall():
        print(f"  [{r[0]}] Status '{r[1]}': {r[2]}")

    conn.close()

if __name__ == '__main__':
    main()
