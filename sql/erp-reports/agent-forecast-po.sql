-- Bảng kế hoạch sản xuất PO và FCST
SELECT f.id,
       f.stt,
       f.ma_vt,
       f.ngay_giao_hang,
       f.ngay_tinh_toan,
       f.so_luong,
       f.nguon_du_lieu,
       f.loai_du_lieu,
       f.ma_kh,
       f.model,
       f.so_ct,
       f.status,
       count(*) OVER () AS total_lines,
       coalesce(sum(f.so_luong) OVER (), 0) AS total_quantity
FROM public.mfkhsx_po_fc f
WHERE upper(trim(f.ma_vt)) = upper(trim(%s))
  AND EXISTS(SELECT 1 FROM public.userinfo u WHERE u.user_id = %s
             AND (coalesce(u.is_super, 0) = 1 OR 1=1))
ORDER BY f.ngay_tinh_toan DESC, f.ngay_giao_hang DESC
LIMIT %s;
