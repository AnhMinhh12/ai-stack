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
    # 1. Search for 4509 or Truong across ERP tables
    print("=== Search 4509 across employee / user tables ===")
    c.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
          AND (table_name ILIKE '%user%' OR table_name ILIKE '%nv%' OR table_name ILIKE '%cbcnv%' OR table_name ILIKE '%nhanvien%' OR table_name ILIKE '%ns%')
    """)
    tables = c.fetchall()
    print("Candidate tables:", [t[0] for t in tables])
    
    for t in [t[0] for t in tables]:
        try:
            c.execute(f"SELECT * FROM public.{t} LIMIT 1")
            col_names = [desc[0] for desc in c.description]
            # search columns for 4509
            for col in col_names:
                try:
                    c.execute(f"SELECT {col} FROM public.{t} WHERE cast({col} as text) ILIKE '%4509%' LIMIT 3")
                    matches = c.fetchall()
                    if matches:
                        print(f"MATCH in {t}.{col}: {matches}")
                except Exception:
                    pass
        except Exception:
            pass

    # 2. Check mold with highest tong_so_shot
    print("\n=== Top molds with highest tong_so_shot ===")
    c.execute("""
        SELECT ma_khuon, ten_khuon, tong_so_shot, so_shot_bh, tinh_trang_khuon, status
        FROM public.dmhosokhuon
        WHERE tong_so_shot IS NOT NULL AND tong_so_shot > 0
        ORDER BY tong_so_shot DESC
        LIMIT 5
    """)
    for r in c.fetchall():
        print("  ", r)

    # 3. Check 25HI117 details
    print("\n=== Mold 25HI117 details ===")
    c.execute("""
        SELECT ma_khuon, ten_khuon, ma_hi, so_cavity, so_shot_bh, tong_so_shot, tinh_trang_khuon, status, ngay
        FROM public.dmhosokhuon
        WHERE ma_khuon ILIKE '%25HI117%' OR ten_khuon ILIKE '%25HI117%'
    """)
    for r in c.fetchall():
        print("  ", r)
