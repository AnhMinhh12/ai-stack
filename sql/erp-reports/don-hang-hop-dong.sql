WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct, coalesce(%s::text, '') AS ma_kh,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_nvbh,
           coalesce(%s::text, '') AS ma_dvcs, coalesce(%s::text, '') AS ma_gd,
           coalesce(%s::text, '') AS status, %s::integer AS authenticated_user_id,
           %s::boolean AS group_yn, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.ds_stocks, '') AS ds_stocks,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), detail AS (
    SELECT 7::smallint AS sysorder, 0::smallint AS systotal,
           row_number() OVER (PARTITION BY a.stt_rec, a.ma_vt ORDER BY a.ln) AS stt,
           a.stt_rec, a.ln, a.ngay_ct, a.so_ct, h.ma_kh, h.ma_dvcs, a.ma_vt,
           v.ten_vt, h.dien_giai, s.statusname AS status, a.ma_kho,
           a.so_luong, gh.so_luong AS so_luong_gh, a.tien2, a.tien_nt2,
           a.ck, a.ck_nt, a.thue, a.thue_nt,
           a.tien2 + a.thue - a.ck AS t_tt,
           a.tien_nt2 + a.thue_nt - a.ck_nt AS t_tt_nt,
           h.ma_nt, h.ty_gia, gh.ngay_yc_gh, gh.ngay_gh,
           count(*) OVER () AS total
    FROM public.ct64 a
    JOIN public.ph64 h ON h.stt_rec = a.stt_rec
    CROSS JOIN access_scope x
    LEFT JOIN public.ctkhgh gh ON gh.stt_rec = a.stt_rec AND gh.ma_ct = 'SO1' AND gh.ma_vt = a.ma_vt
    LEFT JOIN public.dmvt v ON v.ma_vt = a.ma_vt
    LEFT JOIN public.sys_dmtt s ON s.ma_ct = 'SO1' AND s.status = h.status
    WHERE x.authorized_user_id IS NOT NULL
      AND h.ngay_ct BETWEEN x.tu_ngay AND x.den_ngay
      AND (x.so_ct = '' OR h.so_ct = x.so_ct)
      AND (x.ma_kh = '' OR h.ma_kh = ANY(string_to_array(x.ma_kh, ',')))
      AND (x.ma_vt = '' OR a.ma_vt = ANY(string_to_array(x.ma_vt, ',')))
      AND (x.ma_nvbh = '' OR h.ma_nvbh = ANY(string_to_array(x.ma_nvbh, ',')))
      AND (x.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(x.ma_dvcs, ',')))
      AND (x.ma_gd = '' OR h.ma_gd::text = x.ma_gd)
      AND (x.status = '' OR h.status::text = ANY(string_to_array(x.status, ',')))
      AND (x.unrestricted OR coalesce(x.ds_branchs, '') = ''
           OR h.ma_dvcs = ANY(string_to_array(x.ds_branchs, ',')))
      AND (a.ma_kho IS NULL OR a.ma_kho = '' OR x.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho k
          WHERE k.ma_kho = a.ma_kho
            AND k.ma_dvcs = ANY(string_to_array(coalesce(x.ds_branchs, ''), ','))
      ))
), page_detail AS (
    SELECT d.* FROM detail d CROSS JOIN params p
    ORDER BY d.stt_rec, d.ln LIMIT (SELECT row_limit FROM params)
), grouped_header AS (
    SELECT 3::smallint, 1::smallint, NULL::bigint, d.stt_rec, 0::integer,
           max(d.ngay_ct), max(d.so_ct), max(d.ma_kh), max(d.ma_dvcs), NULL::text,
           max(k.ten_kh), max(d.dien_giai), max(d.status), NULL::text,
           sum(d.so_luong), sum(d.so_luong_gh), sum(d.tien2), sum(d.tien_nt2),
           sum(d.ck), sum(d.ck_nt), sum(d.thue), sum(d.thue_nt), sum(d.t_tt), sum(d.t_tt_nt),
           max(d.ma_nt), max(d.ty_gia), NULL::date, NULL::date, max(d.total)
    FROM page_detail d LEFT JOIN public.dmkh k ON k.ma_kh = d.ma_kh GROUP BY d.stt_rec
), grouped_schedule AS (
    SELECT 5::smallint, 1::smallint, NULL::bigint, stt_rec, 0::integer,
           NULL::date, NULL::text, NULL::text, NULL::text, NULL::text,
           NULL::text, NULL::text, NULL::text, NULL::text,
           NULL::numeric, sum(so_luong_gh), NULL::numeric, NULL::numeric,
           NULL::numeric, NULL::numeric, NULL::numeric, NULL::numeric, NULL::numeric, NULL::numeric,
           NULL::text, NULL::numeric, NULL::date, NULL::date, max(total)
    FROM page_detail GROUP BY stt_rec, ma_vt
), total_row AS (
    SELECT 1::smallint, 1::smallint, NULL::bigint, NULL::text, NULL::integer,
           NULL::date, NULL::text, NULL::text, NULL::text, NULL::text,
           'Tổng cộng'::text, NULL::text, NULL::text, NULL::text,
           sum(so_luong), sum(so_luong_gh), sum(tien2), sum(tien_nt2),
           sum(ck), sum(ck_nt), sum(thue), sum(thue_nt), sum(t_tt), sum(t_tt_nt),
           NULL::text, NULL::numeric, NULL::date, NULL::date, max(total)
    FROM detail HAVING count(*) > 0
), ui_rows AS (
    SELECT * FROM page_detail
    UNION ALL SELECT h.* FROM grouped_header h CROSS JOIN params p WHERE p.group_yn
    UNION ALL SELECT g.* FROM grouped_schedule g CROSS JOIN params p WHERE p.group_yn
    UNION ALL SELECT * FROM total_row
)
SELECT * FROM ui_rows
ORDER BY stt_rec NULLS LAST, ln DESC, sysorder, stt
