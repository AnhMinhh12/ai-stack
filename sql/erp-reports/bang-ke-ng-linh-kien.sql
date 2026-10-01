WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay, %s::time AS tu_gio, %s::time AS den_gio,
           coalesce(%s::text, '') AS ma_lenh, coalesce(%s::text, '') AS ma_sp,
           coalesce(%s::text, '') AS ma_may, coalesce(%s::text, '') AS id_oi,
           coalesce(%s::text, '0') AS phan_loai, coalesce(%s::text, '') AS ma_dvcs,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR coalesce(u.ds_branchs, '') = '' AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), base AS (
    SELECT n.id_oi, c.mes_scheduling_code, c.product_code, n.material_code, v.ten_vt AS material_name,
           c.machine_code, c.create_date, c.create_time, c.end_date, c.end_time, n.ng_qty,
           n.error_code, e.ten_loi AS error_name, n.phan_loai, o.form_name AS ten_phan_loai,
           n.ma_nv, kh.ten_kh AS ten_nv, n.create_date AS ngay_dk, n.create_time AS gio_dk, n.step_code
    FROM public.mes_oi_ng_materrial n JOIN public.mes_oi_confirm c ON c.id_oi = n.id_oi
    CROSS JOIN scope s LEFT JOIN public.dmvt v ON v.ma_vt = n.material_code
    LEFT JOIN public.dmloi e ON e.ma_loi = n.error_code LEFT JOIN public.dmkh kh ON kh.ma_kh = n.ma_nv
    LEFT JOIN public.sys_listoptions o ON o.form = 'OI' AND o.form_type = 'PHAN_LOAI' AND o.form_value = n.phan_loai
    WHERE s.authorized_user_id IS NOT NULL
      AND c.create_date + c.create_time BETWEEN s.tu_ngay + s.tu_gio AND s.den_ngay + s.den_gio
      AND c.end_date + c.end_time <= s.den_ngay + s.den_gio
      AND (s.ma_lenh = '' OR c.mes_scheduling_code = ANY(string_to_array(s.ma_lenh, ',')))
      AND (s.ma_sp = '' OR c.product_code = ANY(string_to_array(s.ma_sp, ',')))
      AND (s.ma_may = '' OR c.machine_code = ANY(string_to_array(s.ma_may, ',')))
      AND (s.id_oi = '' OR n.id_oi = ANY(string_to_array(s.id_oi, ',')))
      AND (s.phan_loai = '0' OR n.phan_loai = ANY(string_to_array(s.phan_loai, ',')))
      AND (s.ma_dvcs = '' OR c.branch_code = ANY(string_to_array(s.ma_dvcs, ',')))
      AND (s.unrestricted OR c.branch_code = ANY(string_to_array(s.ds_branchs, ',')))
      AND EXISTS (SELECT 1 FROM public.mes_oi_material m WHERE m.id_oi = n.id_oi AND m.material_code = n.material_code AND m.product_code = n.product_code)
)
SELECT row_number() OVER (ORDER BY b.id_oi DESC, b.mes_scheduling_code, b.material_code) AS stt,
       b.id_oi, b.mes_scheduling_code, b.product_code,
       b.material_code, b.material_name, b.machine_code, b.create_date, b.create_time, b.end_date, b.end_time,
       b.ng_qty, b.error_code, b.error_name, b.phan_loai, b.ten_phan_loai, b.ma_nv, b.ten_nv, b.ngay_dk, b.gio_dk,
       b.step_code, count(*) OVER () AS total
FROM base b ORDER BY b.id_oi DESC, b.mes_scheduling_code, b.material_code
LIMIT (SELECT row_limit FROM params);
