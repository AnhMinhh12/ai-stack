# Khảo sát cấu trúc ERP ngày 2026-10-29

Khảo sát qua tài khoản kết nối ERP của container Open WebUI, trong giao dịch chỉ đọc. Chỉ đọc metadata `information_schema`, không đọc các dòng dữ liệu nghiệp vụ. Phạm vi là schema `public` mà tài khoản kết nối nhìn thấy.

- 600 đối tượng: 598 bảng và 2 view; 12.167 cột.
- Không trả về khóa ngoại khai báo qua `information_schema`. Điều này không chứng minh không có quan hệ nghiệp vụ hoặc không có khóa ngoại mà tài khoản không nhìn thấy. Không suy đoán đường nối từ tên cột.
- 82 bản mô tả báo cáo trong danh mục tham chiếu 100 tên nguồn khác nhau; cả 100 tên đều xuất hiện trong các đối tượng nhìn thấy. Còn 500 đối tượng chưa được tham chiếu theo tên trong các bản mô tả này. Đây là số lượng bao phủ metadata, không phải đánh giá bao phủ nghiệp vụ.
- Bản metadata đầy đủ được ghi tạm tại `/tmp/htmp-erp-schema-inventory.json`. Không đưa bản này trực tiếp vào ngữ cảnh model hay xem nó là cấp quyền.

Cách tạo lại: chạy `scripts/erp_schema_inventory.py` trong môi trường đã có các biến kết nối ERP, chuyển stdout vào một tệp được bảo vệ. Script không in chuỗi kết nối hoặc thông báo lỗi từ driver.

Để có thể truy vấn tổng quát an toàn, cần xác nhận quan hệ, công thức, phạm vi dữ liệu và quyền theo người dùng từ nguồn nghiệp vụ/ERP; metadata cấu trúc và tên bảng không đủ. Các định nghĩa chưa xác minh không được dùng làm hợp đồng thực thi.

## Đối chiếu trực tiếp với bản mô tả báo cáo

Công cụ `scripts/erp_semantic_audit.py` đối chiếu nguồn và các tham chiếu `bang.cot` được ghi trực tiếp trong `ui_column_mapping`. Ngày 2026-10-29, trong 82 bản mô tả có 264 tham chiếu cột trực tiếp được kiểm tra và không có tham chiếu nào thiếu trong metadata nhìn thấy. Các biểu thức dùng alias, cột tính toán và đường nối không được tự suy đoán hoặc coi là đã kiểm tra. Kết quả chi tiết tạm thời tại `/tmp/htmp-erp-semantic-audit.json`.

Chạy lại: `python3 scripts/erp_semantic_audit.py --schema /tmp/htmp-erp-schema-inventory.json --output /tmp/htmp-erp-semantic-audit.json`.

## Ứng viên quan hệ từ SQL báo cáo

`scripts/erp_relationship_candidates.py` tìm các điều kiện bằng nhau giữa những cột được xác nhận tồn tại trong metadata, dựa trên tên bảng và alias trong SQL báo cáo. Lần chạy này tạo 202 ứng viên có nguồn SQL, mã băm và trạng thái của tài liệu báo cáo tại `/tmp/htmp-erp-relationship-candidates.json`.

Đây là trích xuất bằng quy tắc đơn giản, không phải bộ phân tích SQL đầy đủ. Alias có thể bị tái sử dụng trong các phạm vi truy vấn, điều kiện bằng nhau có thể không phải phép nối, và điều kiện bổ sung có thể quyết định ý nghĩa của quan hệ. Do đó từng ứng viên phải được kiểm tra trong toàn bộ SQL, cùng lực lượng nghiệp vụ, phạm vi quyền và tính duy nhất trước khi phê duyệt. Tuyệt đối không dùng tập ứng viên này để tạo hoặc thực thi SQL.

Chạy lại: `python3 scripts/erp_relationship_candidates.py --schema /tmp/htmp-erp-schema-inventory.json --output /tmp/htmp-erp-relationship-candidates.json`.
