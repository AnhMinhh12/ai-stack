WITH params AS (
    SELECT coalesce(%s::text, '') AS id_tem, coalesce(%s::text, '') AS ma_vt,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT i.id_tem, i.data_tem->0->>'ma_vt' AS ma_vt,
       i.data_tem->0->>'ten_vt' AS ten_vt, i.data_tem->0->>'ma_lo' AS ma_lo,
       i.status_qc, o.form_name AS status_name, i.ma_kho,
       p.id_pallet, t.id_oi, t.mes_scheduling_code, count(*) OVER () AS total
FROM public.intem_log i
CROSS JOIN access_scope a
LEFT JOIN public.mes_oi_dong_thung t ON t.serial_tem_thung = i.id_tem
LEFT JOIN public.palletct p ON p.id_carton = i.id_tem
LEFT JOIN public.sys_listoptions o ON o.form = 'OQC' AND o.form_type = 'TYPE_ST'
                                 AND o.form_value::text = i.status_qc::text
WHERE a.authorized_user_id IS NOT NULL
  AND i.status = '1' AND i.nxt = 1
  AND (a.id_tem = '' OR i.id_tem = a.id_tem)
  AND (a.ma_vt = '' OR i.data_tem->0->>'ma_vt' = ANY(string_to_array(a.ma_vt, ',')))
  AND (i.ma_kho IS NULL OR i.ma_kho = '' OR a.unrestricted OR EXISTS (
      SELECT 1 FROM public.dmkho w
      WHERE w.ma_kho = i.ma_kho AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))
  ))
ORDER BY i.id_tem
LIMIT (SELECT row_limit FROM params);
