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
    print("=== TOP 5 MOLDS BY TONG_SO_SHOT ===")
    c.execute("""
        SELECT ma_khuon, ten_khuon, tong_so_shot, so_shot_bh, tinh_trang_khuon
        FROM public.dmhosokhuon
        WHERE tong_so_shot IS NOT NULL AND tong_so_shot > 0
        ORDER BY tong_so_shot DESC
        LIMIT 5
    """)
    for r in c.fetchall():
        print("  ", r)

    print("\n=== MOLD 25HI117 ===")
    c.execute("""
        SELECT ma_khuon, ten_khuon, ma_hi, so_cavity, so_shot_bh, tong_so_shot, tinh_trang_khuon, status
        FROM public.dmhosokhuon
        WHERE ma_khuon ILIKE '%25HI117%' OR ten_khuon ILIKE '%25HI117%'
    """)
    for r in c.fetchall():
        print("  ", r)

    print("\n=== MOLD 25HI83 ===")
    c.execute("""
        SELECT ma_khuon, ten_khuon, ma_hi, so_cavity, so_shot_bh, tong_so_shot, tinh_trang_khuon, status
        FROM public.dmhosokhuon
        WHERE ma_khuon ILIKE '%25HI83%' OR ten_khuon ILIKE '%25HI83%'
    """)
    for r in c.fetchall():
        print("  ", r)
