import psycopg2, os, json

conn = psycopg2.connect(
    dbname=os.environ.get('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    user=os.environ.get('HTMP_DB_USER', 'htmp_ro'),
    password=os.environ.get('HTMP_DB_PASSWORD', 'Htmp@2026_Secure'),
    host=os.environ.get('HTMP_DB_HOST', '10.0.6.2'),
    port=os.environ.get('HTMP_DB_PORT', '5410'),
    connect_timeout=5
)
cur = conn.cursor()

print("--- 1. TEST mfkhsx_bom ---")
cur.execute("""
    SELECT b.ma_sp, b.ten_sp, b.bom_version, b.ma_vt, b.ten_vt, b.so_luong_dm, b.ty_le_hao_hut, b.ty_le_tron
    FROM public.mfkhsx_bom b
    WHERE upper(trim(b.ma_sp)) = '009-M66-198'
    ORDER BY b.bom_version DESC, b.ma_vt;
""")
for r in cur.fetchall():
    print(r)

print("\n--- 2. TEST phiqc + ctiqc ---")
cur.execute("""
    SELECT h.so_ct, h.ngay_ct, h.ma_ncc, coalesce(k.ten_kh, h.ma_ncc) AS ten_ncc,
           h.ma_vt, coalesce(v.ten_vt, h.ma_vt) AS ten_vt, h.ma_lo, h.so_luong,
           d.ma_chi_tieu, d.gia_tri, d.ket_qua, d.kq_danh_gia
    FROM public.phiqc h
    JOIN public.ctiqc d USING(stt_rec)
    LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_ncc
    LEFT JOIN public.dmvt v ON v.ma_vt = h.ma_vt
    WHERE h.ngay_ct >= '2026-10-01'
    ORDER BY h.ngay_ct DESC, h.so_ct DESC
    LIMIT 3;
""")
for r in cur.fetchall():
    print(r)

print("\n--- 3. TEST ph85 + ct85 (PXK) ---")
cur.execute("""
    SELECT h.so_ct, h.ngay_ct, h.ma_kh, coalesce(k.ten_kh, h.ma_kh) AS ten_kh,
           d.ma_vt, coalesce(v.ten_vt, d.ma_vt) AS ten_vt, d.dvt, d.so_luong, d.ma_kho
    FROM public.ph85 h
    JOIN public.ct85 d USING(stt_rec)
    LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
    LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
    WHERE h.ngay_ct >= '2026-10-01'
    ORDER BY h.ngay_ct DESC, h.so_ct DESC
    LIMIT 3;
""")
for r in cur.fetchall():
    print(r)

print("\n--- 4. TEST ph76 + ct76 (Xuất kho SX) ---")
cur.execute("""
    SELECT h.so_ct, h.ngay_ct, h.ma_kh, coalesce(h.ten_kh, '') AS ten_kh,
           d.ma_vt, coalesce(v.ten_vt, d.ma_vt) AS ten_vt, d.dvt, d.so_luong, d.ma_kho
    FROM public.ph76 h
    JOIN public.ct76 d USING(stt_rec)
    LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
    WHERE h.ngay_ct >= '2026-10-01'
    ORDER BY h.ngay_ct DESC, h.so_ct DESC
    LIMIT 3;
""")
for r in cur.fetchall():
    print(r)

print("\n--- 5. TEST pallet + palletct ---")
cur.execute("""
    SELECT p.id_pallet, p.so_luong_thung, p.so_luong AS tong_sl_pallet,
           p.ma_lo, p.ngay_sx, p.status, c.id_carton, c.ma_vt, c.dvt, c.so_luong AS sl_thung
    FROM public.pallet p
    JOIN public.palletct c ON c.id_pallet = p.id_pallet
    WHERE p.ngay_sx >= '2026-01-01'
    ORDER BY p.ngay_sx DESC
    LIMIT 3;
""")
for r in cur.fetchall():
    print(r)
