WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den,
           coalesce(%s::text, '') AS ma_kh, coalesce(%s::text, '') AS ma_kho,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_dvcs,
           coalesce(%s::text, '') AS status, %s::integer AS authenticated_user_id,
           %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
)
SELECT 5::smallint AS sysorder, d.stt_rec, d.ln, h.ngay_lct, h.ngay_ct, h.so_ct,
       h.ma_kh, k.ten_viet_tat AS ten_kh, h.ma_dvcs, h.ma_nt, h.ty_gia,
       h.dien_giai, s.statusname, d.ma_vt, v.ten_vt, d.dvt, d.ma_kho,
       d.so_luong, d.sl_duyet, d.gia_nt2, d.gia2, d.tien_nt2, d.tien2,
       d.ck_nt, d.ck, d.thue_nt, d.thue,
       d.tien2 - d.ck + d.thue AS pt,
       d.tien_nt2 - d.ck_nt + d.thue_nt AS pt_nt,
       coalesce(p_customer.gia0, p_general.gia0, 0) AS gia_chuan_nt,
       coalesce(p_customer.gia0, p_general.gia0, 0) * h.ty_gia AS gia_chuan,
       abs(d.gia_nt2 - coalesce(p_customer.gia0, p_general.gia0, 0)) AS gia_chenh_lech_nt,
       abs(d.gia2 - coalesce(p_customer.gia0, p_general.gia0, 0) * h.ty_gia) AS gia_chenh_lech,
       d.sl_duyet * d.gia_nt2 AS tien2_closing,
       d.sl_duyet * d.gia_nt2 * d.thue_suat / 100 AS thue_closing,
       d.sl_duyet * d.gia_nt2 * d.pt_ck / 100 AS ck_closing,
       d.sl_duyet * d.gia_nt2 * (1 - d.pt_ck / 100 + d.thue_suat / 100) AS pt_closing,
       gh.ghi_chu, u.user_name, count(*) OVER () AS total
FROM public.ct81 d
JOIN public.ph81 h ON h.stt_rec = d.stt_rec
CROSS JOIN access_scope x
LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
LEFT JOIN public.sys_dmtt s ON s.ma_ct = 'HDA' AND s.status = h.status
LEFT JOIN public.ctkhgh gh ON gh.stt_rec = d.stt_rec_to2 AND gh.ln = d.ln_to2
LEFT JOIN public.userinfo u ON u.user_id = h.user_id0
LEFT JOIN LATERAL (
    SELECT g.gia0 FROM public.dmbanggiact g
    WHERE g.loai_gia = 3 AND g.ma_kh = h.ma_kh AND g.ma_vt = d.ma_vt
      AND g.dvt = d.dvt AND g.ma_nt = h.ma_nt AND h.ngay_ct BETWEEN g.ngay_bd AND g.ngay_kt
      AND g.sl_min <= d.so_luong
    ORDER BY g.sl_min DESC LIMIT 1
) p_customer ON true
LEFT JOIN LATERAL (
    SELECT g.gia0 FROM public.dmbanggiact g
    WHERE g.loai_gia = 1 AND g.ma_vt = d.ma_vt AND g.dvt = d.dvt
      AND g.ma_nt = h.ma_nt AND h.ngay_ct BETWEEN g.ngay_bd AND g.ngay_kt
      AND g.sl_min <= d.so_luong
    ORDER BY g.sl_min DESC LIMIT 1
) p_general ON true
WHERE x.authorized_user_id IS NOT NULL AND h.ma_gd <> 4
  AND h.ngay_lct BETWEEN x.tu_ngay AND x.den_ngay
  AND (x.so_ct_tu = '' OR h.so_ct >= x.so_ct_tu) AND (x.so_ct_den = '' OR h.so_ct <= x.so_ct_den)
  AND (x.ma_kh = '' OR h.ma_kh = ANY(string_to_array(x.ma_kh, ',')))
  AND (x.ma_kho = '' OR d.ma_kho = ANY(string_to_array(x.ma_kho, ',')))
  AND (x.ma_vt = '' OR d.ma_vt = ANY(string_to_array(x.ma_vt, ',')))
  AND (x.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(x.ma_dvcs, ',')))
  AND (x.status = '' OR h.status = ANY(string_to_array(x.status, ',')))
  AND (x.unrestricted OR x.ds_branchs = '' OR h.ma_dvcs = ANY(string_to_array(x.ds_branchs, ',')))
  AND (d.ma_kho IS NULL OR d.ma_kho = '' OR x.unrestricted OR EXISTS (
      SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho
        AND w.ma_dvcs = ANY(string_to_array(x.ds_branchs, ','))
  ))
ORDER BY d.stt_rec, d.ln
LIMIT (SELECT row_limit FROM params)
