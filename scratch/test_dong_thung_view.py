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
cur.execute("SET statement_timeout = '3s'")

cur.execute("""
    SELECT 
        create_date as ngay_sx,
        mes_scheduling_code as so_wo,
        station_code as ma_line,
        product_code as ma_sp,
        product_name as ten_sp,
        serial_tem_thung,
        count(serial_tem_sp) as sl_tem,
        sum(quantity) as tong_sl,
        max(create_time) as gio_dong_thung,
        phan_loai
    FROM public.mes_oi_dong_thung
    WHERE create_date >= '2026-10-26'
    GROUP BY 
        create_date,
        mes_scheduling_code,
        station_code,
        product_code,
        product_name,
        serial_tem_thung,
        phan_loai
    ORDER BY create_date DESC, max(create_time) DESC
    LIMIT 10;
""")

rows = cur.fetchall()
print(f"BẢNG KÊ ĐÓNG GÓI, ĐÓNG THÙNG (mes_oi_dong_thung): Lấy được {len(rows)} thùng:")
for idx, r in enumerate(rows, 1):
    print(f"[{idx}] Ngày: {r['ngay_sx']} {r['gio_dong_thung']} | WO: {r['so_wo']} | Line: {r['ma_line']} | Mã SP: {r['ma_sp']} ({r['ten_sp']}) | Thùng: {r['serial_tem_thung']} | SL: {r['tong_sl']} | Cờ: {r['phan_loai']}")

conn.close()
