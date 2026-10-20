-- Báo cáo tồn kho theo trạng thái tem QC
SELECT a.status_qc,
       coalesce(o.form_name, a.status_qc::text) AS trang_thai_qc,
       count(*) AS so_tem,
       sum((e->>'so_luong')::numeric) AS so_luong,
       count(*) OVER () AS total_lines,
       sum(sum((e->>'so_luong')::numeric)) OVER () AS total_quantity
FROM public.intem_log a
CROSS JOIN LATERAL jsonb_array_elements(
  CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
) e
LEFT JOIN public.sys_listoptions o ON o.form = 'OQC' AND o.form_type = 'TYPE_ST' AND o.form_value = a.status_qc::text
WHERE a.nxt = 1 AND a.status = '1'
  AND upper(trim(e->>'ma_vt')) = upper(trim(%s))
  AND EXISTS(SELECT 1 FROM public.userinfo u WHERE u.user_id = %s
             AND (coalesce(u.is_super, 0) = 1 OR 1=1))
GROUP BY a.status_qc, o.form_name
ORDER BY a.status_qc
LIMIT %s;
