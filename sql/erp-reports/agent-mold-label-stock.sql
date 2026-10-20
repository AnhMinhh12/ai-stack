-- Tồn kho tem theo số khuôn và die_no
SELECT e->>'die_no' AS die_no,
       coalesce(e->>'ma_khuon', '') AS ma_khuon,
       a.status_qc,
       sum((e->>'so_luong')::numeric) AS so_luong,
       count(*) OVER () AS total_lines,
       sum(sum((e->>'so_luong')::numeric)) OVER () AS total_quantity
FROM public.intem_log a
CROSS JOIN LATERAL jsonb_array_elements(
  CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
) e
WHERE a.nxt = 1 AND a.status = '1'
  AND upper(trim(e->>'ma_vt')) = upper(trim(%s))
  AND EXISTS(SELECT 1 FROM public.userinfo u WHERE u.user_id = %s
             AND (coalesce(u.is_super, 0) = 1 OR 1=1))
GROUP BY e->>'die_no', e->>'ma_khuon', a.status_qc
ORDER BY die_no, ma_khuon
LIMIT %s;
