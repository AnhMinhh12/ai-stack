#!/usr/bin/env python3
import psycopg
from psycopg.rows import dict_row

conn = psycopg.connect(
    host='10.0.6.2',
    port=5410,
    dbname='3SERP_HTMP_DATA',
    user='read_htmp',
    password='P@ss@Htmp@W0rd!2025',
    connect_timeout=5
)

with conn.cursor(row_factory=dict_row) as cur:
    cur.execute("SET statement_timeout = 8000")
    
    print("=== 1. Lệnh sản xuất gần đây (phlsx + ctlsx) ===")
    cur.execute("""
        SELECT 
            h.ngay_ct,
            h.so_ct AS so_lsx,
            d.ma_vt,
            v.ten_vt,
            d.dvt,
            d.so_luong AS sl_ke_hoach,
            h.mes_scheduling_code AS so_wo,
            h.ma_phan_xuong,
            h.status
        FROM public.phlsx h
        JOIN public.ctlsx d USING(stt_rec)
        LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
        WHERE h.ngay_ct >= CURRENT_DATE - 7
        ORDER BY h.ngay_ct DESC, h.so_ct DESC
        LIMIT 5;
    """)
    for r in cur.fetchall():
        print(f"  LSX: {r['so_lsx']} | SP: {r['ma_vt']} ({r['ten_vt']}) | SL: {r['sl_ke_hoach']} {r['dvt']} | WO: {r['so_wo']}")

    print("\n=== 2. Dừng máy gần đây (mes_oi_stop_line + dmnndungmay) ===")
    cur.execute("""
        SELECT 
            s.create_date AS ngay_dung,
            to_char(s.create_time, 'HH24:MI:SS') AS gio_bat_dau,
            to_char(s.end_time, 'HH24:MI:SS') AS gio_ket_thuc,
            s.machine_code AS ma_may,
            s.station_code AS ma_line,
            s.mes_scheduling_code AS so_wo,
            s.error_code AS ma_nguyen_nhan,
            coalesce(nn.ten_loi, s.error_code) AS ten_nguyen_nhan,
            round(extract(epoch from (s.end_date + s.end_time - (s.create_date + s.create_time))) / 60)::numeric AS phut_dung,
            s.note AS ghi_chu
        FROM public.mes_oi_stop_line s
        LEFT JOIN public.dmnndungmay nn ON nn.ma_loi = s.error_code
        WHERE s.create_date >= CURRENT_DATE - 7
        ORDER BY s.create_date DESC, s.create_time DESC
        LIMIT 5;
    """)
    for r in cur.fetchall():
        print(f"  Máy: {r['ma_may']} | Ngày: {r['ngay_dung']} {r['gio_bat_dau']} - {r['gio_ket_thuc']} | Lý do: {r['ten_nguyen_nhan']} ({r['ma_nguyen_nhan']}) | Phút: {r['phut_dung']}")

    print("\n=== 3. Phế phẩm NG gần đây (mes_oi_ng_confirm + dmloi + dmvt) ===")
    cur.execute("""
        SELECT 
            n.create_date AS ngay_ghi_nhan,
            to_char(n.create_time, 'HH24:MI:SS') AS gio_ghi_nhan,
            n.machine_code AS ma_may,
            n.station_code AS ma_line,
            n.production_order AS so_lsx,
            n.mes_scheduling_code AS so_wo,
            n.product_code AS ma_sp,
            coalesce(v.ten_vt, n.product_code) AS ten_sp,
            n.ng_qty AS sl_ng,
            n.error_code AS ma_loi,
            coalesce(l.ten_loi, n.error_code) AS ten_loi,
            n.ma_nv AS nhan_vien
        FROM public.mes_oi_ng_confirm n
        LEFT JOIN public.dmloi l ON l.ma_loi = n.error_code
        LEFT JOIN public.dmvt v ON v.ma_vt = n.product_code
        WHERE n.create_date >= CURRENT_DATE - 7
        ORDER BY n.create_date DESC, n.create_time DESC
        LIMIT 5;
    """)
    for r in cur.fetchall():
        print(f"  SP: {r['ma_sp']} ({r['ten_sp']}) | NG: {r['sl_ng']} PCS | Lỗi: {r['ten_loi']} ({r['ma_loi']}) | Máy: {r['ma_may']} | Ngày: {r['ngay_ghi_nhan']} {r['gio_ghi_nhan']}")
