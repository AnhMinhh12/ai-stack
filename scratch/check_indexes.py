#!/usr/bin/env python3
import psycopg

def main():
    conn = psycopg.connect(
        host='10.0.6.2',
        port=5410,
        dbname='3SERP_HTMP_DATA',
        user='read_htmp',
        password='P@ss@Htmp@W0rd!2025',
        connect_timeout=3
    )
    cur = conn.cursor()
    tables = ['ph64', 'ct64', 'ph81', 'ct81', 'ph94', 'ct94', 'ph74', 'ct74', 'dmhosokhuon', 'dmbanggiact']
    cur.execute("""
        SELECT tablename, indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = ANY(%s) 
        ORDER BY tablename, indexname;
    """, (tables,))
    for tbl, idx, df in cur.fetchall():
        print(f"[{tbl}] {idx}: {df}")
    conn.close()

if __name__ == '__main__':
    main()
