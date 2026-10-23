-- Read-only ledger balance per warehouse for one material and as-of date.
WITH scope AS (
    SELECT user_id, coalesce(is_super, 0) = 1 AS superuser,
           string_to_array(coalesce(ds_stocks, ''), ',') AS warehouses
    FROM public.userinfo WHERE user_id = %s
), opening AS (
    SELECT c.ma_kho, sum(c.ton00) AS qty
    FROM public.cdvt c CROSS JOIN scope s
    WHERE c.nam = extract(year FROM %s::date)::smallint
      AND upper(trim(c.ma_vt)) = upper(trim(%s))
      AND (s.superuser OR c.ma_kho = ANY(s.warehouses))
    GROUP BY c.ma_kho
), movements AS (
    SELECT c.ma_kho, sum(c.sl_nhap - c.sl_xuat) AS qty
    FROM public.ct70 c CROSS JOIN scope s
    WHERE upper(trim(c.ma_vt)) = upper(trim(%s))
      AND c.ngay_ct BETWEEN make_date(extract(year FROM %s::date)::integer, 1, 1) AND %s::date
      AND (s.superuser OR c.ma_kho = ANY(s.warehouses))
    GROUP BY c.ma_kho
), balances AS (
    SELECT ma_kho, qty FROM opening
    UNION ALL
    SELECT ma_kho, qty FROM movements
), grouped AS (
    SELECT ma_kho, sum(qty) AS so_luong_ton FROM balances GROUP BY ma_kho
)
SELECT g.ma_kho, k.ten_kho, v.dvt, g.so_luong_ton,
       count(*) OVER () AS total_lines,
       sum(g.so_luong_ton) OVER () AS total_quantity
FROM grouped g JOIN public.dmkho k ON k.ma_kho = g.ma_kho
JOIN public.dmvt v ON v.ma_vt = %s
WHERE g.so_luong_ton <> 0
ORDER BY g.ma_kho
LIMIT %s
