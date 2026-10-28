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
    # Q7 Part 2: FCST
    # ----------------------------------------------------
    print_sec(7, "Chi tiết FCST của QC7-5146-000")
    fcst_tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND (table_name LIKE '%%fcst%%' OR table_name LIKE '%%forecast%%')
    """)
    for t in [tb['table_name'] for tb in fcst_tables]:
        try:
            r = query(f"SELECT * FROM {t} WHERE ma_vt = 'QC7-5146-000' OR ma_sp = 'QC7-5146-000' LIMIT 5")
            if r:
                print(f"Data in {t}:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
            else:
                print(f"Table {t} has 0 rows for QC7-5146-000")
        except Exception as e:
            print(f"Error {t}:", e)

    # ----------------------------------------------------
    # Q9: Khuôn K_QC5-2919-000-V1
    # ----------------------------------------------------
    print_sec(9, "Khuôn K_QC5-2919-000-V1 & Demand KH0015")
    khuon = query("""
        SELECT ma_khuon, ten_khuon, ma_hi, so_cavity, so_shot_bh, tong_so_shot, so_shot_baotri,
               ngay_bh, so_shot_sau_bd, ngay_bd_gan_nhat, status
        FROM dmhosokhuon WHERE ma_khuon ILIKE '%%QC5-2919%%'
    """)
    print("dmhosokhuon:", json.dumps(khuon, ensure_ascii=False, indent=2, default=str))

    # Also check shot in MES for this mold and product
    try:
        shot_mes = query("""
            SELECT ma_khuon, ma_sp, SUM(so_shot) as tong_shot_mes
            FROM mes_oi_bo_shot
            WHERE ma_khuon ILIKE '%%QC5-2919%%'
            GROUP BY ma_khuon, ma_sp
        """)
        print("mes_oi_bo_shot:", json.dumps(shot_mes, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("mes_oi_bo_shot err:", e)

    # Demand of KH0015
    demand = query("""
        SELECT COUNT(DISTINCT h.so_ct) as so_don, SUM(d.so_luong) as tong_so_luong,
               MIN(h.ngay_ct) as tu_ngay, MAX(h.ngay_ct) as den_ngay
        FROM ph64 h JOIN ct64 d USING(stt_rec)
        WHERE h.ma_kh = 'KH0015' AND d.ma_vt = 'QC7-5146-000'
    """)
    print("Tổng demand đơn hàng SO1 của KH0015:", json.dumps(demand, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q11: Tồn kho theo khuôn của QC7-5146-000
    # ----------------------------------------------------
    print_sec(11, "Tồn kho theo khuôn của QC7-5146-000")
    for tb in ['intem_log', 'intem_carton_log', 'mes_oi_dong_thung']:
        try:
            r = query(f"SELECT ma_khuon, COUNT(*) as so_tem FROM {tb} WHERE ma_vt = 'QC7-5146-000' GROUP BY ma_khuon")
            print(f"{tb} theo khuôn:", json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception as e:
            print(f"{tb} err:", e)

    # ----------------------------------------------------
    # Q14: Tồn kho hiện tại QC7-5146-000 ở từng kho
    # ----------------------------------------------------
    print_sec(14, "Tồn kho hiện tại QC7-5146-000 ở từng kho")
    # Tồn đầu năm cdvt + nhập - xuất trong ct70
    ton_kho = query("""
        WITH dau_nam AS (
            SELECT ma_kho, SUM(ton00) as ton_dau
            FROM cdvt
            WHERE ma_vt = 'QC7-5146-000'
            GROUP BY ma_kho
        ),
        ps_kho AS (
            SELECT ma_kho, SUM(sl_nhap) as tong_nhap, SUM(sl_xuat) as tong_xuat
            FROM ct70
            WHERE ma_vt = 'QC7-5146-000'
            GROUP BY ma_kho
        )
        SELECT COALESCE(d.ma_kho, p.ma_kho) as ma_kho,
               k.ten_kho,
               COALESCE(d.ton_dau, 0) as ton_dau,
               COALESCE(p.tong_nhap, 0) as tong_nhap,
               COALESCE(p.tong_xuat, 0) as tong_xuat,
               COALESCE(d.ton_dau, 0) + COALESCE(p.tong_nhap, 0) - COALESCE(p.tong_xuat, 0) as ton_hien_tai
        FROM dau_nam d
        FULL OUTER JOIN ps_kho p ON d.ma_kho = p.ma_kho
        LEFT JOIN dmkho k ON COALESCE(d.ma_kho, p.ma_kho) = k.ma_kho
        ORDER BY ma_kho
    """)
    print("Tồn kho hiện tại từng kho:", json.dumps(ton_kho, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q15: Lot thành phẩm QC cần chú ý
    # ----------------------------------------------------
    print_sec(15, "Lot thành phẩm QC cần chú ý")
    cols_intem = query("SELECT column_name FROM information_schema.columns WHERE table_name = 'intem_log'")
    print("Cols intem_log:", [c['column_name'] for c in cols_intem if 'qc' in c['column_name'] or 'status' in c['column_name'] or 'lo' in c['column_name']])
    
    # Let's see unique values of status_qc in intem_log
    qc_vals = query("""
        SELECT status_qc, COUNT(*) as c
        FROM intem_log
        WHERE ma_vt = 'QC7-5146-000'
        GROUP BY status_qc
    """)
    print("status_qc phân bố:", json.dumps(qc_vals, ensure_ascii=False, indent=2, default=str))

    # Check non-OK lots
    qc_lots = query("""
        SELECT ma_lo, status_qc, ngay_sx, ca_sx, date0, ma_may, ma_khuon
        FROM intem_log
        WHERE ma_vt = 'QC7-5146-000' AND status_qc NOT IN ('OK', '1', '')
        ORDER BY date0 DESC LIMIT 10
    """)
    print("Các lot QC đáng chú ý:", json.dumps(qc_lots, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q16: Đơn hàng KH0015 chưa có giá chuẩn
    # ----------------------------------------------------
    print_sec(16, "Đơn hàng KH0015 chưa có giá chuẩn được liên kết")
    q16 = query("""
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
    print(f"Tổng số mặt hàng trong SO1 chưa có giá chuẩn hoặc giá = 0: {len(q16)}")
    for r in q16:
        print(f"Đơn: {r['so_ct']} | Ngày: {r['ngay_ct']} | Mã: {r['ma_vt']} | Tên: {r['ten_vt']} | Giá SO: {r['gia2']} | Giá BGC: {r['gia_bg']}")

    # ----------------------------------------------------
    # Q18: Giao bù NG vs Giao bù thiếu (01/10/2026 - 20/10/2026)
    # ----------------------------------------------------
    print_sec(18, "Giao bù NG vs Giao bù thiếu")
    # Check ph82/ct82 (Hàng bán trả lại)
    r_tra = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai
        FROM ph82 h JOIN ct82 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
    """)
    print("Hàng bán trả lại ph82/ct82:", r_tra)

    # Check all ph81 exports with keywords 'bù', 'ng', 'thiếu'
    r_bu = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai, h.ma_gd
        FROM ph81 h JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
          AND (h.dien_giai ILIKE '%%bù%%' OR d.dien_giai ILIKE '%%bù%%' 
               OR h.dien_giai ILIKE '%%ng%%' OR d.dien_giai ILIKE '%%ng%%'
               OR h.dien_giai ILIKE '%%thiếu%%' OR d.dien_giai ILIKE '%%thiếu%%')
    """)
    print("Xuất giao bù trong ph81/ct81:", r_bu)

if __name__ == '__main__':
    main()
