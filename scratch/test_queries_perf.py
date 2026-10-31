import psycopg2, os, time

conn = psycopg2.connect(
    dbname=os.environ.get('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    user=os.environ.get('HTMP_DB_USER', 'htmp_ro'),
    password=os.environ.get('HTMP_DB_PASSWORD', 'Htmp@2026_Secure'),
    host=os.environ.get('HTMP_DB_HOST', '10.0.6.2'),
    port=os.environ.get('HTMP_DB_PORT', '5410'),
    connect_timeout=5
)
cur = conn.cursor()

def test_q(name, sql, params=None):
    t0 = time.time()
    cur.execute(sql, params or ())
    rows = cur.fetchall()
    dt = time.time() - t0
    print(f"{name}: {len(rows)} rows returned in {dt*1000:.1f}ms")

# 1. BOM
test_q("1. BOM", """
    SELECT DISTINCT b.ma_sp, b.ten_sp, b.bom_version, b.ma_vt, b.ten_vt, b.so_luong_dm, b.ty_le_hao_hut, b.ty_le_tron
    FROM public.mfkhsx_bom b
    WHERE b.ma_sp = %s
    ORDER BY b.bom_version DESC, b.ma_vt
    LIMIT 30;
""", ('009-M66-198',))

# 2. IQC
test_q("2. IQC", """
    SELECT h.so_ct, h.ngay_ct, h.ma_ncc, coalesce(k.ten_kh, h.ma_ncc) AS ten_ncc,
           h.ma_vt, coalesce(v.ten_vt, h.ma_vt) AS ten_vt, h.ma_lo,
           h.so_luong, h.so_luong_mau,
           d.ma_chi_tieu, d.gia_tri, d.ket_qua, coalesce(d.kq_danh_gia, '') AS kq_danh_gia
    FROM public.phiqc h
    JOIN public.ctiqc d USING(stt_rec)
    LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_ncc
    LEFT JOIN public.dmvt v ON v.ma_vt = h.ma_vt
    WHERE h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31' AND h.ma_ncc = 'NCC0619'
    ORDER BY h.ngay_ct DESC, h.so_ct DESC
    LIMIT 30;
""")

# 3. PXK
test_q("3. PXK", """
    SELECT h.so_ct, h.ngay_ct, h.ma_kh, coalesce(k.ten_kh, h.ma_kh) AS ten_kh,
           d.ma_vt, coalesce(v.ten_vt, d.ma_vt) AS ten_vt, d.dvt, d.so_luong,
           d.ma_kho, coalesce(d.tien2, 0) AS thanh_tien
    FROM public.ph85 h
    JOIN public.ct85 d USING(stt_rec)
    LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
    LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
    WHERE h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31'
    ORDER BY h.ngay_ct DESC, h.so_ct DESC
    LIMIT 30;
""")

# 4. Xuất kho sản xuất
test_q("4. Xuất SX", """
    SELECT h.so_ct, h.ngay_ct, h.ma_kh AS phan_xuong, coalesce(h.ten_kh, '') AS ten_xuong,
           d.ma_vt, coalesce(v.ten_vt, d.ma_vt) AS ten_vt, d.dvt, d.so_luong, d.ma_kho
    FROM public.ph76 h
    JOIN public.ct76 d USING(stt_rec)
    LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
    WHERE h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31'
    ORDER BY h.ngay_ct DESC, h.so_ct DESC
    LIMIT 30;
""")

# 5. Nhập kho thành phẩm
test_q("5. Nhập TP", """
    SELECT h.so_ct, h.ngay_ct, h.ma_kh AS phan_xuong,
           d.ma_vt, coalesce(v.ten_vt, d.ma_vt) AS ten_vt, d.dvt, d.so_luong, d.ma_kho
    FROM public.ph77 h
    JOIN public.ct77 d USING(stt_rec)
    LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
    WHERE h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31'
    ORDER BY h.ngay_ct DESC, h.so_ct DESC
    LIMIT 30;
""")

# 6. Pallet
test_q("6. Pallet", """
    SELECT p.id_pallet, p.serial_tem, p.so_luong_thung, p.so_luong AS tong_sl_pallet,
           p.ma_lo, p.ngay_sx, p.status
    FROM public.pallet p
    ORDER BY p.id_pallet DESC
    LIMIT 20;
""")
