#!/usr/bin/env python3
import json
import psycopg
from psycopg.rows import dict_row

CONN_PARAMS = {
    "host": "10.0.6.2",
    "port": 5410,
    "dbname": "3SERP_HTMP_DATA",
    "user": "read_htmp",
    "password": "P@ss@Htmp@W0rd!2025",
    "connect_timeout": 5
}

def query(sql, params=None):
    with psycopg.connect(**CONN_PARAMS, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def main():
    print("=== Checking DO in ph96/ct96 for QC7-5146-000 ===")
    dos = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ngay_gh, d.so_luong, d.so_po, d.so_do, d.so_ct_so1, h.status
        FROM ph96 h JOIN ct96 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000'
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC
        LIMIT 10
    """)
    print("DOs:", json.dumps(dos, ensure_ascii=False, indent=2, default=str))

    print("\n=== Checking FCST tables ===")
    fcst_tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND (table_name LIKE '%%fcst%%' OR table_name LIKE '%%forecast%%')
    """)
    print("FCST tables:", [t['table_name'] for t in fcst_tables])
    for tb in [t['table_name'] for t in fcst_tables]:
        try:
            cnt = query(f"SELECT COUNT(*) as c FROM {tb}")
            print(f"Table {tb} total rows: {cnt[0]['c']}")
            # Check columns
            cols = query(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{tb}'")
            print(f"Cols {tb}:", [c['column_name'] for c in cols])
            r = query(f"SELECT * FROM {tb} WHERE ma_vt = 'QC7-5146-000' OR ma_sp = 'QC7-5146-000' LIMIT 5")
            print(f"Rows for QC7-5146-000 in {tb}:", len(r))
            if r:
                print(json.dumps(r, ensure_ascii=False, indent=2, default=str))
        except Exception as e:
            print(f"Error {tb}:", e)

if __name__ == '__main__':
    main()
