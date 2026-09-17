SELECT a.ngay_ct, a.so_ct, a.ma_ct, a.ma_gd, a.ma_kh,
       k.ten_kh, a.ma_vt, v.ten_vt, coalesce(v.dvt, a.dvt) AS dvt,
       a.ma_kho, a.ma_nt, CASE WHEN a.ty_gia = 0 THEN 1 ELSE a.ty_gia END AS ty_gia,
       a.loai_vt_xuat, a.sl_nhap, a.sl_xuat, a.gia, a.tien_nhap, a.tien_xuat,
       CASE WHEN a.ty_gia <> 0 THEN a.gia / a.ty_gia ELSE a.gia END AS gia_nt,
       CASE WHEN a.ty_gia <> 0 THEN a.tien_nhap / a.ty_gia ELSE a.tien_nhap END AS tien_nhap_nt,
       CASE WHEN a.ty_gia <> 0 THEN a.tien_xuat / a.ty_gia ELSE a.tien_xuat END AS tien_xuat_nt,
       a.ma_cp, a.ma_vv, CASE WHEN a.ma_ct = 'PND' THEN p74.ma_loainx WHEN a.ma_ct = 'PXA' THEN p84.ma_loainx END AS ma_loainx,
       a.ma_cd_gt, a.ma_bp, a.tk_vt, a.ma_nx, a.tk_gv, v.tk_dt, a.nxt,
       a.date0, a.time0, u0.user_name AS user_name, a.date2, a.time2, u2.user_name AS user_name2,
       a.dien_giai, status.statusname AS status_name, count(*) OVER() AS total
FROM public.ct70 AS a
LEFT JOIN public.dmvt AS v ON v.ma_vt = a.ma_vt
LEFT JOIN public.dmkh AS k ON k.ma_kh = a.ma_kh
LEFT JOIN public.userinfo AS u0 ON u0.user_id = a.user_id0
LEFT JOIN public.userinfo AS u2 ON u2.user_id = a.user_id2
LEFT JOIN public.sys_dmtt AS status ON status.ma_ct = a.ma_ct AND status.status = a.status
LEFT JOIN public.ph74 AS p74 ON p74.stt_rec = a.stt_rec AND a.ma_ct = 'PND'
LEFT JOIN public.ph84 AS p84 ON p84.stt_rec = a.stt_rec AND a.ma_ct = 'PXA'
WHERE a.ngay_ct BETWEEN %s AND %s AND a.ma_dvcs2 = %s
  AND (%s = '' OR upper(trim(a.ma_vt)) = %s)
  AND (%s = '' OR upper(trim(a.ma_kho)) = %s)
  AND (%s = '' OR upper(trim(coalesce(u0.user_name, ''))) = %s)
  AND (%s = '' OR upper(trim(coalesce(u2.user_name, ''))) = %s)
ORDER BY a.stt_rec, a.ma_vt
LIMIT %s
