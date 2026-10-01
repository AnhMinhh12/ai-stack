WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct, coalesce(%s::text, '') AS ma_kh,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_dvcs,
           coalesce(%s::text, '') AS status, %s::integer AS authenticated_user_id,
           %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT h.stt_rec, d.ln, h.ngay_ct, h.so_ct, h.ma_kh, h.ten_kh, h.ma_dvcs,
       h.ma_nvbh, h.ma_nvgh, h.dien_giai, h.status,
       d.ma_vt, v.ten_vt, d.dvt, d.ma_kho, d.so_luong, d.so_luong_cl,
       d.gia2, d.tien2, d.ck, d.thue, d.tien2 + d.thue - d.ck AS t_tt,
       d.ngay_gh, d.gio_gh, gh.ngay_yc_gh, gh.ngay_gh AS ngay_gh_ke_hoach,
       gh.gio_gh AS gio_gh_ke_hoach, gh.so_luong AS so_luong_ke_hoach,
       d.stt_rec_so1, d.so_ct_so1, d.ln_so1, count(*) OVER () AS total
FROM public.ph96 h
JOIN public.ct96 d ON d.stt_rec = h.stt_rec
CROSS JOIN access_scope x
LEFT JOIN public.ctkhgh gh ON gh.stt_rec = d.stt_rec_gh AND gh.ln = d.ln_gh
LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
WHERE x.authorized_user_id IS NOT NULL
  AND h.ngay_ct BETWEEN x.tu_ngay AND x.den_ngay
  AND (x.so_ct = '' OR h.so_ct = x.so_ct)
  AND (x.ma_kh = '' OR h.ma_kh = ANY(string_to_array(x.ma_kh, ',')))
  AND (x.ma_vt = '' OR d.ma_vt = ANY(string_to_array(x.ma_vt, ',')))
  AND (x.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(x.ma_dvcs, ',')))
  AND (x.status = '' OR h.status = ANY(string_to_array(x.status, ',')))
  AND (x.unrestricted OR x.ds_branchs = ''
       OR h.ma_dvcs = ANY(string_to_array(x.ds_branchs, ',')))
  AND (d.ma_kho IS NULL OR d.ma_kho = '' OR x.unrestricted OR EXISTS (
      SELECT 1 FROM public.dmkho k
      WHERE k.ma_kho = d.ma_kho
        AND k.ma_dvcs = ANY(string_to_array(x.ds_branchs, ','))
  ))
ORDER BY h.stt_rec, d.ln
LIMIT (SELECT row_limit FROM params)
