import psycopg
from psycopg.rows import dict_row

conn = psycopg.connect(
    host='10.0.6.2',
    port=5410,
    dbname='3SERP_HTMP_DATA',
    user='read_htmp',
    password='P@ss@Htmp@W0rd!2025',
    connect_timeout=3
)
cur = conn.cursor(row_factory=dict_row)
cur.execute("SET statement_timeout = '3s'")
cur.execute("SET lock_timeout = '2s'")

cur.execute("SELECT * FROM public.intem_carton_log ORDER BY date0 DESC, time0 DESC LIMIT 5;")
rows = cur.fetchall()
print(f"intem_carton_log: {len(rows)} rows")
for r in rows:
    print(r)

conn.close()
