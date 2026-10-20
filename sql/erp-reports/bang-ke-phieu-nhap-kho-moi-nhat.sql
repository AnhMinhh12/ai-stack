WITH access_scope AS (
    SELECT u.user_id, coalesce(u.ds_branchs, '') AS ds_branchs,
           coalesce(u.is_super, 0) = 1
             OR (coalesce(u.ds_branchs, '') = '' AND coalesce(u.ds_stocks, '') = '') AS unrestricted
    FROM public.userinfo AS u
    WHERE u.user_id = %s
)
SELECT a.ngay_ct, a.so_ct, a.ma_vt, vt.ten_vt, a.ma_kho, kho.ten_kho,
       a.sl_nhap AS so_luong, a.dvt, creator.user_name AS nguoi_lap
FROM public.ct70 AS a
CROSS JOIN access_scope AS scope
LEFT JOIN public.dmvt AS vt ON vt.ma_vt = a.ma_vt
LEFT JOIN public.dmkho AS kho ON kho.ma_kho = a.ma_kho AND kho.ma_dvcs = a.ma_dvcs2
LEFT JOIN public.userinfo AS creator ON creator.user_id = a.user_id0
WHERE scope.user_id IS NOT NULL
  AND a.nxt = 1
  AND a.ma_vt = %s
  AND (scope.unrestricted OR scope.ds_branchs = ''
       OR a.ma_dvcs2 = ANY(string_to_array(scope.ds_branchs, ',')))
  AND (a.ma_kho IS NULL OR a.ma_kho = '' OR scope.unrestricted OR EXISTS (
      SELECT 1
      FROM public.dmkho AS permitted_stock
      WHERE permitted_stock.ma_kho = a.ma_kho
        AND permitted_stock.ma_dvcs = a.ma_dvcs2
        AND (scope.ds_branchs = ''
             OR permitted_stock.ma_dvcs = ANY(string_to_array(scope.ds_branchs, ',')))
  ))
ORDER BY a.ngay_ct DESC, a.so_ct DESC, a.stt_rec DESC, a.ln DESC
LIMIT %s;
