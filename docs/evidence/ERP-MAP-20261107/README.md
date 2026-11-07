# Bản đồ bằng chứng giao diện ERP, metadata và DB

Ngày 07/11/2026. Theo người dùng, giao diện ERP đang mở là môi trường thử nghiệm không được cập nhật dữ liệu mới. Vì vậy dữ liệu UI rỗng hoặc khác dữ liệu DB không chứng minh có lỗi dữ liệu; giao diện được dùng để hiểu bộ lọc, cột và thao tác nghiệp vụ. Chưa xác minh UI và DB trỏ cùng cơ sở dữ liệu hay đồng bộ cùng thời điểm.

## Phạm vi bản đồ

- `screen-map.json`: 254 mục trong inventory trước; 196 mục có ghi nhận đã thao tác mở trong lượt trước. 72 mục có ứng viên grid khớp đúng tên state kèm hậu tố số; 64 mục có function trùng tên. Các tên là ứng viên, không chứng minh lưới, function hay bảng được backend sử dụng.
- 2.890 dòng cấu hình cột ứng viên: 888 có tên bảng/cột vật lý tương ứng trong schema DB được đọc, 636 không tìm thấy cặp bảng/cột (có thể là cột tính toán, alias, bảng tạm hoặc metadata cũ), 1.346 không khai báo đủ bảng/cột nguồn, 20 khai báo bảng không thấy trong schema `public`. Đếm theo cột trên từng grid, không phải số nghiệp vụ đã hiểu hay số lỗi.
- `screen-summary.csv`: danh mục rút gọn theo màn; trạng thái `unverified` cho API→function, công thức, quyền và nghiệm thu.
- `sobctiendogh-ui-columns.json`: đối chiếu trực tiếp 22 tiêu đề và ID cột trên màn tiến độ giao với cấu hình `sys_gridconfig` chụp trước và khóa trả về trong 5 dòng tổng hợp API. 21/22 tên trường có cấu hình grid, 22/22 xuất hiện trong những dòng tổng hợp; không có dòng chi tiết để kiểm tra trị số.

## Ví dụ vì sao cần đối chiếu nhiều tầng

Trên màn tiến độ giao, cột **Trạng thái** có ID `status_name`, trong metadata cùng trường có nhãn cấu hình “Số CT” và nguồn khai báo `ct61.status_name`. Điều đó không chứng minh nguồn thực tế là `ct61`; nó cho thấy nhãn, tên trường và dữ liệu nguồn không thể mặc định là một. Các cột `so_luong`, `so_luong_hda`, `so_luong_cl` hiển thị lần lượt số đơn, số đã giao và số còn lại, nhưng metadata không khai báo bảng nguồn. Định nghĩa function ứng viên có logic lịch giao, phiếu xuất và đóng đơn; chưa xác minh API gọi function này hoặc nghiệp vụ duyệt công thức.

## Nguồn và giới hạn

- UI/metadata/function candidates: `docs/evidence/ERP-UI-20261106/continuation/`, gồm trạng thái quan sát và cảnh báo về độ trễ hoặc màn cũ. Không coi toàn bộ 196 lượt đã hiểu nghiệp vụ.
- DB schema được thu thập qua `information_schema.columns` trong transaction READ ONLY ngày 07/11; chỉ đối chiếu sự tồn tại tên bảng/cột. Dữ liệu schema snapshot không chứng minh DB là cùng môi trường với UI.
- Cột trùng tên không chứng minh join, grain, công thức, quyền hay thời điểm. Từ khóa SQL trong source có thể xuất hiện trong comment, alias hoặc SQL động.
- Các số/phiếu ở `docs/evidence/ERP-SEMANTIC-20261107/` là quan sát từng môi trường; không dùng để khẳng định sai lệch sản xuất.
- Chưa rà đầy đủ 254 màn, đối chiếu từng cột, xác thực chuỗi UI→API→function, phân quyền và nghiệm thu nghiệp vụ. Không triển khai mapping này vào chatbot như hợp đồng đã duyệt.

Tái tạo: `python3 scripts/build_erp_screen_evidence_map.py --columns <schema-json> --output docs/evidence/ERP-MAP-20261107`. Tệp schema là JSON các bộ `[table_name, column_name, data_type]` từ `information_schema.columns` của schema `public`.
