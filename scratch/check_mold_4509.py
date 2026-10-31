import psycopg, os

settings = {
    "host": os.getenv("HTMP_DB_HOST"),
    "port": os.getenv("HTMP_DB_PORT", "5410"),
    "dbname": os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
    "user": os.getenv("HTMP_DB_USER"),
    "password": os.getenv("HTMP_DB_PASSWORD"),
    "connect_timeout": 5,
}

with psycopg.connect(**settings) as conn:
    with conn.cursor() as cur:
        print("=== Searching for 4509 in dmhosokhuon ===")
        cur.execute("SELECT ma_khuon, ten_khuon, so_cavity, so_shot_bh, tinh_trang_khuon FROM dmhosokhuon WHERE ma_khuon LIKE '%4509%' OR ten_khuon LIKE '%4509%';")
        r1 = cur.fetchall()
        print(f"Found {len(r1)} molds matching 4509:")
        for r in r1:
            print(r)

        print("\n=== Searching for 101 40481 01 ===")
        cur.execute("SELECT ma_khuon, ten_khuon, so_cavity, so_shot_bh, tinh_trang_khuon FROM dmhosokhuon WHERE ma_khuon ILIKE '%101%40481%' OR ten_khuon ILIKE '%101%40481%';")
        r2 = cur.fetchall()
        print(f"Found {len(r2)} molds matching 101 40481:")
        for r in r2:
            print(r)
