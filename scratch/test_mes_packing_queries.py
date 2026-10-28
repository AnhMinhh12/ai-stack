#!/usr/bin/env python3
import psycopg
from psycopg.rows import dict_row

def main():
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
    cur.execute("SET lock_timeout = '2s'")

    print("=== 1. Test Bảng kê đóng gói, đóng thùng (mes_oi_dong_thung) ===")
    cur.execute("""
        SELECT 
            min(stt) as stt,
            create_date as ngay_sx_thuc_te,
            station_code as ma_day_chuyen,
            mes_scheduling_code as so_wo,
            product_code as ma_san_pham,
            product_name as ten_san_pham,
            sum(quantity) as sl_thuc_te,
            count(serial_tem_sp) as sl_theo_thung,
            serial_tem_thung,
            max(create_date || ' ' || create_time) as thoi_gian_dong_thung,
            phan_loai
        FROM public.mes_oi_dong_thung
        WHERE nullif(serial_tem_thung, '') IS NOT NULL
        GROUP BY 
            create_date,
            station_code,
            mes_scheduling_code,
            product_code,
            product_name,
            serial_tem_thung,
            phan_loai
        ORDER BY create_date DESC
        LIMIT 5;
    """)
    rows = cur.fetchall()
    print(f"Lấy được {len(rows)} thùng mẫu:")
    for r in rows:
        print(f"  WO: {r['so_wo']} | Thùng: {r['serial_tem_thung']} | SP: {r['ma_san_pham']} | SL: {r['sl_thuc_te']} | Thời gian: {r['thoi_gian_dong_thung']}")

    print("\n=== 2. Test Bảng kê gộp tách thùng (intem_carton_log) ===")
    cur.execute("""
        SELECT 
            date0 as ngay_ghi_nhan,
            time0 as gio_tao,
            id_carton as id_tem_cu,
            id_carton_new as id_tem_moi
        FROM public.intem_carton_log
        ORDER BY date0 DESC, time0 DESC
        LIMIT 5;
    """)
    rows2 = cur.fetchall()
    print(f"Lấy được {len(rows2)} giao dịch gộp/tách mẫu:")
    for r in rows2:
        print(f"  Ngày: {r['ngay_ghi_nhan']} {r['gio_tao']} | Tem cũ: {r['id_tem_cu']} -> Tem mới: {r['id_tem_moi']}")

    print("\n=== 3. Test Bảng kê bổ sung shot (mes_oi_bo_shot) ===")
    cur.execute("""
        SELECT 
            date0 as ngay,
            time0 as gio,
            machine_code as ma_may,
            station_code as ma_line,
            mes_scheduling_code as so_wo,
            product_code as ma_sp,
            quantity as so_shot,
            cavity
        FROM public.mes_oi_bo_shot
        ORDER BY date0 DESC, time0 DESC
        LIMIT 5;
    """)
    rows3 = cur.fetchall()
    print(f"Lấy được {len(rows3)} shot mẫu:")
    for r in rows3:
        print(f"  Ngày: {r['ngay']} {r['gio']} | Line: {r['ma_line']} | Máy: {r['ma_may']} | WO: {r['so_wo']} | Shot: {r['so_shot']} | Cavity: {r['cavity']}")

    conn.close()

if __name__ == '__main__':
    main()
