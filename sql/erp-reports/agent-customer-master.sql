-- Staging slice: customer directory lookup by code, exact name, or partial name.
WITH scope AS (
    SELECT user_id, coalesce(is_super, 0) = 1 AS superuser
    FROM public.userinfo WHERE user_id = %s
)
SELECT k.ma_kh, k.ten_kh, k.ten_viet_tat, k.dien_thoai, k.dia_chi,
       coalesce(k.ma_bp, '') AS ma_bp, coalesce(k.nv_yn, 0) AS nv_yn,
       coalesce(k.kh_yn, 0) AS kh_yn, coalesce(k.cc_yn, 0) AS cc_yn,
       k.status,
       count(*) OVER () AS total_lines
FROM public.dmkh k
CROSS JOIN scope s
WHERE (s.superuser OR s.user_id IS NOT NULL)
  AND (
      upper(trim(k.ma_kh)) = upper(trim(%s))
      OR lower(trim(k.ten_kh)) = lower(trim(%s))
      OR strpos(
          lower(translate(coalesce(k.ten_kh, ''), 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ', 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyydAAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD')),
          lower(translate(trim(%s), 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ', 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyydAAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD'))
      ) > 0
  )
ORDER BY k.ma_kh
LIMIT %s
