# Giao bù và đổi trả hàng

## Nguồn và dữ liệu
Dữ liệu giao bù lưu tại `public.ph96` và `public.ct96` với mã giao dịch `ma_gd = 10`.
Dữ liệu yêu cầu đổi trả hàng lưu tại `public.ph66` và `public.ct66`.

## Quy tắc nghiệp vụ
Mã giao dịch 10 gồm cả hàng giao bù NG và giao bù hàng thiếu. Trường `dien_giai` chứa ghi chú phân biệt. Khi tra cứu giao bù, phân tích nội dung diễn giải và số lượng. Nếu trong kỳ không có bản ghi phát sinh, báo cáo rõ không có bản ghi trong khoảng thời gian đã lọc.
