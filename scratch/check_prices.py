import psycopg
from functions.htmp_postgres_query import connection_settings

conn = psycopg.connect(**connection_settings())
cur = conn.cursor()

for code in ('T1015910DA', '156279430'):
    print(f"\n==========================================")
    print(f"CHECKING CODE: {code}")
    cur.execute("SELECT ma_vt, ten_vt, dvt, ma_kh FROM public.dmvt WHERE upper(trim(ma_vt)) = %s", (code,))
    print("dmvt:", cur.fetchall())

    # 1. dmbanggiact
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'dmbanggiact'
    """)
    cols = [r[0] for r in cur.fetchall()]
    print("dmbanggiact columns:", cols)

    cur.execute("SELECT * FROM public.dmbanggiact WHERE upper(trim(ma_vt)) = %s LIMIT 5", (code,))
    print("dmbanggiact rows:", cur.fetchall())

    # 2. dmgiavtsalect
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'dmgiavtsalect'
    """)
    cols2 = [r[0] for r in cur.fetchall()]
    print("dmgiavtsalect columns:", cols2)

    cur.execute("SELECT * FROM public.dmgiavtsalect WHERE upper(trim(ma_vt)) = %s LIMIT 5", (code,))
    print("dmgiavtsalect rows:", cur.fetchall())

    # 3. ct81 (Phiếu xuất bán)
    cur.execute("SELECT ngay_ct, so_ct, gia_nt, gia2, ma_vt FROM public.ct81 WHERE upper(trim(ma_vt)) = %s ORDER BY ngay_ct DESC LIMIT 3", (code,))
    print("ct81 recent shipments:", cur.fetchall())

    # 4. ct61 (Hóa đơn bán)
    cur.execute("SELECT ngay_ct, so_ct, gia_nt, gia2, ma_vt FROM public.ct61 WHERE upper(trim(ma_vt)) = %s ORDER BY ngay_ct DESC LIMIT 3", (code,))
    print("ct61 recent invoices:", cur.fetchall())

    # 5. ct64 (Đơn hàng bán)
    cur.execute("SELECT ngay_ct, so_ct, gia_nt, gia2, ma_vt FROM public.ct64 WHERE upper(trim(ma_vt)) = %s ORDER BY ngay_ct DESC LIMIT 3", (code,))
    print("ct64 recent SOs:", cur.fetchall())
