WITH params AS (
    SELECT %s::date AS tu_ngay, %s::date AS den_ngay,
           coalesce(%s::text, '') AS so_ct_tu, coalesce(%s::text, '') AS so_ct_den,
           coalesce(%s::text, '') AS ma_kh, coalesce(%s::text, '') AS ma_kho,
           coalesce(%s::text, '') AS ma_vt, coalesce(%s::text, '') AS ma_nvbh,
           coalesce(%s::text, '') AS ma_dvcs, coalesce(%s::text, '') AS status,
           %s::integer AS authenticated_user_id, %s::integer AS row_limit
), access_scope AS (
    SELECT p.*, u.user_id AS authorized_user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM params p LEFT JOIN public.userinfo u ON u.user_id = p.authenticated_user_id
), orders AS (
    SELECT h.stt_rec, d.ln, h.ngay_ct, h.so_ct, h.ma_dvcs, h.ma_kh, h.ma_nvbh,
           h.so_po, h.status, d.ma_vt, d.ma_kho, d.so_luong, d.sl_rev,
           d.close_yn, d.gia_nt2, d.gia2, d.tien_nt2, d.tien2
    FROM public.ph64 h JOIN public.ct64 d ON d.stt_rec = h.stt_rec
    CROSS JOIN access_scope a
    WHERE a.authorized_user_id IS NOT NULL AND h.status NOT IN ('0', '15')
      AND h.ngay_ct BETWEEN a.tu_ngay AND a.den_ngay
      AND (a.so_ct_tu = '' OR h.so_ct >= a.so_ct_tu) AND (a.so_ct_den = '' OR h.so_ct <= a.so_ct_den)
      AND (a.ma_kh = '' OR h.ma_kh = ANY(string_to_array(a.ma_kh, ',')))
      AND (a.ma_kho = '' OR d.ma_kho = ANY(string_to_array(a.ma_kho, ',')))
      AND (a.ma_vt = '' OR d.ma_vt = ANY(string_to_array(a.ma_vt, ',')))
      AND (a.ma_nvbh = '' OR h.ma_nvbh = ANY(string_to_array(a.ma_nvbh, ',')))
      AND (a.ma_dvcs = '' OR h.ma_dvcs = ANY(string_to_array(a.ma_dvcs, ',')))
      AND (a.status = '' OR h.status::text = ANY(string_to_array(a.status, ',')))
      AND (a.unrestricted OR a.ds_branchs = '' OR h.ma_dvcs = ANY(string_to_array(a.ds_branchs, ',')))
      AND (d.ma_kho IS NULL OR d.ma_kho = '' OR a.unrestricted OR EXISTS (
          SELECT 1 FROM public.dmkho w WHERE w.ma_kho = d.ma_kho
            AND w.ma_dvcs = ANY(string_to_array(a.ds_branchs, ','))
      ))
), schedules AS (
    SELECT g.stt_rec, g.ln_item AS ln, g.ma_vt, g.ngay_gh, max(g.so_po) AS so_po_gh,
           sum(g.so_luong) AS so_luong_don
    FROM public.ctkhgh g JOIN orders o ON o.stt_rec = g.stt_rec AND o.ln = g.ln_item AND o.ma_vt = g.ma_vt
    GROUP BY g.stt_rec, g.ln_item, g.ma_vt, g.ngay_gh
), dispatched AS (
    SELECT g.stt_rec_so1 AS stt_rec, CASE WHEN g.ln_so1 = 0 THEN g.ln_so1_goc ELSE g.ln_so1 END AS ln,
           g.ma_vt, sum(g.so_luong) AS so_luong_lenh
    FROM public.ctkhgh g JOIN public.ph96 h ON h.stt_rec = g.stt_rec
    WHERE g.ma_ct = 'TO2' AND h.status IN ('1', '11', '12')
    GROUP BY g.stt_rec_so1, CASE WHEN g.ln_so1 = 0 THEN g.ln_so1_goc ELSE g.ln_so1 END, g.ma_vt
), delivered AS (
    SELECT coalesce(nullif(i.stt_rec_so1, ''), i.stt_rec_so1_goc) AS stt_rec,
           CASE WHEN i.ln_so1 = 0 THEN i.ln_so1_goc ELSE i.ln_so1 END AS ln,
           i.ma_vt, max(i.ngay_ct) AS ngay_gh_thuc_te, min(i.so_ct) AS so_ct_hda,
           sum(i.so_luong) AS so_luong_giao
    FROM public.ct81 i JOIN public.ph81 h ON h.stt_rec = i.stt_rec
    WHERE h.status NOT IN ('0', '15')
    GROUP BY coalesce(nullif(i.stt_rec_so1, ''), i.stt_rec_so1_goc),
             CASE WHEN i.ln_so1 = 0 THEN i.ln_so1_goc ELSE i.ln_so1 END, i.ma_vt
)
SELECT 5::smallint AS sysorder, row_number() OVER (ORDER BY o.stt_rec, s.ngay_gh, o.ln) AS stt,
       o.stt_rec, o.ln, o.ngay_ct, o.so_ct, o.ma_dvcs, o.ma_kh, k.ten_viet_tat AS ten_kh,
       o.so_po, s.so_po_gh, o.ma_vt, v.ten_vt, o.sl_rev AS so_luong_revise,
       s.so_luong_don, coalesce(x.so_luong_lenh, 0) AS so_luong_lenh,
       s.so_luong_don - coalesce(x.so_luong_lenh, 0) AS so_luong_chua_lenh,
       coalesce(y.so_luong_giao, 0) AS so_luong_giao,
       CASE WHEN o.close_yn = 1 OR o.status = '13' THEN s.so_luong_don - coalesce(y.so_luong_giao, 0) ELSE 0 END AS sl_dong,
       CASE WHEN o.status = '14' THEN 0 ELSE s.so_luong_don - coalesce(y.so_luong_giao, 0)
            - CASE WHEN o.close_yn = 1 OR o.status = '13' THEN s.so_luong_don - coalesce(y.so_luong_giao, 0) ELSE 0 END END AS so_luong_con_lai,
       o.gia_nt2, o.gia2, o.tien_nt2, o.tien2, s.ngay_gh AS ngay_gh_ke_hoach,
       y.ngay_gh_thuc_te AS ngay_hd, y.so_ct_hda AS so_hd,
       o.gia2 AS gia_ban, o.tien2 AS tien_ban,
       y.ngay_gh_thuc_te, y.ngay_gh_thuc_te - s.ngay_gh AS cl_ngay,
       CASE WHEN s.ngay_gh > current_date THEN 'chua_den_han'
            WHEN y.ngay_gh_thuc_te IS NULL THEN 'chua_giao'
            WHEN y.ngay_gh_thuc_te < s.ngay_gh THEN 'truoc_han'
            WHEN y.ngay_gh_thuc_te > s.ngay_gh THEN 'giao_muon' ELSE 'dung_han' END AS tinh_trang_giao_hang,
       st.statusname AS tinh_trang_don_hang, count(*) OVER () AS total
FROM schedules s JOIN orders o ON o.stt_rec = s.stt_rec AND o.ln = s.ln AND o.ma_vt = s.ma_vt
LEFT JOIN dispatched x ON x.stt_rec = o.stt_rec AND x.ln = o.ln AND x.ma_vt = o.ma_vt
LEFT JOIN delivered y ON y.stt_rec = o.stt_rec AND y.ln = o.ln AND y.ma_vt = o.ma_vt
LEFT JOIN public.dmkh k ON k.ma_kh = o.ma_kh LEFT JOIN public.dmvt v ON v.ma_vt = o.ma_vt
LEFT JOIN public.sys_dmtt st ON st.ma_ct = 'SO1' AND st.status = o.status
ORDER BY o.stt_rec, s.ngay_gh, o.ln
LIMIT (SELECT row_limit FROM params)
