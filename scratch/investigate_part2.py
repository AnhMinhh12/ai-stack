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
    # Q3 Deep Check: Lot xuất giao
    # ----------------------------------------------------
    print_section("CÂU 3: Kiểm tra ma_lo trong ct81 và ct70 xuất")
    # Check if ct81 has non-empty ma_lo
    ct81_lo = query("""
        SELECT h.so_ct, h.ngay_ct, d.ma_vt, d.so_luong, d.ma_lo
        FROM ph81 h JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND d.ma_lo IS NOT NULL AND d.ma_lo != ''
          AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct DESC LIMIT 5
    """)
    print("ct81 non-empty ma_lo:", ct81_lo)

    # Check ct70 for export
    try:
        ct70_lo = query("""
            SELECT ngay_ct, so_ct, ma_ct, sl_xuat, ma_kho
            FROM ct70
            WHERE ma_vt = 'QC7-5146-000' AND sl_xuat > 0 AND ngay_ct <= '2026-10-20'
            ORDER BY ngay_ct DESC, so_ct DESC LIMIT 10
        """)
        print("ct70 export (up to 20/10/2026):", json.dumps(ct70_lo, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("ct70 error:", e)

    # Also check MES carton / tem for export
    mes_tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND (table_name LIKE '%%xuat%%' OR table_name LIKE '%%ship%%' OR table_name LIKE '%%giao%%')
    """)
    print("Export / shipment tables:", [t['table_name'] for t in mes_tables])

    # ----------------------------------------------------
    # Q6: Nhập kho (01/10/2026 - 20/10/2026)
    # ----------------------------------------------------
    print_section("CÂU 6: Nhập kho QC7-5146-000 (01/10/2026 - 20/10/2026)")
    # Get user table name
    user_tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND table_name LIKE '%%user%%'
    """)
    print("User tables:", [u['table_name'] for u in user_tables])
    
    # Check ct74
    q6_ph74 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_ct, h.user_id0, h.user_id2,
               d.ma_vt, d.so_luong, d.ma_kho, k1.ten_kho as ten_kho_xuat,
               d.ma_khon, k2.ten_kho as ten_kho_nhap, d.ma_lo
        FROM ph74 h
        JOIN ct74 d USING(stt_rec)
        LEFT JOIN dmkho k1 ON d.ma_kho = k1.ma_kho
        LEFT JOIN dmkho k2 ON d.ma_khon = k2.ma_kho
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct ASC, h.so_ct ASC
    """)
    print(f"Tổng số phiếu nhập kho ph74/ct74: {len(q6_ph74)}")
    for r in q6_ph74:
        print(f"Phiếu: {r['so_ct']} ({r['ma_ct']}) | Ngày: {r['ngay_ct']} | SL: {r['so_luong']} | Từ kho: {r['ma_kho']} ({r['ten_kho_xuat']}) -> Sang: {r['ma_khon']} ({r['ten_kho_nhap']}) | User0: {r['user_id0']} | Lot: {r['ma_lo']}")

    # Check user table content for user_id0
    u_ids = list(set(r['user_id0'] for r in q6_ph74 if r['user_id0'] is not None))
    if u_ids:
        # Find which table has user_id
        for ut in ['userinfo', 'sysuserinfo', 'sys_users', 'users']:
            try:
                us = query(f"SELECT * FROM {ut} WHERE user_id IN ({','.join(str(x) for x in u_ids)})")
                print(f"Found in {ut}:", json.dumps(us, ensure_ascii=False, indent=2, default=str))
            except Exception:
                pass

    # ----------------------------------------------------
    # Q7: DO và FCST
    # ----------------------------------------------------
    print_section("CÂU 7: DO và FCST của QC7-5146-000")
    # Check ph96/ct96
    try:
        q7_do = query("""
            SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, h.status
            FROM ph96 h JOIN ct96 d USING(stt_rec)
            WHERE d.ma_vt = 'QC7-5146-000'
            ORDER BY h.ngay_ct DESC LIMIT 5
        """)
        print("DO (ph96/ct96):", json.dumps(q7_do, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("DO error:", e)

    # Check FCST tables
    fcst_tbs = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND (table_name LIKE '%%fcst%%' OR table_name LIKE '%%forecast%%')
    """)
    print("FCST tables:", [t['table_name'] for t in fcst_tbs])
    for tb in [t['table_name'] for t in fcst_tbs]:
        try:
            r = query(f"SELECT * FROM {tb} WHERE ma_vt = 'QC7-5146-000' LIMIT 5")
            if r:
                print(f"Data in {tb}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception as e:
            pass

    # ----------------------------------------------------
    # Q8: Quy cách đóng gói & Quy đổi tồn kho
    # ----------------------------------------------------
    print_section("CÂU 8: Quy cách đóng gói & Quy đổi tồn kho QC7-5146-000")
    vt_pkg = query("""
        SELECT ma_vt, ten_vt, packs0, ma_thung, ma_khay, so_luong_vt_khay,
               ma_vt_c1, sl_sp_ma_vt_c1, sl_ma_vt_c1_thung, han_su_dung, weight, weight_runner
        FROM dmvt WHERE ma_vt = 'QC7-5146-000'
    """)
    print("Quy cách đóng gói trong dmvt:", json.dumps(vt_pkg, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q9: Khuôn K_QC5-2919-000-V1 & Shot khuôn & Demand KH0015
    # ----------------------------------------------------
    print_section("CÂU 9: Khuôn K_QC5-2919-000-V1 & Demand KH0015")
    khuon = query("""
        SELECT * FROM dmhosokhuon WHERE ma_khuon ILIKE '%%QC5-2919%%'
    """)
    print("dmhosokhuon:", json.dumps(khuon, ensure_ascii=False, indent=2, default=str))

    # Check shot in MES
    for tb in ['tb_khuon_can_bao_duong', 'tb_dong_thung_in_tem']:
        try:
            r = query(f"SELECT * FROM {tb} WHERE ma_khuon ILIKE '%%QC5-2919%%' LIMIT 5")
            print(f"Sample from {tb}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception as e:
            pass

    # ----------------------------------------------------
    # Q10: Doanh thu KH0015 (01/09 - 20/09 vs 01/10 - 20/10/2026)
    # ----------------------------------------------------
    print_section("CÂU 10: So sánh doanh thu KH0015 (Tháng 9 vs Tháng 10)")
    q10_sep = query("""
        SELECT h.ma_nt, COUNT(DISTINCT h.so_ct) as so_phieu,
               SUM(d.so_luong) as tong_sl,
               SUM(d.tien2) as tong_tien_vnd,
               SUM(d.tien_nt2) as tong_tien_nt
        FROM ph81 h JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ma_kh = 'KH0015'
          AND h.ngay_ct >= '2026-09-01' AND h.ngay_ct <= '2026-09-20'
        GROUP BY h.ma_nt
    """)
    q10_oct = query("""
        SELECT h.ma_nt, COUNT(DISTINCT h.so_ct) as so_phieu,
               SUM(d.so_luong) as tong_sl,
               SUM(d.tien2) as tong_tien_vnd,
               SUM(d.tien_nt2) as tong_tien_nt
        FROM ph81 h JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ma_kh = 'KH0015'
          AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        GROUP BY h.ma_nt
    """)
    print("Tháng 9 (01/09/2026 - 20/09/2026):", json.dumps(q10_sep, ensure_ascii=False, indent=2, default=str))
    print("Tháng 10 (01/10/2026 - 20/10/2026):", json.dumps(q10_oct, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q11: Tồn kho theo khuôn của QC7-5146-000
    # ----------------------------------------------------
    print_section("CÂU 11: Tồn kho theo khuôn của QC7-5146-000")
    # Check carton log or intem
    for tb in ['tb_dong_thung_in_tem', 'intem_carton_log', 'intem_log']:
        try:
            r = query(f"""
                SELECT ma_khuon, COUNT(*) as so_luong_tem, SUM(so_luong) as tong_sl
                FROM {tb} WHERE ma_vt = 'QC7-5146-000'
                GROUP BY ma_khuon
            """)
            print(f"Tồn/sản lượng theo khuôn trong {tb}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception as e:
            pass

    # ----------------------------------------------------
    # Q12: Đơn hàng bán của KH0015 (01/10/2026 - 20/10/2026)
    # ----------------------------------------------------
    print_section("CÂU 12: Đơn hàng bán KH0015 (01/10/2026 - 20/10/2026)")
    q12 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.so_po, d.ma_vt, d.so_luong, d.gia2, d.tien2, h.status,
               t.statusname
        FROM ph64 h
        JOIN ct64 d USING(stt_rec)
        LEFT JOIN sys_dmtt t ON t.ma_ct = 'SO1' AND t.status = h.status
        WHERE h.ma_kh = 'KH0015' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct ASC, h.so_ct ASC
    """)
    print(f"Tổng số dòng chi tiết đơn hàng: {len(q12)}")
    for r in q12:
        print(f"Số đơn: {r['so_ct']} | Ngày đặt: {r['ngay_ct']} | PO: {r['so_po']} | Mã hàng: {r['ma_vt']} | SL: {r['so_luong']} | Trạng thái: {r['status']} ({r['statusname']})")

    # ----------------------------------------------------
    # Q13: Lệnh giao hàng 001-2610-001811
    # ----------------------------------------------------
    print_section("CÂU 13: Lệnh giao hàng 001-2610-001811")
    for tb in ['ph96', 'ph81', 'ph64', 'ct96', 'ct81']:
        try:
            r = query(f"SELECT * FROM {tb} WHERE so_ct = '001-2610-001811'")
            if r:
                print(f"Found in {tb}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception as e:
            pass

    # ----------------------------------------------------
    # Q14: Tồn kho hiện tại QC7-5146-000 ở từng kho
    # ----------------------------------------------------
    print_section("CÂU 14: Tồn kho hiện tại theo từng kho")
    q14 = query("""
        SELECT c.ma_kho, k.ten_kho, c.ton_dau, c.sl_nhap, c.sl_xuat, c.ton_cuoi
        FROM cdvt c
        LEFT JOIN dmkho k ON c.ma_kho = k.ma_kho
        WHERE c.ma_vt = 'QC7-5146-000'
    """)
    print("cdvt:", json.dumps(q14, ensure_ascii=False, indent=2, default=str))
    
    # ----------------------------------------------------
    # Q15: Lot thành phẩm QC cần chú ý
    # ----------------------------------------------------
    print_section("CÂU 15: Lot thành phẩm QC cần chú ý")
    try:
        q15 = query("""
            SELECT ma_lo, status_qc, ngay_sx, ca_sx, so_luong, date0
            FROM intem_log
            WHERE ma_vt = 'QC7-5146-000'
            ORDER BY date0 DESC LIMIT 20
        """)
        print("intem_log recent:", json.dumps(q15[:10], ensure_ascii=False, indent=2, default=str))
        q15_abnormal = query("""
            SELECT status_qc, COUNT(*) as c, SUM(so_luong) as tong_sl
            FROM intem_log
            WHERE ma_vt = 'QC7-5146-000'
            GROUP BY status_qc
        """)
        print("Phân bố status_qc:", json.dumps(q15_abnormal, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("intem_log error:", e)

    # ----------------------------------------------------
    # Q16: Đơn hàng KH0015 (01/10 - 20/10/2026) chưa có giá chuẩn
    # ----------------------------------------------------
    print_section("CÂU 16: Đơn hàng KH0015 chưa có giá chuẩn")
    q16 = query("""
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
    print("Danh sách đối soát giá:", json.dumps(q16, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q18: Giao bù NG vs giao bù hàng thiếu (01/10 - 20/10/2026)
    # ----------------------------------------------------
    print_section("CÂU 18: Giao bù NG vs Nhận hàng trả lại")
    q18_tra = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai
        FROM ph82 h JOIN ct82 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
    """)
    print("Hàng bán trả lại ph82/ct82:", q18_tra)

    q18_xuat = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai, h.ma_gd
        FROM ph81 h JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
          AND (h.dien_giai ILIKE '%%bù%%' OR d.dien_giai ILIKE '%%bù%%' OR h.dien_giai ILIKE '%%ng%%' OR d.dien_giai ILIKE '%%ng%%')
    """)
    print("Xuất giao bù ph81/ct81:", q18_xuat)

if __name__ == '__main__':
    main()
