WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den,
           coalesce(%s::text, '') AS ma_kh, coalesce(%s::text, '') AS ma_kho,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_dvcs,
           coalesce(%s::text, '') AS ma_loainx, coalesce(%s::text, '') AS status,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), base AS (
    SELECT h.stt_rec, d.ln, h.ngay_ct, h.ngay_lct, h.so_ct, h.ma_ct, h.ma_dvcs, h.ma_kh,
           h.ong_ba, h.dien_giai, h.ma_gd, h.ma_loainx, h.ma_nt, h.ty_gia, h.status,
           h.ma_bp, h.ma_day_chuyen, h.t_so_luong, h.t_tien_nt, h.t_tien,
           h.user_id0, h.date0, h.time0, h.user_id2, h.date2, h.time2,
           d.ma_vt, d.dvt, d.ma_kho, d.so_luong, d.he_so, d.px_gia_dd, d.gia_nt, d.gia,
           d.tien_nt, d.tien, d.tk_vt, d.ma_nx, d.ma_vv, d.ma_cd_gt, d.ma_bp AS ma_bp_ct,
           d.ma_cp, d.sl_qt, d.stt_rec_dxv, d.so_ct_dxv, d.ln_dxv, d.stt_rec_kk1,
           d.so_ct_kk1, d.ln_kk1, d.stt_rec_pnd, d.so_ct_pnd, d.ln_pnd, d.loai_hinh
    FROM public.ct84 d JOIN public.ph84 h ON h.stt_rec = d.stt_rec CROSS JOIN access_scope a
    WHERE a.authorized_user_id IS NOT NULL AND h.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
      AND (a.so_ct_tu = '' OR h.so_ct >= a.so_ct_tu) AND (a.so_ct_den = '' OR h.so_ct <= a.so_ct_den)
      AND (a.ma_kh = '' OR h.ma_kh = ANY(string_to_array(a.ma_kh, ',')))
      AND (a.ma_kho = '' OR d.ma_kho = ANY(string_to_array(a.ma_kho, ',')))
      AND (a.ma_vt = '' OR d.ma_vt = ANY(string_to_array(a.ma_vt, ',')))
      AND (a.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(a.ma_dvcs, ',')))
      AND (a.ma_loainx = '' OR h.ma_loainx = ANY(string_to_array(a.ma_loainx, ',')))
      AND (a.status = '' OR h.status::text = ANY(string_to_array(a.status, ',')))
      AND (a.unrestricted OR a.ds_branchs = '' OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
      AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))
      ))
)
SELECT 5::smallint AS sysorder, row_number() OVER (ORDER BY x.ngay_ct DESC, x.so_ct DESC, x.ln) AS stt,
       x.stt_rec, x.ln, x.ngay_ct, x.ngay_lct, x.so_ct, x.ma_ct, x.ma_dvcs,
       x.ma_kh, kh.ten_kh, kh.ten_kh2, x.ong_ba, x.dien_giai,
       x.ma_gd, gd.ten_gd, gd.ten_gd2, x.ma_loainx, x.ma_nt, x.ty_gia,
       x.ma_vt, vt.ten_vt, vt.ten_vt2, x.dvt, x.ma_kho, kho.ten_kho, kho.ten_kho2,
       x.so_luong AS sl_xuat, x.he_so, x.px_gia_dd, x.gia_nt, x.gia,
       x.tien_nt AS tien_xuat_nt, x.tien AS tien_xuat, x.tk_vt, x.ma_nx,
       x.ma_vv, vv.ten_vv, x.ma_cd_gt, cd.ten_cd_gt, coalesce(x.ma_bp_ct, x.ma_bp) AS ma_bp,
       bp.ten_bp, x.ma_cp, cp.ten_cp, x.sl_qt, x.stt_rec_dxv, x.so_ct_dxv, x.ln_dxv,
       x.stt_rec_kk1, x.so_ct_kk1, x.ln_kk1, x.stt_rec_pnd, x.so_ct_pnd, x.ln_pnd,
       x.loai_hinh, x.ma_day_chuyen, x.t_so_luong, x.t_tien_nt, x.t_tien,
       x.status, st.statusname, creator.user_name AS nguoi_tao, x.date0, x.time0,
       editor.user_name AS nguoi_sua, x.date2, x.time2, count(*) OVER () AS total
FROM base x
LEFT JOIN public.dmkh kh ON kh.ma_kh = x.ma_kh LEFT JOIN public.dmvt vt ON vt.ma_vt = x.ma_vt
LEFT JOIN public.dmkho kho ON kho.ma_kho = x.ma_kho AND kho.ma_dvcs = x.ma_dvcs
LEFT JOIN public.dmvv vv ON vv.ma_vv = x.ma_vv LEFT JOIN public.dmbp bp ON bp.ma_bp = coalesce(x.ma_bp_ct, x.ma_bp)
LEFT JOIN public.dmcp cp ON cp.ma_cp = x.ma_cp LEFT JOIN public.dmcdgt cd ON cd.ma_cd_gt = x.ma_cd_gt
LEFT JOIN public.sys_dmmagd gd ON gd.ma_ct = x.ma_ct AND gd.ma_gd = x.ma_gd
LEFT JOIN public.sys_dmtt st ON st.ma_ct = 'PXB' AND st.status = x.status
LEFT JOIN public.userinfo creator ON creator.user_id = x.user_id0 LEFT JOIN public.userinfo editor ON editor.user_id = x.user_id2
ORDER BY x.ngay_ct DESC, x.so_ct DESC, x.ln LIMIT (SELECT row_limit FROM params);
