# scratch/check_sys_getrolerecord.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host=os.environ.get("HTMP_DB_HOST", "10.0.6.2"),
    port=int(os.environ.get("HTMP_DB_PORT", "5410")),
    dbname=os.environ.get("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
    user=os.environ.get("HTMP_DB_USER", "read_htmp"),
    password=os.environ.get("HTMP_DB_PASSWORD"),
    connect_timeout=10
)
cur = conn.cursor(cursor_factory=RealDictCursor)

cur.execute("""
    SELECT p.proname, pg_get_functiondef(p.oid) as src
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public' AND LOWER(p.proname) = 'sys_getrolerecord';
""")
row = cur.fetchone()
if row:
    print(f"=== Function sys_getrolerecord ===")
    print(row['src'][:2000])

cur.close()
conn.close()
