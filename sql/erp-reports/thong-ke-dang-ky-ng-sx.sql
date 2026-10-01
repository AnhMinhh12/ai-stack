WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS product_code,
           coalesce(%s::text, '') AS mes_scheduling_code,
           coalesce(%s::text, '') AS work_center_code,
           coalesce(%s::text, '') AS id_oi,
           coalesce(%s::text, '') AS branch_code,
           %s::integer AS authenticated_user_id,
           %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR coalesce(u.ds_branchs, '') = '' AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), production AS (
    SELECT c.id_oi, c.mes_scheduling_code, c.product_code, c.branch_code,
           max(c.quantity) AS sl_ke_hoach, sum(c.in_process) AS sl_thuc_te
    FROM public.mes_oi_confirm c CROSS JOIN access_scope a
    WHERE a.authorized_user_id IS NOT NULL
      AND c.create_date BETWEEN a.tu_ngay AND a.den_ngay
      AND (a.product_code = '' OR c.product_code = ANY(string_to_array(a.product_code, ',')))
      AND (a.mes_scheduling_code = '' OR c.mes_scheduling_code = ANY(string_to_array(a.mes_scheduling_code, ',')))
      AND (a.work_center_code = '' OR c.machine_code = ANY(string_to_array(a.work_center_code, ',')))
      AND (a.id_oi = '' OR c.id_oi = ANY(string_to_array(a.id_oi, ',')))
      AND (a.branch_code = '' OR c.branch_code = ANY(string_to_array(a.branch_code, ',')))
      AND (a.unrestricted OR c.branch_code = ANY(string_to_array(a.ds_branchs, ',')))
    GROUP BY c.id_oi, c.mes_scheduling_code, c.product_code, c.branch_code
), nonconforming AS (
    SELECT n.id_oi, n.mes_scheduling_code, n.product_code, sum(n.ng_qty) AS sl_ng
    FROM public.mes_oi_ng_confirm n
    GROUP BY n.id_oi, n.mes_scheduling_code, n.product_code
)
SELECT p.id_oi, p.mes_scheduling_code, p.product_code, p.branch_code,
       p.sl_ke_hoach, p.sl_thuc_te, coalesce(n.sl_ng, 0) AS sl_ng,
       count(*) OVER () AS total
FROM production p
LEFT JOIN nonconforming n ON n.id_oi = p.id_oi
                         AND n.mes_scheduling_code = p.mes_scheduling_code
                         AND n.product_code = p.product_code
ORDER BY p.id_oi
LIMIT (SELECT row_limit FROM params);
