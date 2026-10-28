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
    tables = query("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND (
            table_name LIKE '%%ke_hoach%%' OR table_name LIKE '%%khgh%%' 
            OR table_name LIKE '%%khsx%%' OR table_name LIKE '%%dudoan%%'
            OR table_name LIKE '%%du_bao%%' OR table_name LIKE '%%ctkh%%'
            OR table_name LIKE '%%khbh%%'
        )
    """)
    print("Found tables:", [t['table_name'] for t in tables])
    for tb in [t['table_name'] for t in tables]:
        try:
            r = query(f"SELECT COUNT(*) as c FROM {tb} WHERE ma_vt = 'QC7-5146-000' OR ma_sp = 'QC7-5146-000'")
            if r[0]['c'] > 0:
                print(f"Table {tb} has {r[0]['c']} rows for QC7-5146-000")
        except Exception:
            pass

if __name__ == '__main__':
    main()
