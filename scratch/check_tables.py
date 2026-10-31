import psycopg2, os

conn = psycopg2.connect(
    dbname=os.environ.get('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    user=os.environ.get('HTMP_DB_USER', 'htmp_ro'),
    password=os.environ.get('HTMP_DB_PASSWORD', 'Htmp@2026_Secure'),
    host=os.environ.get('HTMP_DB_HOST', '10.0.6.2'),
    port=os.environ.get('HTMP_DB_PORT', '5410'),
    connect_timeout=5
)
cur = conn.cursor()
for name in ['dmkh', 'dmkho', 'dmnv', 'dmvt', 'cdvt']:
    cur.execute("""
        SELECT c.relname, c.reltuples, s.n_live_tup
        FROM pg_class c
        LEFT JOIN pg_stat_user_tables s ON c.relname = s.relname
        WHERE c.relname = %s
    """, (name,))
    row = cur.fetchone()
    print(f"{name}: {row}")
