WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay, coalesce(%s::text, '') AS ma_dvcs,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), requested AS (
    SELECT h.stt_rec, d.ln, h.ngay_ct, h.so_ct, h.ma_dvcs, h.ma_bp AS ma_bp_header, h.dien_giai, h.status,
           h.user_id0, d.ma_bp, d.ma_kh, d.ma_vt, d.dvt, d.so_luong, d.ngay_yc, d.dien_giai AS mo_ta,
           d.muc_dich_sd, d.ma_kho, d.loai_hinh, d.close_yn
    FROM public.ct91 d JOIN public.ph91 h ON h.stt_rec = d.stt_rec CROSS JOIN access_scope a
    WHERE a.authorized_user_id IS NOT NULL AND h.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
      AND (a.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(a.ma_dvcs, ',')))
      AND (a.unrestricted OR a.ds_branchs = '' OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
      AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))))
), ordered AS (
    SELECT x.stt_rec_pr0 AS stt_rec, x.ln_pr0 AS ln, x.ma_vt, sum(x.so_luong) AS so_luong_dh
    FROM public.ctkhnh_po1 x JOIN public.ph94 h ON h.stt_rec = x.stt_rec
    JOIN requested r ON r.stt_rec = x.stt_rec_pr0 AND r.ln = x.ln_pr0 AND r.ma_vt = x.ma_vt
    WHERE h.status IN ('1', '2', '3', '4', '11')
    GROUP BY x.stt_rec_pr0, x.ln_pr0, x.ma_vt
), received AS (
    SELECT x.stt_rec_pr0 AS stt_rec, x.ln_pr0 AS ln, x.ma_vt, sum(i.so_luong) AS sl_nhap
    FROM public.ctkhnh x JOIN public.ct77 i ON i.stt_rec_po1 = x.stt_rec AND i.ln_po1 = x.ln
    JOIN public.ph94 h ON h.stt_rec = x.stt_rec
    JOIN requested r ON r.stt_rec = x.stt_rec_pr0 AND r.ln = x.ln_pr0 AND r.ma_vt = x.ma_vt
    WHERE h.status IN ('12', '13')
    GROUP BY x.stt_rec_pr0, x.ln_pr0, x.ma_vt
), quantities AS (
    SELECT r.*, coalesce(o.so_luong_dh, 0) AS so_luong_dh, coalesce(i.sl_nhap, 0) AS sl_nhap,
           CASE WHEN r.close_yn = 1 THEN r.so_luong - coalesce(o.so_luong_dh, 0) - coalesce(i.sl_nhap, 0) ELSE 0 END AS so_luong_dong
    FROM requested r LEFT JOIN ordered o ON o.stt_rec = r.stt_rec AND o.ln = r.ln AND o.ma_vt = r.ma_vt
    LEFT JOIN received i ON i.stt_rec = r.stt_rec AND i.ln = r.ln AND i.ma_vt = r.ma_vt
)
SELECT row_number() OVER (ORDER BY q.ngay_ct DESC, q.so_ct DESC, q.ln) AS stt,
       q.stt_rec, q.ln, q.ngay_ct, q.so_ct, q.ma_dvcs, coalesce(q.ma_bp, q.ma_bp_header) AS ma_bp, bp.ten_bp,
       q.ma_vt, v.ten_vt, v.ten_vt2, q.dvt, q.so_luong, q.so_luong_dh, q.sl_nhap, q.so_luong_dong,
       CASE WHEN q.status = '12' THEN 0 ELSE q.so_luong - q.so_luong_dh - q.sl_nhap - q.so_luong_dong END AS so_luong_cl,
       q.ngay_yc, q.ngay_yc + v.leadtime::integer AS ngay_ve_tc,
       abs((q.ngay_yc + v.leadtime::integer) - q.ngay_yc) AS ngay_cl,
       ncc.ten_kh, v.nh_vt1, v.nh_vt2, v.nh_vt3, v.nh_vt4, v.nh_vt5, v.nh_vt6, v.nh_vt7,
       q.mo_ta, q.muc_dich_sd, q.ma_kho, q.loai_hinh, q.dien_giai, creator.user_name AS nguoi_tao,
       q.status, status.statusname, count(*) OVER () AS total
FROM quantities q
LEFT JOIN public.dmvt v ON v.ma_vt = q.ma_vt
LEFT JOIN public.dmkh ncc ON ncc.ma_kh = q.ma_kh
LEFT JOIN public.dmbp bp ON bp.ma_bp = coalesce(q.ma_bp, q.ma_bp_header)
LEFT JOIN public.userinfo creator ON creator.user_id = q.user_id0
LEFT JOIN public.sys_dmtt status ON status.ma_ct = 'PR0' AND status.status = q.status
ORDER BY q.ngay_ct DESC, q.so_ct DESC, q.ln LIMIT (SELECT row_limit FROM params);
