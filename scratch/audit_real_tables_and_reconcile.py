import os, sys, json
sys.path.insert(0, '/home/admin/ai-stack')
import psycopg
from psycopg.rows import dict_row

os.environ["HTMP_DB_PORT"] = "5410"
from functions.htmp_postgres_query import Tools

tools = Tools()

conn = psycopg.connect(
    host="10.0.6.2", port=5410, user="read_htmp", password="P@ss@Htmp@W0rd!2025", dbname="3SERP_HTMP_DATA"
)

# Test and verify Q08: Mua hang PS-576D
with conn.cursor() as cur:
    print("=== Q08: Lịch sử mua hàng PS-576D ===")
    cur.execute("""
        SELECT count(*) AS so_lan_mua, min(d.gia0) AS gia_min, max(d.gia0) AS gia_max, avg(d.gia0) AS gia_avg
        FROM public.ph61 h
        JOIN public.ct61 d USING (stt_rec)
        WHERE d.ma_vt = 'PS-576D' AND h.status::text NOT IN ('14', '15');
    """)
    print("DB truth:", cur.fetchone())

    print("\n=== Q09: Lỗi NG theo máy ===")
    cur.execute("""
        SELECT count(*) as total_records FROM information_schema.tables WHERE table_name IN ('mfdongmay_ng', 'mfstopline', 'mfkhsx');
    """)
    print("Tables exist:", cur.fetchall())

    print("\n=== Q34: Khuôn K_VGY1A061 ===")
    cur.execute("""
        SELECT ma_khuon, ten_khuon, sl_shot_dm, status FROM public.dmkhuon WHERE ma_khuon = 'K_VGY1A061';
    """)
    print("DB truth:", cur.fetchone())

    print("\n=== Q39: Bảng giá hiện hành ===")
    cur.execute("""
        SELECT count(*) FROM public.dmbanggia;
    """)
    print("Total bang gia:", cur.fetchone())

    print("\n=== Q40: BOM mã QC7-5146-000 ===")
    cur.execute("""
        SELECT ma_vt, ma_nvl, he_so FROM public.mfbom_material WHERE ma_vt = 'QC7-5146-000' LIMIT 5;
    """)
    print("BOM:", cur.fetchall())

    print("\n=== Q42: Quản lý mã QC7-5146-000 ===")
    cur.execute("""
        SELECT v.ma_vt, v.ten_vt, v.ma_kh, k.ten_kh 
        FROM public.dmvt v 
        LEFT JOIN public.dmkh k ON k.ma_kh = v.ma_kh 
        WHERE v.ma_vt = 'QC7-5146-000';
    """)
    print("Khach hang quan ly:", cur.fetchone())
