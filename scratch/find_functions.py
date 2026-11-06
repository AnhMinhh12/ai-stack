# scratch/find_functions.py
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

targets = ['inbctontheokho', 'inbcthnxt', 'inso1', 'inbcnhatkynxt', 'sobkdonhang', 'pobkdonhang', 'postatus', 'sobctiendogh', 'sobkhoadonbh']

for t in targets:
    cur.execute("""
        SELECT p.proname, pg_get_function_arguments(p.oid) as args, pg_get_functiondef(p.oid) as src
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND LOWER(p.proname) LIKE %s;
    """, (f"%{t}%",))
    rows = cur.fetchall()
    print(f"\n=== Functions for {t} ({len(rows)} found) ===")
    for r in rows:
        lines = r['src'].split('\n')
        print(f"  {r['proname']}({r['args']}): {len(lines)} lines")
        # Find referenced tables in source
        words = set([w.lower() for w in lines if 'from ' in w.lower() or 'join ' in w.lower()])
        ref_sample = [line.strip() for line in lines if any(k in line.lower() for k in ['cdvt', 'ct70', 'ph64', 'ct64', 'ph71', 'ct71', 'ph81', 'ct81', 'dmvt', 'dmkho', 'sys_'])]
        print(f"    Sample references ({len(ref_sample)} lines matched):")
        for ref in ref_sample[:4]:
            print(f"      {ref[:100]}")

cur.close()
conn.close()
