import psycopg
conn = psycopg.connect('host=10.0.6.2 port=5410 dbname=3SERP_HTMP_DATA user=read_htmp password=P@ss@Htmp@W0rd!2025')
cur = conn.cursor()
cur.execute("""
    SELECT ma_kho, sum(ton_dau + du_nhap - du_xuat) as ton 
    FROM cdvt2026 
    WHERE upper(trim(ma_vt)) = 'QC7-5146-000' 
    GROUP BY ma_kho 
    HAVING sum(ton_dau + du_nhap - du_xuat) > 0 
    ORDER BY ton DESC
""")
print("=== cdvt2026 ===")
rows = cur.fetchall()
for r in rows:
    print(r)
print("Total cdvt2026:", sum(r[1] for r in rows))
