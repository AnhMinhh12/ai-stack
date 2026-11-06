# scratch/extract_db_metadata.py
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

screens = [
    'inbctontheokho', 'inbkdonhangban', 'inbkdonhangmua', 'inbctinhtrangdonhangmua',
    'inbcxnt', 'inbcthekho', 'mftkhsx', 'so1', 'to2', 'hda', 'po1', 'pn1'
]

results = {}

for sc in screens:
    # 1. Check sys_reports
    cur.execute("""
        SELECT state, rep_id, rep_text, rep_title, rep_file, gridid, status, ma_gd
        FROM sys_reports
        WHERE LOWER(state) = %s OR LOWER(rep_id) = %s OR LOWER(gridid) LIKE %s;
    """, (sc, sc, f"%{sc}%"))
    reports = [dict(r) for r in cur.fetchall()]

    # 2. Check sys_reportparams
    cur.execute("""
        SELECT module, stateid, column_name, show_yn, index, column_title, control_type, form_name, form_value, col_select, where_clause, load_from
        FROM sys_reportparams
        WHERE LOWER(stateid) = %s
        ORDER BY index ASC;
    """, (sc,))
    params = [dict(p) for p in cur.fetchall()]

    # 3. Check sys_gridconfig for gridids associated with reports or sc
    gridids = set([sc])
    for r in reports:
        if r.get('gridid'):
            gridids.add(r['gridid'].lower())

    grids = []
    for gid in gridids:
        cur.execute("""
            SELECT gridid, fieldname, field_root, tablename, leftjoin, table_as, fieldposition, fieldcaption, visible, style, editable_yn, hidden_yn
            FROM sys_gridconfig
            WHERE LOWER(gridid) LIKE %s
            ORDER BY fieldposition ASC;
        """, (f"%{gid}%",))
        grids.extend([dict(g) for g in cur.fetchall()])

    # 4. Check routines
    cur.execute("""
        SELECT routine_name, routine_type, data_type
        FROM information_schema.routines
        WHERE specific_schema = 'public' AND LOWER(routine_name) LIKE %s;
    """, (f"%{sc}%",))
    routines = [dict(rt) for rt in cur.fetchall()]

    results[sc] = {
        "reports": reports,
        "params": params,
        "grids": grids,
        "routines": routines
    }

print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
cur.close()
conn.close()
