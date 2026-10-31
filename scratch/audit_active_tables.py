import psycopg2
import os
import json

conn = psycopg2.connect(
    dbname=os.environ.get('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    user=os.environ.get('HTMP_DB_USER', 'htmp_ro'),
    password=os.environ.get('HTMP_DB_PASSWORD', 'Htmp@2026_Secure'),
    host=os.environ.get('HTMP_DB_HOST', '10.0.6.2'),
    port=os.environ.get('HTMP_DB_PORT', '5410'),
    connect_timeout=5
)
cur = conn.cursor()

# Get all tables with n_live_tup > 0
cur.execute("""
    SELECT relname, n_live_tup
    FROM pg_stat_user_tables
    WHERE schemaname = 'public' AND n_live_tup > 0
    ORDER BY n_live_tup DESC;
""")
rows = cur.fetchall()

result = []
for relname, n_live_tup in rows:
    # Also get sample column names (first 8)
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
        LIMIT 8;
    """, (relname,))
    cols = [f"{c[0]} ({c[1]})" for c in cur.fetchall()]
    result.append({
        "table": relname,
        "rows": n_live_tup,
        "sample_cols": cols
    })

print(f"TOTAL_ACTIVE_TABLES: {len(result)}")
with open('/tmp/active_tables_audit.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("AUDIT_COMPLETED")
