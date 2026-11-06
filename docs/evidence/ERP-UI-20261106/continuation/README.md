# Tiếp tục khảo sát giao diện và đối chiếu metadata ERP

Lượt này đọc màn qua phiên Edge do người dùng đăng nhập, tài khoản IT.ERP, không lưu, duyệt, xóa, nhập hoặc sửa dữ liệu. Danh mục nguồn có 254 mã menu; nhóm menu, thao tác phiên và màn chưa phân loại không mặc nhiên là màn nghiệp vụ. Lượt tự động chỉ điều hướng các mục đã phân loại báo cáo, danh mục và chứng từ; không tự chạy chức năng ghi. Nội dung được ghi từng dòng trong `ui-observations.jsonl`, chỉ gồm tiêu đề, URL dạng hash, nhãn bộ lọc và tiêu đề cột. Do độ trễ tải và điều hướng khác tên, từng kết quả phải kiểm tra lại trước khi gắn với màn; có tiêu đề hoặc cột không chứng minh hiểu nghiệp vụ.

`function-candidates.json` là phép ghép tên state với function PostgreSQL `public`, đọc trong transaction READ ONLY. Danh sách bảng và từ khóa được trích bằng biểu thức văn bản từ source function, có thể lẫn alias, comment hoặc SQL động; không chứng minh function được UI gọi, mối nối, hành vi an toàn hay công thức. Không thực thi các function.

`grid-metadata.json` gồm cấu hình lưới khớp các grid ID trong inventory; nhãn và nguồn khai báo là metadata, chưa chứng minh output thực tế hoặc nguồn vật lý. `mapping-progress.csv` là bảng theo dõi được tạo từ inventory và lượt quan sát; các cột API, công thức, quyền và nghiệm thu để UNVERIFIED cho đến khi có bằng chứng tương ứng. Nhãn `fields_or_columns_observed_requires_review` chỉ là tín hiệu có dữ liệu trên trang sau thao tác; có thể là dữ liệu trang trước hoặc tải chưa xong.

Lượt này chưa xác minh được toàn bộ quy trình, endpoint, dữ liệu thực tế, function thực sự được gọi, điều kiện quyền, kết quả DB hay nghiệm thu nghiệp vụ. Một phiên IT.ERP không chứng minh bao phủ các màn không hiển thị theo quyền.

## Kiểm tra lại bảy màn không có cột/bộ lọc ở lượt đầu

Sau thời gian chờ dài hơn, cả bảy màn đều hiển thị tiêu đề và nội dung, trong `retry-unresolved.json`. `MfTKHSX` hiển thị lưới với các nhãn kế hoạch; `DMNamTCList` là form năm tài chính; `INBCTrangThaiKho` hiển thị trạng thái kho; `InTemAriston` và `InTemEero` là form in tem; `INTonKhoTucThoi` là form có nút thực hiện; `UpdateTemKK` là form cập nhật tem kiểm kê. Chỉ mở và đọc màn, không bấm in, thực hiện hoặc cập nhật. Mô tả này không xác minh tính toán, quyền hoặc tác dụng của nút.
