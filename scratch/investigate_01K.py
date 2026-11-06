# scratch/investigate_01K.py
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

item = '01K-2A00C-0000-1'

# 1. Check dmvt
cur.execute("SELECT ma_vt, ten_vt, dvt, status FROM dmvt WHERE ma_vt = %s;", (item,))
print("Item metadata:", cur.fetchall())

# 2. Check cdvt (opening balance 2026)
cur.execute("SELECT nam, ma_kho, ton00, du00 FROM cdvt WHERE ma_vt = %s ORDER BY nam DESC, ma_kho;", (item,))
print("\nOpening balance (cdvt):")
for r in cur.fetchall():
    print(" ", r)

# 3. Check ct70 transactions in 2026 for KHO-IN
cur.execute("""
    SELECT ngay_ct, time0, so_ct, ma_ct, ma_kho, sl_nhap, sl_xuat, dien_giai
    FROM ct70
    WHERE ma_vt = %s AND ma_kho = 'KHO-IN' AND ngay_ct >= '2026-01-01'
    ORDER BY ngay_ct ASC, time0 ASC;
""", (item,))
print("\nTransactions in KHO-IN (ct70):")
rows = cur.fetchall()
tot_nhap = sum(r['sl_nhap'] for r in rows)
tot_xuat = sum(r['sl_xuat'] for r in rows)
print(f"Total ct70 rows: {len(rows)}, Total Nhap: {tot_nhap}, Total Xuat: {tot_xuat}")
for r in rows[-15:]:
    print(" ", r)

# 4. Check all warehouses ct70 summary
cur.execute("""
    SELECT ma_kho, sum(sl_nhap) as nhap, sum(sl_xuat) as xuat, sum(sl_nhap - sl_xuat) as ps
    FROM ct70
    WHERE ma_vt = %s AND ngay_ct >= '2026-01-01'
    GROUP BY ma_kho;
""", (item,))
print("\nSummary by warehouse (ct70 in 2026):")
for r in cur.fetchall():
    print(" ", r)

cur.close()
conn.close()
