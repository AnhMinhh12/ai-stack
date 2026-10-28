import psycopg

conn = psycopg.connect(
    host='10.0.6.2',
    port=5410,
    dbname='3SERP_HTMP_DATA',
    user='read_htmp',
    password='P@ss@Htmp@W0rd!2025',
    connect_timeout=5
)
cur = conn.cursor()
cur.execute("SET statement_timeout = '4000'")

# Other customers
cur.execute("SELECT trim(ma_kh), trim(ten_kh) FROM dmkh WHERE ten_kh != '' ORDER BY random() LIMIT 5")
print("Random customers:", cur.fetchall())

# Materials in intem_log with multiple dies
cur.execute("""
    SELECT upper(trim(e->>'ma_vt')) AS ma_vt,
           array_agg(distinct e->>'die_no') as dies,
           sum((e->>'so_luong')::numeric) as total_qty
    FROM public.intem_log a CROSS JOIN LATERAL jsonb_array_elements(
        CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
    ) e
    WHERE a.nxt = 1 AND a.status = '1'
      AND e->>'die_no' IS NOT NULL AND e->>'die_no' != ''
    GROUP BY 1
    HAVING count(distinct e->>'die_no') >= 2
    ORDER BY total_qty DESC
    LIMIT 10
""")
print("Multi-die materials:", cur.fetchall())

conn.close()
