-- Tra cứu nhanh tem QR / ID tem / thùng / serial EERO & Ariston theo chỉ mục khóa chính
SELECT source_table,
       trace_code,
       parent_code,
       material_code,
       material_name,
       customer_code,
       warehouse_code,
       location_code,
       mold_code,
       lot_no,
       quantity,
       mfg_date,
       created_date,
       status_flag
FROM (
  SELECT 'data_intem'::text AS source_table,
         trim(d.id_tem) AS trace_code,
         coalesce(d.ma_thung, d.ma_khay, '') AS parent_code,
         ''::text AS material_code,
         ''::text AS material_name,
         ''::text AS customer_code,
         coalesce(d.ma_kho, '') AS warehouse_code,
         coalesce(d.ma_vi_tri, '') AS location_code,
         ''::text AS mold_code,
         ''::text AS lot_no,
         coalesce(d.so_luong_khay_thung, 0) AS quantity,
         NULL::date AS mfg_date,
         d.date0 AS created_date,
         coalesce(d.status::text, '') AS status_flag
  FROM public.data_intem d
  WHERE d.id_tem = trim(%s)
  UNION ALL
  SELECT 'intemeerolog'::text,
         trim(e.qrcode),
         coalesce(e.ma_in, e.ma_ban_ve, ''),
         coalesce(e.ma_vt, ''),
         coalesce(e.ten_vt, ''),
         coalesce(e.ma_kh, ''),
         ''::text,
         ''::text,
         coalesce(e.mold, ''),
         coalesce(e.ma_dinh_danh, ''),
         1::numeric,
         e.ngay_sx,
         e.date0,
         coalesce(e.status::text, '')
  FROM public.intemeerolog e
  WHERE e.qrcode = trim(%s)
  UNION ALL
  SELECT 'intem_serisp_log'::text,
         trim(s.qrcode),
         coalesce(s.ma_in, s.ma_ban_ve, ''),
         coalesce(s.ma_vt, ''),
         coalesce(s.ten_vt, ''),
         coalesce(s.ma_kh, ''),
         ''::text,
         ''::text,
         coalesce(s.mold, ''),
         coalesce(s.ma_dinh_danh, ''),
         1::numeric,
         s.ngay_sx,
         s.date0,
         coalesce(s.status::text, '')
  FROM public.intem_serisp_log s
  WHERE s.qrcode = trim(%s)
  UNION ALL
  SELECT 'mes_oi_dong_thung_eero'::text,
         trim(m.serial_tem_sp),
         coalesce(m.serial_tem_thung, ''),
         coalesce(m.ma_sp, ''),
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         coalesce(m.so_luong, 0),
         NULL::date,
         m.date0,
         coalesce(m.cavity::text, '')
  FROM public.mes_oi_dong_thung_eero m
  WHERE m.serial_tem_sp = trim(%s) OR m.serial_tem_thung = trim(%s)
  UNION ALL
  SELECT 'intem_aristonlog'::text,
         trim(a.qrcode),
         ''::text,
         coalesce(a.ma_vt, ''),
         coalesce(a.ten_vt, ''),
         coalesce(a.ma_kh, ''),
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         1::numeric,
         a.ngay_sx,
         a.date0,
         coalesce(a.status::text, '')
  FROM public.intem_aristonlog a
  WHERE a.qrcode = trim(%s)
  UNION ALL
  SELECT 'intem_carton_log'::text,
         trim(c.id_carton),
         coalesce(c.id_carton_new, ''),
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         1::numeric,
         NULL::date,
         c.date0,
         ''::text
  FROM public.intem_carton_log c
  WHERE c.id_carton = trim(%s) OR c.id_carton_new = trim(%s)
) res
WHERE EXISTS (SELECT 1 FROM public.userinfo u WHERE u.user_id = %s)
LIMIT %s;
