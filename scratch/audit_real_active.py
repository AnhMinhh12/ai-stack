import psycopg2, os, json

conn = psycopg2.connect(
    dbname=os.environ.get('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    user=os.environ.get('HTMP_DB_USER', 'htmp_ro'),
    password=os.environ.get('HTMP_DB_PASSWORD', 'Htmp@2026_Secure'),
    host=os.environ.get('HTMP_DB_HOST', '10.0.6.2'),
    port=os.environ.get('HTMP_DB_PORT', '5410'),
    connect_timeout=5
)
cur = conn.cursor()

# Query pg_class for all user tables in public schema
cur.execute("""
    SELECT c.relname, c.reltuples::bigint as est_rows
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' 
      AND c.relkind = 'r'
    ORDER BY c.reltuples DESC;
""")
rows = cur.fetchall()

positive_tables = []
zero_tables = []
for relname, est_rows in rows:
    # If est_rows is 0 or -1, double check with a quick SELECT 1 ... LIMIT 1
    if est_rows <= 0:
        cur.execute(f'SELECT 1 FROM "{relname}" LIMIT 1;')
        has_data = cur.fetchone() is not None
        if has_data:
            positive_tables.append((relname, 1)) # has at least some data
        else:
            zero_tables.append(relname)
    else:
        positive_tables.append((relname, est_rows))

print(f"Total tables: {len(rows)}")
print(f"Tables with data: {len(positive_tables)}")
print(f"Empty tables: {len(zero_tables)}")

with open('/tmp/real_active_tables.json', 'w', encoding='utf-8') as f:
    json.dump({
        "total": len(rows),
        "with_data": len(positive_tables),
        "empty": len(zero_tables),
        "active_tables": positive_tables,
        "empty_tables": zero_tables
    }, f, ensure_ascii=False, indent=2)

print("AUDIT_DONE")
