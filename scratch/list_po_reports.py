# scratch/list_po_reports.py
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
    SELECT state, rep_id, rep_text, gridid
    FROM sys_reports
    WHERE state ILIKE 'PO%'
    ORDER BY state, rep_id;
""")
for r in cur.fetchall():
    print(f"  {r['state']} [{r['rep_id']}]: {r['rep_text']} -> {r['gridid']}")

cur.close()
conn.close()
