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
    cols = query("SELECT column_name FROM information_schema.columns WHERE table_name = 'mfkhsx_po_fc'")
    print("Cols mfkhsx_po_fc:", [c['column_name'] for c in cols])
    
    # Check sample
    sample = query("SELECT * FROM mfkhsx_po_fc LIMIT 3")
    print("Sample:", json.dumps(sample, ensure_ascii=False, indent=2, default=str))

    r = query("SELECT id, date0, so_ct, loai_du_lieu, nguon_du_lieu, ngay_giao_hang, so_luong, status FROM mfkhsx_po_fc WHERE ma_vt = 'QC7-5146-000' ORDER BY date0 DESC, ngay_giao_hang ASC LIMIT 20")
    print("For QC7-5146-000:", json.dumps(r, ensure_ascii=False, indent=2, default=str))

if __name__ == '__main__':
    main()
