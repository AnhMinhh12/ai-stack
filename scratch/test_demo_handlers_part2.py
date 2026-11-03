import re
import json
import psycopg
from decimal import Decimal

DB_KWARGS = dict(host='10.0.6.2', port=5410, dbname='3SERP_HTMP_DATA', user='read_htmp', password='P@ss@Htmp@W0rd!2025')

def test_q4_sales_month_comparison():
    print("=== TEST Q4: HK2C2-393-01-00 THÁNG 9 VS THÁNG 10 ===")
    ma_vt = "HK2C2-393-01-00"
    with psycopg.connect(**DB_KWARGS) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                WITH k1 AS (
                    SELECT sum(d.so_luong) AS sl_ky_1, sum(d.tien2) AS tien_ky_1
                    FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
                    WHERE upper(trim(d.ma_vt)) = %s AND h.ngay_ct BETWEEN '2026-09-01' AND '2026-09-30'
                      AND h.status::text NOT IN ('14', '15')
                ), k2 AS (
                    SELECT sum(d.so_luong) AS sl_ky_2, sum(d.tien2) AS tien_ky_2
                    FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
                    WHERE upper(trim(d.ma_vt)) = %s AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31'
                      AND h.status::text NOT IN ('14', '15')
                )
                SELECT coalesce(k1.sl_ky_1, 0), coalesce(k1.tien_ky_1, 0),
                       coalesce(k2.sl_ky_2, 0), coalesce(k2.tien_ky_2, 0),
                       coalesce(v.ten_vt, %s), coalesce(v.dvt, 'PCS')
                FROM k1 CROSS JOIN k2
                LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = %s
            """, (ma_vt, ma_vt, ma_vt, ma_vt))
            row = cur.fetchone()
            sl1, tien1, sl2, tien2, ten_vt, dvt = row
            diff_sl = sl2 - sl1
            pct_sl = (diff_sl / sl1 * 100) if sl1 > 0 else 0
            diff_tien = tien2 - tien1
            pct_tien = (diff_tien / tien1 * 100) if tien1 > 0 else 0
            print(f"Product: {ma_vt} ({ten_vt})")
            print(f"Tháng 09/2026: {sl1:,.0f} {dvt} | Doanh thu: {tien1:,.0f} VND")
            print(f"Tháng 10/2026: {sl2:,.0f} {dvt} | Doanh thu: {tien2:,.0f} VND")
            print(f"Tăng trưởng: {diff_sl:+,.0f} {dvt} ({pct_sl:+.2f}%) | Doanh thu: {diff_tien:+,.0f} VND ({pct_tien:+.2f}%)")

def test_q2_do_snapshot_comparison():
    print("\n=== TEST Q2: DO DEMAND SNAPSHOT COMPARISON ===")
    ma_vt = "QC7-5146-000"
    with psycopg.connect(**DB_KWARGS) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT id, date0
                FROM public.mfkhsx_po_fc
                ORDER BY id DESC LIMIT 2
            """)
            snapshots = cur.fetchall()
            id1, d1 = snapshots[0]
            id2, d2 = snapshots[1]
            print(f"Comparing snapshot {id1} ({d1}) vs {id2} ({d2}) for {ma_vt}:")
            cur.execute("""
                SELECT id, nguon_du_lieu, coalesce(sum(so_luong), 0)
                FROM public.mfkhsx_po_fc
                WHERE upper(trim(ma_vt)) = %s AND id IN (%s, %s)
                GROUP BY id, nguon_du_lieu
                ORDER BY id DESC, nguon_du_lieu
            """, (ma_vt, id1, id2))
            for r in cur.fetchall():
                print(" ", r)

