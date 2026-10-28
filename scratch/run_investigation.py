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

def print_sec(num, title):
    print(f"\n{'='*15} CÂU {num}: {title} {'='*15}")

def main():
    # ----------------------------------------------------
    # Q1: Loại nhựa & Cấu trúc sản phẩm
    # ----------------------------------------------------
    print_sec(1, "Loại nhựa & Cấu trúc sản phẩm của QC7-5146-000")
    try:
        r_bom = query("""
            SELECT ma_sp, ten_sp, ma_vt as ma_nhua, ten_vt as ten_nhua, so_luong_dm, so_luong_cua_sp, so_luong_gate_runner, ty_le_hao_hut, ma_cong_doan
            FROM mfkhsx_bom
            WHERE ma_sp = 'QC7-5146-000'
            LIMIT 1
        """)
        print("mfkhsx_bom:", json.dumps(r_bom, ensure_ascii=False, indent=2, default=str))
        r_pkg = query("""
            SELECT ma_vt, ten_vt, dvt, weight, weight_runner, cavity, die_no,
                   ma_thung, ma_khay, so_luong_vt_khay, packs0, ma_vt_c1, sl_sp_ma_vt_c1, sl_ma_vt_c1_thung
            FROM dmvt WHERE ma_vt = 'QC7-5146-000'
        """)
        print("dmvt cấu trúc bao bì:", json.dumps(r_pkg, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q1:", e)

    # ----------------------------------------------------
    # Q2: MOQ báo giá hiện tại & Giá áp dụng
    # ----------------------------------------------------
    print_sec(2, "MOQ báo giá & Giá áp dụng theo từng mức MOQ")
    try:
        r_bg = query("""
            SELECT c.ma_bang_gia, c.ma_vt, c.ma_kh, c.sl_min, c.gia, c.gia_nt, c.ma_nt,
                   c.ngay_bd, c.ngay_kt, c.stt_rec_from_sq1
            FROM dmbanggiact c
            WHERE c.ma_vt = 'QC7-5146-000'
            ORDER BY c.ngay_bd DESC
        """)
        for b in r_bg:
            print(f"Bảng: {b['ma_bang_gia']} | KH: {b['ma_kh']} | sl_min (MOQ): {b['sl_min']} | Giá: {b['gia_nt']} {b['ma_nt']} | Hiệu lực: {b['ngay_bd']} -> {b['ngay_kt']} | SQ1: {b['stt_rec_from_sq1']}")
    except Exception as e:
        print("Lỗi Q2:", e)

    # ----------------------------------------------------
    # Q3: Lot gần nhất xuất giao tính đến 20/10/2026
    # ----------------------------------------------------
    print_sec(3, "Lot gần nhất xuất giao tính đến 20/10/2026")
    try:
        r_q3 = query("""
            SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.ma_lo, d.so_po, d.gia_nt2, h.ma_nt
            FROM ph81 h JOIN ct81 d USING(stt_rec)
            WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct <= '2026-10-20'
            ORDER BY h.ngay_ct DESC, h.stt_rec DESC
            LIMIT 5
        """)
        for r in r_q3:
            print(f"Số phiếu xuất: {r['so_ct']} | Ngày: {r['ngay_ct']} | KH: {r['ma_kh']} | SL: {r['so_luong']} | Lot trên phiếu: '{r['ma_lo']}' | PO: {r['so_po']}")
        
        # Check if DO (ph96/ct96) has lot
        r_do_lot = query("""
            SELECT h.so_ct, h.ngay_ct, d.ma_vt, d.so_luong, d.ma_lo
            FROM ph96 h JOIN ct96 d USING(stt_rec)
            WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct <= '2026-10-20' AND d.ma_lo != ''
            ORDER BY h.ngay_ct DESC LIMIT 3
        """)
        print("Lot trong ph96/ct96:", r_do_lot)
    except Exception as e:
        print("Lỗi Q3:", e)

    # ----------------------------------------------------
    # Q4: Xuất bán 01/10/2026 - 20/10/2026
    # ----------------------------------------------------
    print_sec(4, "Tổng SL xuất bán & Doanh thu (01/10/2026 - 20/10/2026)")
    try:
        r_q4 = query("""
            SELECT h.ma_nt, COUNT(DISTINCT h.so_ct) as so_phieu,
                   SUM(d.so_luong) as tong_sl,
                   SUM(d.tien2) as tong_tien_vnd,
                   SUM(d.tien_nt2) as tong_tien_nt
            FROM ph81 h JOIN ct81 d USING(stt_rec)
            WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
            GROUP BY h.ma_nt
        """)
        print(json.dumps(r_q4, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q4:", e)

    # ----------------------------------------------------
    # Q5 & Q17: Khách hàng
    # ----------------------------------------------------
    print_sec(5, "Mã hàng QC7-5146-000 thuộc khách hàng nào?")
    try:
        r_kh = query("SELECT ma_vt, ma_kh, nh_vt6 FROM dmvt WHERE ma_vt = 'QC7-5146-000'")
        print("dmvt:", r_kh)
        r_kh_info = query("SELECT ma_kh, ten_kh, dia_chi FROM dmkh WHERE ma_kh = %s", [r_kh[0]['ma_kh']])
        print("dmkh:", json.dumps(r_kh_info, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q5:", e)

    # ----------------------------------------------------
    # Q6: Nhập kho (01/10/2026 - 20/10/2026)
    # ----------------------------------------------------
    print_sec(6, "Nhập kho QC7-5146-000 (01/10/2026 - 20/10/2026)")
    try:
        # Check ct70 receipt transactions
        r_q6_ct70 = query("""
            SELECT c.ngay_ct, c.so_ct, c.ma_ct, c.sl_nhap, c.ma_kho, k.ten_kho, c.ma_khon, kn.ten_kho as ten_kho_nhap, c.user_id0, u.comment as creator
            FROM ct70 c
            LEFT JOIN dmkho k ON c.ma_kho = k.ma_kho
            LEFT JOIN dmkho kn ON c.ma_khon = kn.ma_kho
            LEFT JOIN userinfo u ON c.user_id0 = u.user_id
            WHERE c.ma_vt = 'QC7-5146-000' AND c.ngay_ct >= '2026-10-01' AND c.ngay_ct <= '2026-10-20' AND c.sl_nhap > 0
            ORDER BY c.ngay_ct ASC, c.so_ct ASC
        """)
        print(f"Số phiếu nhập kho trong ct70: {len(r_q6_ct70)}")
        for r in r_q6_ct70:
            print(f"Ngày: {r['ngay_ct']} | Số CT: {r['so_ct']} ({r['ma_ct']}) | SL nhập: {r['sl_nhap']} | Kho: {r['ma_kho']} ({r['ten_kho']}) | Kho nhận: {r['ma_khon']} ({r['ten_kho_nhap']}) | User tạo: {r['creator']} (ID {r['user_id0']})")
        
        # Also check ph74
        r_q6_74 = query("""
            SELECT h.so_ct, h.ngay_ct, h.ma_ct, h.user_id0, u.comment as creator, d.ma_vt, d.so_luong, d.ma_kho, k.ten_kho
            FROM ph74 h
            JOIN ct74 d USING(stt_rec)
            LEFT JOIN dmkho k ON d.ma_kho = k.ma_kho
            LEFT JOIN userinfo u ON h.user_id0 = u.user_id
            WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
            ORDER BY h.ngay_ct ASC
        """)
        print(f"Số phiếu nhập trong ph74/ct74: {len(r_q6_74)}")
        for r in r_q6_74:
            print(f"Phiếu ph74: {r['so_ct']} ({r['ma_ct']}) | Ngày: {r['ngay_ct']} | SL: {r['so_luong']} | Kho: {r['ma_kho']} ({r['ten_kho']}) | User tạo: {r['creator']} (ID {r['user_id0']})")
    except Exception as e:
        print("Lỗi Q6:", e)

    # ----------------------------------------------------
    # Q7: DO và FCST
    # ----------------------------------------------------
    print_sec(7, "So sánh DO và FCST hiện tại với bản trước của QC7-5146-000")
    try:
        # Check ph96/ct96 DO
        r_do = query("""
            SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.so_ct_so1, d.so_luong, h.status
            FROM ph96 h JOIN ct96 d USING(stt_rec)
            WHERE d.ma_vt = 'QC7-5146-000'
            ORDER BY h.ngay_ct DESC LIMIT 5
        """)
        print("DO (ph96/ct96):", json.dumps(r_do, ensure_ascii=False, indent=2, default=str))

        # Check all FCST tables
        fcst_tbs = query("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema='public' AND (table_name LIKE '%%fcst%%' OR table_name LIKE '%%forecast%%')
        """)
        print("Bảng FCST:", [t['table_name'] for t in fcst_tbs])
        for tb in [t['table_name'] for t in fcst_tbs]:
            try:
                cnt = query(f"SELECT COUNT(*) as c FROM {tb} WHERE ma_vt = 'QC7-5146-000'")
                print(f"  {tb}: {cnt[0]['c']} bản ghi")
                if cnt[0]['c'] > 0:
                    sample = query(f"SELECT * FROM {tb} WHERE ma_vt = 'QC7-5146-000' ORDER BY 1 DESC LIMIT 3")
                    print(f"    Sample: {json.dumps(sample, ensure_ascii=False, indent=2, default=str)}")
            except Exception as ex:
                print(f"  Error on {tb}:", ex)
    except Exception as e:
        print("Lỗi Q7:", e)

    # ----------------------------------------------------
    # Q8: Quy cách đóng gói & Quy đổi tồn kho
    # ----------------------------------------------------
    print_sec(8, "Quy cách đóng gói & Quy đổi tồn kho")
    try:
        r_q8 = query("""
            SELECT ma_vt, ten_vt, dvt, packs0, ma_thung, ma_khay, so_luong_vt_khay,
                   ma_vt_c1, sl_sp_ma_vt_c1, sl_ma_vt_c1_thung, han_su_dung
            FROM dmvt WHERE ma_vt = 'QC7-5146-000'
        """)
        print("Quy cách:", json.dumps(r_q8, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q8:", e)

    # ----------------------------------------------------
    # Q9: Khuôn K_QC5-2919-000-V1 & Demand KH0015 & Tuổi thọ
    # ----------------------------------------------------
    print_sec(9, "Khuôn K_QC5-2919-000-V1 & Dự kiến hết tuổi thọ")
    try:
        r_khuon = query("""
            SELECT ma_khuon, ten_khuon, ma_kh, so_cavity, so_shot_bh, so_shot_thuc_te, ngay_bh, status
            FROM dmhosokhuon
            WHERE ma_khuon ILIKE '%%QC5-2919%%'
        """)
        print("Hồ sơ khuôn:", json.dumps(r_khuon, ensure_ascii=False, indent=2, default=str))
        
        # Check demand of KH0015 for QC7-5146-000
        r_demand = query("""
            SELECT COUNT(DISTINCT h.so_ct) as so_don, SUM(d.so_luong) as tong_demand,
                   MIN(h.ngay_ct) as tu_ngay, MAX(h.ngay_ct) as den_ngay
            FROM ph64 h JOIN ct64 d USING(stt_rec)
            WHERE h.ma_kh = 'KH0015' AND d.ma_vt = 'QC7-5146-000'
        """)
        print("Demand SO1 của KH0015:", json.dumps(r_demand, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q9:", e)

    # ----------------------------------------------------
    # Q10: So sánh doanh thu KH0015 (Tháng 9 vs Tháng 10)
    # ----------------------------------------------------
    print_sec(10, "So sánh doanh thu QC7-5146-000 khách KH0015 (01/09-20/09 vs 01/10-20/10)")
    try:
        sep = query("""
            SELECT h.ma_nt, COUNT(DISTINCT h.so_ct) as so_phieu,
                   SUM(d.so_luong) as tong_sl,
                   SUM(d.tien2) as tong_tien_vnd,
                   SUM(d.tien_nt2) as tong_tien_nt
            FROM ph81 h JOIN ct81 d USING(stt_rec)
            WHERE d.ma_vt = 'QC7-5146-000' AND h.ma_kh = 'KH0015'
              AND h.ngay_ct >= '2026-09-01' AND h.ngay_ct <= '2026-09-20'
            GROUP BY h.ma_nt
        """)
        oct_ = query("""
            SELECT h.ma_nt, COUNT(DISTINCT h.so_ct) as so_phieu,
                   SUM(d.so_luong) as tong_sl,
                   SUM(d.tien2) as tong_tien_vnd,
                   SUM(d.tien_nt2) as tong_tien_nt
            FROM ph81 h JOIN ct81 d USING(stt_rec)
            WHERE d.ma_vt = 'QC7-5146-000' AND h.ma_kh = 'KH0015'
              AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
            GROUP BY h.ma_nt
        """)
        print("Kỳ 01/09/2026 - 20/09/2026:", json.dumps(sep, ensure_ascii=False, indent=2, default=str))
        print("Kỳ 01/10/2026 - 20/10/2026:", json.dumps(oct_, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q10:", e)

    # ----------------------------------------------------
    # Q11: Tồn kho theo khuôn của QC7-5146-000
    # ----------------------------------------------------
    print_sec(11, "Tồn kho theo khuôn của QC7-5146-000")
    try:
        r_thung_khuon = query("""
            SELECT ma_khuon, COUNT(*) as so_thung, SUM(so_luong) as tong_sl
            FROM tb_dong_thung_in_tem
            WHERE ma_vt = 'QC7-5146-000'
            GROUP BY ma_khuon
        """)
        print("tb_dong_thung_in_tem theo khuôn:", json.dumps(r_thung_khuon, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q11:", e)

    # ----------------------------------------------------
    # Q12: Đơn hàng bán KH0015 (01/10/2026 - 20/10/2026)
    # ----------------------------------------------------
    print_sec(12, "Đơn hàng bán KH0015 (01/10/2026 - 20/10/2026)")
    try:
        r_so = query("""
            SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.so_po, d.ma_vt, d.so_luong, d.gia2, d.tien2, h.status,
                   t.statusname
            FROM ph64 h
            JOIN ct64 d USING(stt_rec)
            LEFT JOIN sys_dmtt t ON t.ma_ct = 'SO1' AND t.status = h.status
            WHERE h.ma_kh = 'KH0015' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
            ORDER BY h.ngay_ct ASC, h.so_ct ASC
        """)
        print(f"Tổng số dòng chi tiết SO1: {len(r_so)}")
        for r in r_so:
            print(f"Số đơn: {r['so_ct']} | Ngày đặt: {r['ngay_ct']} | PO: {r['so_po']} | Mã hàng: {r['ma_vt']} | SL: {r['so_luong']} | Trạng thái: {r['status']} ({r['statusname']}) | Giá: {r['gia2']}")
    except Exception as e:
        print("Lỗi Q12:", e)

    # ----------------------------------------------------
    # Q13: Lệnh giao hàng 001-2610-001811
    # ----------------------------------------------------
    print_sec(13, "Lệnh giao hàng 001-2610-001811")
    try:
        # Search in ph96
        r_do13 = query("SELECT * FROM ph96 WHERE so_ct = '001-2610-001811'")
        if r_do13:
            print("ph96:", json.dumps(r_do13, ensure_ascii=False, indent=2, default=str))
        # Search in ph81
        r_hda13 = query("SELECT * FROM ph81 WHERE so_ct = '001-2610-001811'")
        if r_hda13:
            print("ph81:", json.dumps(r_hda13, ensure_ascii=False, indent=2, default=str))
        # Search in ph64
        r_so13 = query("SELECT * FROM ph64 WHERE so_ct = '001-2610-001811'")
        if r_so13:
            print("ph64:", json.dumps(r_so13, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q13:", e)

    # ----------------------------------------------------
    # Q14: Tồn kho hiện tại QC7-5146-000 ở từng kho
    # ----------------------------------------------------
    print_sec(14, "Tồn kho hiện tại của QC7-5146-000 ở từng kho")
    try:
        r_cdvt = query("""
            SELECT c.ma_kho, k.ten_kho, c.ton_dau, c.sl_nhap, c.sl_xuat, c.ton_cuoi
            FROM cdvt c
            LEFT JOIN dmkho k ON c.ma_kho = k.ma_kho
            WHERE c.ma_vt = 'QC7-5146-000'
        """)
        print("cdvt:", json.dumps(r_cdvt, ensure_ascii=False, indent=2, default=str))
        r_ct70_sum = query("""
            SELECT c.ma_kho, k.ten_kho, SUM(c.sl_nhap) - SUM(c.sl_xuat) as ton_luy_ke
            FROM ct70 c
            LEFT JOIN dmkho k ON c.ma_kho = k.ma_kho
            WHERE c.ma_vt = 'QC7-5146-000'
            GROUP BY c.ma_kho, k.ten_kho
        """)
        print("ct70 tồn lũy kế:", json.dumps(r_ct70_sum, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q14:", e)

    # ----------------------------------------------------
    # Q15: Lot thành phẩm ở trạng thái QC cần chú ý
    # ----------------------------------------------------
    print_sec(15, "Lot thành phẩm ở trạng thái QC cần chú ý")
    try:
        r_qc_dist = query("""
            SELECT status_qc, COUNT(*) as so_luong_tem, SUM(so_luong) as tong_so_luong
            FROM intem_log
            WHERE ma_vt = 'QC7-5146-000'
            GROUP BY status_qc
        """)
        print("Phân bố status_qc trong intem_log:", json.dumps(r_qc_dist, ensure_ascii=False, indent=2, default=str))
        r_qc_attn = query("""
            SELECT ma_lo, status_qc, ngay_sx, ca_sx, so_luong, date0
            FROM intem_log
            WHERE ma_vt = 'QC7-5146-000' AND status_qc NOT IN ('OK', '1', '')
            ORDER BY date0 DESC LIMIT 10
        """)
        print("Lot QC cần chú ý:", json.dumps(r_qc_attn, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q15:", e)

    # ----------------------------------------------------
    # Q16: Đơn hàng KH0015 (01/10 - 20/10/2026) chưa có giá chuẩn
    # ----------------------------------------------------
    print_sec(16, "Đơn hàng KH0015 chưa có giá chuẩn được liên kết")
    try:
        r_q16 = query("""
            WITH so_items AS (
                SELECT DISTINCT d.ma_vt, v.ten_vt, d.gia2 as gia_so, h.so_ct, h.ngay_ct
                FROM ph64 h
                JOIN ct64 d USING(stt_rec)
                LEFT JOIN dmvt v ON d.ma_vt = v.ma_vt
                WHERE h.ma_kh = 'KH0015' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
            )
            SELECT s.so_ct, s.ngay_ct, s.ma_vt, s.ten_vt, s.gia_so,
                   bg.gia as gia_bang_gia, bg.ma_bang_gia
            FROM so_items s
            LEFT JOIN dmbanggiact bg ON s.ma_vt = bg.ma_vt AND bg.ma_kh = 'KH0015'
            ORDER BY s.ma_vt ASC
        """)
        print(f"Tổng số đối soát: {len(r_q16)}")
        for r in r_q16:
            print(f"Đơn: {r['so_ct']} | Mã VT: {r['ma_vt']} | Tên: {r['ten_vt']} | Giá SO: {r['gia_so']} | Bảng giá: {r['gia_bang_gia']} ({r['ma_bang_gia']})")
    except Exception as e:
        print("Lỗi Q16:", e)

    # ----------------------------------------------------
    # Q17: Mã KH của Canon Thăng Long
    # ----------------------------------------------------
    print_sec(17, "Mã khách hàng Canon Thăng Long")
    try:
        r_q17 = query("SELECT ma_kh, ten_kh, dia_chi FROM dmkh WHERE ten_kh ILIKE '%%Canon%%Thăng Long%%'")
        print(json.dumps(r_q17, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Lỗi Q17:", e)

    # ----------------------------------------------------
    # Q18: Giao bù NG vs Giao bù thiếu (01/10 - 20/10/2026)
    # ----------------------------------------------------
    print_sec(18, "Giao bù NG vs Giao bù thiếu (01/10/2026 - 20/10/2026)")
    try:
        r_tra = query("""
            SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai
            FROM ph82 h JOIN ct82 d USING(stt_rec)
            WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        """)
        print("Hàng bán trả lại ph82/ct82:", r_tra)
        r_bu = query("""
            SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai, h.ma_gd
            FROM ph81 h JOIN ct81 d USING(stt_rec)
            WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
              AND (h.dien_giai ILIKE '%%bù%%' OR d.dien_giai ILIKE '%%bù%%' OR h.dien_giai ILIKE '%%ng%%' OR d.dien_giai ILIKE '%%ng%%')
        """)
        print("Xuất giao bù trong ph81/ct81:", r_bu)
    except Exception as e:
        print("Lỗi Q18:", e)

if __name__ == '__main__':
    main()
