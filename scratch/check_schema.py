import psycopg
from psycopg.rows import dict_row

conn = psycopg.connect("host=10.0.6.2 port=5410 dbname=3SERP_HTMP_DATA user=read_htmp password=P@ss@Htmp@W0rd!2025", connect_timeout=5)
with conn.cursor(row_factory=dict_row) as cur:
    cur.execute("SET statement_timeout = '5s'")
    # Columns
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'mes_oi_dong_thung'
    """)
    cols = cur.fetchall()
    print("Columns:", [f"{c['column_name']} ({c['data_type']})" for c in cols])
    
    # Indexes
    cur.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE schemaname = 'public' AND tablename = 'mes_oi_dong_thung'
    """)
    indexes = cur.fetchall()
    print("\nIndexes:")
    for idx in indexes:
        print(" ", idx['indexname'], ":", idx['indexdef'])
