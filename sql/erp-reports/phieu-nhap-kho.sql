WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den,
           coalesce(%s::text, '') AS ma_kh, coalesce(%s::text, '') AS ma_kho,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_dvcs,
           coalesce(%s::text, '') AS ma_gd, coalesce(%s::text, '') AS status,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), base AS (
    SELECT h.stt_rec, d.ln, h.ma_dvcs, h.ma_ct, h.ma_gd, h.ngay_ct, h.ngay_lct, h.so_ct,
           h.ma_kh, h.ong_ba, h.dien_giai, h.ma_loainx, h.ma_nt, h.ty_gia,
           h.t_so_luong, h.t_tien_nt, h.t_tien, h.status, h.user_id0, h.date0, h.time0,
           h.user_id2, h.date2, h.time2, d.ma_vt, d.dvt, d.he_so, d.ma_kho, d.ton13,
           d.so_luong, d.pn_gia_tb, d.gia_nt, d.gia, d.tien_nt, d.tien, d.tk_vt,
           d.ma_nx, d.ma_vv, d.ma_cd_gt, d.ma_bp, d.ma_cp, d.sl_qt,
           d.stt_rec_pxa, d.so_ct_pxa, d.ln_pxa, d.stt_rec_kk1, d.so_ct_kk1, d.ln_kk1,
           d.stt_rec_tk1, d.so_ct_tk1, d.ln_tk1, d.stt_rec_pd1, d.so_ct_pd1, d.ln_pd1,
           d.stt_rec_dnv, d.so_ct_dnv, d.ln_dnv
    FROM public.ct74 d JOIN public.ph74 h ON h.stt_rec = d.stt_rec CROSS JOIN access_scope a
    WHERE a.authorized_user_id IS NOT NULL AND h.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
      AND (a.so_ct_tu = '' OR h.so_ct >= a.so_ct_tu) AND (a.so_ct_den = '' OR h.so_ct <= a.so_ct_den)
      AND (a.ma_kh = '' OR h.ma_kh = ANY(string_to_array(a.ma_kh, ',')))
      AND (a.ma_kho = '' OR d.ma_kho = ANY(string_to_array(a.ma_kho, ',')))
      AND (a.ma_vt = '' OR d.ma_vt = ANY(string_to_array(a.ma_vt, ',')))
      AND (a.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(a.ma_dvcs, ',')))
      AND (a.ma_gd = '' OR h.ma_gd::text = ANY(string_to_array(a.ma_gd, ',')))
      AND (a.status = '' OR h.status::text = ANY(string_to_array(a.status, ',')))
      AND (a.unrestricted OR a.ds_branchs = '' OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
      AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho
            AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))))
)
SELECT 5::smallint AS sysorder, row_number() OVER (ORDER BY b.ngay_ct DESC, b.so_ct DESC, b.ln) AS stt,
       b.stt_rec, b.ln, b.ma_dvcs, b.ma_ct, b.ma_gd, b.ngay_ct, b.ngay_lct, b.so_ct,
       b.ma_kh, kh.ten_kh, kh.ten_kh2, b.ong_ba, b.dien_giai, b.ma_loainx, b.ma_nt, b.ty_gia,
       b.ma_vt, vt.ten_vt, vt.ten_vt2, b.dvt, b.he_so, b.ma_kho, kho.ten_kho, kho.ten_kho2,
       b.ton13, b.so_luong AS sl_nhap, b.pn_gia_tb, b.gia_nt, b.gia, b.tien_nt,
       b.tien AS tien_nhap, b.tk_vt, b.ma_nx, b.ma_vv, vv.ten_vv, vv.ten_vv2, b.ma_cd_gt,
       b.ma_bp, bp.ten_bp, b.ma_cp, b.sl_qt, b.stt_rec_pxa, b.so_ct_pxa, b.ln_pxa,
       b.stt_rec_kk1, b.so_ct_kk1, b.ln_kk1, b.stt_rec_tk1, b.so_ct_tk1, b.ln_tk1,
       b.stt_rec_pd1, b.so_ct_pd1, b.ln_pd1, b.stt_rec_dnv, b.so_ct_dnv, b.ln_dnv,
       b.t_so_luong, b.t_tien_nt, b.t_tien, b.status, st.statusname, creator.user_name AS nguoi_tao,
       b.date0, b.time0, editor.user_name AS nguoi_sua, b.date2, b.time2, count(*) OVER () AS total
FROM base b
LEFT JOIN public.dmkh kh ON kh.ma_kh = b.ma_kh
LEFT JOIN public.dmvt vt ON vt.ma_vt = b.ma_vt
LEFT JOIN public.dmkho kho ON kho.ma_kho = b.ma_kho AND kho.ma_dvcs = b.ma_dvcs
LEFT JOIN public.dmvv vv ON vv.ma_vv = b.ma_vv
LEFT JOIN public.dmbp bp ON bp.ma_bp = b.ma_bp
LEFT JOIN public.sys_dmtt st ON st.ma_ct = b.ma_ct AND st.loai_gd = b.ma_gd AND st.status = b.status
LEFT JOIN public.userinfo creator ON creator.user_id = b.user_id0
LEFT JOIN public.userinfo editor ON editor.user_id = b.user_id2
ORDER BY b.ngay_ct DESC, b.so_ct DESC, b.ln LIMIT (SELECT row_limit FROM params);
