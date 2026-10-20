WITH params AS (
  SELECT %s::date AS tu_ngay, %s::date AS den_ngay, coalesce(%s::text, '') AS ma_kh,
         coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_dvcs,
         %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
  SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
         coalesce(u.is_super, 0) = 1 OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
  FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT d.ma_vt, max(v.ten_vt) AS ten_vt, max(d.dvt) AS dvt,
       sum(coalesce(d.so_luong, 0)) AS so_luong,
       sum(coalesce(d.tien2, 0)) AS doanh_thu, count(*) OVER() AS total
FROM public.ph81 h
JOIN public.ct81 d ON d.stt_rec = h.stt_rec
LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
CROSS JOIN access_scope x
WHERE x.authorized_user_id IS NOT NULL AND h.ngay_ct BETWEEN x.tu_ngay AND x.den_ngay
  AND h.ma_gd <> 4
  AND h.status IN (SELECT status FROM public.sys_dmtt WHERE ma_ct = 'HDA' AND post_inventory_yn = true)
  AND (x.ma_kh = '' OR h.ma_kh = ANY(string_to_array(x.ma_kh, ',')))
  AND (x.ma_vt = '' OR d.ma_vt = ANY(string_to_array(x.ma_vt, ',')))
  AND (x.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(x.ma_dvcs, ',')))
  AND (x.unrestricted OR h.ma_dvcs = ANY(string_to_array(x.ds_branchs, ',')))
  AND (d.ma_kho IS NULL OR d.ma_kho = '' OR x.unrestricted OR EXISTS (
      SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho
        AND w.ma_dvcs = ANY(string_to_array(x.ds_branchs, ','))
  ))
GROUP BY d.ma_vt
ORDER BY d.ma_vt
LIMIT (SELECT row_limit FROM params);
