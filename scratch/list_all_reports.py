# scratch/list_all_reports.py
import os
import json
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
    SELECT DISTINCT state, rep_id, rep_text, gridid
    FROM sys_reports
    ORDER BY state, rep_id;
""")
reports = cur.fetchall()
print(f"Total reports in sys_reports: {len(reports)}")
by_module = {}
for r in reports:
    s = r['state'] or 'None'
    prefix = s[:2].upper()
    by_module.setdefault(prefix, []).append(r)

for mod, r_list in sorted(by_module.items()):
    print(f"\n--- Module {mod} ({len(r_list)} reports) ---")
    for r in r_list[:10]:
        print(f"  {r['state']} [{r['rep_id']}]: {r['rep_text']} (grid: {r['gridid']})")
    if len(r_list) > 10:
        print(f"  ... and {len(r_list) - 10} more")

cur.close()
conn.close()
