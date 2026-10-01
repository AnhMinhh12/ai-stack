WITH params AS (
    SELECT coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_lo,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT l.ma_vt, v.ten_vt, l.ma_lo, l.ngay_hhsd, (l.ngay_hhsd - current_date + 1) AS ngay_con_han, s.ton13,
       u.date0 AS lan_gia_han_cuoi, count(*) OVER () AS total
FROM public.dmlo l
JOIN public.cdvt13 s ON s.ma_vt = l.ma_vt AND s.ma_lo = l.ma_lo AND s.ton13 > 0
CROSS JOIN access_scope a
LEFT JOIN public.dmvt v ON v.ma_vt = l.ma_vt
LEFT JOIN LATERAL (SELECT x.date0 FROM public.dmloupdatehsd x WHERE x.ma_vt = l.ma_vt AND x.ma_lo = l.ma_lo ORDER BY x.date0 DESC, x.time0 DESC LIMIT 1) u ON true
WHERE a.authorized_user_id IS NOT NULL
  AND v.ql_han_su_dung = 1
  AND (a.ma_vt = '' OR upper(trim(l.ma_vt)) = a.ma_vt)
  AND (a.ma_lo = '' OR upper(trim(l.ma_lo)) = a.ma_lo)
  AND (a.unrestricted OR EXISTS (
      SELECT 1 FROM public.dmkho w
      WHERE w.ma_kho = s.ma_kho AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))
  ))
ORDER BY l.ngay_hhsd, l.ma_vt, l.ma_lo
LIMIT (SELECT row_limit FROM params)
