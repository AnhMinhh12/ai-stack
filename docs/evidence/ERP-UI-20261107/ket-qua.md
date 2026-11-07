# Kiểm thử giao diện ERP chatbot ngày 07/11/2026

Phương pháp: 12 câu mẫu theo các nhóm nghiệp vụ trong tài liệu khảo sát, không phải mẫu ngẫu nhiên có phân tầng. Chạy trên trình duyệt Edge của người dùng, chọn HTMP ERP (`htmp-nhanh`), các cuộc hội thoại mới, tài khoản đang đăng nhập Ho Anh Minh. Không đại diện các quyền khác. Xem chi tiết `chat-results.jsonl`.

| Câu | Nội dung | Kết quả quan sát |
|---|---|---|
| 1 | Đơn bán KH0047 tháng 10 | Lỗi tra cứu; công cụ hiển thị `No module named 'functions'`. |
| 2 | Giá bán 156279430 | Báo lỗi truy cập giá, không trả kết quả. |
| 3 | Đặt, giao, còn giao QC7 | Báo lỗi, in thô `tool_call`, không trả số liệu. |
| 4 | Đơn mua NCC0220 tháng 10 | Báo lỗi, in thô `tool_call`, không trả danh sách. |
| 5 | Giá mua PS-576D tháng 10 | Báo lỗi, không trả lịch sử. |
| 6 | Tồn 75577-BZ010 theo kho | Lỗi công cụ `No module named 'functions'`, không trả số liệu. |
| 7 | Thẻ kho QC7 tại KHOTP00 | Báo lỗi truy cập dữ liệu kho, không trả thẻ kho. |
| 8 | Dừng máy theo nguyên nhân tháng 10 | Không đạt: tool nhận `ma_may: 10/2026`, trả 0 dòng, model kết luận không có dữ liệu. Không chứng minh dữ liệu tháng rỗng. |
| 9 | Lỗi sản phẩm theo mã lỗi tháng 10 | Không đạt: tool nhận `ma_sp: 10/2026`, trả 0 dòng, model kết luận không có dữ liệu. Không chứng minh dữ liệu tháng rỗng. |
| 10 | BOM QC7 | Trả PS-576D và 0.026; chưa đối chiếu độc lập đơn vị, hiệu lực và dữ liệu ERP nên chưa chấm đúng. |
| 11 | Shot và bảo hành khuôn QC7 | Công cụ `No module named 'functions'`; in thô tool_call, không có số liệu. |
| 12 | Đánh giá chất lượng hàng mua theo NCC | Không tạo báo cáo; yêu cầu bổ sung thông tin hoặc xác nhận. |

Các câu 1, 6, 11 đã mở phần INPUT/OUTPUT để xác minh lỗi. Câu 8 và 9 đã mở chi tiết tool và xác minh tháng bị nhầm thành mã máy/mã sản phẩm. Không chứng minh tất cả công cụ lỗi cùng nguyên nhân. Mở được báo cáo tồn theo kho trong ERP nhưng chưa chạy cùng bộ lọc, chưa đối chiếu DB hoặc ERP cho các giá trị trả lời. Không thay đổi cấu hình hoặc sửa hệ thống.
