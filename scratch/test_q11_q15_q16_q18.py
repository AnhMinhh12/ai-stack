#!/usr/bin/env python3
import json
import psycopg
from psycopg.rows import dict_row

CONN_PARAMS = {
    "host": "10.0.6.2",
    "port": 5410,
    "dbname": "3SERP_HTMP_DATA",
    "user": "read_htmp",
    "password": "P@ss@Htmp@W0rd!2025",
    "connect_timeout": 5
}

def query(sql, params=None):
    with psycopg.connect(**CONN_PARAMS, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def main():
    print("=== Q11: Tồn kho theo khuôn / die_no ===")
    sql_q11 = """
        SELECT coalesce(nullif(e->>'die_no', ''), 'Chưa rõ') AS die_no,
               coalesce(nullif(e->>'ma_khuon', ''), '') AS mold,
               sum((e->>'so_luong')::numeric) AS qty
        FROM public.intem_log a CROSS JOIN LATERAL jsonb_array_elements(
            CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
        ) e
        WHERE a.nxt = 1 AND a.status = '1' AND upper(trim(e->>'ma_vt')) = 'QC7-5146-000'
        GROUP BY 1, 2
        ORDER BY 1, 2
    """
    try:
        r11 = query(sql_q11)
        print("Q11 Result:", json.dumps(r11, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Q11 Error:", e)

    print("\n=== Q15: Trạng thái QC ===")
    sql_q15 = """
        SELECT a.status_qc, coalesce(o.form_name, a.status_qc::text) AS form_name,
               sum((e->>'so_luong')::numeric) AS qty
        FROM public.intem_log a
        CROSS JOIN LATERAL jsonb_array_elements(
            CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
        ) e
        LEFT JOIN public.sys_listoptions o ON o.form = 'OQC' AND o.form_type = 'TYPE_ST' AND o.form_value = a.status_qc::text
        WHERE a.nxt = 1 AND a.status = '1' AND upper(trim(e->>'ma_vt')) = 'QC7-5146-000'
        GROUP BY 1, 2
        ORDER BY 1
    """
    try:
        r15 = query(sql_q15)
        print("Q15 Result:", json.dumps(r15, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Q15 Error:", e)

    print("\n=== Q16: Đơn hàng chưa có giá chuẩn (gia_chuan = 0 hoặc NULL) ===")
    sql_q16 = """
        SELECT d.ma_vt, v.ten_vt, count(*) AS lines, d.gia_chuan
        FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
        LEFT JOIN public.dmvt v ON d.ma_vt = v.ma_vt
        WHERE upper(trim(h.ma_kh)) = 'KH0015' AND h.ngay_ct BETWEEN '2026-10-01'::date AND '2026-10-20'::date
          AND (d.gia_chuan IS NULL OR d.gia_chuan = 0)
        GROUP BY d.ma_vt, v.ten_vt, d.gia_chuan
        ORDER BY d.ma_vt
    """
    try:
        r16 = query(sql_q16)
        print("Q16 Result:", json.dumps(r16, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Q16 Error:", e)

    print("\n=== Q18: Giao bù NG vs Nhận lại hàng NG ===")
    sql_q18_bu = """
        SELECT count(*) AS lines, coalesce(sum(d.so_luong), 0) AS qty
        FROM public.ph96 h JOIN public.ct96 d USING(stt_rec)
        WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' AND h.ma_gd = 10 AND h.ngay_ct BETWEEN '2026-10-01'::date AND '2026-10-20'::date
    """
    sql_q18_tra = """
        SELECT count(*) AS lines, coalesce(sum(d.so_luong), 0) AS qty
        FROM public.ph66 h JOIN public.ct66 d USING(stt_rec)
        WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' AND h.ngay_ct BETWEEN '2026-10-01'::date AND '2026-10-20'::date
    """
    try:
        r18_bu = query(sql_q18_bu)
        r18_tra = query(sql_q18_tra)
        print("Q18 Giao bù:", json.dumps(r18_bu, ensure_ascii=False, indent=2, default=str))
        print("Q18 Trả về:", json.dumps(r18_tra, ensure_ascii=False, indent=2, default=str))
    except Exception as e:
        print("Q18 Error:", e)

if __name__ == '__main__':
    main()
