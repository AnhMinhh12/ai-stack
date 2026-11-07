# Pilot ngữ nghĩa ERP — 07/11/2026

Trạng thái: thử nghiệm trong mã nguồn, chưa phát hành lên luồng chat. Không chứng nhận nghiệp vụ, phân quyền ERP hoặc đối chiếu số liệu.

## Đã thực hiện

- Thêm kiểm tra yêu cầu tháng cụ thể trong pilot semantic: kế hoạch phải giữ đủ đầu/cuối tháng trên cùng trường ngày do hợp đồng máy chủ định nghĩa. Khoảng nhiều tháng chưa hỗ trợ sẽ bị từ chối; không tự suy diễn.
- Bộ biên dịch từ chối bộ lọc trùng và khoảng ngày đảo ngược.
- Kiểm thử `python3 -m unittest tests.test_erp_semantic_query tests.test_erp_agent tests.test_erp_semantic_retrieval -q`: 51 test đạt, gồm trường hợp tháng bị bỏ không gọi DB. Đây là bằng chứng kỹ thuật, không phải nghiệm thu ERP.
- Mở qua phiên ERP được cấp quyền hai màn `SOBKDonHang` và `SOBCTienDoGH`. Cả hai có khoảng ngày, khách hàng, vật tư, đơn vị, trạng thái; màn tiến độ có kho và nhóm theo. Bảng kê đơn có bộ lọc giao dịch gồm đơn sang lệnh giao, phiếu xuất, xuất điều chuyển và giao bù. Màn tiến độ có mẫu báo cáo riêng. Chưa chạy báo cáo để so số.

## Chưa hoàn thành

- Pilot chưa có cơ chế bảo toàn toàn bộ thực thể, câu nhiều lượt, nhiều kỳ và các kiểu ngày khác; chốt tháng chỉ bao phủ dạng tháng cụ thể được nhận diện, không thay thế bộ hiểu yêu cầu chung.
- Chưa chứng thực các trường ngày của dataset với ý nghĩa ngày người dùng hỏi, hoặc công thức đơn–giao–còn; không tự ghép đơn với giao từ tên bảng. Chưa xác minh tương đương quyền ERP.
- Chưa kiểm tra nguồn trong cấu hình với người phụ trách nghiệp vụ; nhãn `approved` không phải biên bản duyệt. Chưa có holdout end-to-end UI hoặc so sánh thực tế cùng bộ lọc.
- Không kết nối chức năng thử nghiệm này vào model `htmp-nhanh` hoặc GPT. `erp_ai` là bind mount hiện có; mã mới chưa được chứng minh nạp vào quy trình chat đang chạy.

## Đối chiếu UI và DB bổ sung

Phiên ERP IT.ERP, ngày 07/11: chọn mẫu SO1 `001-2610-012362`, cùng ngày chứng từ 31/10/2026, ĐVCS `001`; giữ các lựa chọn mặc định trên từng báo cáo. Truy vấn DB chỉ đọc tìm thấy một dòng `VMH1A432`, số lượng 100 và một lịch `ctkhgh` số lượng 100. Đây là quan sát DB theo tài khoản kết nối chỉ đọc, chưa chứng minh cùng phạm vi quyền với phiên ERP.

Hai API báo cáo trả `Success: true` với đúng khoảng ngày và số CT được xác nhận trong request; bảng kê không có dòng, tiến độ chỉ có các dòng tổng hợp, không có dòng chi tiết. Chi tiết điều kiện và số dòng: `erp-ui-doi-chieu.json`. Lần đầu nhập ngày trực tiếp bằng chuỗi ISO, thành phần lịch đã chuyển nhầm thành năm 6103; kết quả lần đó bị loại bỏ. Lần sau dùng datepicker và kiểm tra payload thực tế.

Nguồn function `sobctiendogh` cho thấy có điều kiện quyền, lọc trạng thái, lịch giao `ctkhgh` và liên kết số thực xuất; đây là bằng chứng đọc source, chưa chứng minh API thực tế gọi function này. Nguyên nhân ERP trả rỗng chưa rõ: cần đối chiếu cùng cơ sở dữ liệu, cùng danh tính, điều kiện server và nguồn API trước khi xây dựng công thức. Chưa kết luận không có dữ liệu hoặc chứng từ bị mất.

## Phân quyền và bộ lọc báo cáo

Phiên ERP hiện tại là `IT.ERP`, user_id 78, đơn vị 001. Đối chiếu `userinfo` trong DB chỉ đọc: `is_super=0`, `ds_branchs=001`, `ds_stocks` rỗng. Đọc source `sys_getrolerecord` cho thấy với loại quyền báo cáo `R` có nhánh tính kho theo đơn vị trong `dmkho`, và xử lý kho rỗng có điều kiện. Bộ biên dịch pilot `sales_orders_scoped_v1` hiện kiểm tra trực tiếp kho có trong `ds_stocks`, do đó không thể khẳng định tương đương ERP; chưa được sử dụng để trả kết quả thật. Gọi trực tiếp `sys_getrolerecord` trong transaction READ ONLY bị PostgreSQL từ chối vì function có `DROP TABLE`; không đổi transaction sang chế độ ghi để vượt qua giới hạn đó.

Lặp lại hai báo cáo với cùng chứng từ, ngày, đơn vị nhưng chọn nhóm `Không`; cả hai vẫn không có dòng chi tiết. Điều kiện và số dòng tại `erp-ui-khong-nhom.json`. Kết quả không đủ phân biệt quyền, nguồn DB của ứng dụng, hoặc các điều kiện khác; không suy luận nguyên nhân.

Pilot: các cấu hình chưa được nghiệm thu đã đổi trạng thái `pilot_unapproved`. Bổ sung phân loại tập kết quả thiếu giá trị, không để model biến NULL thành 0, và trả lời xác định khi kết quả bị cắt hoặc không có dòng theo phạm vi truy vấn. Bộ `tests.test_erp_semantic_query`, `tests.test_erp_agent`, `tests.test_erp_semantic_retrieval`: 54 kiểm thử kỹ thuật đạt. Chưa tích hợp vào model đang dùng, chưa chứng minh khớp ERP và chưa có business sign-off.

## Hiệu chỉnh về môi trường UI

Người dùng xác nhận ngày 07/11 rằng UI ERP đang mở là môi trường thử nghiệm không được cập nhật dữ liệu mới. Các lần UI không có dòng ở trên chỉ là quan sát trên môi trường thử nghiệm; không coi là lỗi, không dùng để đối soát số liệu DB mới nhất hoặc chứng minh hai nguồn giống nhau. Bản đồ cấu trúc UI–metadata–DB–function: `../ERP-MAP-20261107/README.md`.
