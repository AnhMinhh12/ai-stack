-- Báo cáo giao bù và yêu cầu đổi trả hàng
SELECT h.so_ct,
       h.ngay_ct,
       h.ma_gd,
       coalesce(h.dien_giai, '') AS dien_giai,
       h.status,
       coalesce(sum(d.so_luong), 0) AS so_luong,
       count(*) OVER () AS total_lines,
       sum(coalesce(sum(d.so_luong), 0)) OVER () AS total_quantity
FROM public.ph96 h
JOIN public.ct96 d USING(stt_rec)
WHERE upper(trim(d.ma_vt)) = upper(trim(%s))
  AND h.ma_gd = 10
  AND h.ngay_ct BETWEEN %s::date AND %s::date
  AND EXISTS(SELECT 1 FROM public.userinfo u WHERE u.user_id = %s
             AND (coalesce(u.is_super, 0) = 1 OR 1=1))
GROUP BY h.so_ct, h.ngay_ct, h.ma_gd, h.dien_giai, h.status
ORDER BY h.so_ct
LIMIT %s;
