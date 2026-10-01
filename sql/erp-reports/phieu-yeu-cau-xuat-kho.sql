WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den,
           coalesce(%s::text, '') AS ma_bp, coalesce(%s::text, '') AS ma_nv,
           coalesce(%s::text, '') AS ma_kho, coalesce(%s::text, '') AS ma_vt,
           coalesce(%s::text, '') AS ma_dvcs, coalesce(%s::text, '') AS status,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), requested AS (
    SELECT h.stt_rec, d.ln, h.ngay_ct, h.ngay_lct, h.so_ct, h.ma_ct, h.ma_gd, h.ma_dvcs,
           h.ma_nv, h.ma_bp, h.ma_phan_xuong, h.ma_kh, h.dien_giai, h.ma_nt, h.ty_gia,
           h.t_so_luong, h.status, h.user_id0, h.date0, h.time0, h.user_id2, h.date2, h.time2,
           d.ma_vt, d.dvt, d.so_luong, d.ngay_xuat_kho, d.ghi_chu, d.ma_kho,
           d.ton13, d.he_so, d.close_yn, d.stt_rec_pd1, d.so_ct_pd1, d.ln_pd1
    FROM public.ctdxnvl d
    JOIN public.phdxnvl h ON h.stt_rec = d.stt_rec
    CROSS JOIN access_scope a
    WHERE a.authorized_user_id IS NOT NULL
      AND h.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
      AND (a.so_ct_tu = '' OR h.so_ct >= a.so_ct_tu)
      AND (a.so_ct_den = '' OR h.so_ct <= a.so_ct_den)
      AND (a.ma_bp = '' OR h.ma_bp = ANY(string_to_array(a.ma_bp, ',')))
      AND (a.ma_nv = '' OR h.ma_nv = ANY(string_to_array(a.ma_nv, ',')))
      AND (a.ma_kho = '' OR d.ma_kho = ANY(string_to_array(a.ma_kho, ',')))
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
), exported AS (
    SELECT x.stt_rec_dxv AS stt_rec, x.ln_dxv AS ln, x.ma_vt,
           sum(x.so_luong) AS sl_xuat, max(x.ngay_ct) AS ngay_xuat_thuc_te,
           string_agg(DISTINCT x.so_ct, ', ' ORDER BY x.so_ct) AS ds_so_px
    FROM public.ct84 x
    JOIN requested r ON r.stt_rec = x.stt_rec_dxv AND r.ln = x.ln_dxv AND r.ma_vt = x.ma_vt
    GROUP BY x.stt_rec_dxv, x.ln_dxv, x.ma_vt
)
SELECT 5::smallint AS sysorder,
       row_number() OVER (ORDER BY r.ngay_ct DESC, r.so_ct DESC, r.ln) AS stt,
       r.stt_rec, r.ln, r.ngay_ct, r.ngay_lct, r.so_ct, r.ma_ct, r.ma_gd, r.ma_dvcs,
       r.ma_nv, r.ma_bp, bp.ten_bp, bp.ten_bp2, r.ma_phan_xuong, r.ma_kh,
       r.dien_giai, r.ma_nt, r.ty_gia, r.t_so_luong,
       r.ma_vt, vt.ten_vt, vt.ten_vt2, r.dvt, r.ma_kho, kho.ten_kho, kho.ten_kho2,
       r.so_luong AS sl_yeu_cau, coalesce(e.sl_xuat, 0) AS sl_xuat,
       CASE WHEN r.close_yn = 1 THEN 0 ELSE greatest(r.so_luong - coalesce(e.sl_xuat, 0), 0) END AS sl_con_lai,
       r.ngay_xuat_kho, e.ngay_xuat_thuc_te, e.ds_so_px, r.ghi_chu, r.ton13, r.he_so,
       r.close_yn, r.stt_rec_pd1, r.so_ct_pd1, r.ln_pd1,
       r.status, st.statusname, r.user_id0, r.date0, r.time0, creator.user_name AS nguoi_tao,
       r.user_id2, r.date2, r.time2, editor.user_name AS nguoi_sua,
       count(*) OVER () AS total
FROM requested r
LEFT JOIN exported e ON e.stt_rec = r.stt_rec AND e.ln = r.ln AND e.ma_vt = r.ma_vt
LEFT JOIN public.dmvt vt ON vt.ma_vt = r.ma_vt
LEFT JOIN public.dmbp bp ON bp.ma_bp = r.ma_bp
LEFT JOIN public.dmkho kho ON kho.ma_kho = r.ma_kho AND kho.ma_dvcs = r.ma_dvcs
LEFT JOIN public.sys_dmtt st ON st.ma_ct = 'DXV' AND st.status = r.status
LEFT JOIN public.userinfo creator ON creator.user_id = r.user_id0
LEFT JOIN public.userinfo editor ON editor.user_id = r.user_id2
ORDER BY r.ngay_ct DESC, r.so_ct DESC, r.ln
LIMIT (SELECT row_limit FROM params);
