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

print("--- 1. Materials with stock across multiple dies in intem_log ---")
cur.execute("""
    SELECT upper(trim(e->>'ma_vt')) AS ma_vt,
           count(distinct e->>'die_no') as die_count,
           sum((e->>'so_luong')::numeric) as total_qty
    FROM public.intem_log a CROSS JOIN LATERAL jsonb_array_elements(
        CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
    ) e
    WHERE a.nxt = 1 AND a.status = '1'
      AND e->>'die_no' IS NOT NULL AND e->>'die_no' != ''
    GROUP BY 1
    HAVING count(distinct e->>'die_no') >= 2
    ORDER BY total_qty DESC
    LIMIT 10
""")
multi_die = cur.fetchall()
for r in multi_die:
    print("  ", r)

print("\n--- 2. Materials with current stock in cd13 / dmvt ---")
cur.execute("""
    SELECT c.ma_vt, v.ten_vt, count(distinct c.ma_kho) as kho_count, sum(c.ton00) as ton
    FROM cd13 c
    JOIN dmvt v ON trim(c.ma_vt) = trim(v.ma_vt)
    WHERE c.ton00 > 0
    GROUP BY c.ma_vt, v.ten_vt
    HAVING count(distinct c.ma_kho) >= 2
    ORDER BY ton DESC
    LIMIT 10
""")
multi_kho = cur.fetchall()
for r in multi_kho:
    print("  ", r)

print("\n--- 3. Materials with imports in October 2026 (ct70/ph70) ---")
cur.execute("""
    SELECT trim(d.ma_vt) as ma_vt, trim(v.ten_vt) as ten_vt, count(distinct h.ngay_ct) as days, sum(d.sl_nhap) as sl
    FROM ct70 d
    JOIN ph70 h ON d.stt_rec = h.stt_rec
    JOIN dmvt v ON trim(d.ma_vt) = trim(v.ma_vt)
    WHERE h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-25'
    GROUP BY trim(d.ma_vt), trim(v.ten_vt)
    HAVING count(distinct h.ngay_ct) >= 2
    ORDER BY sl DESC
    LIMIT 10
""")
recent_imports = cur.fetchall()
for r in recent_imports:
    print("  ", r)

print("\n--- 4. Materials with sales in October 2026 (ct81/ph81) ---")
cur.execute("""
    SELECT trim(d.ma_vt) as ma_vt, trim(v.ten_vt) as ten_vt, count(distinct h.ngay_ct) as days, sum(d.sl_xuat) as sl, sum(d.tien2) as rev
    FROM ct81 d
    JOIN ph81 h ON d.stt_rec = h.stt_rec
    JOIN dmvt v ON trim(d.ma_vt) = trim(v.ma_vt)
    WHERE h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-25'
    GROUP BY trim(d.ma_vt), trim(v.ten_vt)
    HAVING count(distinct h.ngay_ct) >= 2
    ORDER BY sl DESC
    LIMIT 10
""")
recent_sales = cur.fetchall()
for r in recent_sales:
    print("  ", r)

print("\n--- 5. Materials with BOM components (v_bom / ct00) ---")
cur.execute("""
    SELECT trim(ma_vt_me) as ma_vt_me, count(*) as count
    FROM (
        SELECT distinct ma_vt_me, ma_vt_con FROM ct00 WHERE ma_vt_me != ''
    ) t
    GROUP BY 1
    HAVING count(*) >= 3
    ORDER BY count DESC
    LIMIT 10
""")
boms = cur.fetchall()
for r in boms:
    print("  ", r)

print("\n--- 6. Random Customers (dmkh) with active orders ---")
cur.execute("""
    SELECT trim(h.ma_kh) as ma_kh, trim(k.ten_kh) as ten_kh, count(distinct h.so_ct) as orders
    FROM ph64 h
    JOIN dmkh k ON trim(h.ma_kh) = trim(k.ma_kh)
    WHERE h.ngay_ct >= '2026-08-01'
    GROUP BY 1, 2
    ORDER BY orders DESC
    LIMIT 10
""")
customers = cur.fetchall()
for r in customers:
    print("  ", r)

conn.close()
