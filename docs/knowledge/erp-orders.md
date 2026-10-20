# Đơn hàng bán (SO) và liên kết giá

## Nguồn và dữ liệu
Dữ liệu đơn hàng bán lưu tại `public.ph64` (tiêu đề) và `public.ct64` (chi tiết dòng đơn).
- `gia_chuan`: đơn giá chuẩn theo hợp đồng / bảng giá. Nếu `gia_chuan IS NULL` hoặc `gia_chuan = 0` là dấu hiệu dòng đơn hàng chưa liên kết giá chuẩn.

## Quy tắc nghiệp vụ
- Tra cứu dữ liệu đơn hàng quá khứ theo khách hàng và khoảng thời gian.
- Khi người dùng hỏi khách hàng có mã hàng nào chưa liên kết giá trên ERP không, lọc các dòng có `gia_chuan IS NULL OR gia_chuan = 0` và liệt kê các mã vật tư đó.
