import psycopg

settings = {
    "host": "10.0.6.2",
    "port": 5410,
    "dbname": "3SERP_HTMP_DATA",
    "user": "read_htmp",
    "password": "P@ss@Htmp@W0rd!2025",
    "connect_timeout": 5
}

with psycopg.connect(**settings) as conn:
    with conn.cursor() as cur:
        print("=== CT64 OF 001-2610-010538 (Luxshare) ===")
        cur.execute("""
            SELECT c.so_ct, c.ma_vt, v.ten_vt, c.so_luong, c.gia_nt2, c.gia2, c.tien_nt2, c.tien2
            FROM public.ct64 c
            LEFT JOIN public.dmvt v ON v.ma_vt = c.ma_vt
            WHERE c.so_ct = '001-2610-010538'
            LIMIT 5;
        """)
        for r in cur.fetchall():
            print(r)

        print("\n=== CT64 OF 001-2610-000458 (Funing) ===")
        cur.execute("""
            SELECT c.so_ct, c.ma_vt, v.ten_vt, c.so_luong, c.gia_nt2, c.gia2, c.tien_nt2, c.tien2
            FROM public.ct64 c
            LEFT JOIN public.dmvt v ON v.ma_vt = c.ma_vt
            WHERE c.so_ct = '001-2610-000458'
            LIMIT 5;
        """)
        for r in cur.fetchall():
            print(r)

        print("\n=== ARE THERE ANY ORDERS FOR KH0067 OR KH0078 WITH PRICE > 0 IN ALL TIME? ===")
        cur.execute("""
            SELECT h.ma_kh, count(*) as total_orders, 
                   count(*) FILTER (WHERE h.t_tien2 > 0 OR h.t_tien_nt2 > 0) as orders_with_price,
                   count(*) FILTER (WHERE h.t_tien2 = 0 AND h.t_tien_nt2 = 0) as zero_price_orders
            FROM public.ph64 h
            WHERE h.ma_kh IN ('KH0067', 'KH0078', 'KH0044', 'KH0045', 'KH0047')
              AND h.ma_ct = 'SO1'
            GROUP BY h.ma_kh;
        """)
        for r in cur.fetchall():
            print(r)
