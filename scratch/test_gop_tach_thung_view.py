import psycopg
from psycopg.rows import dict_row

conn = psycopg.connect(
    host='10.0.6.2',
    port=5410,
    dbname='3SERP_HTMP_DATA',
    user='read_htmp',
    password='P@ss@Htmp@W0rd!2025',
    connect_timeout=3
)
cur = conn.cursor(row_factory=dict_row)
cur.execute("SET statement_timeout = '5s'")

cur.execute("""
    WITH carton_details AS (
        SELECT 
            c.date0 AS ngay_ghi_nhan,
            c.time0 AS gio_tao,
            c.id_carton AS id_tem_cu,
            c.id_carton_new AS id_tem_moi,
            e_cu->>'ma_vt' AS ma_sp,
            e_cu->>'ten_vt' AS ten_sp,
            e_cu->>'dvt' AS dvt,
            e_cu->>'ma_thung' AS ma_thung_cu,
            (e_cu->>'so_luong')::numeric AS sl_cu,
            e_moi->>'ma_thung' AS ma_thung_moi,
            (e_moi->>'so_luong')::numeric AS sl_moi,
            u.user_name AS user_tao
        FROM public.intem_carton_log c
        LEFT JOIN public.intem_log l_cu ON l_cu.id_tem = c.id_carton
        LEFT JOIN LATERAL jsonb_array_elements(
            CASE WHEN jsonb_typeof(l_cu.data_tem) = 'array' THEN l_cu.data_tem ELSE '[]'::jsonb END
        ) e_cu ON true
        LEFT JOIN public.intem_log l_moi ON l_moi.id_tem = c.id_carton_new
        LEFT JOIN LATERAL jsonb_array_elements(
            CASE WHEN jsonb_typeof(l_moi.data_tem) = 'array' THEN l_moi.data_tem ELSE '[]'::jsonb END
        ) e_moi ON true
        LEFT JOIN public.userinfo u ON u.user_id = l_moi.user_id0
        WHERE c.date0 >= '2026-10-20'
        ORDER BY c.date0 DESC, c.time0 DESC
        LIMIT 10
    )
    SELECT * FROM carton_details;
""")

rows = cur.fetchall()
print(f"BẢNG KÊ GỘP TÁCH THÙNG: Lấy được {len(rows)} dòng thực tế:")
for idx, r in enumerate(rows, 1):
    print(f"[{idx}] Ngày: {r['ngay_ghi_nhan']} {r['gio_tao']} | Mã SP: {r['ma_sp']} | Tem cũ: {r['id_tem_cu']} (SL: {r['sl_cu']}) -> Tem mới: {r['id_tem_moi']} (SL: {r['sl_moi']}) | User: {r['user_tao']}")

conn.close()
