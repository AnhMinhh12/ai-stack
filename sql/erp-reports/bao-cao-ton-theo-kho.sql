WITH params AS (
    SELECT %s::date AS den_ngay, coalesce(%s::text, '') AS ma_kho, coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_dvcs,
           coalesce(%s::text, '*') AS trang_thai_kho, %s::integer AS authenticated_user_id, %s::integer AS row_limit
), scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs, coalesce(u.is_super, 0) = 1 OR coalesce(u.ds_branchs, '') = '' AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), balances AS (
    SELECT c.ma_kho, c.ma_vt, sum(c.ton00) AS so_luong, sum(c.du00) AS tien FROM public.cdvt c JOIN public.dmkho k ON k.ma_kho=c.ma_kho CROSS JOIN scope s
    WHERE s.authorized_user_id IS NOT NULL AND c.nam=extract(year FROM s.den_ngay)::smallint AND (s.ma_kho='' OR c.ma_kho=ANY(string_to_array(s.ma_kho,',')))
      AND (s.ma_dvcs='' OR k.ma_dvcs=ANY(string_to_array(s.ma_dvcs,','))) AND (s.unrestricted OR k.ma_dvcs=ANY(string_to_array(s.ds_branchs,','))) GROUP BY c.ma_kho,c.ma_vt
    UNION ALL SELECT c.ma_kho,c.ma_vt,sum(c.sl_nhap-c.sl_xuat),sum(c.tien_nhap-c.tien_xuat) FROM public.ct70 c CROSS JOIN scope s
    WHERE s.authorized_user_id IS NOT NULL AND c.ngay_ct BETWEEN make_date(extract(year FROM s.den_ngay)::integer,1,1) AND s.den_ngay
      AND (s.ma_kho='' OR c.ma_kho=ANY(string_to_array(s.ma_kho,','))) AND (s.ma_vt='' OR c.ma_vt=ANY(string_to_array(s.ma_vt,',')))
      AND (s.ma_dvcs='' OR c.ma_dvcs2=ANY(string_to_array(s.ma_dvcs,','))) AND (s.unrestricted OR c.ma_dvcs2=ANY(string_to_array(s.ds_branchs,','))) GROUP BY c.ma_kho,c.ma_vt
), base AS (SELECT ma_kho,ma_vt,sum(so_luong) so_luong,sum(tien) tien FROM balances GROUP BY ma_kho,ma_vt)
SELECT row_number() OVER (ORDER BY b.ma_kho,b.ma_vt) AS stt,b.ma_kho,k.ten_kho,b.ma_vt,v.ten_vt,v.ten_vt2,v.dvt,v.nh_vt1,v.nh_vt2,v.nh_vt3,v.nh_vt4,v.nh_vt5,v.nh_vt6,
       b.so_luong,b.tien,b.tien AS tien_nt,count(*) OVER () AS total FROM base b JOIN public.dmkho k ON k.ma_kho=b.ma_kho JOIN public.dmvt v ON v.ma_vt=b.ma_vt CROSS JOIN scope s
WHERE b.so_luong<>0 AND (s.trang_thai_kho='*' OR k.status=s.trang_thai_kho) ORDER BY b.ma_kho,b.ma_vt LIMIT (SELECT row_limit FROM params);
