WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den,
           coalesce(%s::text, '') AS ma_kh, coalesce(%s::text, '') AS ma_kho,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_dvcs,
           coalesce(%s::text, '') AS ma_gd, coalesce(%s::text, '') AS ma_vv,
           coalesce(%s::text, '') AS tk_vt, coalesce(%s::text, '') AS status,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), base AS (
    SELECT a.stt_rec, a.ln, a.ngay_lct, a.ngay_ct, a.so_ct, a.ma_ct, a.ma_gd,
           a.ma_kh, a.ma_kho, a.ma_nt, a.ty_gia, a.ma_vt, a.dvt,
           a.sl_nhap, a.sl_xuat, a.gia, a.tien_nhap, a.tien_xuat, a.nk, a.cp,
           a.tk_vt, a.tk_gv, a.ma_nx, a.ma_dvcs2 AS ma_dvcs, a.ma_vv, a.ma_bp,
           a.ma_cp, a.ma_cd_gt, a.stt_rec_dc, a.dien_giai, a.date0, a.time0,
           a.user_id0, a.date2, a.time2, a.user_id2, a.status,
           h.ma_loainx, h.ong_ba, h.ma_day_chuyen, h.t_so_luong, h.t_tien_nt,
           h.t_tien, d.loai_hinh
    FROM public.ct70 a
    JOIN public.ph84 h ON h.stt_rec = a.stt_rec AND a.ma_ct = 'PXA'
    LEFT JOIN public.ct84 d ON d.stt_rec = a.stt_rec AND d.ln = a.ln
    CROSS JOIN access_scope s
    WHERE s.authorized_user_id IS NOT NULL
      AND a.nxt = 2 AND a.ma_ct = 'PXA'
      AND a.ngay_ct BETWEEN s.tu_ngay AND s.den_ngay
      AND (s.so_ct_tu = '' OR a.so_ct >= s.so_ct_tu)
      AND (s.so_ct_den = '' OR a.so_ct <= s.so_ct_den)
      AND (s.ma_kh = '' OR a.ma_kh = ANY(string_to_array(s.ma_kh, ',')))
      AND (s.ma_kho = '' OR a.ma_kho = ANY(string_to_array(s.ma_kho, ',')))
      AND (s.ma_vt = '' OR a.ma_vt = ANY(string_to_array(s.ma_vt, ',')))
      AND (s.ma_dvcs = '' OR a.ma_dvcs2 = ANY(string_to_array(s.ma_dvcs, ',')))
      AND (s.ma_gd = '' OR a.ma_gd::text = ANY(string_to_array(s.ma_gd, ',')))
      AND (s.ma_vv = '' OR a.ma_vv = ANY(string_to_array(s.ma_vv, ',')))
      AND (s.tk_vt = '' OR a.tk_vt = ANY(string_to_array(s.tk_vt, ',')))
      AND (s.status = '' OR a.status = ANY(string_to_array(s.status, ',')))
      AND (s.unrestricted OR s.ds_branchs = '' OR a.ma_dvcs2 = ANY(string_to_array(s.ds_branchs, ',')))
      AND (a.ma_kho IS NULL OR a.ma_kho = '' OR s.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho k WHERE k.ma_kho = a.ma_kho
            AND k.ma_dvcs = ANY(string_to_array(s.ds_branchs, ','))
      ))
)
SELECT 5::smallint AS sysorder,
       row_number() OVER (ORDER BY b.ngay_ct DESC, b.so_ct DESC, b.stt_rec, b.ln) AS stt,
       b.stt_rec, b.ln, b.ngay_lct, b.ngay_ct, b.so_ct, b.ma_ct, b.ma_gd,
       b.ma_dvcs, b.ma_kh, kh.ten_kh, kh.ten_kh2, b.ma_kho, kho.ten_kho, kho.ten_kho2,
       b.ma_vt, vt.ten_vt, vt.ten_vt2, coalesce(vt.dvt, b.dvt) AS dvt,
       b.sl_xuat AS so_luong, b.sl_nhap, b.sl_xuat, b.gia,
       CASE WHEN b.ty_gia <> 0 THEN b.gia / b.ty_gia ELSE b.gia END AS gia_nt,
       b.tien_nhap AS tien, CASE WHEN b.ty_gia <> 0 THEN b.tien_nhap / b.ty_gia ELSE b.tien_nhap END AS tien_nt,
       b.tien_nhap, CASE WHEN b.ty_gia <> 0 THEN b.tien_nhap / b.ty_gia ELSE b.tien_nhap END AS tien_nhap_nt,
       b.tien_xuat, CASE WHEN b.ty_gia <> 0 THEN b.tien_xuat / b.ty_gia ELSE b.tien_xuat END AS tien_xuat_nt,
       b.nk, CASE WHEN b.ty_gia <> 0 THEN b.nk / b.ty_gia ELSE b.nk END AS nk_nt,
       b.cp, CASE WHEN b.ty_gia <> 0 THEN b.cp / b.ty_gia ELSE b.cp END AS cp_nt,
       b.ma_nt, CASE WHEN b.ty_gia = 0 THEN 1 ELSE b.ty_gia END AS ty_gia,
       b.ma_nx, b.ma_loainx, b.ma_vv, vv.ten_vv, b.ma_bp, bp.ten_bp,
       b.ma_day_chuyen, b.ma_cp, cp.ten_cp, b.ma_cd_gt, cd.ten_cd_gt,
       b.dien_giai, b.ong_ba AS nguoi_nhan, gd.ten_gd, b.loai_hinh,
       b.stt_rec_dc, b.t_so_luong, b.t_tien_nt, b.t_tien,
       b.status, st.statusname, b.date0, b.time0, creator.user_name AS nguoi_tao,
       b.date2, b.time2, editor.user_name AS nguoi_sua, count(*) OVER () AS total
FROM base b
LEFT JOIN public.dmkh kh ON kh.ma_kh = b.ma_kh
LEFT JOIN public.dmvt vt ON vt.ma_vt = b.ma_vt
LEFT JOIN public.dmkho kho ON kho.ma_kho = b.ma_kho AND kho.ma_dvcs = b.ma_dvcs
LEFT JOIN public.dmvv vv ON vv.ma_vv = b.ma_vv
LEFT JOIN public.dmbp bp ON bp.ma_bp = b.ma_bp
LEFT JOIN public.dmcp cp ON cp.ma_cp = b.ma_cp
LEFT JOIN public.dmcdgt cd ON cd.ma_cd_gt = b.ma_cd_gt
LEFT JOIN public.sys_dmmagd gd ON gd.ma_ct = b.ma_ct AND gd.ma_gd = b.ma_gd
LEFT JOIN public.sys_dmtt st ON st.ma_ct = b.ma_ct AND st.status = b.status
LEFT JOIN public.userinfo creator ON creator.user_id = b.user_id0
LEFT JOIN public.userinfo editor ON editor.user_id = b.user_id2
ORDER BY b.ngay_ct DESC, b.so_ct DESC, b.stt_rec, b.ln
LIMIT (SELECT row_limit FROM params);
