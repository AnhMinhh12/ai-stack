# Báo Cáo Kiểm Toán & Tình Trạng Thực Tế ERP Mapping (Audit & Progress Register)

- **Thời điểm cập nhật**: `2026-10-27T09:52:00+07:00`
- **Môi trường khảo sát**: `10.0.6.2:1004` (ERP Web) & `10.0.6.2:1006` (Grafana)
- **Tài khoản**: `IT.ERP` / Đơn vị: `001 - HTMP QM` (quyền: `is_admin=1`, `is_super=0`)
- **Ngôn ngữ**: `vi-VN`

---

## 1. Bảng Trạng Thái Thực Nghiệm Các Hạng Mục A1 – A11

| Mã ID | Hạng mục công việc | Trạng thái thực tế | Bằng chứng hiện có | Việc còn thiếu / Cần làm tiếp |
|:---:|---|:---:|---|---|
| **A1** | **Bảo mật khu vực làm việc** | **Đang thực hiện (In Progress)** | - Đã xóa file `session_info.json` chứa token thô khỏi ổ đĩa.<br>- Đã lưu bản che dữ liệu: `evidence/session_info_redacted.json`.<br>- Đã cấu hình `.gitignore`. | - Cần thu hồi/hủy phiên làm việc (revoke session) trên hệ thống khi kết thúc đợt khảo sát. |
| **A2** | **Tái hiện cây menu gốc** | **Hoàn thành (Completed)** | - `evidence/menu/menu-tree-redacted.json` (337 mục).<br>- `coverage/screens.csv` (171 màn hình lá). | Đã khớp 100% số lượng menu và màn hình lá. |
| **A3** | **Kiểm tra cấu hình Grid** | **Đạt mức Metadata** | - Đủ 171 file JSON trong `evidence/config/<screen_state>.json`.<br>- Ghi nhận mã HTTP thực tế: 114 `CONFIG_FOUND`, 11 `NO_GRID_CONFIG` (grid rỗng), 15 `GRAFANA_EMBED`, 31 `SPECIAL_PAGE`. | Chưa chụp request/response của màn hình khi chạy dữ liệu thật. |
| **A4** | **Phân loại màn hình phi-Grid** | **Một phần (Partial)** | - Đã lập sổ đăng ký 15 Dashboard Grafana trong `evidence/dashboards/dashboard_register.csv`. | 31 `SPECIAL_PAGE` mới chỉ phân loại theo URL/templateUrl từ menu; **chưa mở từng trang** trên trình duyệt để xác minh hành vi thực tế (modal, redirect hay container). |
| **A5** | **Bắt API đọc dữ liệu thật** | **Hoàn thành cho SO1 (Completed for SO1)** | - `handoff/sales_orders/request.json`: request GET `/SOAPI/api/Vouchers/SO1API/GetData/?searchDynamic=...` kèm headers và tham số chuẩn.<br>- `handoff/sales_orders/response.json`: response thật từ ERP với `TotalItems: 579.110` và 20 dòng dữ liệu (đã che PII khách hàng). | Mở rộng bắt API cho các màn hình ưu tiên tiếp theo (Wave 1: `inventory_by_warehouse`). |
| **A6** | **Xác minh chứng từ SO1** | **Hoàn thành UI & API (UI & API Captured)** | - `handoff/sales_orders/ui.png`: ảnh chụp grid rõ 10 cột, 20 dòng, tổng 579.110 (đã che PII).<br>- `handoff/sales_orders/ui-cases.md`: 3 ca thực tế (Duyệt, Chờ duyệt, Giao bù `ma_gd = 10`).<br>- `handoff/sales_orders/metric-definition.md`: trả lời đủ 8 câu hỏi về URL, endpoint, date, status, grain, paging, grouping, null/zero.<br>- Gói bàn giao sẵn sàng gửi Máy A: `handoff/sales_orders/`. | Chờ Máy A đối soát Database Catalog, viết reference SQL và đối soát 3 chiều (`RECONCILED`). |
| **A7** | **Khảo sát Database Catalog** | **Chưa bắt đầu (Not Started)** | **Không có**. Chưa có kết nối SQL chỉ đọc, chưa có `evidence/db/`. | Cần tài khoản DB chỉ đọc để lấy danh mục bảng, view, function, procedure, khóa chính/ngoại. |
| **A8** | **Ánh xạ cột sang Database** | **Chỉ ở mức Metadata** | - `mapping/field-map.csv` (1.712 dòng): 1.335 `UI_CONFIG_LIVE`, 362 `UNVERIFIED`, 15 `MENU_LIVE`.<br>- **0 dòng `DB_VERIFIED`**. | Chưa có định nghĩa catalog DB hoặc query SELECT tham chiếu để chứng minh nguồn bảng vật lý và khóa nối. |
| **A9** | **Đối soát luồng nghiệp vụ 3 chiều** | **Chưa bắt đầu (Not Started)** | **Không có**. Chưa có thư mục `evidence/reconciliation/`. | Chưa đối chiếu ca mẫu nào theo công thức: `Giao diện Web == Phản hồi API == Câu lệnh SQL SELECT`. |
| **A10** | **Xác thực Dashboard** | **Một phần (Partial)** | - Chỉ mới có danh mục URL nhúng Grafana (`MENU_LIVE`) trong `evidence/dashboards/dashboard_register.csv`. | Chưa trích xuất panel query, datasource, biến số (variables) hoặc công thức tính của Grafana. |
| **A11** | **Công bố phạm vi hỗ trợ** | **Chưa hoàn thành (Incomplete)** | - Đã công bố phạm vi và ranh giới tại `coverage/summary.md`. | **Chưa có bất kỳ metric nghiệp vụ nào đạt mức `RECONCILED`**. Trợ lý AI chưa được phép trả lời số liệu tài chính/tồn kho/sản xuất dựa trên metadata. |

---

## 2. Thống Kê Phân Loại Cột Trong `mapping/field-map.csv`

- **`UI_RENDERED_LIVE`**: **0 dòng** (Đã hạ cấp toàn bộ các trường dữ liệu bảng SO1 về `UI_CONFIG_LIVE` vì chưa có đối soát DB).
- **`UI_CONFIG_LIVE`**: **1.335 dòng** (Có khai báo bảng `tablename`, khóa nối và style từ API `InitGridMenu`, nhưng chưa kiểm chứng với DB).
- **`MENU_LIVE`**: **15 dòng** (Liên kết iframe Grafana từ cấu hình menu).
- **`UNVERIFIED`**: **362 dòng** (Không có thông tin bảng nguồn từ metadata).
- **`DB_VERIFIED`**: **0 dòng** (Chưa có kết nối DB).
- **`RECONCILED`**: **0 dòng** (Chưa đối soát 3 chiều).
