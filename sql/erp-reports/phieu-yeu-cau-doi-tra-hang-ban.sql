WITH params AS (
  SELECT %s::date AS tu_ngay, %s::date AS den_ngay, coalesce(%s::text, '') AS ma_kh,
         coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS status,
         %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
  SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
         coalesce(u.is_super, 0) = 1 OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
  FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT s.statusname AS status, h.ngay_ct, h.so_ct, h.ma_gd, h.ma_kh, h.ten_kh,
       d.ma_vt, v.ten_vt, d.dvt, d.ma_kho, d.so_luong, d.tien_ban, d.ck,
       d.tien_ban + d.thue - d.ck AS t_tt, d.so_ct_dh, d.so_ct_hda, h.dien_giai,
       count(*) OVER () AS total
FROM public.ph66 h
JOIN public.ct66 d ON d.stt_rec = h.stt_rec
LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
LEFT JOIN public.sys_dmtt s ON s.ma_ct = 'RQ1' AND s.status = h.status
CROSS JOIN access_scope x
WHERE x.authorized_user_id IS NOT NULL AND h.ngay_ct BETWEEN x.tu_ngay AND x.den_ngay
  AND (x.ma_kh = '' OR h.ma_kh = ANY(string_to_array(x.ma_kh, ',')))
  AND (x.ma_vt = '' OR d.ma_vt = ANY(string_to_array(x.ma_vt, ',')))
  AND (x.status = '' OR h.status::text = ANY(string_to_array(x.status, ',')))
  AND (x.unrestricted OR h.ma_dvcs = ANY(string_to_array(x.ds_branchs, ',')))
  AND (d.ma_kho IS NULL OR d.ma_kho = '' OR x.unrestricted OR EXISTS (SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho AND w.ma_dvcs = ANY(string_to_array(x.ds_branchs, ','))))
ORDER BY h.ngay_ct DESC, h.so_ct DESC, d.ln
LIMIT (SELECT row_limit FROM params);
