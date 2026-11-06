import psycopg
from functions.htmp_postgres_query import connection_settings

conn = psycopg.connect(**connection_settings())
cur = conn.cursor()

print("=" * 70)
print("1. INVESTIGATE 1014084300 STOCK BY WAREHOUSE:")
cur.execute("SELECT public.sys_getstartdate(CURRENT_DATE)")
sd = cur.fetchone()[0]
print("sys_getstartdate:", sd)

cur.execute("""
    SELECT c.ma_kho, sum(c.ton00) AS qty
    FROM public.cdvt c
    WHERE c.nam = extract(year FROM %s::date)::smallint AND upper(trim(c.ma_vt)) = '1014084300'
    GROUP BY c.ma_kho
""", (sd,))
print("Opening cdvt 1014084300:", cur.fetchall())

cur.execute("""
    SELECT c.ma_kho, sum(c.sl_nhap - c.sl_xuat) AS qty
    FROM public.ct70 c
    WHERE upper(trim(c.ma_vt)) = '1014084300' AND c.ngay_ct >= %s
    GROUP BY c.ma_kho
""", (sd,))
print("Movements ct70 1014084300:", cur.fetchall())

print("=" * 70)
print("2. INVESTIGATE T1015910DA:")
cur.execute("SELECT ma_vt, ten_vt, dvt, gia_chuan, ma_kh FROM public.dmvt WHERE upper(trim(ma_vt)) = 'T1015910DA'")
print("dmvt T1015910DA:", cur.fetchall())
# Search price lists / bang gia
cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_name ILIKE '%gia%' OR table_name ILIKE '%price%'
""")
print("Price tables:", [r[0] for r in cur.fetchall()])

print("=" * 70)
print("3. INVESTIGATE 156279430:")
cur.execute("SELECT ma_vt, ten_vt, dvt, gia_chuan, ma_kh FROM public.dmvt WHERE upper(trim(ma_vt)) = '156279430'")
print("dmvt 156279430:", cur.fetchall())

# Check recent sales order or invoice prices for both
for code in ('T1015910DA', '156279430'):
    print(f"\nSales/Invoice/Shipment for {code}:")
    # ct64 (SO)
    cur.execute("SELECT ngay_ct, so_ct, gia_nt, gia2, ma_kh FROM public.ct64 WHERE upper(trim(ma_vt)) = %s ORDER BY ngay_ct DESC LIMIT 3", (code,))
    print(f"ct64 (SO):", cur.fetchall())
    # ct81 (PXK)
    cur.execute("SELECT ngay_ct, so_ct, gia_nt, gia2, ma_kh FROM public.ct81 WHERE upper(trim(ma_vt)) = %s ORDER BY ngay_ct DESC LIMIT 3", (code,))
    print(f"ct81 (PXK):", cur.fetchall())
    # ct61 (HD)
    cur.execute("SELECT ngay_ct, so_ct, gia_nt, gia2, ma_kh FROM public.ct61 WHERE upper(trim(ma_vt)) = %s ORDER BY ngay_ct DESC LIMIT 3", (code,))
    print(f"ct61 (HD):", cur.fetchall())
