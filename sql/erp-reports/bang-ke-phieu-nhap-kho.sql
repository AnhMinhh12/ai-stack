WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay, %s::time AS tu_gio, %s::time AS den_gio,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den,
           coalesce(%s::text, '') AS ma_kh, coalesce(%s::text, '') AS ma_kho, coalesce(%s::text, '') AS ma_vt,
           coalesce(%s::text, '') AS nh_vt1, coalesce(%s::text, '') AS nh_vt2, coalesce(%s::text, '') AS nh_vt3,
           coalesce(%s::text, '') AS nh_vt4, coalesce(%s::text, '') AS nh_vt5, coalesce(%s::text, '') AS nh_vt6,
           coalesce(%s::text, '') AS nh_vt7, coalesce(%s::text, '') AS tk_vt, coalesce(%s::text, '') AS ma_ct,
           coalesce(%s::text, '') AS ma_vv, coalesce(%s::text, '') AS ma_dvcs, coalesce(%s::text, '') AS ma_gd,
           coalesce(%s::text, '') AS status, %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), rounding AS (
    SELECT coalesce(max(value1::integer) FILTER (WHERE trim(option_name) = 'M_ROUND_GIA_NT'), 4) AS gia_nt_scale,
           coalesce(max(value1::integer) FILTER (WHERE trim(option_name) = 'M_ROUND_TIEN_NT'), 4) AS tien_nt_scale
    FROM public.sys_options
), base AS (
    SELECT a.stt_rec, a.ln, a.stt_rec_dc, a.ln_dc, a.ma_dvcs2, a.ma_ct, a.ma_gd,
           a.ngay_ct, a.ngay_lct, a.so_ct, a.ma_vt, a.dvt, a.ma_kho, a.dien_giai,
           a.sl_nhap, a.sl_xuat, a.gia, a.ty_gia, a.tien_nhap, a.tien_xuat, a.nk,
           a.cp, a.ma_nt, a.ma_nx, a.tk_vt, a.ma_vv, a.ma_bp, a.ma_cp, a.ma_cd_gt,
           a.date0, a.time0, a.user_id0, a.date2, a.time2, a.user_id2, a.status,
           h.ma_gd AS ma_gd_ph, h.ma_loainx,
           coalesce(nullif(a.ma_kh, ''), nullif(h.ma_kh, ''), dn.ma_kh) AS ma_kh_hien_thi
    FROM public.ct70 a LEFT JOIN public.ph74 h ON h.stt_rec = a.stt_rec
    LEFT JOIN LATERAL (
        SELECT nullif(p.ma_kh, '') AS ma_kh FROM public.ct74 d JOIN public.phdnv p ON p.stt_rec = d.stt_rec_dnv
        WHERE d.stt_rec = a.stt_rec AND d.ma_vt = a.ma_vt ORDER BY d.ln LIMIT 1
    ) dn ON true CROSS JOIN access_scope s
    WHERE s.authorized_user_id IS NOT NULL AND a.nxt = 1 AND a.date0 BETWEEN s.tu_ngay AND s.den_ngay
      AND (a.date0 + a.time0) BETWEEN (s.tu_ngay + s.tu_gio) AND (s.den_ngay + s.den_gio)
      AND (s.so_ct_tu = '' OR a.so_ct >= s.so_ct_tu) AND (s.so_ct_den = '' OR a.so_ct <= s.so_ct_den)
      AND (s.ma_kho = '' OR a.ma_kho = ANY(string_to_array(s.ma_kho, ',')))
      AND (s.ma_vt = '' OR a.ma_vt = ANY(string_to_array(s.ma_vt, ',')))
      AND (s.tk_vt = '' OR a.tk_vt = ANY(string_to_array(s.tk_vt, ',')))
      AND (s.ma_ct = '' OR a.ma_ct = ANY(string_to_array(s.ma_ct, ',')))
      AND (s.ma_vv = '' OR a.ma_vv = ANY(string_to_array(s.ma_vv, ',')))
      AND (s.ma_dvcs = '' OR a.ma_dvcs2 = ANY(string_to_array(s.ma_dvcs, ',')))
      AND (s.ma_gd = '' OR coalesce(h.ma_gd, a.ma_gd)::text = ANY(string_to_array(s.ma_gd, ',')))
      AND (s.status = '' OR a.status::text = ANY(string_to_array(s.status, ',')))
      AND (s.nh_vt1 = '' OR EXISTS (SELECT 1 FROM public.dmvt v WHERE v.ma_vt = a.ma_vt AND v.nh_vt1 = ANY(string_to_array(s.nh_vt1, ','))))
      AND (s.nh_vt2 = '' OR EXISTS (SELECT 1 FROM public.dmvt v WHERE v.ma_vt = a.ma_vt AND v.nh_vt2 = ANY(string_to_array(s.nh_vt2, ','))))
      AND (s.nh_vt3 = '' OR EXISTS (SELECT 1 FROM public.dmvt v WHERE v.ma_vt = a.ma_vt AND v.nh_vt3 = ANY(string_to_array(s.nh_vt3, ','))))
      AND (s.nh_vt4 = '' OR EXISTS (SELECT 1 FROM public.dmvt v WHERE v.ma_vt = a.ma_vt AND v.nh_vt4 = ANY(string_to_array(s.nh_vt4, ','))))
      AND (s.nh_vt5 = '' OR EXISTS (SELECT 1 FROM public.dmvt v WHERE v.ma_vt = a.ma_vt AND v.nh_vt5 = ANY(string_to_array(s.nh_vt5, ','))))
      AND (s.nh_vt6 = '' OR EXISTS (SELECT 1 FROM public.dmvt v WHERE v.ma_vt = a.ma_vt AND v.nh_vt6 = ANY(string_to_array(s.nh_vt6, ','))))
      AND (s.nh_vt7 = '' OR EXISTS (SELECT 1 FROM public.dmvt v WHERE v.ma_vt = a.ma_vt AND v.nh_vt7 = ANY(string_to_array(s.nh_vt7, ','))))
      AND (s.unrestricted OR s.ds_branchs = '' OR a.ma_dvcs2 = ANY(string_to_array(s.ds_branchs, ',')))
      AND (a.ma_kho IS NULL OR a.ma_kho = '' OR s.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho k WHERE k.ma_kho = a.ma_kho AND k.ma_dvcs = a.ma_dvcs2
            AND (s.ds_branchs = '' OR k.ma_dvcs = ANY(string_to_array(s.ds_branchs, ',')))
      ))
)
SELECT 5::smallint AS sysorder, row_number() OVER (ORDER BY b.ngay_ct DESC, b.so_ct DESC, b.stt_rec, b.ln) AS stt,
       b.stt_rec, b.ln, b.stt_rec_dc, b.ln_dc, b.ma_dvcs2 AS ma_dvcs, b.ma_ct, coalesce(b.ma_gd_ph, b.ma_gd) AS ma_gd,
       gd.ten_gd, b.ngay_ct, b.ngay_lct, b.so_ct, b.ma_kh_hien_thi AS ma_kh, kh.ten_kh, kh.ten_kh2,
       b.ma_vt, vt.ten_vt, vt.ten_vt2, b.dvt, b.ma_kho, kho.ten_kho, kho.ten_kho2, b.ma_loainx, b.dien_giai,
       b.sl_nhap AS so_luong, b.sl_nhap, b.sl_xuat, b.gia,
       CASE WHEN b.ty_gia <> 0 THEN round(b.gia / b.ty_gia, r.gia_nt_scale) ELSE b.gia END AS gia_nt,
       b.tien_nhap AS tien, CASE WHEN b.ty_gia <> 0 THEN round(b.tien_nhap / b.ty_gia, r.tien_nt_scale) ELSE b.tien_nhap END AS tien_nt,
       b.tien_nhap, CASE WHEN b.ty_gia <> 0 THEN round(b.tien_nhap / b.ty_gia, r.tien_nt_scale) ELSE b.tien_nhap END AS tien_nhap_nt,
       b.tien_xuat, CASE WHEN b.ty_gia <> 0 THEN round(b.tien_xuat / b.ty_gia, r.tien_nt_scale) ELSE b.tien_xuat END AS tien_xuat_nt,
       b.nk, CASE WHEN b.ty_gia <> 0 THEN round(b.nk / b.ty_gia, r.tien_nt_scale) ELSE b.nk END AS nk_nt,
       b.cp, CASE WHEN b.ty_gia <> 0 THEN round(b.cp / b.ty_gia, r.tien_nt_scale) ELSE b.cp END AS cp_nt,
       b.ma_nt, CASE WHEN b.ty_gia = 0 THEN 1 ELSE b.ty_gia END AS ty_gia, b.ma_nx, b.tk_vt,
       b.ma_vv, vv.ten_vv, vv.ten_vv2, b.ma_bp, bp.ten_bp, bp.ten_bp2, b.ma_cp, cp.ten_cp, cp.ten_cp2,
       b.ma_cd_gt, cd.ten_cd_gt, cd.ten_cd_gt2, b.date0, b.time0, creator.user_name AS nguoi_lap,
       b.date2, b.time2, editor.user_name AS nguoi_sua, b.status, count(*) OVER () AS total
