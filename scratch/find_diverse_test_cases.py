import psycopg

conn = psycopg.connect(
    host='10.0.6.2',
    port=5410,
    dbname='3SERP_HTMP_DATA',
    user='read_htmp',
    password='P@ss@Htmp@W0rd!2025',
    connect_timeout=5
)
cur = conn.cursor()

# 1. Multi-die material
cur.execute("""
    SELECT upper(trim(e->>'ma_vt')) AS ma_vt, count(distinct e->>'die_no') as dies, sum((e->>'so_luong')::numeric) as qty
    FROM public.intem_log a CROSS JOIN LATERAL jsonb_array_elements(
        CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
    ) e
    WHERE a.nxt = 1 AND a.status = '1' AND e->>'die_no' IS NOT NULL AND e->>'die_no' != ''
    GROUP BY 1 HAVING count(distinct e->>'die_no') >= 2
    ORDER BY qty DESC LIMIT 3
""")
print("Die cases:", cur.fetchall())

# 2. Material with warehouse stock in cdvt
cur.execute("""
    SELECT trim(ma_vt), count(distinct ma_kho), sum(ton00)
    FROM cdvt
    WHERE ton00 > 0
    GROUP BY trim(ma_vt) HAVING count(distinct ma_kho) >= 2
    ORDER BY sum(ton00) DESC LIMIT 3
""")
print("Stock by warehouse cases:", cur.fetchall())

# 3. Inbound receipts in ct70
cur.execute("""
    SELECT trim(d.ma_vt), trim(v.ten_vt), count(distinct h.ngay_ct), sum(d.sl_nhap)
    FROM ct70 d
    JOIN ph70 h ON d.stt_rec = h.stt_rec
    JOIN dmvt v ON trim(d.ma_vt) = trim(v.ma_vt)
    WHERE h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-25'
    GROUP BY 1, 2 HAVING count(distinct h.ngay_ct) >= 2
    ORDER BY sum(d.sl_nhap) DESC LIMIT 3
""")
print("Inbound receipt cases:", cur.fetchall())

# 4. Outbound sales in ct81
cur.execute("""
    SELECT trim(d.ma_vt), trim(v.ten_vt), count(distinct h.ngay_ct), sum(d.sl_xuat), sum(d.tien2)
    FROM ct81 d
    JOIN ph81 h ON d.stt_rec = h.stt_rec
    JOIN dmvt v ON trim(d.ma_vt) = trim(v.ma_vt)
    WHERE h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-25'
    GROUP BY 1, 2 HAVING count(distinct h.ngay_ct) >= 2
    ORDER BY sum(d.sl_xuat) DESC LIMIT 3
""")
print("Outbound sales cases:", cur.fetchall())

# 5. BOM structure
cur.execute("""
    SELECT trim(ma_vt_me), count(*)
    FROM (SELECT distinct ma_vt_me, ma_vt_con FROM ct00 WHERE ma_vt_me != '') t
    GROUP BY 1 HAVING count(*) >= 3
    ORDER BY count DESC LIMIT 3
""")
print("BOM cases:", cur.fetchall())

# 6. Customer order history
cur.execute("""
    SELECT trim(h.ma_kh), trim(k.ten_kh), count(distinct h.so_ct)
    FROM ph64 h JOIN dmkh k ON trim(h.ma_kh) = trim(k.ma_kh)
    WHERE h.ngay_ct >= '2026-08-01'
    GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 3
""")
print("Customer cases:", cur.fetchall())

# 7. Price list & MOQ
cur.execute("""
    SELECT trim(ma_vt), count(*)
    FROM ct61
    GROUP BY 1 HAVING count(*) >= 2
    LIMIT 3
""")
print("Price/MOQ cases:", cur.fetchall())

# 8. QC status
cur.execute("""
    SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '%qc%' LIMIT 10
""")
print("QC tables:", cur.fetchall())

conn.close()
