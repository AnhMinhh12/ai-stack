import psycopg

def get_connection():
    return psycopg.connect(
        host='10.0.6.2',
        port=5410,
        dbname='3SERP_HTMP_DATA',
        user='read_htmp',
        password='P@ss@Htmp@W0rd!2025',
        connect_timeout=3
    )

def main():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '3s'")
    cur.execute("SET lock_timeout = '2s'")
    
    tables = ['mes_oi_dong_thung', 'mes_oi_dong_thung1', 'mes_oi_bo_shot', 'intem_carton_log']
    for t in tables:
        cur.execute("""
            SELECT a.attname, format_type(a.atttypid, a.atttypmod)
            FROM pg_attribute a
            JOIN pg_class c ON c.oid = a.attrelid
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = %s AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY a.attnum;
        """, (t,))
        cols = cur.fetchall()
        print(f'=== TABLE: {t} ({len(cols)} columns) ===')
        for c, dt in cols:
            print(f'  {c}: {dt}')

    conn.close()

if __name__ == '__main__':
    main()
