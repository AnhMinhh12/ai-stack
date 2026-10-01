WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_lo,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), opening_balance AS (
    SELECT b.ma_vt, b.ma_lo, sum(b.ton00) AS so_luong
    FROM public.cdbsp b CROSS JOIN access_scope p
    WHERE p.authorized_user_id IS NOT NULL
      AND b.nam = extract(year FROM p.tu_ngay)::smallint
      AND (p.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho w
          WHERE w.ma_kho = b.ma_kho AND w.ma_dvcs = ANY(string_to_array(p.ds_branchs, ','))
      ))
    GROUP BY b.ma_vt, b.ma_lo
), opening_movement AS (
    SELECT m.ma_vt, m.ma_lo, sum(m.sl_nhap - m.sl_xuat) AS so_luong
    FROM public.ct70bsp m CROSS JOIN access_scope p
    WHERE p.authorized_user_id IS NOT NULL
      AND m.ngay_ct BETWEEN make_date(extract(year FROM p.tu_ngay)::integer, 1, 1)
                            AND p.tu_ngay - 1
      AND (p.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho w
          WHERE w.ma_kho = m.ma_kho AND w.ma_dvcs = ANY(string_to_array(p.ds_branchs, ','))
      ))
    GROUP BY m.ma_vt, m.ma_lo
), dk AS (
    SELECT ma_vt, ma_lo, sum(so_luong) AS ton_dau
    FROM (SELECT * FROM opening_balance UNION ALL SELECT * FROM opening_movement) x
    GROUP BY ma_vt, ma_lo
), ps AS (
    SELECT m.ma_vt, m.ma_lo, sum(m.sl_nhap) AS sl_nhap, sum(m.sl_xuat) AS sl_xuat
    FROM public.ct70bsp m CROSS JOIN access_scope p
    WHERE p.authorized_user_id IS NOT NULL
      AND m.ngay_ct BETWEEN p.tu_ngay AND p.den_ngay
      AND (p.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho w
          WHERE w.ma_kho = m.ma_kho AND w.ma_dvcs = ANY(string_to_array(p.ds_branchs, ','))
      ))
    GROUP BY m.ma_vt, m.ma_lo
)
SELECT coalesce(ps.ma_vt, dk.ma_vt) AS ma_vt, v.ten_vt, coalesce(ps.ma_lo, dk.ma_lo) AS ma_lo,
       coalesce(dk.ton_dau, 0) AS ton_dau, coalesce(ps.sl_nhap, 0) AS sl_nhap,
       coalesce(ps.sl_xuat, 0) AS sl_xuat,
       coalesce(dk.ton_dau, 0) + coalesce(ps.sl_nhap, 0) - coalesce(ps.sl_xuat, 0) AS ton_cuoi,
       count(*) OVER () AS total
FROM ps FULL JOIN dk ON dk.ma_vt = ps.ma_vt AND dk.ma_lo = ps.ma_lo
LEFT JOIN public.dmvt v ON v.ma_vt = coalesce(ps.ma_vt, dk.ma_vt)
CROSS JOIN access_scope p
WHERE (p.ma_vt = '' OR coalesce(ps.ma_vt, dk.ma_vt) = ANY(string_to_array(p.ma_vt, ',')))
  AND (p.ma_lo = '' OR coalesce(ps.ma_lo, dk.ma_lo) = ANY(string_to_array(p.ma_lo, ',')))
ORDER BY ma_vt, ma_lo
LIMIT (SELECT row_limit FROM params);
