# scratch/check_ct70_today.py
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
    SELECT ngay_ct, time0, so_ct, ma_ct, ma_kho, sl_nhap, sl_xuat, dien_giai
    FROM ct70
    WHERE ma_vt = '75577-BZ010' AND ngay_ct >= '2026-11-05'
    ORDER BY ngay_ct ASC, time0 ASC;
""")
rows = cur.fetchall()
print(f"Transactions in ct70 on 05-06 Nov 2026 ({len(rows)} rows):")
for r in rows:
    print(" ", r)

cur.close()
conn.close()
