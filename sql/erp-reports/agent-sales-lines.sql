-- Staging slice: line grain, conservative branch AND warehouse ACL.
-- Empty branch/warehouse scope denies access unless ERP explicitly marks superuser.
WITH scope AS (
    SELECT user_id, coalesce(is_super, 0) = 1 AS superuser,
           string_to_array(coalesce(ds_branchs, ''), ',') AS branches,
           string_to_array(coalesce(ds_stocks, ''), ',') AS warehouses
    FROM public.userinfo WHERE user_id = %s
)
SELECT h.stt_rec, d.ln, h.ngay_lct, h.ngay_ct, h.so_ct, h.ma_dvcs,
       h.ma_kh, h.status, d.ma_vt, d.ma_kho, d.ma_lo, d.dvt, d.so_luong, d.tien2,
       count(*) OVER () AS total_lines,
       coalesce(sum(d.so_luong) OVER (), 0) AS total_quantity,
       coalesce(sum(d.tien2) OVER (), 0) AS total_revenue
FROM public.ph81 h JOIN public.ct81 d ON d.stt_rec = h.stt_rec
CROSS JOIN scope s
WHERE upper(trim(d.ma_vt)) = upper(%s)
  AND h.ngay_lct BETWEEN %s::date AND %s::date
  AND h.ma_gd <> 4
  AND (s.superuser OR h.ma_dvcs = ANY(s.branches))
  AND (s.superuser OR d.ma_kho = ANY(s.warehouses))
ORDER BY h.ngay_lct DESC, h.ngay_ct DESC, h.so_ct DESC, h.stt_rec DESC, d.ln DESC
LIMIT %s
