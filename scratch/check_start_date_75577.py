# scratch/check_start_date_75577.py
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

item = '75577-BZ010'

cur.execute("""
    WITH opening AS (
        SELECT c.ma_kho, sum(c.ton00) AS qty
        FROM public.cdvt c
        WHERE c.nam = extract(year FROM CURRENT_DATE)::smallint
          AND upper(trim(c.ma_vt)) = %s
        GROUP BY c.ma_kho
    ),
    movements AS (
        SELECT c.ma_kho, sum(c.sl_nhap - c.sl_xuat) AS qty
        FROM public.ct70 c
        WHERE upper(trim(c.ma_vt)) = %s
          AND c.ngay_ct >= public.sys_getstartdate(CURRENT_DATE)
        GROUP BY c.ma_kho
    ),
    combined AS (
        SELECT ma_kho, qty FROM opening
        UNION ALL
        SELECT ma_kho, qty FROM movements
    )
    SELECT ma_kho, sum(qty) AS ton_kho
    FROM combined
    GROUP BY ma_kho
    ORDER BY ma_kho;
""", (item, item))
print("Stock with sys_getstartdate for 75577-BZ010:")
for r in cur.fetchall():
    print(" ", r)

cur.close()
conn.close()
