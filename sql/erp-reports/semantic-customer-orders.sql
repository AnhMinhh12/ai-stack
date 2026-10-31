-- Candidate for review, not registered for chat or approved semantic use.
-- Ranking is per original currency; declined/cancelled documents are excluded.
-- Branch and warehouse scope are both required except for ERP superusers.
WITH scope AS (
  SELECT coalesce(is_super, 0) = 1 AS superuser,
         string_to_array(coalesce(ds_branchs, ''), ',') AS branches,
         string_to_array(coalesce(ds_stocks, ''), ',') AS warehouses
  FROM public.userinfo WHERE user_id = %(erp_user_id)s
), grouped AS (
  SELECT h.ma_kh, h.ma_nt, count(DISTINCT h.stt_rec) AS order_count,
         sum(d.tien_nt2) AS order_amount
  FROM public.ph64 h
  JOIN public.ct64 d ON d.stt_rec = h.stt_rec
  CROSS JOIN scope s
  WHERE h.ngay_ct BETWEEN %(date_from)s::date AND %(date_to)s::date
    AND h.status::text NOT IN ('14', '15')
    AND (s.superuser OR h.ma_dvcs = ANY(s.branches))
    AND (s.superuser OR d.ma_kho = ANY(s.warehouses))
  GROUP BY h.ma_kh, h.ma_nt
), ranked AS (
  SELECT *, row_number() OVER (PARTITION BY ma_nt ORDER BY order_amount DESC NULLS LAST, ma_kh) AS position
  FROM grouped
)
SELECT ma_kh, ma_nt, order_count, order_amount, position
FROM ranked WHERE position <= %(top_n)s
ORDER BY ma_nt, position
