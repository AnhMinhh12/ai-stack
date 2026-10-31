# Khảo sát đơn hàng ERP ngày 2026-10-29

Các phép kiểm tra thực hiện trong giao dịch chỉ đọc trên cơ sở dữ liệu ERP từ container Open WebUI. Kết quả là ảnh chụp theo thời điểm, không phải cam kết tính đúng nghiệp vụ hay quyền UI.

- `ph64`: 625.137 tiêu đề, mỗi `stt_rec` duy nhất, không có mã khách hàng trống; ngày chứng từ từ 2021-06-26 đến 2026-10-29.
- `ct64`: 813.406 dòng, 625.135 mã chứng từ khác nhau; không thấy dòng mồ côi khi nối `ph64` bằng `stt_rec`. Có 456.301 dòng `tien2 = 0`. Vì thế số dòng không thể thay thế số đơn và số tiền bằng 0 không tự chứng minh lỗi.
- Đơn hàng có USD, VND và SGD. Phải giữ đơn vị tiền tệ hoặc có quy tắc quy đổi đã duyệt; không cộng lẫn tiền nguyên tệ.
- Danh mục trạng thái `SO1` ghi 14 là Từ chối, 15 là Hủy phiếu; các trạng thái còn lại gồm Nháp, Chờ duyệt, Duyệt, Thực hiện, Hoàn thành, Đóng. Cần xác nhận trường hợp nghiệp vụ nào được tính vào chỉ tiêu, không tự cho rằng mọi trạng thái khác đều hợp lệ.
- Trong 30 ngày tính tại thời điểm kiểm tra, tổng `ct64.tien2` khớp `ph64.t_tien2` cho 12.396 đơn có dòng chi tiết. Đây là một phép đối chiếu kỹ thuật trên khoảng thời gian đó, chưa xác nhận ý nghĩa tiền cơ sở, thuế, chiết khấu hoặc công thức kinh doanh.
- `dmkh.ma_kh` duy nhất trong 3.587 dòng tại thời điểm kiểm tra. Có 241 tài khoản `userinfo`, 3 tài khoản `is_super`, không tài khoản nào đồng thời có cả hai trường `ds_branchs` và `ds_stocks` trống.

SQL ứng viên `sql/erp-reports/semantic-customer-orders.sql` xếp hạng khách theo `sum(ct64.tien_nt2)` riêng từng nguyên tệ, loại trạng thái 14 và 15, và ràng buộc đơn vị/kho. Đây chưa phải hợp đồng đã duyệt: cần đối chiếu quyền thực tế theo từng tài khoản, cách hiểu các trạng thái khác, tiền/thuế/chiết khấu và kết quả giao diện ERP trước khi nối chat. Chưa tạo view hay thay đổi dữ liệu ERP.

## Đối chiếu truy vấn ứng viên

Khoảng 2026-09-29 đến 2026-10-29, top 5 khách hàng theo từng nguyên tệ trả về 10 dòng. Kết quả trùng với một truy vấn tổng hợp độc lập theo cùng điều kiện, một lần với tài khoản ERP superuser và một lần với tài khoản ERP thông thường có phạm vi đơn vị/kho. Đây chỉ kiểm tra hai tài khoản và cùng giả định về quyền, trạng thái và công thức; chưa chứng minh cách lọc tương đương quyền thực tế trên UI hoặc chỉ tiêu kinh doanh đã được duyệt. Không xuất tên khách hàng hoặc danh tính tài khoản kiểm tra trong báo cáo này.
