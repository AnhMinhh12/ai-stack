# Kiểm thử giao diện và đối soát DB ngày 09/11/2026

Phiên Open WebUI tài khoản Ho Anh Minh, lựa chọn hiển thị HTMP ERP, 15:09–15:10 giờ Việt Nam. Sáu câu hỏi được gửi qua trình duyệt; câu trả lời thực tế và URL hội thoại nằm trong `chat-results.jsonl`. Chưa xác minh quyền theo các tài khoản khác hoặc đối chiếu báo cáo ERP chính thức. Truy vấn DB trực tiếp dùng giao dịch READ ONLY và timeout; kết quả là bằng chứng kỹ thuật, không mặc định là quy tắc nghiệp vụ được phê duyệt.

| Câu | Kết quả | Đối chiếu |
|---|---|---|
| 1. Đơn bán KH0047 tháng 10 | Sai kỳ: chat trả 20 dòng, 69.642 PCS | `ct64`/`ph64`, 20 dòng mới nhất của KH0047 đều ngày 07/11, tổng 69.642. Lọc 01/10–31/10 có 5.631 dòng, tổng số lượng thô 20.391.373; chưa xác nhận trạng thái, đơn vị và quyền nên không coi tổng này là kết quả báo cáo ERP. |
| 2. Giá bán 156279430 | Khớp dòng giá được kiểm tra | `dmbanggiact`: KH0056, Antolin, 12.105 VND, 27/01–31/12/2026, số lượng tối thiểu 1. Cần xác nhận quy tắc hiệu lực và phân quyền trước nghiệm thu toàn diện. |
| 3. Tiến độ QC7-5146-000 tháng 10 | Thiếu bằng chứng | Chat nêu đặt 167.440, giao 160.100, còn 2.320 PCS. Phép trừ là 7.340; chưa rõ quy tắc báo cáo cho số còn lại, chưa xác nhận báo cáo ERP hay procedure nên không kết luận số nào đúng. Danh sách 20 dòng gần đây cũng cần xác nhận kỳ. |
| 5. Lịch sử mua PS-576D tháng 10 | Sai kỳ và tổng hợp | Chat nêu 20 lần, gần nhất 09/11, trung bình 42.655,95. `ct94`/`ph94`: 20 dòng gần nhất từ 01/10 đến 09/11 cho trung bình đó; riêng tháng 10 có 13 dòng, trung bình số học 41.710,9231, min 41.220, max 44.411. Chưa xác nhận trạng thái, loại tiền và định nghĩa bình quân nghiệp vụ. |
| 8. Dừng máy tháng 10 | Sai tính đầy đủ theo công thức truy vấn hiện tại | Chat nêu 13.862 lượt, 501.131,8 phút. DB cùng điều kiện ngày, phép nối và công thức thời gian của mã: 129 nhóm, 21.267 lượt, 754.668,1 phút; đúng 15 nhóm đầu là 13.862 lượt, 501.131,8 phút. Chưa xác nhận công thức và phép nối với báo cáo MES chính thức. |
| 11. Khuôn QC7-5146-000 | Câu trả lời không tìm thấy mâu thuẫn dữ liệu liên kết | `dmhosokhuonsp` nối `dmhosokhuon` có K_QC5-2919-000-V1: 1.722.770 shot, bảo hành 1.000.000; V2: 1.169.359 shot, bảo hành 1.000.000. Cần xác nhận ý nghĩa trường shot và khuôn áp dụng thực tế; chưa kết luận số shot vận hành hiện tại. |

Mã nguồn làm việc `erp_ai/native_tools.py` cho thấy các nhánh đơn bán, đơn mua giới hạn 20 dòng mà không áp dụng điều kiện ngày tại truy vấn thường; nhánh dừng máy cộng sau `LIMIT 15`. Cần kiểm tra mã đăng ký runtime trước khi quy nguyên nhân chính thức. Không gọi stored procedure trong lượt đối soát này vì chưa xác minh toàn bộ tác động và quyền.
