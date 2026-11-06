# scratch/check_report_params.py
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

for st in ['POBKDonHang', 'SOBKDonHang', 'InBCTonTheoKho', 'POStatus', 'SOBCTienDoGH', 'SOBKHoaDonBH', 'InBCXNT']:
    cur.execute("""
        SELECT column_name, column_title, control_type, form_name, form_value, show_yn, index
        FROM sys_reportparams
        WHERE LOWER(stateid) = LOWER(%s)
        ORDER BY index ASC;
    """, (st,))
    rows = cur.fetchall()
    print(f"\n=== Report Params for {st} ({len(rows)} params) ===")
    for r in rows:
        print(f"  [{r['index']}] {r['column_name']} ({r['column_title']}): type={r['control_type']}, default={r['form_value']}")

cur.close()
conn.close()
