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

t0 = time.time()
cur.execute("SELECT public.sys_getstartdate(CURRENT_DATE)")
start_date = cur.fetchone()[0]
print(f"sys_getstartdate took: {time.time() - t0:.2f}s, start_date = {start_date}")

# Query 1: ct70 grouped by warehouse with literal start_date
t1 = time.time()
cur.execute("""
    SELECT ma_kho, sum(sl_nhap - sl_xuat) AS qty 
    FROM public.ct70 
    WHERE ngay_ct >= %s 
    GROUP BY ma_kho
""", (start_date,))
rows = cur.fetchall()
print(f"ct70 grouped by warehouse took: {time.time() - t1:.2f}s, rows = {len(rows)}")

# Query 2: full query
t2 = time.time()
cur.execute("""
    WITH opening AS (
        SELECT ma_kho, sum(ton00) AS qty FROM public.cdvt WHERE nam = extract(year FROM %s::date)::smallint GROUP BY ma_kho
    ), movements AS (
        SELECT ma_kho, sum(sl_nhap - sl_xuat) AS qty FROM public.ct70 WHERE ngay_ct >= %s GROUP BY ma_kho
    ), balances AS (
        SELECT ma_kho, qty FROM opening UNION ALL SELECT ma_kho, qty FROM movements
    )
    SELECT b.ma_kho, coalesce(k.ten_kho, b.ma_kho) AS ten_kho, sum(b.qty) AS tong_ton_kho
    FROM balances b 
    LEFT JOIN public.dmkho k ON k.ma_kho = b.ma_kho
    GROUP BY b.ma_kho, k.ten_kho
    HAVING sum(b.qty) > 0
    ORDER BY tong_ton_kho DESC;
""", (start_date, start_date))
full_rows = cur.fetchall()
print(f"full query took: {time.time() - t2:.2f}s, rows = {len(full_rows)}")
print("First 3 rows:", full_rows[:3])

conn.close()
