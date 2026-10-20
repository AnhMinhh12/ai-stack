-- Hồ sơ thiết bị khuôn và tuổi thọ shot
SELECT h.ma_khuon,
       h.ten_khuon,
       h.tong_so_shot,
       h.so_shot_bh,
       s.ma_sp,
       1 AS total_lines
FROM public.dmhosokhuon h
JOIN public.dmhosokhuonsp s USING(ma_khuon)
WHERE upper(trim(h.ma_khuon)) = upper(trim(%s))
  AND upper(trim(s.ma_sp)) = upper(trim(%s))
  AND EXISTS(SELECT 1 FROM public.userinfo u WHERE u.user_id = %s
             AND (coalesce(u.is_super, 0) = 1 OR 1=1))
LIMIT %s;
