# scratch/test_inbctontheokho_live.py
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

params = json.dumps({
    "JSON": {
        "user_id": "1",
        "searchDynamic": {
            "dto": "2026-11-06",
            "cma_kho": "",
            "cma_vt": "75577-BZ010",
            "cnh_vt1": "",
            "cnh_vt2": "",
            "cnh_vt3": "",
            "cnh_vt4": "",
            "cnh_vt5": "",
            "cnh_vt6": "",
            "ctk_vt": "",
            "cma_dvcs": "001",
            "cgroup": "",
            "cstatus": "*",
            "mau_bc": "001",
            "gridid": "InBCTonTheoKho1",
            "culture": "vi-VN"
        }
    }
})

try:
    cur.execute("SELECT * FROM public.inbctontheokho(%s);", (params,))
    rows = cur.fetchall()
    print(f"Query returned {len(rows)} rows for 75577-BZ010:")
    for r in rows:
        filtered = {k: v for k, v in r.items() if v is not None and str(v).strip() != ''}
        print(" ", filtered)
except Exception as e:
    print("Error executing inbctontheokho:", e)

cur.close()
conn.close()
