WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           %s::date AS tu_ngay_gh, %s::date AS den_ngay_gh,
           coalesce(%s::text, '') AS so_ct, coalesce(%s::text, '') AS ma_kh,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_dvcs,
           coalesce(%s::text, '') AS status, coalesce(%s::smallint, 0) AS loai_chi_thi,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT 5::smallint AS sysorder,
       row_number() OVER (ORDER BY h.so_ct DESC, d.ln) AS stt,
       h.stt_rec, d.ln, h.ngay_ct, h.so_ct, h.ma_ct, h.ma_dvcs, h.ma_kh,
       k.ten_viet_tat AS ten_kh, h.ngay_gh, h.gio_gh, x.ngay_gh_tt,
       d.ma_vt, v.ten_vt, v.ten_vt2, d.dvt, d.ma_kho, d.so_luong,
       lo.ma_lo, coalesce(lo.so_luong, 0) AS so_luong_da_lo, d.so_luong_cl,
       h.ma_nt, h.ty_gia, h.dien_giai, gh.ghi_chu,
       st.statusname AS status_name, h.date0 AS ngay_tao, h.time0 AS gio_tao,
       creator.user_name AS nguoi_tao, h.date2 AS ngay_sua, h.time2 AS gio_sua,
       editor.user_name AS nguoi_sua, count(*) OVER () AS total
FROM public.ct96 d
JOIN public.ph96 h ON h.stt_rec = d.stt_rec
CROSS JOIN access_scope a
LEFT JOIN public.ct96lo lo ON lo.stt_rec = d.stt_rec AND lo.ma_vt = d.ma_vt AND lo.ln_ct96 = d.ln
LEFT JOIN public.ctkhgh gh ON gh.stt_rec = d.stt_rec AND gh.ma_vt = d.ma_vt AND gh.ln_item = d.ln
LEFT JOIN LATERAL (
    SELECT min(i.ngay_ct) AS ngay_gh_tt FROM public.ct81 i
    WHERE i.stt_rec_to2 = d.stt_rec AND i.ma_vt = d.ma_vt AND i.ngay_ct >= a.tu_ngay
) x ON true
LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
LEFT JOIN public.sys_dmtt st ON st.ma_ct = 'TO2' AND st.status = h.status
LEFT JOIN public.userinfo creator ON creator.user_id = h.user_id0
LEFT JOIN public.userinfo editor ON editor.user_id = h.user_id2
WHERE a.authorized_user_id IS NOT NULL
  AND h.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
  AND (a.tu_ngay_gh IS NULL OR h.ngay_gh >= a.tu_ngay_gh)
  AND (a.den_ngay_gh IS NULL OR h.ngay_gh <= a.den_ngay_gh)
  AND (a.so_ct = '' OR h.so_ct = a.so_ct)
  AND (a.ma_kh = '' OR h.ma_kh = ANY(string_to_array(a.ma_kh, ',')))
  AND (a.ma_vt = '' OR d.ma_vt = ANY(string_to_array(a.ma_vt, ',')))
  AND (a.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(a.ma_dvcs, ',')))
  AND (a.status = '' OR h.status::text = ANY(string_to_array(a.status, ',')))
  AND (a.loai_chi_thi = 0 OR (a.loai_chi_thi = 1 AND d.so_luong_cl > 0)
       OR (a.loai_chi_thi = 2 AND coalesce(lo.so_luong, 0) > 0))
  AND (a.unrestricted OR a.ds_branchs = '' OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
  AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (
      SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho
        AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))
  ))
ORDER BY h.so_ct DESC, d.ma_vt, d.ln
LIMIT (SELECT row_limit FROM params)
