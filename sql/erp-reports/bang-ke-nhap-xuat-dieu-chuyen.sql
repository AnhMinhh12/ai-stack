WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay, %s::time AS tu_gio, %s::time AS den_gio,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den, coalesce(%s::text, '') AS ma_gd,
           coalesce(%s::text, '') AS ma_kh, coalesce(%s::text, '') AS ma_kho_xuat, coalesce(%s::text, '') AS ma_kho_nhap,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS nh_vt1, coalesce(%s::text, '') AS nh_vt2,
           coalesce(%s::text, '') AS nh_vt3, coalesce(%s::text, '') AS nh_vt4, coalesce(%s::text, '') AS nh_vt5,
           coalesce(%s::text, '') AS nh_vt6, coalesce(%s::text, '') AS nh_vt7, coalesce(%s::text, '') AS ma_dvcs,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), base AS (
    SELECT d.stt_rec, d.ln, h.ma_dvcs, h.ma_gd, d.ngay_ct, d.ma_ct, d.so_ct_to1, d.so_ct AS so_ct_pxb,
           i.so_ct AS so_ct_pnf, d.ma_vt, d.dvt, d.ma_kho, coalesce(i.ma_kho, h.ma_khon) AS ma_kho_nhap,
           lo.ma_vi_tri, pos.ma_vi_tri AS ma_vi_trin, d.so_luong, h.ma_kh, h.dien_giai,
           h.date0, h.time0, h.user_id0, h.date2, h.time2, h.user_id2
    FROM public.ct85 d JOIN public.ph85 h ON h.stt_rec = d.stt_rec CROSS JOIN access_scope a
    LEFT JOIN public.ctlo lo ON lo.stt_rec = d.stt_rec AND lo.ma_vt = d.ma_vt
    LEFT JOIN LATERAL (
        SELECT n.so_ct, n.ma_kho FROM public.ct85 n
        WHERE n.ma_ct = 'PNF' AND n.stt_rec_pxb = d.stt_rec ORDER BY n.ln LIMIT 1
    ) i ON true
    LEFT JOIN LATERAL (
        SELECT b.ma_vi_tri FROM public.ct70bsp b
        WHERE b.ma_ct = 'PNF' AND b.ma_vt = d.ma_vt AND b.ma_kho = coalesce(i.ma_kho, h.ma_khon)
          AND b.so_ct = coalesce(i.so_ct, d.so_ct) AND b.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
        ORDER BY b.ngay_ct DESC, b.ln LIMIT 1
    ) pos ON true
    LEFT JOIN public.dmvt vf ON vf.ma_vt = d.ma_vt
    WHERE a.authorized_user_id IS NOT NULL AND d.ma_ct = 'PXB'
      AND h.date0 BETWEEN a.tu_ngay AND a.den_ngay
      AND (h.date0 + h.time0) BETWEEN (a.tu_ngay + a.tu_gio) AND (a.den_ngay + a.den_gio)
      AND (a.so_ct_tu = '' OR d.so_ct >= a.so_ct_tu) AND (a.so_ct_den = '' OR d.so_ct <= a.so_ct_den)
      AND (a.ma_gd = '' OR h.ma_gd::text = ANY(string_to_array(a.ma_gd, ',')))
      AND (a.ma_kh = '' OR h.ma_kh = ANY(string_to_array(a.ma_kh, ',')))
      AND (a.ma_kho_xuat = '' OR d.ma_kho = ANY(string_to_array(a.ma_kho_xuat, ',')))
      AND (a.ma_kho_nhap = '' OR coalesce(i.ma_kho, h.ma_khon) = ANY(string_to_array(a.ma_kho_nhap, ',')))
      AND (a.ma_vt = '' OR d.ma_vt = ANY(string_to_array(a.ma_vt, ',')))
      AND (a.nh_vt1 = '' OR vf.nh_vt1 = ANY(string_to_array(a.nh_vt1, ',')))
      AND (a.nh_vt2 = '' OR vf.nh_vt2 = ANY(string_to_array(a.nh_vt2, ',')))
      AND (a.nh_vt3 = '' OR vf.nh_vt3 = ANY(string_to_array(a.nh_vt3, ',')))
      AND (a.nh_vt4 = '' OR vf.nh_vt4 = ANY(string_to_array(a.nh_vt4, ',')))
      AND (a.nh_vt5 = '' OR vf.nh_vt5 = ANY(string_to_array(a.nh_vt5, ',')))
      AND (a.nh_vt6 = '' OR vf.nh_vt6 = ANY(string_to_array(a.nh_vt6, ',')))
      AND (a.nh_vt7 = '' OR vf.nh_vt7 = ANY(string_to_array(a.nh_vt7, ',')))
      AND (a.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(a.ma_dvcs, ',')))
      AND (a.unrestricted OR a.ds_branchs = '' OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
      AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))))
      AND (coalesce(i.ma_kho, h.ma_khon) IS NULL OR coalesce(i.ma_kho, h.ma_khon) = '' OR a.unrestricted OR EXISTS (SELECT 1 FROM public.dmkho w WHERE w.ma_kho = coalesce(i.ma_kho, h.ma_khon) AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))))
)
SELECT 5::smallint AS sysorder, 1::smallint AS sysprint, 0::smallint AS systotal,
       row_number() OVER (ORDER BY b.so_ct_pxb DESC, b.stt_rec, b.ln) AS stt,
       b.stt_rec, b.ma_dvcs, b.ma_gd, b.ngay_ct, b.ma_ct, b.ma_ct AS ma_ct0, b.so_ct_to1,
       b.so_ct_pxb, b.so_ct_pnf, b.ln, b.ma_kh, kh.ten_kh, b.ma_kho, kx.ten_kho AS ten_kho_xuat,
       b.ma_kho_nhap AS ma_khon, kn.ten_kho AS ten_kho_nhap, b.ma_vi_tri, b.ma_vi_trin,
       b.dien_giai, b.ma_vt, vt.ten_vt, b.dvt, b.so_luong, gd.ten_gd, b.date0, b.time0,
       creator.user_name AS user_name0, b.date2, b.time2, editor.user_name AS user_name2,
       b.user_id0, b.user_id2, count(*) OVER () AS total
FROM base b LEFT JOIN public.dmvt vt ON vt.ma_vt = b.ma_vt LEFT JOIN public.dmkh kh ON kh.ma_kh = b.ma_kh
LEFT JOIN public.dmkho kx ON kx.ma_kho = b.ma_kho AND kx.ma_dvcs = b.ma_dvcs
LEFT JOIN public.dmkho kn ON kn.ma_kho = b.ma_kho_nhap AND kn.ma_dvcs = b.ma_dvcs
LEFT JOIN public.sys_dmmagd gd ON gd.ma_ct = b.ma_ct AND gd.ma_gd = b.ma_gd
LEFT JOIN public.userinfo creator ON creator.user_id = b.user_id0 LEFT JOIN public.userinfo editor ON editor.user_id = b.user_id2
ORDER BY b.so_ct_pxb DESC, b.stt_rec, b.ln LIMIT (SELECT row_limit FROM params);
