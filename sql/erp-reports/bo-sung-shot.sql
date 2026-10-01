WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay, coalesce(%s::text, '') AS ma_day_chuyen,
           coalesce(%s::text, '') AS ma_lenh, coalesce(%s::text, '') AS id_oi, coalesce(%s::text, '') AS ma_vt,
           coalesce(%s::text, '') AS ma_nv, coalesce(%s::text, '') AS ma_dvcs,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR coalesce(u.ds_branchs, '') = '' AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT row_number() OVER (ORDER BY a.date0 DESC, a.time0 DESC, a.id_add) AS stt,
       a.line_code, a.mes_scheduling_code, a.id_oi, a.date0, a.time0, a.product_code, v.ten_vt,
       a.quantity, a.user_xac_nhan, kh.ten_kh AS ten_nv, a.ghi_chu, count(*) OVER () AS total
FROM public.mes_oi_add_quantity a CROSS JOIN scope s
LEFT JOIN public.dmvt v ON v.ma_vt = a.product_code LEFT JOIN public.dmkh kh ON kh.ma_kh = a.user_xac_nhan
WHERE s.authorized_user_id IS NOT NULL AND a.date0 BETWEEN s.tu_ngay AND s.den_ngay
  AND (s.ma_day_chuyen = '' OR a.line_code = ANY(string_to_array(s.ma_day_chuyen, ',')))
  AND (s.ma_lenh = '' OR a.mes_scheduling_code = ANY(string_to_array(s.ma_lenh, ',')))
  AND (s.id_oi = '' OR a.id_oi ILIKE '%%' || s.id_oi || '%%') AND (s.ma_vt = '' OR a.product_code = ANY(string_to_array(s.ma_vt, ',')))
  AND (s.ma_nv = '' OR a.user_xac_nhan = ANY(string_to_array(s.ma_nv, ',')))
  AND (s.ma_dvcs = '' OR EXISTS (SELECT 1 FROM public.mes_oi_confirm c WHERE c.id_oi = a.id_oi AND c.branch_code = ANY(string_to_array(s.ma_dvcs, ','))))
  AND (s.unrestricted OR EXISTS (SELECT 1 FROM public.mes_oi_confirm c WHERE c.id_oi = a.id_oi AND c.branch_code = ANY(string_to_array(s.ds_branchs, ','))))
ORDER BY a.date0 DESC, a.time0 DESC, a.id_add LIMIT (SELECT row_limit FROM params);
