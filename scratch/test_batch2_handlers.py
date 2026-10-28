#!/usr/bin/env python3
import time
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
    cur.execute("SET statement_timeout = 4000")
    
    # Filter test 1: WO by material code (using phlsx + ctlsx)
    t0 = time.time()
    code = "1014082701"
    sql_wo_mat = """
        SELECT 
            coalesce(h.mes_scheduling_code, h.so_ct) AS so_wo,
            d.ma_vt AS ma_sp,
            coalesce(v.ten_vt, d.ma_vt) AS ten_sp,
            d.ma_version AS version_bom,
            h.ma_phan_xuong AS ma_may,
            '' AS ma_khuon,
            d.so_luong AS sl_ke_hoach,
            to_char(h.ngay_ct, 'YYYY-MM-DD') AS bat_dau,
            to_char(h.ngay_ht, 'YYYY-MM-DD') AS ket_thuc,
            h.so_ct AS so_lsx,
            h.status AS trang_thai
        FROM public.phlsx h
        JOIN public.ctlsx d USING(stt_rec)
        LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
        WHERE h.ngay_ct >= CURRENT_DATE - 30
          AND (d.ma_vt = %s OR h.mes_scheduling_code = %s OR h.so_ct = %s)
        ORDER BY h.ngay_ct DESC, h.so_ct DESC
        LIMIT 30;
    """
    cur.execute(sql_wo_mat, (code, code, code))
    r = cur.fetchall()
    print(f"Filter 1: WO by mat: {len(r)} rows in {time.time()-t0:.3f}s", flush=True)

    # Filter test 2: Stop line by machine
    t0 = time.time()
    machine = "DUC-0266"
    sql_stop_mach = """
        SELECT 
            to_char(s.create_date, 'YYYY-MM-DD') AS ngay_dung,
            to_char(s.create_time, 'HH24:MI:SS') AS gio_bat_dau,
            to_char(s.end_time, 'HH24:MI:SS') AS gio_ket_thuc,
            round(extract(epoch from (s.end_date + s.end_time - (s.create_date + s.create_time))) / 60)::numeric AS phut_dung,
            s.machine_code AS ma_may,
            s.station_code AS ma_line,
            s.mes_scheduling_code AS so_wo,
            s.error_code AS ma_loi,
            coalesce(nn.ten_loi, s.error_code) AS ten_nguyen_nhan,
            coalesce(s.note, '') AS ghi_chu
        FROM public.mes_oi_stop_line s
        LEFT JOIN public.dmnndungmay nn ON nn.ma_loi = s.error_code
        WHERE s.create_date >= CURRENT_DATE - 14
          AND (s.machine_code = %s OR s.station_code = %s OR s.mes_scheduling_code = %s)
        ORDER BY s.create_date DESC, s.create_time DESC
        LIMIT 30;
    """
    cur.execute(sql_stop_mach, (machine, machine, machine))
    r = cur.fetchall()
    print(f"Filter 2: Stop line by machine: {len(r)} rows in {time.time()-t0:.3f}s", flush=True)

    # Filter test 3: NG by product
    t0 = time.time()
    mat = "QC7-5021-000"
    sql_ng_mat = """
        SELECT 
            to_char(n.create_date, 'YYYY-MM-DD') AS ngay,
            to_char(n.create_time, 'HH24:MI:SS') AS gio,
            n.machine_code AS ma_may,
            n.station_code AS ma_line,
            n.production_order AS so_lsx,
            n.mes_scheduling_code AS so_wo,
            n.product_code AS ma_sp,
            coalesce(v.ten_vt, n.product_code) AS ten_sp,
            n.ng_qty AS sl_ng,
            n.error_code AS ma_loi,
            coalesce(l.ten_loi, n.error_code) AS ten_loi,
            n.step_code AS cong_doan,
            n.ma_nv AS nhan_vien
        FROM public.mes_oi_ng_confirm n
        LEFT JOIN public.dmloi l ON l.ma_loi = n.error_code
        LEFT JOIN public.dmvt v ON v.ma_vt = n.product_code
        WHERE n.create_date >= CURRENT_DATE - 30
          AND (n.product_code = %s OR n.machine_code = %s OR n.mes_scheduling_code = %s)
        ORDER BY n.create_date DESC, n.create_time DESC
        LIMIT 30;
    """
    cur.execute(sql_ng_mat, (mat, mat, mat))
    r = cur.fetchall()
    print(f"Filter 3: NG by product: {len(r)} rows in {time.time()-t0:.3f}s", flush=True)
