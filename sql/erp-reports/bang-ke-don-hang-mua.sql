WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den,
           coalesce(%s::text, '') AS ma_kh, coalesce(%s::text, '') AS ma_vt,
           coalesce(%s::text, '') AS ma_dvcs, coalesce(%s::text, '') AS status,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT 5::smallint AS sysorder, row_number() OVER (ORDER BY h.so_ct DESC, d.ln) AS stt,
       h.stt_rec, d.ln, h.ngay_ct, h.so_ct, h.ma_ct, h.ma_dvcs, h.ma_kh,
       k.ten_kh, k.ten_kh2, h.ma_nt, h.ty_gia, h.ma_nx, h.ma_bp, bp.ten_bp,
       h.dien_giai, h.status, s.statusname, h.date0, h.time0, creator.user_name,
       h.date2, h.time2, editor.user_name, d.ma_vt, v.ten_vt, v.ten_vt2, d.dvt,
       v.nh_vt1, v.nh_vt2, v.nh_vt3, v.nh_vt4, v.nh_vt5, v.nh_vt6, v.nh_vt7,
       d.so_luong, d.gia_nt0, d.tien_nt0, d.gia_nt, d.tien_nt, d.thue_nt, d.ck_nt, d.nk_nt,
       d.gia, d.tien, d.thue, d.ck, d.nk, d.ma_kho, d.ma_vv, vv.ten_vv, d.tk_vt,
       d.so_ct_pr0, count(*) OVER () AS total
FROM public.ct94 d JOIN public.ph94 h ON h.stt_rec = d.stt_rec
CROSS JOIN access_scope a
LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
LEFT JOIN public.dmbp bp ON bp.ma_bp = h.ma_bp LEFT JOIN public.dmvv vv ON vv.ma_vv = d.ma_vv
LEFT JOIN public.sys_dmtt s ON s.ma_ct = 'PO1' AND s.status = h.status
LEFT JOIN public.userinfo creator ON creator.user_id = h.user_id0 LEFT JOIN public.userinfo editor ON editor.user_id = h.user_id2
WHERE a.authorized_user_id IS NOT NULL AND h.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
  AND (a.so_ct_tu = '' OR h.so_ct >= a.so_ct_tu) AND (a.so_ct_den = '' OR h.so_ct <= a.so_ct_den)
  AND (a.ma_kh = '' OR h.ma_kh = ANY(string_to_array(a.ma_kh, ',')))
  AND (a.ma_vt = '' OR d.ma_vt = ANY(string_to_array(a.ma_vt, ',')))
  AND (a.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(a.ma_dvcs, ',')))
  AND (a.status = '' OR h.status::text = ANY(string_to_array(a.status, ',')))
  AND (a.unrestricted OR a.ds_branchs = '' OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
  AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (
      SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))
  ))
ORDER BY h.so_ct DESC, d.ln
LIMIT (SELECT row_limit FROM params)
