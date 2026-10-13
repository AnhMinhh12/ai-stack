WITH params AS (
  SELECT coalesce(%s::text, '') AS ma_bang_gia, coalesce(%s::text, '') AS ma_vt,
         coalesce(%s::text, '') AS ma_kh, coalesce(%s::text, '') AS status,
         %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
  SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
         coalesce(u.is_super, 0) = 1 OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
  FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT h.ma_dvcs, h.ma_bang_gia, h.ten_bang_gia, h.loai_ban, h.loai_bang_gia,
       d.ma_vt, v.ten_vt, d.ma_kh, k.ten_kh, d.dvt, d.sl_min, d.ma_nt,
       d.gia0, d.gia, d.ma_thue, d.thue_suat, d.ngay_bd, d.ngay_kt, h.status,
       count(*) OVER () AS total
FROM public.dmbanggia h
JOIN public.dmbanggiact d ON d.ma_bang_gia = h.ma_bang_gia
LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
LEFT JOIN public.dmkh k ON k.ma_kh = d.ma_kh
CROSS JOIN access_scope x
WHERE x.authorized_user_id IS NOT NULL
  AND (x.ma_bang_gia = '' OR h.ma_bang_gia = ANY(string_to_array(x.ma_bang_gia, ',')))
  AND (x.ma_vt = '' OR d.ma_vt = ANY(string_to_array(x.ma_vt, ',')))
  AND (x.ma_kh = '' OR d.ma_kh = ANY(string_to_array(x.ma_kh, ',')))
  AND (x.status = '' OR h.status::text = ANY(string_to_array(x.status, ',')))
  AND (x.unrestricted OR h.ma_dvcs = ANY(string_to_array(x.ds_branchs, ',')))
ORDER BY h.ma_bang_gia, d.ma_vt, d.ma_kh, d.sl_min, d.ngay_bd DESC
LIMIT (SELECT row_limit FROM params);
