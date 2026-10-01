WITH params AS (
    SELECT %s::date AS den_ngay, coalesce(%s::text, '') AS ma_kho, coalesce(%s::text, '') AS ma_vt,
           coalesce(%s::text, '') AS nh_vt1, coalesce(%s::text, '') AS nh_vt2, coalesce(%s::text, '') AS nh_vt3,
           coalesce(%s::text, '') AS nh_vt4, coalesce(%s::text, '') AS nh_vt5, coalesce(%s::text, '') AS nh_vt6,
           coalesce(%s::text, '') AS nh_vt7, coalesce(%s::text, '') AS tk_vt, coalesce(%s::text, '') AS ma_dvcs,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1 OR coalesce(u.ds_branchs, '') = '' AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), balances AS (
    SELECT c.ma_vt, c.ma_kho, sum(c.ton00) AS so_luong, sum(c.du00) AS tien
    FROM public.cdvt c JOIN public.dmkho k ON k.ma_kho = c.ma_kho CROSS JOIN scope s
    WHERE s.authorized_user_id IS NOT NULL AND c.nam = extract(year FROM s.den_ngay)::smallint
      AND (s.ma_kho = '' OR c.ma_kho = ANY(string_to_array(s.ma_kho, ',')))
      AND (s.ma_vt = '' OR c.ma_vt = ANY(string_to_array(s.ma_vt, ',')))
      AND (s.ma_dvcs = '' OR k.ma_dvcs = ANY(string_to_array(s.ma_dvcs, ',')))
      AND (s.unrestricted OR k.ma_dvcs = ANY(string_to_array(s.ds_branchs, ','))) GROUP BY c.ma_vt, c.ma_kho
    UNION ALL
    SELECT c.ma_vt, c.ma_kho, sum(c.sl_nhap - c.sl_xuat), sum(c.tien_nhap - c.tien_xuat)
    FROM public.ct70 c CROSS JOIN scope s
    WHERE s.authorized_user_id IS NOT NULL AND c.ngay_ct BETWEEN make_date(extract(year FROM s.den_ngay)::integer, 1, 1) AND s.den_ngay
      AND (s.ma_kho = '' OR c.ma_kho = ANY(string_to_array(s.ma_kho, ','))) AND (s.ma_vt = '' OR c.ma_vt = ANY(string_to_array(s.ma_vt, ',')))
      AND (s.ma_dvcs = '' OR c.ma_dvcs2 = ANY(string_to_array(s.ma_dvcs, ',')))
      AND (s.unrestricted OR c.ma_dvcs2 = ANY(string_to_array(s.ds_branchs, ','))) GROUP BY c.ma_vt, c.ma_kho
), base AS (
    SELECT b.ma_vt, v.ten_vt, v.ten_vt2, v.dvt, v.ma_loai_vt, v.nh_vt1, v.nh_vt2, v.nh_vt3, v.nh_vt4, v.nh_vt5, v.nh_vt6, v.nh_vt7, v.tk_vt,
           sum(b.so_luong) AS so_luong, sum(b.tien) AS tien FROM balances b JOIN public.dmvt v ON v.ma_vt = b.ma_vt CROSS JOIN scope s
    WHERE (s.nh_vt1 = '' OR v.nh_vt1 = ANY(string_to_array(s.nh_vt1, ','))) AND (s.nh_vt2 = '' OR v.nh_vt2 = ANY(string_to_array(s.nh_vt2, ',')))
      AND (s.nh_vt3 = '' OR v.nh_vt3 = ANY(string_to_array(s.nh_vt3, ','))) AND (s.nh_vt4 = '' OR v.nh_vt4 = ANY(string_to_array(s.nh_vt4, ',')))
      AND (s.nh_vt5 = '' OR v.nh_vt5 = ANY(string_to_array(s.nh_vt5, ','))) AND (s.nh_vt6 = '' OR v.nh_vt6 = ANY(string_to_array(s.nh_vt6, ',')))
      AND (s.nh_vt7 = '' OR v.nh_vt7 = ANY(string_to_array(s.nh_vt7, ','))) AND (s.tk_vt = '' OR v.tk_vt = ANY(string_to_array(s.tk_vt, ',')))
    GROUP BY b.ma_vt, v.ten_vt, v.ten_vt2, v.dvt, v.ma_loai_vt, v.nh_vt1, v.nh_vt2, v.nh_vt3, v.nh_vt4, v.nh_vt5, v.nh_vt6, v.nh_vt7, v.tk_vt
)
SELECT row_number() OVER (ORDER BY ma_vt) AS stt, ma_vt, ten_vt, ten_vt2, dvt, ma_loai_vt, nh_vt1, nh_vt2, nh_vt3, nh_vt4, nh_vt5, nh_vt6, nh_vt7, tk_vt,
       so_luong, tien, tien AS tien_nt, count(*) OVER () AS total FROM base WHERE so_luong <> 0 ORDER BY ma_vt LIMIT (SELECT row_limit FROM params);
