WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay, %s::time AS tu_gio, %s::time AS den_gio,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_may, coalesce(%s::text, '') AS so_wo,
           coalesce(%s::text, '') AS serial_thung, coalesce(%s::text, '') AS serial_tp, coalesce(%s::text, '') AS ma_dvcs,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR coalesce(u.ds_branchs, '') = '' AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), base AS (
    SELECT c.id_oi AS so_ct, sch.ngay_ct AS ngay_kh, o.mes_scheduling_code AS so_wo, c.product_code AS ma_sp,
           v.ten_vt AS ten_sp, o.quantity AS so_luong_kh, c.in_process AS so_luong_tt, d.serial_tem_thung AS serial_thung,
           d.serial_tem_sp AS serial_tp, d.create_date, d.create_time, d.quantity AS sl_theo_thung, c.machine_code,
           d.phan_loai::text AS phan_loai, v.packs0
    FROM public.mes_oi_confirm c JOIN public.mes_oi_dong_thung d ON d.id_oi = c.id_oi::text AND d.product_code = c.product_code
    LEFT JOIN public.mes_scheduling_output o ON o.mes_scheduling_code = c.mes_scheduling_code AND o.product_code = c.product_code
    LEFT JOIN public.mes_scheduling sch ON sch.stt_rec = o.stt_rec CROSS JOIN scope s LEFT JOIN public.dmvt v ON v.ma_vt = c.product_code
    WHERE s.authorized_user_id IS NOT NULL AND c.create_date BETWEEN s.tu_ngay AND s.den_ngay
      AND d.create_date + d.create_time BETWEEN s.tu_ngay + s.tu_gio AND s.den_ngay + s.den_gio
      AND (s.ma_vt = '' OR c.product_code = ANY(string_to_array(s.ma_vt, ','))) AND (s.ma_may = '' OR c.machine_code = ANY(string_to_array(s.ma_may, ',')))
      AND (s.so_wo = '' OR c.mes_scheduling_code = ANY(string_to_array(s.so_wo, ',')))
      AND (s.serial_thung = '' OR d.serial_tem_thung = ANY(string_to_array(s.serial_thung, ','))) AND (s.serial_tp = '' OR d.serial_tem_sp = ANY(string_to_array(s.serial_tp, ',')))
      AND (s.ma_dvcs = '' OR sch.ma_dvcs = ANY(string_to_array(s.ma_dvcs, ','))) AND (s.unrestricted OR sch.ma_dvcs = ANY(string_to_array(s.ds_branchs, ',')))
)
SELECT row_number() OVER (ORDER BY b.so_ct DESC, b.ma_sp, b.serial_thung, b.serial_tp) AS stt, b.so_ct, max(b.ngay_kh) AS ngay_kh,
       max(b.so_wo) AS so_wo, b.ma_sp, max(b.ten_sp) AS ten_sp, max(b.so_luong_kh) AS so_luong_kh, coalesce(max(b.so_luong_tt), 0) AS so_luong_tt,
       b.serial_thung, CASE WHEN max(b.packs0) <> 0 THEN ceil(max(b.so_luong_tt) / max(b.packs0)) END AS oqm_thung, b.serial_tp,
       max(b.create_date) AS create_date, max(b.sl_theo_thung) AS sl_theo_thung, max(b.create_time) AS create_time,
       max(b.machine_code) AS machine_code, max(b.phan_loai) AS phan_loai, count(*) OVER () AS total
FROM base b GROUP BY b.so_ct, b.ma_sp, b.serial_thung, b.serial_tp
ORDER BY b.so_ct DESC, b.ma_sp, b.serial_thung, b.serial_tp LIMIT (SELECT row_limit FROM params);
