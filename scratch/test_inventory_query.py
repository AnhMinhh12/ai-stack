import psycopg

conn = psycopg.connect('host=10.0.6.2 port=5410 dbname=3SERP_HTMP_DATA user=read_htmp password=P@ss@Htmp@W0rd!2025')
cur = conn.cursor()
material_code = "QC7-5146-000"

cur.execute("""
    WITH opening AS (
        SELECT c.ma_kho, sum(c.ton00) AS qty
        FROM public.cdvt c
        WHERE c.nam = 2026
          AND upper(trim(c.ma_vt)) = %s
        GROUP BY c.ma_kho
    ),
    movements AS (
        SELECT c.ma_kho, sum(c.sl_nhap - c.sl_xuat) AS qty
        FROM public.ct70 c
        WHERE upper(trim(c.ma_vt)) = %s
          AND c.ngay_ct >= '2026-01-01'::date
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

rows = cur.fetchall()
print(f"=== Inventory by warehouse for {material_code} ===")
for r in rows:
    print(r)
print("Total:", sum(r[1] for r in rows))
