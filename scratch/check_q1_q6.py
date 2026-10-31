import psycopg2, os
conn = psycopg2.connect(
    host=os.environ.get('HTMP_DB_HOST'),
    port=os.environ.get('HTMP_DB_PORT', 5410),
    dbname=os.environ.get('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
    user=os.environ.get('HTMP_DB_USER'),
    password=os.environ.get('HTMP_DB_PASSWORD')
)
cur = conn.cursor()
print("=== Q1: BOM & NVL ===")
cur.execute("SELECT ma_vt, ten_vt, ma_nvl, dvt FROM dmvt WHERE ma_vt = 'QC7-5146-000';")
print("dmvt:", cur.fetchall())
cur.execute("SELECT ma_sp, ten_sp, bom_version, ma_vt, ten_vt, so_luong_dm, ty_le_hao_hut, ty_le_tron FROM mfkhsx_bom WHERE ma_sp = 'QC7-5146-000';")
print("mfkhsx_bom:", cur.fetchall())

print("\n=== Q6: Nhập kho 01/10/2026 - 20/10/2026 ===")
cur.execute("""
SELECT h.ngay_ct, h.so_ct, d.ma_vt, d.sl_nhap, h.ma_kho, d.ma_nx, h.user_id, coalesce(u.comment, h.user_id) as user_name
FROM ct70 d
JOIN ph70 h ON d.stt_rec = h.stt_rec
LEFT JOIN sys_dmtt u ON u.user_id = h.user_id
WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20' AND d.sl_nhap > 0
ORDER BY h.ngay_ct, h.so_ct;
""")
rows_q6 = cur.fetchall()
print(f"Total nhập kho rows: {len(rows_q6)}")
for r in rows_q6:
    print(r)

conn.close()
