-- Staging slice: customer directory lookup by code, exact name, or partial name.
WITH scope AS (
    SELECT user_id, coalesce(is_super, 0) = 1 AS superuser
    FROM public.userinfo WHERE user_id = %s
)
SELECT k.ma_kh, k.ten_kh, k.ten_viet_tat, k.dien_thoai, k.dia_chi, k.status,
       count(*) OVER () AS total_lines
FROM public.dmkh k
CROSS JOIN scope s
WHERE (s.superuser OR s.user_id IS NOT NULL)
  AND (
      upper(trim(k.ma_kh)) = upper(trim(%s))
      OR lower(trim(k.ten_kh)) = lower(trim(%s))
      OR lower(k.ten_kh) LIKE '%%' || lower(trim(%s)) || '%%'
  )
ORDER BY k.ma_kh
LIMIT %s
