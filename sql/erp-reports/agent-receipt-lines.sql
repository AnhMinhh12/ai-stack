-- Dòng phiếu nhập kho và điều chuyển
SELECT a.stt_rec,
       a.ln,
       a.so_ct,
       a.ngay_ct,
       a.date0,
       a.time0,
       a.ma_kho,
       a.dvt,
       a.sl_nhap,
       coalesce(u.user_name, '') AS nguoi_nhap,
       coalesce(src.ma_kho, '') AS kho_xuat,
       count(*) OVER () AS total_lines,
       coalesce(sum(a.sl_nhap) OVER (), 0) AS total_quantity
FROM public.ct70 a
LEFT JOIN public.userinfo u ON u.user_id = a.user_id0
LEFT JOIN public.ct70 src ON src.stt_rec = a.stt_rec_dc AND src.ln = a.ln_dc AND src.ma_vt = a.ma_vt AND src.nxt = 2
WHERE upper(trim(a.ma_vt)) = upper(trim(%s))
  AND a.nxt = 1
  AND a.ngay_ct BETWEEN %s::date AND %s::date
  AND EXISTS(SELECT 1 FROM public.userinfo u2 WHERE u2.user_id = %s
             AND (coalesce(u2.is_super, 0) = 1 OR (
                  a.ma_kho = ANY(string_to_array(coalesce(u2.ds_stocks, ''), ','))
             )))
ORDER BY a.ngay_ct DESC, a.so_ct DESC, a.stt_rec, a.ln
LIMIT %s;
