# BÁO CÁO KIỂM THỬ TRỰC TIẾP TRÊN GIAO DIỆN & ĐỐI SOÁT CƠ SỞ DỮ LIỆU ERP
- **Thời điểm kiểm thử:** 2026-11-07 04:55:07 UTC
- **Tài khoản kiểm thử:** hoanhminhz@gmail.com (Hồ Anh Minh)
- **Giao diện:** Open WebUI Chat (`http://127.0.0.1/`) - Model `HTMP ERP` (`htmp-nhanh`)
- **Cơ sở dữ liệu đối soát:** PostgreSQL `3SERP_HTMP_DATA` (Host: 10.0.6.2:5410)

| ID | Nhóm nghiệp vụ | Câu hỏi kiểm thử trên giao diện | Thời gian | Trạng thái | Đối soát số liệu DB |
|:---:|---|---|:---:|:---:|---|
| **Q01** | Phần 1 - Báo cáo tồn kho | Cho tôi xem báo cáo top 10 vật tư có số lượng tồn kho lớn nhất hiện tại | 7.7s | ✅ PASS | Khớp nội dung định tính |
| **Q02** | Phần 1 - Tồn kho theo kho | Tổng hợp số lượng tồn kho phân bổ theo từng kho hàng trong hệ thống | 15.4s | ✅ PASS | Khớp nội dung định tính |
| **Q06** | Phần 1 - Tiến độ giao hàng QC7 | Tổng hợp số lượng xuất kho bán hàng của mã hàng QC7-5146-000 theo từng ngày xuất từ ngày 01/10/2026 đến ngày 20/10/2026 | 14.3s | ✅ PASS | ngay_ct=2026-10-01 |
| **Q08** | Phần 1 - Lịch sử giá mua PS-576D | Tổng hợp lịch sử các lần đặt mua, đơn giá mua thấp nhất, cao nhất và giá bình quân của mã nhựa PS-576D | 5.3s | ✅ PASS | so_lan_mua=0 |
| **Q11** | Phần 1 - Thời gian dừng máy Downtime | Báo cáo tổng số phút dừng máy theo từng nguyên nhân dừng chuyền trong bảng kê stop line gần đây | 7.3s | ✅ PASS | Khớp nội dung định tính |
| **Q45** | Phần 3 - Đối soát SO vs HDA | Kiểm tra tổng số lượng đặt hàng trong đơn SO và tổng số lượng đã xuất kho giao hàng của mã QC7-5146-000 trong tháng 10/2026 | 12.3s | ✅ PASS | Khớp nội dung định tính |
| **Q48** | Phần 4 - Khuôn H131-TBT-H612 & Dự báo tuổi thọ | Khuôn H131-TBT-H612 đã chạy được bao nhiêu shots? Theo demand của khách hàng thì dự kiến khi nào hết tuổi thọ khuôn? | 5.3s | ✅ PASS | Khớp nội dung định tính |
| **Q49** | Phần 4 - So sánh doanh thu HK2C2-393-01-00 T9 vs T10 | so sánh doanh thu mã sản phẩm HK2C2-393-01-00 tháng 9 và tháng 10 | 13.4s | ✅ PASS | Khớp nội dung định tính |
| **Q51** | Phần 4 - Tồn kho QC7-5146-000 theo khuôn | Mã hàng QC7-5146-000 có tồn kho hiện tại bao gồm của những khuôn nào? Số lượng tồn kho cụ thể của từng khuôn? chỉ lấy ở các kho tp, kho xhtl | 13.4s | ✅ PASS | Khớp nội dung định tính |
| **Q53** | Phần 4 - Lệnh giao hàng 001-2611-000004 | lệnh giao hàng 001-2611-000004 được hoàn thiện khi nào lấy theo thời gian kho hoàn thành lệnh out hàng ra khỏi hệ thống | 10.4s | ✅ PASS | so_ct=001-2611-000004, user_id2=27 |
| **Q54** | Phần 4 - KH0062 mã hàng chưa link giá | Khách hàng KH0062 có mã hàng nào chưa link được giá trên ERP không? | 8.4s | ✅ PASS | Khớp nội dung định tính |
| **Q55** | Phần 4 - Mã khách hàng ATSUMITEC | khách hàng ATSUMITEC có mã khách hàng là gì | 5.3s | ✅ PASS | ma_kh=KH0062, ten_kh=CÔNG TY TNHH ATSUMITEC VIỆT NAM |
| **Q56** | Phần 4 - Đối soát NG nhận lại vs giao bù | số lượng NG đã nhận lại và đã giao bù là bao nhiêu | 12.4s | ✅ PASS | Khớp nội dung định tính |