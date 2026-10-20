-- Staging slice: current price list and MOQ lookup.
WITH scope AS (
    SELECT user_id, coalesce(is_super, 0) = 1 AS superuser,
           string_to_array(coalesce(ds_branchs, ''), ',') AS branches
    FROM public.userinfo WHERE user_id = %s
)
SELECT d.ma_kh, k.ten_kh, d.ma_vt, v.ten_vt, d.sl_min, d.dvt,
       d.gia0, d.gia, d.ma_nt, d.ngay_bd, d.ngay_kt, h.status,
       count(*) OVER () AS total_lines
FROM public.dmbanggiact d
JOIN public.dmbanggia h USING (ma_bang_gia)
LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
LEFT JOIN public.dmkh k ON k.ma_kh = d.ma_kh
CROSS JOIN scope s
WHERE (s.superuser OR h.ma_dvcs = ANY(s.branches))
  AND upper(trim(d.ma_vt)) = upper(trim(%s))
  AND (%s::date BETWEEN d.ngay_bd AND d.ngay_kt)
ORDER BY d.ma_kh, d.sl_min, d.ngay_bd DESC
LIMIT %s
