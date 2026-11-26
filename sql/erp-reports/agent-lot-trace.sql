-- Tra cứu lô hàng (ctlo, dmloupdatehsd), vị trí kho (dmvitri), quy cách đóng gói (dmvtqcdg) và quy đổi ĐVT (dmqddvt) theo mã lô hoặc mã vật tư
SELECT source_type,
       material_code,
       material_name,
       lot_no,
       supplier_lot,
       warehouse_code,
       location_code,
       doc_no,
       doc_date,
       mfg_date,
       expiry_date,
       unit,
       factor_or_qty,
       extra_code
FROM (
  SELECT 'ctlo'::text AS source_type,
         coalesce(l.ma_vt, '') AS material_code,
         coalesce(v.ten_vt, '') AS material_name,
         coalesce(l.ma_lo, '') AS lot_no,
         coalesce(l.ma_lo_ncc, '') AS supplier_lot,
         coalesce(l.ma_kho, '') AS warehouse_code,
         coalesce(l.ma_vi_tri, '') AS location_code,
         coalesce(l.so_ct, '') AS doc_no,
         l.ngay_ct AS doc_date,
         l.ngay_sx AS mfg_date,
         l.ngay_hhsd AS expiry_date,
         coalesce(l.dvt, v.dvt, '') AS unit,
         coalesce(l.so_luong, 0) AS factor_or_qty,
         coalesce(l.ma_ct, '') AS extra_code
  FROM public.ctlo l
  LEFT JOIN public.dmvt v ON v.ma_vt = l.ma_vt
  WHERE l.ma_lo = trim(%s) OR l.ma_vt = trim(%s)
  UNION ALL
  SELECT 'dmloupdatehsd'::text,
         coalesce(h.ma_vt, ''),
         coalesce(v.ten_vt, ''),
         coalesce(h.ma_lo, ''),
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         h.ngay_ghdk,
         NULL::date,
         h.ngay_hhsd,
         coalesce(v.dvt, ''),
         0::numeric,
         coalesce(h.status::text, '')
  FROM public.dmloupdatehsd h
  LEFT JOIN public.dmvt v ON v.ma_vt = h.ma_vt
  WHERE h.ma_lo = trim(%s) OR h.ma_vt = trim(%s)
  UNION ALL
  SELECT 'dmvtqcdg'::text,
         coalesce(p.ma_vt, ''),
         coalesce(v.ten_vt, ''),
         ''::text,
         ''::text,
         ''::text,
         coalesce(p.ma_thung, ''),
         ''::text,
         NULL::date,
         NULL::date,
         NULL::date,
         coalesce(v.dvt, ''),
         coalesce(p.so_luong_vt_thung, 0),
         CASE WHEN p.default_yn IS TRUE THEN 'default' ELSE '' END
  FROM public.dmvtqcdg p
  LEFT JOIN public.dmvt v ON v.ma_vt = p.ma_vt
  WHERE p.ma_vt = trim(%s)
  UNION ALL
  SELECT 'dmqddvt'::text,
         coalesce(q.ma_vt, ''),
         coalesce(v.ten_vt, ''),
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         ''::text,
         NULL::date,
         NULL::date,
         NULL::date,
         coalesce(q.dvt, ''),
         coalesce(q.he_so, 0),
         coalesce(q.dvt1, '')
  FROM public.dmqddvt q
  LEFT JOIN public.dmvt v ON v.ma_vt = q.ma_vt
  WHERE q.ma_vt = trim(%s)
) sub
WHERE EXISTS (
  SELECT 1 FROM public.userinfo u WHERE u.user_id = %s
  AND (coalesce(u.is_super, 0) = 1 OR coalesce(u.ds_stocks, '') = '' OR sub.warehouse_code = '' OR sub.warehouse_code = ANY(string_to_array(coalesce(u.ds_stocks, ''), ',')))
)
ORDER BY doc_date DESC NULLS LAST, source_type
LIMIT %s;
