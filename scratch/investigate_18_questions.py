import os
import psycopg2
import psycopg2.extras
import json

ERP_CONN = {
    "host": "10.0.6.2",
    "port": 5410,
    "dbname": "3SERP_HTMP_DATA",
    "user": "read_htmp",
    "password": "Read@HTMP#2026!SafePassword",
    "connect_timeout": 5
}

def get_conn():
    return psycopg2.connect(**ERP_CONN)

def run_query(conn, sql, params=None):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params or {})
        return cur.fetchall()

def search_tables(conn, pattern):
    sql = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name ILIKE %s
        ORDER BY table_name;
    """
    return [r['table_name'] for r in run_query(conn, sql, [f"%{pattern}%"])]

def main():
    conn = get_conn()
    print("Connected successfully!")
    
    # Check tables related to BOM, FCST, DO, QC
    patterns = ['bom', 'fcst', 'do', 'qc', 'carton', 'dong_goi', 'thung', 'lo', 'khuon', 'gia']
    for p in patterns:
        tables = search_tables(conn, p)
        print(f"Pattern '{p}': {tables[:10]}")

    conn.close()

if __name__ == '__main__':
    main()
