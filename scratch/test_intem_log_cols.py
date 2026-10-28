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
cur.execute("""
    SELECT a.attname, format_type(a.atttypid, a.atttypmod)
    FROM pg_attribute a
    JOIN pg_class c ON c.oid = a.attrelid
    WHERE c.relname = 'intem_log' AND a.attnum > 0 AND NOT a.attisdropped
    ORDER BY a.attnum;
""")
cols = cur.fetchall()
print("intem_log columns:")
for c in cols:
    print(f"  {c['attname']}: {c['format_type']}")

cur.execute("SELECT * FROM public.intem_log WHERE id_tem = '20261026000051631577' LIMIT 1;")
row = cur.fetchone()
print("\nSample row for id_tem = 20261026000051631577:")
print(row)
conn.close()
