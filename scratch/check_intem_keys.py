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

def main():
    with psycopg.connect(**CONN_PARAMS, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id_tem, data_tem, status_qc FROM intem_log ORDER BY id_tem DESC LIMIT 3")
            rows = cur.fetchall()
            print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))

if __name__ == '__main__':
    main()
