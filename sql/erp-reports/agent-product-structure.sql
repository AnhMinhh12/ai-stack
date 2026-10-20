-- Staging slice: effective BOM and components.
WITH scope AS (
    SELECT user_id, coalesce(is_super, 0) = 1 AS superuser
    FROM public.userinfo WHERE user_id = %s
)
SELECT b.product_code AS ma_sp_me, b.bom_code, b.bom_version, b.status,
       b.valid_from, b.valid_to, m.material_code, v.ten_vt, m.quantity AS sl_dinh_muc, m.uom AS dvt,
       count(*) OVER () AS total_lines
FROM public.mfbom b
JOIN public.mfbom_material m ON m.bom_code = b.bom_code
LEFT JOIN public.dmvt v ON v.ma_vt = m.material_code
CROSS JOIN scope s
WHERE (s.superuser OR s.user_id IS NOT NULL)
  AND upper(trim(b.product_code)) = upper(trim(%s))
  AND (%s::date BETWEEN b.valid_from AND b.valid_to)
ORDER BY b.bom_version DESC, m.material_code
LIMIT %s
