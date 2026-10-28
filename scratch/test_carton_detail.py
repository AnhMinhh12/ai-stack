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

cur.execute("""
    SELECT 
        l.id_tem, l.ma_vt, v.ten_vt, l.dvt, l.so_luong, l.ma_thung, l.user_id0, l.date0, l.time0
    FROM public.intem_log l
    LEFT JOIN public.dmvt v ON v.ma_vt = l.ma_vt
    WHERE l.id_tem = '20261026000051631577' OR l.id_tem = '20261027000051667704'
    LIMIT 5;
""")
rows = cur.fetchall()
print(f"intem_log for carton: {len(rows)} rows")
for r in rows:
    print(r)

conn.close()
