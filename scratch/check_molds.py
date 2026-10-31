import psycopg
import os

def connection_settings():
    return {
        "host": os.getenv("HTMP_DB_HOST"),
        "port": os.getenv("HTMP_DB_PORT", "5410"),
        "dbname": os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
        "user": os.getenv("HTMP_DB_USER"),
        "password": os.getenv("HTMP_DB_PASSWORD"),
        "connect_timeout": int(os.getenv("HTMP_DB_CONNECT_TIMEOUT_SECONDS", "5")),
    }

conn = psycopg.connect(**connection_settings())
with conn.cursor() as c:
    print("\n--- Search 25HI in dmhosokhuon (ma_khuon, ten_khuon, ma_hi) ---")
    c.execute("""
        SELECT ma_khuon, ten_khuon, ma_hi, so_cavity, tong_so_shot, status 
        FROM dmhosokhuon 
        WHERE ma_khuon ILIKE '%25HI%' OR ten_khuon ILIKE '%25HI%' OR ma_hi ILIKE '%25HI%'
        LIMIT 30
    """)
    for r in c.fetchall():
        print('  ', r)

    print("\n--- Search 117 in dmhosokhuon (ma_khuon, ten_khuon, ma_hi) ---")
    c.execute("""
        SELECT ma_khuon, ten_khuon, ma_hi, so_cavity, tong_so_shot, status 
        FROM dmhosokhuon 
        WHERE ma_khuon ILIKE '%117%' OR ten_khuon ILIKE '%117%' OR ma_hi ILIKE '%117%'
        LIMIT 30
    """)
    for r in c.fetchall():
        print('  ', r)
