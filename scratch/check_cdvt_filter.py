# scratch/check_cdvt_filter.py
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
    SELECT nam, ma_dvcs, ma_kho, ma_vt, ton00, du00
    FROM cdvt
    WHERE ma_vt = %s;
""", (item,))
print("cdvt rows for item:")
for r in cur.fetchall():
    print(" ", r)

cur.execute("""
    SELECT ma_kho, ten_kho, ma_dvcs, status
    FROM dmkho
    WHERE ma_kho = 'KHO-IN';
""")
print("\ndmkho for KHO-IN:")
print(" ", cur.fetchall())

cur.close()
conn.close()
