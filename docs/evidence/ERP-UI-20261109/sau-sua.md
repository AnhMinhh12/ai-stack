# Kết quả sau sửa 09/11/2026

Kiểm thử qua trình duyệt trên tài khoản Ho Anh Minh, model hội thoại được lưu là `htmp-nhanh`. Open WebUI healthy sau khởi động lại. Các câu và nội dung thực tế nằm trong `chat-results-after.jsonl` và `chat-mold-after.jsonl`.

- KH0047 tháng 10: giao diện trả 5.631 dòng, hiển thị 20; số dòng khớp truy vấn DB `ct64`/`ph64` theo kỳ. Chưa xác nhận trạng thái chứng từ hoặc đơn vị nên không đưa tổng.
- Giá bán 156279430: vẫn hiển thị 12.105 VND/PCS, Antolin, hiệu lực 27/01–31/12/2026, khớp dòng bảng giá đã kiểm tra.
- Tiến độ QC7: không còn nêu số đặt/giao/còn chưa xác minh; hiển thị 33 dòng đơn bán, 20 dòng đầu, và nói chưa xác nhận tiến độ. Chưa đáp ứng đầy đủ câu hỏi tiến độ.
- PS-576D tháng 10: 13 dòng đơn mua, khớp số dòng DB. Chưa tổng hợp giá vì chưa xác nhận trạng thái, tiền tệ và quy tắc bình quân; chưa đáp ứng đầy đủ câu hỏi giá.
- Dừng máy tháng 10: 21.267 lượt, 754.668,1 phút, 129 nhóm, khớp truy vấn đối chiếu theo công thức hiện tại. Công thức, phép nối và ý nghĩa số liệu vẫn cần nghiệm thu MES.
- Khuôn QC7: sau khi khắc phục model đưa mã sản phẩm vào tham số mã khuôn, giao diện hiển thị hai hồ sơ V1 và V2 với shot/bảo hành khớp DB; cần xác nhận trường tổng shot có phản ánh shot thực tế.

Truy vấn đơn bán, mua hàng và dừng máy yêu cầu đủ ngày bắt đầu/kết thúc. Có thể cần hỏi lại người dùng nếu model không truyền đủ kỳ. Không thực hiện phân quyền theo yêu cầu. Các kiểm thử này là mẫu giới hạn, không xác nhận toàn ERP/MES. Kiểm tra trực tiếp các bảo vệ ngày thiếu/đảo và tra cứu khuôn thành công; pytest không có sẵn trong môi trường.
