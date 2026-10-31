import psycopg2, os

conn = psycopg2.connect(
    dbname=os.environ.get('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    user=os.environ.get('HTMP_DB_USER', 'htmp_ro'),
    password=os.environ.get('HTMP_DB_PASSWORD', 'Htmp@2026_Secure'),
    host=os.environ.get('HTMP_DB_HOST', '10.0.6.2'),
    port=os.environ.get('HTMP_DB_PORT', '5410'),
    connect_timeout=5
)
cur = conn.cursor()

# Test 1: BOM (mfkhsx_bom)
cur.execute('SELECT ma_sp, ten_sp, bom_version, ma_vt, ten_vt, so_luong_dm FROM mfkhsx_bom LIMIT 3;')
print('--- TEST BOM ---')
for r in cur.fetchall():
    print(r)

# Test 2: IQC (phiqc + ctiqc)
cur.execute('''
    SELECT h.so_ct, h.ngay_ct, h.ma_ncc, d.ma_chi_tieu, d.gia_tri 
    FROM phiqc h 
    JOIN ctiqc d USING(stt_rec) 
    ORDER BY h.ngay_ct DESC LIMIT 3;
''')
print('--- TEST IQC ---')
for r in cur.fetchall():
    print(r)

# Test 3: ph85 + ct85 (Bảng kê xuất kho bán hàng)
cur.execute('''
    SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.ma_kho
    FROM ph85 h
    JOIN ct85 d USING(stt_rec)
    ORDER BY h.ngay_ct DESC LIMIT 3;
''')
print('--- TEST PXK BAN HANG ph85/ct85 ---')
for r in cur.fetchall():
    print(r)

# Test 4: Xuất kho sản xuất ph76/ct76
cur.execute('''
    SELECT h.so_ct, h.ngay_ct, d.ma_vt, d.so_luong, d.ma_kho
    FROM ph76 h
    JOIN ct76 d USING(stt_rec)
    ORDER BY h.ngay_ct DESC LIMIT 3;
''')
print('--- TEST XUAT KHO SAN XUAT ph76/ct76 ---')
for r in cur.fetchall():
    print(r)

# Test 5: Nhập kho thành phẩm ph77/ct77
cur.execute('''
    SELECT h.so_ct, h.ngay_ct, d.ma_vt, d.ma_kho
    FROM ph77 h
    JOIN ct77 d USING(stt_rec)
    ORDER BY h.ngay_ct DESC LIMIT 3;
''')
print('--- TEST NHAP KHO THANH PHAM ph77/ct77 ---')
for r in cur.fetchall():
    print(r)
