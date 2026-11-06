import time
import psycopg

conn = psycopg.connect(
    host="10.0.6.2",
    port="5410",
    dbname="3SERP_HTMP_DATA",
    user="read_htmp",
    password="P@ss@Htmp@W0rd!2025"
)
cur = conn.cursor()

cur.execute("SELECT public.sys_getstartdate(CURRENT_DATE)")
start_date = cur.fetchone()[0]

t0 = time.time()
cur.execute("""
    WITH opening AS (
        SELECT ma_vt, sum(ton00) AS qty FROM public.cdvt WHERE nam = extract(year FROM %s::date)::smallint GROUP BY ma_vt
    ), movements AS (
        SELECT ma_vt, sum(sl_nhap - sl_xuat) AS qty FROM public.ct70 WHERE ngay_ct >= %s GROUP BY ma_vt
    ), balances AS (
        SELECT ma_vt, qty FROM opening UNION ALL SELECT ma_vt, qty FROM movements
    )
    SELECT b.ma_vt, v.ten_vt, v.dvt, sum(b.qty) AS so_luong_ton
    FROM balances b 
    JOIN public.dmvt v ON v.ma_vt = b.ma_vt
    GROUP BY b.ma_vt, v.ten_vt, v.dvt
    HAVING sum(b.qty) > 0
    ORDER BY so_luong_ton DESC
    LIMIT 10;
""", (start_date, start_date))
rows = cur.fetchall()
print(f"Top 10 inventory query took: {time.time() - t0:.2f}s, rows = {len(rows)}")
for r in rows[:3]:
    print(r)

conn.close()
