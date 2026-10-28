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
    # Q3: Lot gần nhất xuất giao tính đến 20/10/2026
    # ----------------------------------------------------
    print_sec(3, "Lot gần nhất xuất giao tính đến 20/10/2026")
    # Check if there is any export lot in ct81 or other tables
    q3_81 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.ma_lo, d.so_po
        FROM ph81 h JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC
        LIMIT 5
    """)
    print("Phiếu xuất bán gần nhất (HDA):", json.dumps(q3_81, ensure_ascii=False, indent=2, default=str))

    # Check intem_carton_log or tb_dong_thung_in_tem or packing for shipped lots
    # Let's inspect columns of intem_carton_log
    cols_carton = query("SELECT column_name FROM information_schema.columns WHERE table_name = 'intem_carton_log'")
    print("Cols intem_carton_log:", [c['column_name'] for c in cols_carton if 'lo' in c['column_name'] or 'xuat' in c['column_name'] or 'ship' in c['column_name']])

    # ----------------------------------------------------
    # Q6: Nhập kho (01/10/2026 - 20/10/2026)
    # ----------------------------------------------------
    print_sec(6, "Nhập kho QC7-5146-000 (01/10/2026 - 20/10/2026)")
    # Inspect ct70 columns
    cols_ct70 = query("SELECT column_name FROM information_schema.columns WHERE table_name = 'ct70'")
    print("Cols ct70:", [c['column_name'] for c in cols_ct70])

    q6_ct70 = query("""
        SELECT c.ngay_ct, c.so_ct, c.ma_ct, c.sl_nhap, c.ma_kho, k.ten_kho, c.user_id0, u.user_name, u.ten
        FROM ct70 c
        LEFT JOIN dmkho k ON c.ma_kho = k.ma_kho
        LEFT JOIN userinfo u ON c.user_id0 = u.user_id
        WHERE c.ma_vt = 'QC7-5146-000' AND c.ngay_ct >= '2026-10-01' AND c.ngay_ct <= '2026-10-20' AND c.sl_nhap > 0
        ORDER BY c.ngay_ct ASC, c.so_ct ASC
    """)
    print(f"Tổng số phiếu nhập kho trong ct70: {len(q6_ct70)}")
    for r in q6_ct70:
        print(f"Ngày: {r['ngay_ct']} | Số CT: {r['so_ct']} ({r['ma_ct']}) | SL: {r['sl_nhap']} | Kho: {r['ma_kho']} ({r['ten_kho']}) | Tài khoản: {r['user_name']} ({r['ten']})")

    # Also check ph74/ct74 (Phiếu nhập từ SX)
    q6_ph74 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_ct, h.dien_giai, h.user_id0, u.user_name, u.ten,
               d.so_luong, d.ma_kho, k.ten_kho
        FROM ph74 h
        JOIN ct74 d USING(stt_rec)
        LEFT JOIN dmkho k ON d.ma_kho = k.ma_kho
        LEFT JOIN userinfo u ON h.user_id0 = u.user_id
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct ASC, h.so_ct ASC
    """)
    print(f"Tổng số phiếu ph74: {len(q6_ph74)}")
    for r in q6_ph74:
        print(f"ph74: {r['so_ct']} ({r['ma_ct']}) | Ngày: {r['ngay_ct']} | SL: {r['so_luong']} | Kho: {r['ma_kho']} ({r['ten_kho']}) | Diễn giải: {r['dien_giai']} | User: {r['user_name']} ({r['ten']})")

    # ----------------------------------------------------
    # Q7: So sánh DO và FCST
    # ----------------------------------------------------
    print_sec(7, "DO và FCST của QC7-5146-000")
    # Check DO in ph96/ct96
    cols_ct96 = query("SELECT column_name FROM information_schema.columns WHERE table_name = 'ct96'")
    print("Cols ct96:", [c['column_name'] for c in cols_ct96])
    cols_ph96 = query("SELECT column_name FROM information_schema.columns WHERE table_name = 'ph96'")
    print("Cols ph96:", [c['column_name'] for c in cols_ph96 if 'so' in c['column_name'] or 'status' in c['column_name'] or 'ver' in c['column_name']])

    r_do_list = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.so_luong, h.status, h.ngay_gh, h.date0, h.date2
        FROM ph96 h JOIN ct96 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000'
        ORDER BY h.ngay_ct DESC, h.so_ct DESC
        LIMIT 10
    """)
    print("DO gần đây của QC7-5146-000:", json.dumps(r_do_list, ensure_ascii=False, indent=2, default=str))

    # Check FCST
    fcst_tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND (table_name LIKE '%%fcst%%' OR table_name LIKE '%%forecast%%')
    """)
    for tb in [t['table_name'] for t in fcst_tables]:
        cnt = query(f"SELECT COUNT(*) as c FROM {tb}")
        print(f"Table {tb}: {cnt[0]['c']} rows")
        if cnt[0]['c'] > 0:
            sample = query(f"SELECT * FROM {tb} LIMIT 2")
            print(f"  Cols {tb}:", list(sample[0].keys()))
            # Search QC7-5146-000
            for col in sample[0].keys():
                if 'vt' in col or 'sp' in col or 'item' in col:
                    try:
                        f_res = query(f"SELECT * FROM {tb} WHERE {col} = 'QC7-5146-000' LIMIT 5")
                        if f_res:
                            print(f"  Found in {tb}.{col}:", json.dumps(f_res, ensure_ascii=False, indent=2, default=str))
                    except Exception:
                        pass

    # ----------------------------------------------------
    # Q9: Khuôn K_QC5-2919-000-V1 & Demand KH0015
    # ----------------------------------------------------
    print_sec(9, "Khuôn K_QC5-2919-000-V1")
    cols_khuon = query("SELECT column_name FROM information_schema.columns WHERE table_name = 'dmhosokhuon'")
    print("Cols dmhosokhuon:", [c['column_name'] for c in cols_khuon])
    khuon_data = query("""
        SELECT ma_khuon, ten_khuon, ma_hi, so_cavity, so_shot_bh, so_shot_thuc_te, ngay_bh, status, dien_giai
        FROM dmhosokhuon WHERE ma_khuon ILIKE '%%QC5-2919%%'
    """)
    print("Hồ sơ khuôn dmhosokhuon:", json.dumps(khuon_data, ensure_ascii=False, indent=2, default=str))

    # Check tb_khuon_can_bao_duong
    tb_k = query("SELECT * FROM tb_khuon_can_bao_duong WHERE ma_khuon ILIKE '%%QC5-2919%%'")
    print("tb_khuon_can_bao_duong:", json.dumps(tb_k, ensure_ascii=False, indent=2, default=str))

    # Check demand in SO1 of KH0015
    demand = query("""
        SELECT COUNT(DISTINCT h.so_ct) as so_don, SUM(d.so_luong) as tong_so_luong,
               MIN(h.ngay_ct) as min_date, MAX(h.ngay_ct) as max_date
        FROM ph64 h JOIN ct64 d USING(stt_rec)
        WHERE h.ma_kh = 'KH0015' AND d.ma_vt = 'QC7-5146-000'
    """)
    print("Demand của KH0015 trong ph64/ct64:", demand)

    # ----------------------------------------------------
    # Q11: Tồn kho theo khuôn của QC7-5146-000
    # ----------------------------------------------------
    print_sec(11, "Tồn kho theo khuôn của QC7-5146-000")
    # Check tb_dong_thung_in_tem
    thung_k = query("""
        SELECT ma_khuon, COUNT(*) as so_thung, SUM(so_luong) as tong_so_luong
        FROM tb_dong_thung_in_tem
        WHERE ma_vt = 'QC7-5146-000'
        GROUP BY ma_khuon
    """)
    print("tb_dong_thung_in_tem theo khuôn:", json.dumps(thung_k, ensure_ascii=False, indent=2, default=str))

    # Check intem_carton_log
    try:
        carton_k = query("""
            SELECT ma_khuon, COUNT(*) as so_thung, SUM(so_luong) as tong_so_luong
            FROM intem_carton_log
            WHERE ma_vt = 'QC7-5146-000'
            GROUP BY ma_khuon
        """)
        print("intem_carton_log theo khuôn:", json.dumps(carton_k, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("intem_carton_log err:", e)

    # ----------------------------------------------------
    # Q14: Tồn kho hiện tại QC7-5146-000 ở từng kho
    # ----------------------------------------------------
    print_sec(14, "Tồn kho hiện tại QC7-5146-000 ở từng kho")
    cols_cdvt = query("SELECT column_name FROM information_schema.columns WHERE table_name = 'cdvt'")
    print("Cols cdvt:", [c['column_name'] for c in cols_cdvt])
    cdvt_data = query("""
        SELECT c.ma_kho, k.ten_kho, c.ton00
        FROM cdvt c
        LEFT JOIN dmkho k ON c.ma_kho = k.ma_kho
        WHERE c.ma_vt = 'QC7-5146-000'
    """)
    print("cdvt:", json.dumps(cdvt_data, ensure_ascii=False, indent=2, default=str))

    ct70_ton = query("""
        SELECT c.ma_kho, k.ten_kho, SUM(c.sl_nhap) - SUM(c.sl_xuat) as ton_luy_ke
        FROM ct70 c
        LEFT JOIN dmkho k ON c.ma_kho = k.ma_kho
        WHERE c.ma_vt = 'QC7-5146-000'
        GROUP BY c.ma_kho, k.ten_kho
    """)
    print("ct70 lũy kế:", json.dumps(ct70_ton, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q15: Lot thành phẩm ở trạng thái QC cần chú ý
    # ----------------------------------------------------
    print_sec(15, "Lot thành phẩm QC cần chú ý")
    cols_intem = query("SELECT column_name FROM information_schema.columns WHERE table_name = 'intem_log'")
    print("Cols intem_log:", [c['column_name'] for c in cols_intem if 'qc' in c['column_name'] or 'status' in c['column_name'] or 'lo' in c['column_name'] or 'sl' in c['column_name']])
    qc_dist = query("""
        SELECT status_qc, COUNT(*) as so_tem
        FROM intem_log
        WHERE ma_vt = 'QC7-5146-000'
        GROUP BY status_qc
    """)
    print("Phân bố status_qc:", json.dumps(qc_dist, ensure_ascii=False, indent=2, default=str))

    qc_abnormal = query("""
        SELECT ma_lo, status_qc, ngay_sx, ca_sx, date0
        FROM intem_log
        WHERE ma_vt = 'QC7-5146-000' AND status_qc NOT IN ('OK', '1', '')
        ORDER BY date0 DESC LIMIT 10
    """)
    print("Lot bất thường:", json.dumps(qc_abnormal, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q16: Đơn hàng KH0015 chưa có giá chuẩn
    # ----------------------------------------------------
    print_sec(16, "Đơn hàng KH0015 chưa có giá chuẩn")
    q16_no_price = query("""
        WITH so_items AS (
            SELECT DISTINCT d.ma_vt, v.ten_vt, d.gia2, h.so_ct, h.ngay_ct
            FROM ph64 h
            JOIN ct64 d USING(stt_rec)
            LEFT JOIN dmvt v ON d.ma_vt = v.ma_vt
            WHERE h.ma_kh = 'KH0015' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        )
        SELECT s.so_ct, s.ngay_ct, s.ma_vt, s.ten_vt, s.gia2, bg.gia as gia_bg
        FROM so_items s
        LEFT JOIN dmbanggiact bg ON s.ma_vt = bg.ma_vt AND bg.ma_kh = 'KH0015'
        WHERE bg.gia IS NULL OR s.gia2 = 0
        ORDER BY s.ma_vt
    """)
    print(f"Số mặt hàng trong SO1 chưa có giá chuẩn / giá = 0: {len(q16_no_price)}")
    for r in q16_no_price[:20]:
        print(f"Đơn: {r['so_ct']} | Ngày: {r['ngay_ct']} | Mã VT: {r['ma_vt']} | Tên: {r['ten_vt']} | Giá SO: {r['gia2']} | Giá chuẩn BG: {r['gia_bg']}")

    # ----------------------------------------------------
    # Q18: Giao bù NG vs giao bù hàng thiếu (01/10/2026 - 20/10/2026)
    # ----------------------------------------------------
    print_sec(18, "Giao bù NG vs giao bù hàng thiếu (01/10 - 20/10/2026)")
    # Check ph82/ct82 (Hàng bán trả lại)
    r_tra = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai
        FROM ph82 h JOIN ct82 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
    """)
    print("Hàng bán trả lại ph82/ct82:", r_tra)

    # Check all ph81 with reason / dien_giai or ma_gd
    r_bu = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai, h.ma_gd
        FROM ph81 h JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
          AND (h.dien_giai ILIKE '%%bù%%' OR d.dien_giai ILIKE '%%bù%%' OR h.dien_giai ILIKE '%%ng%%' OR d.dien_giai ILIKE '%%ng%%' OR h.ma_gd != 1)
    """)
    print("Xuất giao bù trong ph81/ct81:", r_bu)

if __name__ == '__main__':
    main()
