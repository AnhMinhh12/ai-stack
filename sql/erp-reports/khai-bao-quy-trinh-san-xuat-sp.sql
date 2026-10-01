WITH params AS (
    SELECT coalesce(%s::text, '') AS product_code, coalesce(%s::text, '') AS routing_code,
           coalesce(%s::text, '') AS branch_code, coalesce(nullif(%s::text, ''), '1') AS status,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT b.bom_code, b.product_code, v.ten_vt, b.bom_version, b.routing_code, r.routing_name,
       b.branch_list AS branch_code,
       CASE WHEN b.status::text = '1' THEN 'Sử dụng'
            WHEN b.status::text = '0' THEN 'Không sử dụng'
            ELSE '' END AS trang_thai,
       b.status::text AS status,
       count(*) OVER () AS total
FROM public.mfbom b
CROSS JOIN access_scope a
LEFT JOIN public.mflist_routing r ON r.routing_code = b.routing_code
LEFT JOIN public.dmvt v ON v.ma_vt = b.product_code
WHERE a.authorized_user_id IS NOT NULL
  AND (a.unrestricted OR coalesce(b.branch_list, '') = '' OR EXISTS (
      SELECT 1 FROM unnest(string_to_array(a.ds_branchs, ',')) branch_code
      WHERE branch_code = ANY(string_to_array(b.branch_list, ','))
  ))
  AND (a.product_code = '' OR upper(trim(b.product_code)) = a.product_code)
  AND (a.routing_code = '' OR upper(trim(b.routing_code)) = a.routing_code)
  AND (a.branch_code = '' OR b.branch_list = ANY(string_to_array(a.branch_code, ',')))
  AND b.status::text = '1'
  AND (a.status = '*' OR b.status::text = a.status)
ORDER BY b.bom_code
LIMIT (SELECT row_limit FROM params)
