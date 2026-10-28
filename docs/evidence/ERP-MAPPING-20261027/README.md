# Khung khảo sát ERP/MES — 27/10/2026

## Trạng thái truy cập

Đã thử HTTP tới máy ERP được cung cấp. Kết nối mặc định thất bại; lần thử ngoài sandbox hết thời gian sau 8 giây. Chưa nhận được HTTP response, chưa đăng nhập, chưa gửi thao tác nghiệp vụ và chưa truy vấn DB trong đợt này. Không lưu thông tin đăng nhập trong artifact.

## Phạm vi đã lập từ source

- 82 báo cáo/màn đã có manifest trong repository; chưa phải toàn bộ menu ERP/MES.
- 672 khai báo cột đầu ra trên các báo cáo.
- 100 tên nguồn khác nhau được manifest khai báo; chưa phải tổng số bảng trong DB và chưa kiểm tra tồn tại live.
- Trạng thái do manifest tự khai báo: {'validated': 14, 'pending_ui_validation': 67, 'unspecified': 1}. Giữ nguyên nhãn cũ để truy vết, không coi là xác minh trong lần khảo sát này.

## File

- `screen-columns.csv`: nhãn cột và field đầu ra theo từng report; tên bảng/cột vật lý, công thức và phép biến đổi UI để UNVERIFIED.
- `report-sources.csv`: nguồn được từng manifest khai báo; không tự suy ra quan hệ nối.
- `inventory.json`: toàn bộ danh mục hiện có, filter, nguồn, quyền được khai báo, checksum SQL và các bằng chứng còn thiếu.

## Công việc khi kết nối được

1. Đăng nhập và lập danh sách toàn bộ menu/state nhìn thấy theo quyền tài khoản.
2. Chỉ mở danh mục, cấu hình lưới và báo cáo; không bấm lưu, duyệt, xóa, ghi sổ, import hoặc thao tác thay đổi dữ liệu. Không tự gọi endpoint chưa biết tác dụng.
3. Ghi request/response truy vấn đọc, tham số lọc, nhãn/field UI, grouping, subtotal, paging và formatter.
4. Đọc catalog/định nghĩa DB bằng kết nối chỉ đọc hiện có; tìm function/view/query và khóa nối. Quyền trên UI không đảm bảo nhìn thấy mọi bảng hoặc body function.
5. Ánh xạ từng field API về bảng/cột hoặc biểu thức có bằng chứng. Field chưa xác định giữ nguyên trạng thái chưa biết.
6. Kiểm tra ba mẫu mỗi màn cùng quyền, filter và mốc chốt, bổ sung ca khó cho metric và join nhiều–nhiều.
7. Báo cáo phạm vi đã khảo sát, chưa khảo sát, ngoài quyền và các khác biệt chưa giải quyết; không đánh dấu hoàn tất toàn hệ thống khi còn thiếu bằng chứng.

## Điều kiện đang thiếu

Đường mạng từ môi trường chạy agent tới ERP: địa chỉ có thể truy cập, VPN, proxy hoặc máy trung gian được phép. Chưa có công cụ trình duyệt hoặc browser binary trong môi trường hiện tại; sau khi kết nối được sẽ chuẩn bị công cụ phù hợp để khảo sát UI/API.
