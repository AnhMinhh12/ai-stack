-- Staging slice: internal employee (dmkh nv_yn=1) and ERP user account (userinfo) lookup.
WITH params AS (
    SELECT %s::integer AS user_id,
           trim(%s::text) AS q_raw,
           regexp_replace(
               lower(translate(trim(%s::text), 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ', 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyydAAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD')),
               '[^a-z0-9]+', ' ', 'g'
           ) AS q_norm,
           %s::integer AS row_limit
),
tokens AS (
    SELECT array_remove(regexp_split_to_array(trim(q_norm), '\s+'), '') AS words
    FROM params
),
scope AS (
    SELECT u.user_id, coalesce(u.is_super, 0) = 1 AS superuser
    FROM public.userinfo u
    JOIN params p ON u.user_id = p.user_id
),
rows_all AS (
    SELECT 'Nhân viên (DMKH)'::text AS loai_ho_so,
           trim(k.ma_kh) AS ma_nv,
           coalesce(k.ten_kh, '') AS ten_nv,
           coalesce(k.ma_bp, '') AS ma_bp,
           ''::text AS chuc_vu,
           coalesce(k.status, '') AS trang_thai,
           1 AS sort_group
    FROM public.dmkh k
    CROSS JOIN params p
    CROSS JOIN tokens t
    CROSS JOIN scope s
    WHERE (s.superuser OR s.user_id IS NOT NULL)
      AND coalesce(k.nv_yn, 0) = 1
      AND trim(p.q_norm) <> ''
      AND (
          upper(trim(k.ma_kh)) = upper(p.q_raw)
          OR EXISTS (
              SELECT 1 FROM unnest(t.words) w
              WHERE length(w) >= 3 AND lower(trim(k.ma_kh)) = w
          )
          OR strpos(lower(translate(coalesce(k.ten_kh, ''), 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ', 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyydAAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD')), trim(p.q_norm)) > 0
          OR (
              cardinality(t.words) > 1
              AND NOT EXISTS (
                  SELECT 1 FROM unnest(t.words) w
                  WHERE strpos(
                      lower(translate(coalesce(k.ma_kh, '') || ' ' || coalesce(k.ten_kh, ''), 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ', 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyydAAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD')),
                      w
                  ) = 0
              )
          )
      )
    UNION ALL
    SELECT 'Tài khoản ERP'::text AS loai_ho_so,
           trim(u2.user_name) AS ma_nv,
           coalesce(u2.ten, u2.user_name, '') AS ten_nv,
           coalesce(u2.phong_ban, '') AS ma_bp,
           coalesce(u2.chuc_vu, '') AS chuc_vu,
           coalesce(u2.status, '') AS trang_thai,
           2 AS sort_group
    FROM public.userinfo u2
    CROSS JOIN params p
    CROSS JOIN tokens t
    CROSS JOIN scope s
    WHERE (s.superuser OR s.user_id IS NOT NULL)
      AND trim(p.q_norm) <> ''
      AND (
          upper(trim(u2.user_name)) = upper(p.q_raw)
          OR u2.user_id::text = p.q_raw
          OR EXISTS (
              SELECT 1 FROM unnest(t.words) w
              WHERE length(w) >= 3 AND lower(trim(coalesce(u2.user_name, ''))) = w
          )
          OR strpos(lower(translate(coalesce(u2.ten, ''), 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ', 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyydAAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD')), trim(p.q_norm)) > 0
          OR strpos(lower(coalesce(u2.user_name, '')), trim(p.q_norm)) > 0
          OR (
              cardinality(t.words) > 1
              AND NOT EXISTS (
                  SELECT 1 FROM unnest(t.words) w
                  WHERE strpos(
                      lower(translate(coalesce(u2.user_name, '') || ' ' || coalesce(u2.ten, ''), 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ', 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyydAAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD')),
                      w
                  ) = 0
              )
          )
      )
)
SELECT loai_ho_so, ma_nv, ten_nv, ma_bp, chuc_vu, trang_thai,
       count(*) OVER () AS total_lines
FROM rows_all
ORDER BY sort_group, ma_nv
LIMIT (SELECT row_limit FROM params)
