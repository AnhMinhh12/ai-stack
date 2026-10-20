# Tồn kho theo khuôn và die_no

## Nguồn và dữ liệu
Dữ liệu tồn tem theo khuôn/cối lưu tại `public.intem_log` (chiều nhập `nxt = 1`, trạng thái còn hiệu lực `status = '1'`).
Trường `die_no` và `ma_khuon` lưu trong cấu trúc JSON tem.

## Quy tắc nghiệp vụ
Khi người dùng hỏi tồn kho của mã hàng gồm những khuôn nào và số lượng cụ thể, tra cứu theo `die_no` và `ma_khuon`. Báo cáo rõ số lượng tồn tương ứng từng `die_no` (ví dụ: V1, V2).
