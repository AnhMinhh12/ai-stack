WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_kh,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT h.ngay_ct, h.so_ct, h.ma_kh, k.ten_kh, d.ma_vt, v.ten_vt,
       d.so_luong AS sl_don, COALESCE(n.sl_nhap, 0) AS sl_nhap,
       COALESCE(i.sl_hoa_don, 0) AS sl_hoa_don,
       CASE WHEN h.status::text <> '1' THEN d.so_luong - COALESCE(n.sl_nhap, 0) ELSE 0 END AS sl_dong,
       count(*) OVER () AS total
FROM public.ph94 h
JOIN public.ct94 d ON d.stt_rec = h.stt_rec
CROSS JOIN access_scope a
LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
LEFT JOIN LATERAL (SELECT SUM(x.so_luong) AS sl_nhap FROM public.ct77 x WHERE x.stt_rec = d.stt_rec AND x.ln = d.ln) n ON true
LEFT JOIN LATERAL (SELECT SUM(x.so_luong) AS sl_hoa_don FROM public.ct71 x WHERE x.stt_rec = d.stt_rec AND x.ln = d.ln) i ON true
WHERE a.authorized_user_id IS NOT NULL
  AND h.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
  AND (a.ma_vt = '' OR upper(trim(d.ma_vt)) = a.ma_vt)
  AND (a.ma_kh = '' OR upper(trim(h.ma_kh)) = a.ma_kh)
  AND (a.unrestricted OR a.ds_branchs = '' OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
  AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (
      SELECT 1 FROM public.dmkho w
      WHERE w.ma_kho = d.ma_kho AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))
  ))
ORDER BY h.stt_rec, d.ln
LIMIT (SELECT row_limit FROM params)
