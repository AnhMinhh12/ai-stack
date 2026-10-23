import psycopg
import os

conn_params = {
    'host': os.getenv('HTMP_DB_HOST', '10.0.6.2'),
    'port': os.getenv('HTMP_DB_PORT', '5410'),
    'dbname': os.getenv('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    'user': os.getenv('HTMP_DB_USER', 'read_htmp'),
    'password': os.getenv('HTMP_DB_PASSWORD', 'P@ss@Htmp@W0rd!2025'),
    'connect_timeout': 5
}

with psycopg.connect(**conn_params) as conn:
    with conn.cursor() as cur:
        # Check a specific report function
        cur.execute("""
            SELECT p.proname, pg_get_functiondef(p.oid)
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'public' AND p.proname IN ('arso1', 'bcnxtserialcarton')
            LIMIT 2;
        """)
        for name, defn in cur.fetchall():
            print(f"=== FUNCTION: {name} ===")
            print(defn[:800])
            print("...")
