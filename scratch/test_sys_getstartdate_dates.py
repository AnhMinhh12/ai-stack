import psycopg

conn = psycopg.connect(
    host="10.0.6.2",
    port="5410",
    dbname="3SERP_HTMP_DATA",
    user="read_htmp",
    password="P@ss@Htmp@W0rd!2025"
)
cur = conn.cursor()
for d in ['2026-11-06', '2026-05-01', '2026-04-30', '2026-01-01', '2025-12-31']:
    cur.execute("SELECT public.sys_getstartdate(%s::date)", (d,))
    print(f"sys_getstartdate({d}) -> {cur.fetchone()[0]}")
conn.close()
