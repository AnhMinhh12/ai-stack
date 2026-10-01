WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den,
           coalesce(%s::text, '') AS ma_kh, coalesce(%s::text, '') AS ma_kho,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_dvcs,
           coalesce(%s::text, '') AS status, %s::integer AS authenticated_user_id,
           %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), base AS (
    SELECT h.stt_rec, d.ln, h.ngay_ct, h.so_ct, h.ma_ct, h.ma_gd, h.ma_dvcs, h.ma_kh, h.ten_kh, h.ong_ba, h.dia_chi,
           h.ma_nx, h.ma_bp, h.dien_giai, h.ma_nt, h.ty_gia, h.status, h.user_id0, h.date0, h.time0, h.user_id2, h.date2, h.time2,
           h.so_hd, h.ngay_hd, h.t_so_luong, h.t_tien, h.t_thue, h.t_tt, d.ma_vt, d.dvt, d.so_luong, d.gia_nt0, d.tien_nt0,
           d.tien_nt, d.thue_nt, d.ck_nt, d.cp_nt, d.nk_nt, d.gia, d.gia_nt, d.gia0, d.tien0, d.tien,
           d.thue, d.ck, d.cp, d.nk, d.ma_kho, d.ma_vv, d.tk_vt, d.stt_rec_po1, d.ln_po1
    FROM public.ct77 d JOIN public.ph77 h ON h.stt_rec = d.stt_rec CROSS JOIN access_scope a
    WHERE a.authorized_user_id IS NOT NULL AND h.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
      AND (a.so_ct_tu = '' OR h.so_ct >= a.so_ct_tu) AND (a.so_ct_den = '' OR h.so_ct <= a.so_ct_den)
      AND (a.ma_kh = '' OR h.ma_kh = ANY(string_to_array(a.ma_kh, ',')))
      AND (a.ma_kho = '' OR d.ma_kho = ANY(string_to_array(a.ma_kho, ',')))
      AND (a.ma_vt = '' OR d.ma_vt = ANY(string_to_array(a.ma_vt, ',')))
      AND (a.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(a.ma_dvcs, ',')))
      AND (a.status = '' OR h.status::text = ANY(string_to_array(a.status, ',')))
      AND (a.unrestricted OR a.ds_branchs = '' OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
      AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))))
), linked AS (
    SELECT b.*, po.so_ct AS so_dh, pr.so_ct AS so_ycm, po.user_id0 AS po_user_id
    FROM base b LEFT JOIN public.ct94 pod ON pod.stt_rec = b.stt_rec_po1 AND pod.ln = b.ln_po1
    LEFT JOIN public.ph94 po ON po.stt_rec = pod.stt_rec
    LEFT JOIN public.ct91 prd ON prd.stt_rec = pod.stt_rec_pr0 AND prd.ln = pod.ln_pr0
    LEFT JOIN public.ph91 pr ON pr.stt_rec = prd.stt_rec
)
SELECT 5::smallint AS sysorder, row_number() OVER (ORDER BY x.ngay_ct DESC, x.so_ct DESC, x.ln) AS stt,
       x.stt_rec, x.ln, x.ngay_ct, x.so_ct, x.ngay_hd, x.so_hd, x.ma_ct, x.ma_gd, x.ma_dvcs, x.ma_kh, x.ten_kh,
       x.ong_ba, x.dia_chi, x.dien_giai, x.ma_nt, x.ty_gia, x.t_so_luong, x.t_tien, x.t_thue, x.t_tt,
       x.ma_nx, x.ma_vt, vt.ten_vt, vt.ten_vt2, x.dvt, x.so_luong AS sl_nhap, x.gia_nt0, x.tien_nt0, x.tien_nt,
       x.thue_nt, x.ck_nt, x.cp_nt, x.nk_nt, x.gia, x.gia_nt, x.gia0, x.tien0, x.tien AS tien_nhap, x.thue, x.ck, x.cp, x.nk,
       x.ma_kho, x.ma_vv, vv.ten_vv, x.tk_vt, x.ma_bp, bp.ten_bp, x.so_dh, x.so_ycm,
       x.status, st.statusname, gd.ten_gd, creator.user_name AS nguoi_tao, po_creator.user_name AS nguoi_tao_dh,
       concat_ws(' ', x.date2::text, x.time2::text, editor.user_name) AS lich_su_cap_nhat,
       count(*) OVER () AS total
FROM linked x
LEFT JOIN public.dmvt vt ON vt.ma_vt = x.ma_vt LEFT JOIN public.dmvv vv ON vv.ma_vv = x.ma_vv
LEFT JOIN public.dmbp bp ON bp.ma_bp = x.ma_bp
LEFT JOIN public.sys_dmmagd gd ON gd.ma_ct = x.ma_ct AND gd.ma_gd = x.ma_gd
LEFT JOIN public.sys_dmtt st ON st.ma_ct = 'PR1' AND st.status = x.status
LEFT JOIN public.userinfo creator ON creator.user_id = x.user_id0
LEFT JOIN public.userinfo editor ON editor.user_id = x.user_id2
LEFT JOIN public.userinfo po_creator ON po_creator.user_id = x.po_user_id
ORDER BY x.ngay_ct DESC, x.so_ct DESC, x.ln LIMIT (SELECT row_limit FROM params);
