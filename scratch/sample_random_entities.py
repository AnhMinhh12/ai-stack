import psycopg2, os, json, random

conn = psycopg2.connect(
    dbname=os.environ.get('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    user=os.environ.get('HTMP_DB_USER', 'htmp_ro'),
    password=os.environ.get('HTMP_DB_PASSWORD', 'Htmp@2026_Secure'),
    host=os.environ.get('HTMP_DB_HOST', '10.0.6.2'),
    port=os.environ.get('HTMP_DB_PORT', '5410'),
    connect_timeout=5
)
cur = conn.cursor()

entities = {}

# 1. Random product with BOM from mfkhsx_bom
cur.execute("""
    SELECT ma_sp, ten_sp, count(*) as num_materials
    FROM public.mfkhsx_bom
    GROUP BY ma_sp, ten_sp
    HAVING count(*) >= 2
    ORDER BY random()
    LIMIT 3;
""")
entities['bom_products'] = cur.fetchall()

# 2. Random supplier and material from phiqc
cur.execute("""
    SELECT ma_ncc, ten_kh, ma_vt, ten_vt
    FROM (
        SELECT DISTINCT h.ma_ncc, k.ten_kh, h.ma_vt, v.ten_vt
        FROM public.phiqc h
        JOIN public.ctiqc d USING(stt_rec)
        LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_ncc
        LEFT JOIN public.dmvt v ON v.ma_vt = h.ma_vt
        WHERE h.ngay_ct >= '2026-10-01'
    ) sub
    ORDER BY random()
    LIMIT 3;
""")
entities['iqc_samples'] = cur.fetchall()

# 3. Random PXK from ph85/ct85
cur.execute("""
    SELECT so_ct, ngay_ct, ma_vt, ten_vt
    FROM (
        SELECT DISTINCT h.so_ct, h.ngay_ct, d.ma_vt, v.ten_vt
        FROM public.ph85 h
        JOIN public.ct85 d USING(stt_rec)
        LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
        WHERE h.ngay_ct >= '2026-10-20'
    ) sub
    ORDER BY random()
    LIMIT 3;
""")
entities['pxk_samples'] = cur.fetchall()

# 4. Random Xuất SX & Nhập TP from ph76/ct76 and ph77/ct77
cur.execute("""
    SELECT so_ct, ngay_ct, ma_vt, ten_vt, ma_kho
    FROM (
        SELECT DISTINCT h.so_ct, h.ngay_ct, d.ma_vt, v.ten_vt, d.ma_kho
        FROM public.ph76 h
        JOIN public.ct76 d USING(stt_rec)
        LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
        WHERE h.ngay_ct >= '2026-10-20'
    ) sub
    ORDER BY random()
    LIMIT 2;
""")
entities['xuat_sx_samples'] = cur.fetchall()

cur.execute("""
    SELECT so_ct, ngay_ct, ma_vt, ten_vt, ma_kho
    FROM (
        SELECT DISTINCT h.so_ct, h.ngay_ct, d.ma_vt, v.ten_vt, d.ma_kho
        FROM public.ph77 h
        JOIN public.ct77 d USING(stt_rec)
        LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
        WHERE h.ngay_ct >= '2026-10-20'
    ) sub
    ORDER BY random()
    LIMIT 2;
""")
entities['nhap_tp_samples'] = cur.fetchall()

# 5. Random Pallet from pallet
cur.execute("""
    SELECT id_pallet, so_luong_thung, so_luong, ma_lo, ngay_sx
    FROM public.pallet
    WHERE ngay_sx >= '2026-10-20' AND so_luong > 0
    ORDER BY random()
    LIMIT 3;
""")
entities['pallet_samples'] = cur.fetchall()

# 6. Random Mold from dmhosokhuon
cur.execute("""
    SELECT ma_khuon, ten_khuon, so_shot_bh, so_cavity
    FROM public.dmhosokhuon
    WHERE so_shot_bh > 0
    ORDER BY random()
    LIMIT 3;
""")
entities['mold_samples'] = cur.fetchall()

# 7. Random SO from ph64/ct64
cur.execute("""
    SELECT so_ct, ma_kh, ten_kh, ma_vt
    FROM (
        SELECT DISTINCT h.so_ct, h.ma_kh, k.ten_kh, d.ma_vt
        FROM public.ph64 h
        JOIN public.ct64 d USING(stt_rec)
        LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
        WHERE h.ngay_ct >= '2026-10-01' AND h.status NOT IN ('14', '15')
    ) sub
    ORDER BY random()
    LIMIT 3;
""")
entities['so_samples'] = cur.fetchall()

print("SAMPLED ENTITIES:")
for k, v in entities.items():
    print(f"\n=== {k} ===")
    for item in v:
        print(item)

with open('/tmp/sampled_entities.json', 'w', encoding='utf-8') as f:
    json.dump(entities, f, ensure_ascii=False, indent=2, default=str)
