import os
import psycopg

conn = psycopg.connect(
    host=os.getenv("HTMP_DB_HOST", "10.0.6.2"),
    port=os.getenv("HTMP_DB_PORT", "5410"),
    dbname=os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
    user=os.getenv("HTMP_DB_USER", "read_htmp"),
    password=os.getenv("HTMP_DB_PASSWORD", "P@ss@Htmp@W0rd!2025"),
    connect_timeout=10,
)
cursor = conn.cursor()

material_code = "01K-2A00C-0000-1"

# 1. Test sys_getstartdate
cursor.execute("SELECT public.sys_getstartdate(CURRENT_DATE)")
start_date = cursor.fetchone()[0]
print(f"sys_getstartdate(CURRENT_DATE): {start_date}")

# 2. Test query with make_date(extract(year...)) -> OLD BUGGY QUERY
cursor.execute("""
    WITH opening AS (
        SELECT c.ma_kho, sum(c.ton00) AS qty
        FROM public.cdvt c
        WHERE c.nam = extract(year FROM CURRENT_DATE)::smallint
          AND upper(trim(c.ma_vt)) = %s
        GROUP BY c.ma_kho
    ),
    movements AS (
        SELECT c.ma_kho, sum(c.sl_nhap - c.sl_xuat) AS qty
        FROM public.ct70 c
        WHERE upper(trim(c.ma_vt)) = %s
          AND c.ngay_ct >= make_date(extract(year FROM CURRENT_DATE)::integer, 1, 1)
        GROUP BY c.ma_kho
    ),
    combined AS (
        SELECT ma_kho, qty FROM opening
        UNION ALL
        SELECT ma_kho, qty FROM movements
    )
    SELECT ma_kho, sum(qty) AS ton_kho
    FROM combined
    GROUP BY ma_kho
    HAVING sum(qty) > 0
    ORDER BY ton_kho DESC
""", (material_code, material_code))
old_rows = cursor.fetchall()
print(f"OLD QUERY RESULTS for {material_code}: {old_rows}")

# 3. Test query with public.sys_getstartdate(CURRENT_DATE) -> NEW FIXED QUERY
cursor.execute("""
    WITH opening AS (
        SELECT c.ma_kho, sum(c.ton00) AS qty
        FROM public.cdvt c
        WHERE c.nam = extract(year FROM CURRENT_DATE)::smallint
          AND upper(trim(c.ma_vt)) = %s
        GROUP BY c.ma_kho
    ),
    movements AS (
        SELECT c.ma_kho, sum(c.sl_nhap - c.sl_xuat) AS qty
        FROM public.ct70 c
        WHERE upper(trim(c.ma_vt)) = %s
          AND c.ngay_ct >= public.sys_getstartdate(CURRENT_DATE)
        GROUP BY c.ma_kho
    ),
    combined AS (
        SELECT ma_kho, qty FROM opening
        UNION ALL
        SELECT ma_kho, qty FROM movements
    )
    SELECT ma_kho, sum(qty) AS ton_kho
    FROM combined
    GROUP BY ma_kho
    HAVING sum(qty) > 0
    ORDER BY ton_kho DESC
""", (material_code, material_code))
new_rows = cursor.fetchall()
print(f"NEW QUERY RESULTS for {material_code}: {new_rows}")

# 4. Compare with ERP stored procedure inbctontheokho
cursor.execute("SELECT * FROM public.inbctontheokho('2026-01-01'::date, '2026-11-06'::date, %s, '', '', '1')", (material_code,))
erp_rows = cursor.fetchall()
print(f"ERP STORED FUNCTION RESULTS: {[(r[0], r[1], r[2], r[6], r[7], r[8]) for r in erp_rows]}")

conn.close()
