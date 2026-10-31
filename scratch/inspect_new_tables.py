import psycopg2, os, json

conn = psycopg2.connect(
    dbname=os.environ.get('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    user=os.environ.get('HTMP_DB_USER', 'htmp_ro'),
    password=os.environ.get('HTMP_DB_PASSWORD', 'Htmp@2026_Secure'),
    host=os.environ.get('HTMP_DB_HOST', '10.0.6.2'),
    port=os.environ.get('HTMP_DB_PORT', '5410'),
    connect_timeout=5
)
cur = conn.cursor()

def inspect_table(table_name):
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = '{table_name}'
        ORDER BY ordinal_position;
    """)
    cols = cur.fetchall()
    cur.execute(f"SELECT * FROM {table_name} LIMIT 1;")
    sample = cur.fetchone()
    print(f"\n=== TABLE: {table_name} ({len(cols)} cols) ===")
    for col, val in zip(cols, sample if sample else []):
        print(f"  {col[0]} ({col[1]}): {repr(val)[:60]}")

tables = ['mfkhsx_bom', 'phiqc', 'ctiqc', 'ph85', 'ct85', 'ph76', 'ct76', 'ph77', 'ct77', 'pallet', 'palletct']
for t in tables:
    inspect_table(t)
