-- Candidate order materials with missing or zero standard price, within ERP scope.
WITH scope AS (
    SELECT user_id, coalesce(is_super, 0) = 1 AS superuser,
           string_to_array(coalesce(ds_branchs, ''), ',') AS branches
    FROM public.userinfo WHERE user_id = %s
), candidates AS (
    SELECT d.ma_vt, count(*) AS order_lines,
           count(*) FILTER (WHERE d.gia_chuan IS NULL) AS null_price_lines,
           count(*) FILTER (WHERE d.gia_chuan = 0) AS zero_price_lines
    FROM public.ph64 h JOIN public.ct64 d USING (stt_rec)
    CROSS JOIN scope s
    WHERE h.ma_kh = %s
      AND h.ngay_ct BETWEEN %s::date AND %s::date
      AND (s.superuser OR h.ma_dvcs = ANY(s.branches))
    GROUP BY d.ma_vt
    HAVING bool_or(d.gia_chuan IS NULL OR d.gia_chuan = 0)
)
SELECT ma_vt, order_lines, null_price_lines, zero_price_lines,
       count(*) OVER () AS total_lines
FROM candidates ORDER BY ma_vt LIMIT %s
