#!/usr/bin/env python3
import psycopg
import time

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
    cur.execute("SET statement_timeout = '3s'")
    
    tables_to_check = [
        'ph94', 'ct94', 'ph74', 'ct74', 'ph71', 'ct71', 'ph72', 'ct72', 'ph73', 'ct73',
        'ph91', 'ct91', 'ph92', 'ct92', 'ph93', 'ct93', 'ph95', 'ct95', 'ph84', 'ct84',
        'ph85', 'ct85', 'ph88', 'ct88', 'ph89', 'ct89', 'ph90', 'ct90'
    ]
    cur.execute("""
        SELECT c.relname, c.reltuples::bigint
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = ANY(%s)
        ORDER BY c.relname;
    """, (tables_to_check,))
    rows = cur.fetchall()
    print("=== PURCHASING & INVENTORY TABLES IN DB ===")
    for name, cnt in rows:
        print(f"  {name:<10}: {cnt:>12,d} approx rows")

    # Sample ph94
    cur.execute("""
        SELECT so_ct, ngay_ct, ma_kh, ten_kh, t_so_luong, t_tien, status 
        FROM ph94 
        ORDER BY ngay_ct DESC 
        LIMIT 3
    """)
    print("\n=== SAMPLE PH94 (ĐƠN HÀNG MUA PO) ===")
    for r in cur.fetchall():
        print(f"  SO_CT: {r[0]} | Ngày: {r[1]} | NCC: {r[2]} ({r[3]}) | SL: {r[4]} | Tiền: {r[5]} | Status: {r[6]}")

    # Check sys_dmtt for PO1 and SO1
    cur.execute("""
        SELECT ma_ct, status, statusname, statusname2 
        FROM sys_dmtt 
        WHERE ma_ct IN ('PO1', 'SO1', 'HDA', 'PXK', 'PNK', 'PND', 'PXD')
        ORDER BY ma_ct, status;
    """)
    print("\n=== STATUS DICTIONARY (sys_dmtt) ===")
    for r in cur.fetchall():
        print(f"  [{r[0]}] Status {r[1]}: {r[2]}")

    conn.close()

if __name__ == '__main__':
    main()
