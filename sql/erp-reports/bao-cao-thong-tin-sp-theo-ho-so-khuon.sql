WITH params AS (
    SELECT coalesce(%s::text, '') AS mold_code,
           coalesce(%s::text, '') AS product_code,
           coalesce(nullif(%s::text, ''), '*') AS status,
           %s::integer AS authenticated_user_id,
           %s::integer AS row_limit
), scope AS (
    SELECT p.*, u.user_id AS authorized_user_id
    FROM params p
    LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT
    5::smallint AS sysorder,
    row_number() OVER (ORDER BY a.ma_khuon, a.ma_sp) AS stt,
    a.ma_khuon AS mold_code,
    coalesce(h.ten_khuon, '') AS mold_name,
    a.ma_sp AS product_code,
    coalesce(v.ten_vt, '') AS product_name,
    a.id_cap AS level_id,
    a.chu_ki AS cycle_time,
    CASE WHEN a.chinh_phu::text = '1' THEN 'Chính'
         WHEN a.chinh_phu::text = '0' THEN 'Phụ'
         ELSE coalesce(a.chinh_phu::text, '') END AS chinh_phu,
    a.cavity,
    CASE WHEN h.status::text = '1' THEN 'Sử dụng'
         WHEN h.status::text = '0' THEN 'Không sử dụng'
         ELSE '' END AS trang_thai,
    h.status,
    count(*) OVER () AS total
FROM public.dmhosokhuonsp a
JOIN scope s ON s.authorized_user_id IS NOT NULL
LEFT JOIN public.dmhosokhuon h ON h.ma_khuon = a.ma_khuon
LEFT JOIN public.dmvt v ON v.ma_vt = a.ma_sp
WHERE (s.mold_code = '' OR a.ma_khuon = ANY(string_to_array(s.mold_code, ',')))
  AND (s.product_code = '' OR a.ma_sp = ANY(string_to_array(s.product_code, ',')))
  AND (s.status = '*' OR h.status::text = s.status)
ORDER BY a.ma_khuon, a.ma_sp
LIMIT (SELECT row_limit FROM params)
