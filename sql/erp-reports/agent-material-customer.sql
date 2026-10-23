-- Declared customer on the material master, scoped to ERP branches.
WITH scope AS (
    SELECT user_id, coalesce(is_super, 0) = 1 AS superuser,
           string_to_array(coalesce(ds_branchs, ''), ',') AS branches
    FROM public.userinfo WHERE user_id = %s
)
SELECT v.ma_vt, v.ma_kh, k.ten_kh, count(*) OVER () AS total_lines
FROM public.dmvt v LEFT JOIN public.dmkh k ON k.ma_kh = v.ma_kh
CROSS JOIN scope s
WHERE upper(trim(v.ma_vt)) = upper(trim(%s))
  AND (s.superuser OR string_to_array(coalesce(v.ds_ma_dvcs, ''), ',') && s.branches)
LIMIT %s
