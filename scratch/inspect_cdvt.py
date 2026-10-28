import psycopg
conn = psycopg.connect('host=10.0.6.2 port=5410 dbname=3SERP_HTMP_DATA user=read_htmp password=P@ss@Htmp@W0rd!2025')
cur = conn.cursor()
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'cdvt' 
    ORDER BY ordinal_position
""")
print("=== cdvt columns ===")
for r in cur.fetchall():
    print(r[0], r[1])

cur.execute("""
    SELECT nam, ma_kho, ton00
    FROM cdvt 
    WHERE upper(trim(ma_vt)) = 'QC7-5146-000'
""")
print("=== cdvt rows for QC7-5146-000 ===")
for r in cur.fetchall():
    print(r)
