WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den,
           coalesce(%s::text, '') AS ma_nv, coalesce(%s::text, '') AS ma_vt,
           coalesce(%s::text, '') AS ma_dvcs, coalesce(%s::text, '') AS status,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), requested AS (
    SELECT h.stt_rec, d.ln, h.ngay_ct, h.so_ct, h.ma_ct, h.ma_dvcs, h.ma_nv,
           h.ma_bp, h.dien_giai, h.ma_nt, h.ty_gia, h.status, h.ma_ct AS giao_dich,
           h.ma_md AS muc_do, h.t_so_luong,
           h.user_id0, h.date0, h.time0, h.user_id2, h.date2, h.time2,
           d.ma_vt, d.dvt, d.so_luong, d.ngay_yc, d.dien_giai AS mo_ta,
           d.muc_dich_sd, d.ma_kho, d.ma_vv, d.close_yn
    FROM public.ct91 d
    JOIN public.ph91 h ON h.stt_rec = d.stt_rec
    CROSS JOIN access_scope a
    WHERE a.authorized_user_id IS NOT NULL
      AND h.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
      AND (a.so_ct_tu = '' OR h.so_ct >= a.so_ct_tu)
      AND (a.so_ct_den = '' OR h.so_ct <= a.so_ct_den)
      AND (a.ma_nv = '' OR h.ma_nv = ANY(string_to_array(a.ma_nv, ',')))
      AND (a.ma_vt = '' OR d.ma_vt = ANY(string_to_array(a.ma_vt, ',')))
      AND (a.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(a.ma_dvcs, ',')))
      AND (a.status = '' OR h.status::text = ANY(string_to_array(a.status, ',')))
      AND (a.unrestricted OR a.ds_branchs = ''
           OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
      AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho w
          WHERE w.ma_kho = d.ma_kho
            AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))
      ))
), ordered AS (
    SELECT x.stt_rec_pr0 AS stt_rec, x.ln_pr0 AS ln, x.ma_vt, sum(x.so_luong) AS so_luong_dh
    FROM public.ctkhnh_po1 x
    JOIN public.ph94 h ON h.stt_rec = x.stt_rec
    JOIN requested r ON r.stt_rec = x.stt_rec_pr0 AND r.ln = x.ln_pr0 AND r.ma_vt = x.ma_vt
    WHERE h.status IN ('1', '2', '3', '4', '11')
    GROUP BY x.stt_rec_pr0, x.ln_pr0, x.ma_vt
), received AS (
    SELECT x.stt_rec_pr0 AS stt_rec, x.ln_pr0 AS ln, x.ma_vt, coalesce(sum(i.so_luong), 0) AS sl_nhap
    FROM public.ctkhnh x
    LEFT JOIN public.ct77 i ON i.stt_rec_po1 = x.stt_rec AND i.ln_po1 = x.ln
    JOIN public.ph94 h ON h.stt_rec = x.stt_rec
    JOIN requested r ON r.stt_rec = x.stt_rec_pr0 AND r.ln = x.ln_pr0 AND r.ma_vt = x.ma_vt
    WHERE h.status IN ('12', '13')
    GROUP BY x.stt_rec_pr0, x.ln_pr0, x.ma_vt
), quantities AS (
    SELECT r.*, coalesce(o.so_luong_dh, 0) AS so_luong_dh, coalesce(i.sl_nhap, 0) AS sl_nhap,
           CASE WHEN r.close_yn = 1 THEN r.so_luong - coalesce(o.so_luong_dh, 0) - coalesce(i.sl_nhap, 0) ELSE 0 END AS so_luong_dong
    FROM requested r
    LEFT JOIN ordered o ON o.stt_rec = r.stt_rec AND o.ln = r.ln AND o.ma_vt = r.ma_vt
    LEFT JOIN received i ON i.stt_rec = r.stt_rec AND i.ln = r.ln AND i.ma_vt = r.ma_vt
)
SELECT 5::smallint AS sysorder, row_number() OVER (ORDER BY q.ngay_ct DESC, q.so_ct DESC, q.ln) AS stt,
       q.stt_rec, q.ln, q.ngay_ct, q.so_ct, q.ma_ct, q.ma_dvcs, q.ma_nv,
       requester.ten_kh AS ten_nv, q.dien_giai, q.ma_nt, q.ty_gia, q.giao_dich,
       q.muc_do, q.t_so_luong,
       q.user_id0, q.date0, q.time0, creator.user_name AS user_name,
       q.user_id2, q.date2, q.time2, updater.user_name AS updated_by,
       concat_ws(' ', q.date2::text, q.time2::text, updater.user_name) AS lich_su_cap_nhat,
       q.ma_vt, v.ten_vt, v.ten_vt2,
       v.nh_vt1, v.nh_vt2, v.nh_vt3, v.nh_vt4, v.nh_vt5, v.nh_vt6, v.nh_vt7,
       q.dvt, q.so_luong, q.so_luong_dh, q.sl_nhap, q.so_luong_dong,
       CASE WHEN q.status = '12' THEN 0 ELSE q.so_luong - q.so_luong_dh - q.sl_nhap - q.so_luong_dong END AS so_luong_cl,
       q.ngay_yc, q.ngay_yc + v.leadtime::integer AS ngay_ve_tc,
       abs((q.ngay_yc + v.leadtime::integer) - q.ngay_yc) AS ngay_cl,
       q.mo_ta, q.muc_dich_sd, q.ma_kho, q.ma_vv, vv.ten_vv,
       q.ma_bp, bp.ten_bp, q.status, st.statusname, q.close_yn,
       count(*) OVER () AS total
FROM quantities q
LEFT JOIN public.dmkh requester ON requester.ma_kh = q.ma_nv
LEFT JOIN public.dmvt v ON v.ma_vt = q.ma_vt
LEFT JOIN public.dmvv vv ON vv.ma_vv = q.ma_vv
LEFT JOIN public.dmbp bp ON bp.ma_bp = q.ma_bp
LEFT JOIN public.userinfo creator ON creator.user_id = q.user_id0
LEFT JOIN public.userinfo updater ON updater.user_id = q.user_id2
LEFT JOIN public.sys_dmtt st ON st.ma_ct = 'PR0' AND st.status = q.status
ORDER BY q.ngay_ct DESC, q.so_ct DESC, q.ln
LIMIT (SELECT row_limit FROM params);
