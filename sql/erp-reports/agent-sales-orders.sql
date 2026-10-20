-- Bảng kê đơn hàng bán (SO) và đối soát giá chuẩn
SELECT h.stt_rec,
       h.so_ct,
       h.ngay_ct,
       h.ma_kh,
       h.status,
       d.ln,
       d.ma_vt,
       d.dvt,
       d.so_luong,
       d.gia2,
       d.gia_chuan,
       count(*) OVER () AS total_lines,
       coalesce(sum(d.so_luong) OVER (), 0) AS total_quantity
FROM public.ph64 h
JOIN public.ct64 d USING(stt_rec)
WHERE upper(trim(h.ma_kh)) = upper(trim(%s))
  AND h.ngay_ct BETWEEN %s::date AND %s::date
  AND EXISTS(SELECT 1 FROM public.userinfo u WHERE u.user_id = %s
             AND (coalesce(u.is_super, 0) = 1 OR (
                  h.ma_dvcs = ANY(string_to_array(coalesce(u.ds_branchs, ''), ','))
             )))
ORDER BY h.ngay_ct DESC, h.so_ct DESC, d.ln
LIMIT %s;
