# scratch/calc_exact_stock.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host=os.environ.get("HTMP_DB_HOST", "10.0.6.2"),
    port=int(os.environ.get("HTMP_DB_PORT", "5410")),
    dbname=os.environ.get("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
    user=os.environ.get("HTMP_DB_USER", "read_htmp"),
    password=os.environ.get("HTMP_DB_PASSWORD"),
    connect_timeout=10
)
cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute("""
    SELECT a.ma_kho, k.ten_kho,
           coalesce(sum(c.ton00), 0) as ton_dau_ky_2026,
           coalesce(sum(t.sl_nhap), 0) as tong_nhap_2026,
           coalesce(sum(t.sl_xuat), 0) as tong_xuat_2026,
           coalesce(sum(c.ton00), 0) + coalesce(sum(t.sl_nhap - t.sl_xuat), 0) as ton_hien_tai
    FROM (
        SELECT ma_kho FROM cdvt WHERE ma_vt = '75577-BZ010' AND nam = 2026
        UNION
        SELECT ma_kho FROM ct70 WHERE ma_vt = '75577-BZ010' AND ngay_ct >= '2026-01-01'
    ) a
    LEFT JOIN dmkho k ON a.ma_kho = k.ma_kho
    LEFT JOIN (
        SELECT ma_kho, sum(ton00) as ton00
        FROM cdvt
        WHERE ma_vt = '75577-BZ010' AND nam = 2026
        GROUP BY ma_kho
    ) c ON a.ma_kho = c.ma_kho
    LEFT JOIN (
        SELECT ma_kho, sum(sl_nhap) as sl_nhap, sum(sl_xuat) as sl_xuat
        FROM ct70
        WHERE ma_vt = '75577-BZ010' AND ngay_ct >= '2026-01-01'
        GROUP BY ma_kho
    ) t ON a.ma_kho = t.ma_kho
    GROUP BY a.ma_kho, k.ten_kho
    ORDER BY a.ma_kho;
""")
rows = cur.fetchall()
print(f"Exact stock calculation for 75577-BZ010 in DB:")
total_stock = 0
for r in rows:
    total_stock += r['ton_hien_tai']
    print(f"  Kho {r['ma_kho']} ({r['ten_kho']}): Đầu kỳ={r['ton_dau_ky_2026']}, Nhập={r['tong_nhap_2026']}, Xuất={r['tong_xuat_2026']} -> Tồn={r['ton_hien_tai']}")
print(f"  TOTAL ALL WAREHOUSES: {total_stock}")

cur.close()
conn.close()
