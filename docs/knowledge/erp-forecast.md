# Kế hoạch sản xuất PO và Forecast

## Nguồn và dữ liệu
Dữ liệu kế hoạch lưu tại `public.mfkhsx_po_fc` với `nguon_du_lieu` ('PO' hoặc 'FC'), `loai_du_lieu`, `ngay_tinh_toan`, `ngay_giao_hang`, và `so_luong`.

## Quy tắc nghiệp vụ
Khi người dùng hỏi về biến động DO và FCST, tra cứu các bản ghi trong `mfkhsx_po_fc`.
Hệ thống lưu các đợt tính toán theo ngày `ngay_tinh_toan`. Lưu ý hiện tại hệ thống ERP lưu dữ liệu theo snapshot tính toán; tính năng so sánh lịch sử revision giữa các phiên bản chưa hỗ trợ hoàn toàn tự động.
