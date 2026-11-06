# scratch/view_inbctontheokho_head.py
import os
import psycopg2

conn = psycopg2.connect(
    host=os.environ.get("HTMP_DB_HOST", "10.0.6.2"),
    port=int(os.environ.get("HTMP_DB_PORT", "5410")),
    dbname=os.environ.get("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
    user=os.environ.get("HTMP_DB_USER", "read_htmp"),
    password=os.environ.get("HTMP_DB_PASSWORD"),
    connect_timeout=10
)
cur = conn.cursor()

cur.execute("""
    SELECT pg_get_functiondef(oid)
    FROM pg_proc
    WHERE proname = 'inbctontheokho' AND pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
""")
src = cur.fetchone()[0]
lines = src.split('\n')
print('\n'.join(lines[:70]))

cur.close()
conn.close()
