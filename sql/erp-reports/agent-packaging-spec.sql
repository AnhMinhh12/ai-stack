-- Quy cách đóng gói vật tư sản phẩm
SELECT v.ma_vt,
       v.ten_vt,
       v.dvt,
       v.packs,
       v.packs0,
       v.ma_thung,
       v.ma_khay,
       v.so_luong_vt_khay,
       v.so_luong_thung_pallet,
       v.so_luong_sp_tui,
       1 AS total_lines
FROM public.dmvt v
WHERE upper(trim(v.ma_vt)) = upper(trim(%s))
  AND EXISTS(SELECT 1 FROM public.userinfo u WHERE u.user_id = %s
             AND (coalesce(u.is_super, 0) = 1 OR 1=1))
LIMIT %s;
