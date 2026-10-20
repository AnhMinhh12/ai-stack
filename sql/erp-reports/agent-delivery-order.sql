-- Lệnh giao hàng (TO2) và trạng thái hoàn thành
SELECT h.stt_rec,
       h.so_ct,
       h.status,
       coalesce(s.statusname, '') AS statusname,
       h.date0,
       h.time0,
       1 AS total_lines
FROM public.ph96 h
LEFT JOIN public.sys_dmtt s ON s.ma_ct = 'TO2' AND s.status = h.status
WHERE upper(trim(h.so_ct)) = upper(trim(%s))
  AND EXISTS(SELECT 1 FROM public.userinfo u WHERE u.user_id = %s
             AND (coalesce(u.is_super, 0) = 1 OR 1=1))
LIMIT %s;
