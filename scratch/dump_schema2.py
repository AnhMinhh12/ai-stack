import psycopg2, os

conn = psycopg2.connect(
    dbname=os.environ.get('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    user=os.environ.get('HTMP_DB_USER', 'htmp_ro'),
    password=os.environ.get('HTMP_DB_PASSWORD', 'Htmp@2026_Secure'),
    host=os.environ.get('HTMP_DB_HOST', '10.0.6.2'),
    port=os.environ.get('HTMP_DB_PORT', '5410'),
    connect_timeout=5
)
cur = conn.cursor()

def dump_schema(t):
    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t}' ORDER BY ordinal_position;")
    cols = [f"{c[0]} ({c[1]})" for c in cur.fetchall()]
    print(f"=== {t} ===")
    print(", ".join(cols[:15]))

for t in ['mfkhsx_bom', 'phiqc', 'ctiqc', 'ph85', 'ct85', 'ph76', 'ct76']:
    dump_schema(t)
