# scratch/list_other_reports.py
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

for prefix in ['GL%', 'CA%', 'FA%', 'AR%', 'AP%']:
    cur.execute("SELECT state, rep_id, rep_text, gridid FROM sys_reports WHERE state ILIKE %s ORDER BY state, rep_id;", (prefix,))
    rows = cur.fetchall()
    print(f"\n--- {prefix} ({len(rows)} reports) ---")
    for r in rows[:10]:
        print(f"  {r['state']} [{r['rep_id']}]: {r['rep_text']} -> {r['gridid']}")
    if len(rows) > 10:
        print(f"  ... and {len(rows)-10} more")

cur.close()
conn.close()
