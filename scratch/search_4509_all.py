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
        print("=== Searching for 4509 in dmhosokhuonsp ===")
        cur.execute("SELECT * FROM dmhosokhuonsp WHERE ma_khuon LIKE '%4509%' OR ma_sp LIKE '%4509%';")
        print("dmhosokhuonsp:", cur.fetchall())

        print("=== Searching for 4509 in dmvt ===")
        cur.execute("SELECT ma_vt, ten_vt FROM dmvt WHERE ma_vt LIKE '%4509%' OR ten_vt LIKE '%4509%';")
        print("dmvt:", cur.fetchall())

        print("=== Searching for 4509 in mes_oi_stop_line or other tables ===")
        cur.execute("SELECT count(*) FROM dmhosokhuon;")
        print("Total dmhosokhuon rows:", cur.fetchone())

        print("=== Check if 4509 is in userinfo / sys_dmtt ===")
        cur.execute("SELECT user_id, comment FROM sys_dmtt WHERE user_id LIKE '%4509%' OR comment ILIKE '%Trường%';")
        print("sys_dmtt:", cur.fetchall())
