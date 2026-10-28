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
    # -------------------------------------------------------------------------
    # Q2: MOQ & Bảng giá
    # -------------------------------------------------------------------------
    print_section("CÂU 2: Bảng giá chi tiết của QC7-5146-000")
    banggia = query("""
        SELECT c.ma_bang_gia, c.ma_vt, c.ma_kh, c.sl_min, c.gia, c.gia_nt, c.ma_nt,
               c.ngay_bd, c.ngay_kt, c.stt_rec_from_sq1
        FROM dmbanggiact c
        WHERE c.ma_vt = 'QC7-5146-000'
        ORDER BY c.ngay_bd DESC
    """)
    for bg in banggia:
        print(f"Bảng: {bg['ma_bang_gia']} | KH: {bg['ma_kh']} | sl_min: {bg['sl_min']} | Giá: {bg['gia_nt']} {bg['ma_nt']} | Hiệu lực: {bg['ngay_bd']} -> {bg['ngay_kt']} | Từ SQ1: {bg['stt_rec_from_sq1']}")

    # -------------------------------------------------------------------------
    # Q3: Lot gần nhất xuất giao tính đến 20/10/2026
    # -------------------------------------------------------------------------
    print_section("CÂU 3: Xuất giao HDA tính đến 20/10/2026")
    q3 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.ma_lo, d.so_po, d.gia2, d.tien2
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC
        LIMIT 5
    """)
    for r in q3:
        print(f"Số CT: {r['so_ct']} | Ngày: {r['ngay_ct']} | KH: {r['ma_kh']} | SL: {r['so_luong']} | Lot: '{r['ma_lo']}' | PO: {r['so_po']} | Giá: {r['gia2']}")

    # -------------------------------------------------------------------------
    # Q4: Từ 01/10/2026 đến hết 20/10/2026: Tổng SL xuất bán & Doanh thu
    # -------------------------------------------------------------------------
    print_section("CÂU 4: Tổng SL xuất bán & Doanh thu (01/10/2026 - 20/10/2026)")
    q4_detail = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.so_luong, d.gia2, d.tien2, h.ma_nt, h.ty_gia
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct ASC, h.so_ct ASC
    """)
    for r in q4_detail:
        print(f"Phiếu: {r['so_ct']} | Ngày: {r['ngay_ct']} | KH: {r['ma_kh']} | SL: {r['so_luong']} | Đơn giá: {r['gia2']} | Thành tiền: {r['tien2']} {r['ma_nt']}")
    q4_sum = query("""
        SELECT h.ma_nt, COUNT(DISTINCT h.so_ct) as so_phieu, SUM(d.so_luong) as tong_sl, SUM(d.tien2) as tong_tien2
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        GROUP BY h.ma_nt
    """)
    print("Tổng cộng:", q4_sum)

    # -------------------------------------------------------------------------
    # Q6: Nhập kho (01/10/2026 - 20/10/2026)
    # -------------------------------------------------------------------------
    print_section("CÂU 6: Nhập kho QC7-5146-000 (01/10/2026 - 20/10/2026)")
    q6 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_ct, h.user_id0, u.user_name,
               d.ma_vt, d.so_luong, d.ma_kho, k1.ten_kho as ten_kho_xuat,
               d.ma_khon, k2.ten_kho as ten_kho_nhap, d.ma_lo
        FROM ph74 h
        JOIN ct74 d USING(stt_rec)
        LEFT JOIN sys_userinfo u ON h.user_id0 = u.user_id
        LEFT JOIN dmkho k1 ON d.ma_kho = k1.ma_kho
        LEFT JOIN dmkho k2 ON d.ma_khon = k2.ma_kho
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct ASC, h.so_ct ASC
    """)
    for r in q6:
        print(f"Số CT: {r['so_ct']} ({r['ma_ct']}) | Ngày: {r['ngay_ct']} | SL: {r['so_luong']} | Từ kho: {r['ma_kho']} ({r['ten_kho_xuat']}) -> Sang kho: {r['ma_khon']} ({r['ten_kho_nhap']}) | User: {r['user_name']} (ID {r['user_id0']}) | Lot: {r['ma_lo']}")

    # Also check if any other receipt in ct70
    q6_ct70 = query("""
        SELECT ngay_ct, so_ct, ma_ct, sl_nhap, ma_kho, ma_khon, ma_lo, user_id0
        FROM ct70
        WHERE ma_vt = 'QC7-5146-000' AND ngay_ct >= '2026-10-01' AND ngay_ct <= '2026-10-20' AND sl_nhap > 0
        ORDER BY ngay_ct ASC
    """)
    print("Trong ct70 nhập:", len(q6_ct70), "dòng")

    # -------------------------------------------------------------------------
    # Q7: DO & FCST
    # -------------------------------------------------------------------------
    print_section("CÂU 7: DO & FCST của QC7-5146-000")
    # Check tables for DO (ph96/ct96 or others)
    do_tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND (table_name LIKE '%%fcst%%' OR table_name LIKE '%%ph96%%' OR table_name LIKE '%%ct96%%' OR table_name LIKE '%%do%%')
    """)
    print("Tables related to FCST/DO:", [t['table_name'] for t in do_tables])
    for tb in [t['table_name'] for t in do_tables]:
        try:
            cnt = query(f"SELECT COUNT(*) as c FROM {tb} WHERE ma_vt = 'QC7-5146-000'")
            print(f"Table {tb}: {cnt[0]['c']} rows for QC7-5146-000")
            if cnt[0]['c'] > 0:
                sample = query(f"SELECT * FROM {tb} WHERE ma_vt = 'QC7-5146-000' ORDER BY 1 DESC LIMIT 3")
                print(f"  Sample from {tb}:", json.dumps(sample, ensure_ascii=False, indent=2, default=str))
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Q9: Khuôn K_QC5-2919-000-V1 & Demand KH0015
    # -------------------------------------------------------------------------
    print_section("CÂU 9: Khuôn K_QC5-2919-000-V1 & Shot khuôn")
    khuon = query("""
        SELECT * FROM dmhosokhuon WHERE ma_khuon ILIKE '%%QC5-2919%%'
    """)
    print("dmhosokhuon:", json.dumps(khuon, ensure_ascii=False, indent=2, default=str))
    # Check shot in MES / tb_khuon_can_bao_duong / tb_khuon
    mes_khuon = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%%khuon%%'
    """)
    for tb in [t['table_name'] for t in mes_khuon]:
        try:
            r = query(f"SELECT * FROM {tb} WHERE ma_khuon ILIKE '%%QC5-2919%%' LIMIT 5")
            if r:
                print(f"Found in {tb}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Q10: So sánh doanh thu 01/09-20/09/2026 vs 01/10-20/10/2026 của KH0015
    # -------------------------------------------------------------------------
    print_section("CÂU 10: So sánh doanh thu KH0015 (01/09-20/09 vs 01/10-20/10/2026)")
    sep_data = query("""
        SELECT h.ma_nt, COUNT(DISTINCT h.so_ct) as so_phieu, SUM(d.so_luong) as tong_sl, SUM(d.tien2) as tong_tien2
        FROM ph81 h JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ma_kh = 'KH0015'
          AND h.ngay_ct >= '2026-09-01' AND h.ngay_ct <= '2026-09-20'
        GROUP BY h.ma_nt
    """)
    oct_data = query("""
        SELECT h.ma_nt, COUNT(DISTINCT h.so_ct) as so_phieu, SUM(d.so_luong) as tong_sl, SUM(d.tien2) as tong_tien2
        FROM ph81 h JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ma_kh = 'KH0015'
          AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        GROUP BY h.ma_nt
    """)
    print("Kỳ 01/09/2026 - 20/09/2026:", sep_data)
    print("Kỳ 01/10/2026 - 20/10/2026:", oct_data)

    # -------------------------------------------------------------------------
    # Q11: Tồn kho theo khuôn của QC7-5146-000
    # -------------------------------------------------------------------------
    print_section("CÂU 11: Tồn kho theo khuôn của QC7-5146-000")
    # Check MES packing / carton log with mold
    tb_thung = query("""
        SELECT ma_khuon, COUNT(*) as so_thung, SUM(so_luong) as tong_sl
        FROM tb_dong_thung_in_tem
        WHERE ma_vt = 'QC7-5146-000'
        GROUP BY ma_khuon
    """)
    print("tb_dong_thung_in_tem theo khuôn:", tb_thung)

    # -------------------------------------------------------------------------
    # Q12: Đơn hàng bán của KH0015 từ 01/10/2026 đến hết 20/10/2026
    # -------------------------------------------------------------------------
    print_section("CÂU 12: Đơn hàng bán của KH0015 (01/10/2026 - 20/10/2026)")
    q12 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.so_po, d.ma_vt, d.so_luong, d.gia2, d.tien2, h.status,
               t.statusname
        FROM ph64 h
        JOIN ct64 d USING(stt_rec)
        LEFT JOIN sys_dmtt t ON t.ma_ct = 'SO1' AND t.status = h.status
        WHERE h.ma_kh = 'KH0015' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct ASC, h.so_ct ASC
    """)
    print(f"Tổng số dòng SO1: {len(q12)}")
    for r in q12[:15]:
        print(f"Đơn: {r['so_ct']} | Ngày: {r['ngay_ct']} | PO: {r['so_po']} | VT: {r['ma_vt']} | SL: {r['so_luong']} | Trạng thái: {r['status']} ({r['statusname']}) | Giá: {r['gia2']}")

    # -------------------------------------------------------------------------
    # Q13: Lệnh giao hàng 001-2610-001811
    # -------------------------------------------------------------------------
    print_section("CÂU 13: Lệnh giao hàng 001-2610-001811")
    # Check ph96 or any table with so_ct = '001-2610-001811'
    q13_find = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name IN ('ph96', 'ct96', 'ph81', 'ct81', 'ph64', 'ct64')
    """)
    for tb in ['ph96', 'ct96', 'ph81', 'ph64']:
        try:
            r = query(f"SELECT * FROM {tb} WHERE so_ct = '001-2610-001811'")
            if r:
                print(f"Found in {tb}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Q14: Tồn kho hiện tại của QC7-5146-000 ở từng kho
    # -------------------------------------------------------------------------
    print_section("CÂU 14: Tồn kho hiện tại của QC7-5146-000 ở từng kho")
    cdvt = query("""
        SELECT c.ma_kho, k.ten_kho, c.ton_dau, c.sl_nhap, c.sl_xuat, c.ton_cuoi
        FROM cdvt c
        LEFT JOIN dmkho k ON c.ma_kho = k.ma_kho
        WHERE c.ma_vt = 'QC7-5146-000'
    """)
    print("cdvt (tồn tức thời):", json.dumps(cdvt, ensure_ascii=False, indent=2, default=str))

    # Also check latest ct70 balance
    ct70_balance = query("""
        SELECT ma_kho, SUM(sl_nhap) - SUM(sl_xuat) as ton_luy_ke
        FROM ct70
        WHERE ma_vt = 'QC7-5146-000'
        GROUP BY ma_kho
    """)
    print("ct70 tồn lũy kế:", json.dumps(ct70_balance, ensure_ascii=False, indent=2, default=str))

    # -------------------------------------------------------------------------
    # Q15: Lot thành phẩm ở trạng thái QC cần chú ý
    # -------------------------------------------------------------------------
    print_section("CÂU 15: Lot thành phẩm ở trạng thái QC cần chú ý")
    qc_tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%%qc%%'
    """)
    print("QC tables:", [t['table_name'] for t in qc_tables])
    for tb in [t['table_name'] for t in qc_tables]:
        try:
            r = query(f"SELECT * FROM {tb} WHERE ma_vt = 'QC7-5146-000' LIMIT 5")
            if r:
                print(f"Found in {tb}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception:
            pass
    # Check intem_log status_qc
    try:
        intem_qc = query("""
            SELECT status_qc, COUNT(*) as c FROM intem_log WHERE ma_vt = 'QC7-5146-000' GROUP BY status_qc
        """)
        print("intem_log status_qc:", intem_qc)
        intem_qc_detail = query("""
            SELECT ma_lo, status_qc, ngay_sx, ca_sx, so_luong, date0
            FROM intem_log WHERE ma_vt = 'QC7-5146-000' AND status_qc NOT IN ('OK', '1', '') LIMIT 10
        """)
        print("intem_log QC chú ý:", json.dumps(intem_qc_detail, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("intem_log query error:", e)

    # -------------------------------------------------------------------------
    # Q16: Trong đơn hàng KH0015 (01/10 - 20/10/2026), mã hàng nào chưa có giá chuẩn?
    # -------------------------------------------------------------------------
    print_section("CÂU 16: Đơn hàng KH0015 chưa có giá chuẩn")
    q16 = query("""
        SELECT DISTINCT d.ma_vt, v.ten_vt, d.gia2, d.ma_nt
        FROM ph64 h
        JOIN ct64 d USING(stt_rec)
        LEFT JOIN dmvt v ON d.ma_vt = v.ma_vt
        WHERE h.ma_kh = 'KH0015' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
          AND (d.gia2 = 0 OR d.gia2 IS NULL)
    """)
    print("Mã hàng có giá = 0 hoặc NULL trong SO1:", q16)

    # Also compare all items in SO1 of KH0015 against dmbanggiact
    q16_check_bg = query("""
        WITH so_items AS (
            SELECT DISTINCT d.ma_vt, d.gia2 as gia_so, h.ngay_ct
            FROM ph64 h
            JOIN ct64 d USING(stt_rec)
            WHERE h.ma_kh = 'KH0015' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        )
        SELECT s.ma_vt, s.gia_so, bg.gia as gia_bang_gia, bg.ma_bang_gia, bg.ngay_bd, bg.ngay_kt
        FROM so_items s
        LEFT JOIN dmbanggiact bg ON s.ma_vt = bg.ma_vt AND bg.ma_kh = 'KH0015'
    """)
    print("Đối soát đơn giá SO1 với bảng giá:", json.dumps(q16_check_bg[:15], ensure_ascii=False, indent=2, default=str))

    # -------------------------------------------------------------------------
    # Q18: Giao bù NG vs Giao bù thiếu (01/10 - 20/10/2026)
    # -------------------------------------------------------------------------
    print_section("CÂU 18: Giao bù NG & Nhận lại hàng NG")
    # Check ph82/ct82 (Hàng bán trả lại)
    tra_lai = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai
        FROM ph82 h
        JOIN ct82 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
    """)
    print("Hàng trả lại (ph82/ct82):", tra_lai)

    # Check ph81 xuất giao bù
    xuat_bu = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai, h.ma_gd
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
          AND (h.dien_giai ILIKE '%%bù%%' OR d.dien_giai ILIKE '%%bù%%' OR h.dien_giai ILIKE '%%ng%%' OR d.dien_giai ILIKE '%%ng%%')
    """)
    print("Xuất giao bù trong ph81/ct81:", xuat_bu)

if __name__ == '__main__':
    main()