def test_q1_q5_split_sales_and_ng():
    print("\n=== TEST Q1 & Q5: SPLIT SALES VS NG COMPENSATION ===")
    for ma_vt in ["H131-TBT-H612", ""]:
        label = ma_vt if ma_vt else "TOÀN CÔNG TY"
        print(f"--- {label} (01/09/2026 - 31/10/2026) ---")
        with psycopg.connect(**DB_KWARGS) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COALESCE(ph64.ma_gd, 1) as ma_gd,
                        CASE WHEN COALESCE(ph64.ma_gd, 1) = 10 THEN 'Đơn hàng xuất bù hàng lỗi (NG)' ELSE 'Đơn hàng bán thương mại' END as loai_don,
                        count(DISTINCT h.stt_rec) as so_phieu,
                        count(d.stt_rec) as so_dong,
                        coalesce(sum(d.so_luong), 0) as tong_sl,
                        coalesce(sum(d.tien2), 0) as tong_tien
                    FROM public.ph81 h
                    JOIN public.ct81 d USING(stt_rec)
                    LEFT JOIN public.ph64 ph64 ON d.stt_rec_so1 = ph64.stt_rec
                    WHERE (%s = '' OR upper(trim(d.ma_vt)) = %s)
                      AND h.ngay_ct BETWEEN '2026-09-01' AND '2026-10-31'
                    GROUP BY COALESCE(ph64.ma_gd, 1)
                    ORDER BY ma_gd
                """, (ma_vt, ma_vt))
                for r in cur.fetchall():
                    print(" ", r)

def test_q6_stock_by_mold():
    print("\n=== TEST Q6: STOCK BY MOLD (TP & XHTL ONLY) ===")
    ma_vt = "QC7-5146-000"
    with psycopg.connect(**DB_KWARGS) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.ma_sp, s.ma_khuon, h.ten_khuon, h.so_cavity, h.tong_so_shot, h.tinh_trang_khuon
                FROM public.dmhosokhuonsp s
                JOIN public.dmhosokhuon h ON s.ma_khuon = h.ma_khuon
                WHERE s.ma_sp = %s
            """, (ma_vt,))
            molds = cur.fetchall()
            print("Molds:", molds)
            cur.execute("""
                WITH opening AS (
                    SELECT c.ma_kho, sum(c.ton00) AS qty
                    FROM public.cdvt c
                    WHERE c.nam = 2026 AND upper(trim(c.ma_vt)) = %s
                      AND (c.ma_kho ILIKE 'KHOTP%%' OR c.ma_kho ILIKE 'KHO-XH%%')
                    GROUP BY c.ma_kho
                ),
                movements AS (
                    SELECT c.ma_kho, sum(c.sl_nhap - c.sl_xuat) AS qty
                    FROM public.ct70 c
                    WHERE upper(trim(c.ma_vt)) = %s AND c.ngay_ct >= '2026-01-01'
                      AND (c.ma_kho ILIKE 'KHOTP%%' OR c.ma_kho ILIKE 'KHO-XH%%')
                    GROUP BY c.ma_kho
                ),
                combined AS (
                    SELECT ma_kho, qty FROM opening
                    UNION ALL
                    SELECT ma_kho, qty FROM movements
                )
                SELECT c.ma_kho, k.ten_kho, sum(c.qty) AS ton_kho
                FROM combined c
                JOIN public.dmkho k ON c.ma_kho = k.ma_kho
                GROUP BY c.ma_kho, k.ten_kho
                HAVING sum(c.qty) > 0
                ORDER BY ton_kho DESC
            """, (ma_vt, ma_vt))
            stocks = cur.fetchall()
            print("Stocks in TP & XHTL:", stocks)

def test_q7_historical_orders():
    print("\n=== TEST Q7: HISTORICAL ORDERS 09/2026 FOR H131-TBT-H612 ===")
    ma_vt = "H131-TBT-H612"
    with psycopg.connect(**DB_KWARGS) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT h.so_ct, h.ngay_ct, h.ma_kh, k.ten_kh, d.so_luong, d.dvt, h.status
                FROM public.ph64 h
                JOIN public.ct64 d USING(stt_rec)
                LEFT JOIN public.dmkh k ON h.ma_kh = k.ma_kh
                WHERE upper(trim(d.ma_vt)) = %s AND h.ngay_ct BETWEEN '2026-09-01' AND '2026-09-30'
            """, (ma_vt,))
            sos = cur.fetchall()
            print("Sales Orders SO1:", sos)
            cur.execute("""
                SELECT count(d.stt_rec), sum(d.so_luong), sum(d.tien2)
                FROM public.ph81 h
                JOIN public.ct81 d USING(stt_rec)
                WHERE upper(trim(d.ma_vt)) = %s AND h.ngay_ct BETWEEN '2026-09-01' AND '2026-09-30'
            """, (ma_vt,))
            hda = cur.fetchone()
            print("Shipments HDA:", hda)

test_q4_sales_month_comparison()
test_q2_do_snapshot_comparison()
test_q1_q5_split_sales_and_ng()
test_q6_stock_by_mold()
test_q7_historical_orders()
