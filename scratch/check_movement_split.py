# scratch/check_movement_split.py
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

cur.execute("""
    SELECT 
        sum(case when ngay_ct < '2026-05-01' then sl_nhap - sl_xuat else 0 end) as ps_before_may,
        sum(case when ngay_ct >= '2026-05-01' then sl_nhap - sl_xuat else 0 end) as ps_after_may,
        sum(sl_nhap - sl_xuat) as ps_all_2026
    FROM ct70
    WHERE ma_vt = %s AND ma_kho = 'KHO-IN' AND ngay_ct >= '2026-01-01';
""", (item,))
row = cur.fetchone()
print("KHO-IN movements breakdown:")
print("  Phát sinh từ 01/01 đến 30/04/2026:", row['ps_before_may'])
print("  Phát sinh từ 01/05 đến nay:", row['ps_after_may'])
print("  Phát sinh cả năm 2026:", row['ps_all_2026'])

cur.execute("SELECT ton00 FROM cdvt WHERE ma_vt = %s AND ma_kho = 'KHO-IN' AND nam = 2026;", (item,))
print("  ton00 trong cdvt 2026:", cur.fetchone()['ton00'])

cur.close()
conn.close()