FROM base b CROSS JOIN rounding r CROSS JOIN params p
LEFT JOIN public.dmkh kh ON kh.ma_kh = b.ma_kh_hien_thi LEFT JOIN public.dmvt vt ON vt.ma_vt = b.ma_vt
LEFT JOIN public.dmkho kho ON kho.ma_kho = b.ma_kho AND kho.ma_dvcs = b.ma_dvcs2
LEFT JOIN public.dmvv vv ON vv.ma_vv = b.ma_vv LEFT JOIN public.dmbp bp ON bp.ma_bp = b.ma_bp
LEFT JOIN public.dmcp cp ON cp.ma_cp = b.ma_cp LEFT JOIN public.dmcdgt cd ON cd.ma_cd_gt = b.ma_cd_gt
LEFT JOIN public.sys_dmmagd gd ON gd.ma_ct = b.ma_ct AND gd.ma_gd = coalesce(b.ma_gd_ph, b.ma_gd)
LEFT JOIN public.userinfo creator ON creator.user_id = b.user_id0 LEFT JOIN public.userinfo editor ON editor.user_id = b.user_id2
WHERE p.ma_kh = '' OR b.ma_kh_hien_thi = ANY(string_to_array(p.ma_kh, ','))
ORDER BY b.ngay_ct DESC, b.so_ct DESC, b.stt_rec, b.ln LIMIT (SELECT row_limit FROM params);
