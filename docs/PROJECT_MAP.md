# BẢN ĐỒ CẤU TRÚC VÀ TỔNG QUAN NỘI DUNG TỪNG FILE TRONG DỰ ÁN (PROJECT CODEBASE MAP)

> **Dành cho:** Thành viên mới tham gia dự án, kỹ sư bảo trì và lập trình viên AI.  
> **Cập nhật:** Tháng 11/2026 (Sau đợt chuẩn hóa và tinh gọn codebase).  
> **Vị trí file:** [`docs/PROJECT_MAP.md`](file:///home/admin/ai-stack/docs/PROJECT_MAP.md)

---

## 1. THƯ MỤC GỐC (ROOT DIRECTORY)

Thư mục gốc chỉ giữ lại các cấu hình vận hành container, khởi chạy Docker và các tài liệu điều hành cấp cao:

| Tên File / Thư mục | Chức năng & Nội dung chính |
| :--- | :--- |
| [`README.md`](file:///home/admin/ai-stack/README.md) | **Cổng thông tin tổng quan:** Giới thiệu nền tảng Local AI Stack trên máy chủ NVIDIA GB10 (vLLM, Qwen 2.5 14B, Open WebUI, Qdrant). |
| [`RUNBOOK.md`](file:///home/admin/ai-stack/RUNBOOK.md) | **Sổ tay kỹ thuật & quy trình vận hành:** Hướng dẫn bật/tắt container, xử lý sự cố, cấu hình Cronjob backup tự động 02:00 sáng hàng ngày (giữ 30 ngày). |
| [`docker-compose.yml`](file:///home/admin/ai-stack/docker-compose.yml) | **Topology chính:** Khai báo 8 dịch vụ production: Nginx gateway, Open WebUI, vLLM engine, Qdrant vector DB, Redis cache, PostgreSQL (Langfuse), Tika và OCI Registry. |
| [`docker-compose.dev.yml`](file:///home/admin/ai-stack/docker-compose.dev.yml) | Cấu hình chạy chế độ phát triển (live-reload) cho Open WebUI khi cần sửa trực tiếp frontend/backend. |
| [`docker-compose.registry.yml`](file:///home/admin/ai-stack/docker-compose.registry.yml) | Cấu hình chạy Docker Registry nội bộ trên cổng loopback `5443`. |
| [`docker-compose.oidc.yml`](file:///home/admin/ai-stack/docker-compose.oidc.yml) | File mẫu overlay tích hợp đăng nhập tập trung OIDC / SSO (dự phòng). |
| [`Dockerfile.openwebui-speed-runtime`](file:///home/admin/ai-stack/Dockerfile.openwebui-speed-runtime) | Dockerfile chuẩn dùng để build image Open WebUI có sẵn bộ chọn model tốc độ HTMP Speed và logo doanh nghiệp. |
| [`.env`](file:///home/admin/ai-stack/.env) | **Biến môi trường mật:** Chứa mật khẩu, API keys, chuỗi kết nối PostgreSQL ERP (`HTMP_DB_*`), cổng mạng và khóa mã hóa GPG backup. |
| [`.gitignore`](file:///home/admin/ai-stack/.gitignore) | Khai báo các file/thư mục không đưa lên Git (ví dụ `.env`, `backups/`, `data/`, `open-webui-dev/`). |

---

## 2. THƯ MỤC TÀI LIỆU CHUẨN (`docs/`)

Toàn bộ tri thức, kế hoạch, bộ câu hỏi kiểm thử và bằng chứng đối soát CSDL ERP/MES được tập trung tại đây:

| Tên File / Thư mục | Chức năng & Nội dung chính |
| :--- | :--- |
| [`docs/TONG_QUAN_KHAO_SAT_ERP_MES_VA_HUONG_CHATBOT.md`](file:///home/admin/ai-stack/docs/TONG_QUAN_KHAO_SAT_ERP_MES_VA_HUONG_CHATBOT.md) | **Tài liệu Kế hoạch Master (Quan trọng nhất):** Báo cáo khảo sát toàn diện ERP 3S & MES, định hướng chuẩn sang Stored Procedure tổng quát, kết quả test 4 đợt đạt 100%. |
| [`docs/DANH_SACH_CAU_HOI_TEST_ERP_VA_BAO_CAO.md`](file:///home/admin/ai-stack/docs/DANH_SACH_CAU_HOI_TEST_ERP_VA_BAO_CAO.md) | **Test Suite chuẩn:** Tập hợp hơn 70 câu hỏi thực tế (18 câu Sales, câu hỏi demo lãnh đạo, câu hỏi ngẫu nhiên) kèm câu prompt mẫu và căn cứ đối soát CSDL. |
| [`docs/ERP-COMPLETE-MAPPING-66-TABLES.md`](file:///home/admin/ai-stack/docs/ERP-COMPLETE-MAPPING-66-TABLES.md) | **Từ điển ánh xạ 66 bảng:** Chi tiết 66 bảng tra cứu trọng yếu trong ERP 3S & MES, tên bảng DB vật lý (`ph64, ct64, ph81, ct81...`), khóa JOIN và ý nghĩa nghiệp vụ. |
| [`docs/erp.md`](file:///home/admin/ai-stack/docs/erp.md) | **Văn bản kiến trúc nền tảng:** Định nghĩa triết lý cốt lõi: *"Không để LLM sinh SQL tự do mà dùng Deterministic Query qua Semantic Request"*. |
| [`docs/ERP_CHANGE_CHECKLIST.md`](file:///home/admin/ai-stack/docs/ERP_CHANGE_CHECKLIST.md) | **Checklist kiểm thử nghiệp vụ:** Quy trình bắt buộc gồm 9 bước phải tuân thủ mỗi khi thêm mới hoặc sửa đổi một chức năng tra cứu ERP. |
| [`docs/freecad-mcp-local.md`](file:///home/admin/ai-stack/docs/freecad-mcp-local.md) | Hướng dẫn kết nối mô hình vẽ kỹ thuật FreeCAD từ máy cá nhân qua MCP bridge và mạng Tailscale. |
| [`docs/PLAN.md`](file:///home/admin/ai-stack/docs/PLAN.md) | Nhật ký ghi nhận các mốc triển khai (changelog) của hệ thống từ tháng 9 đến nay. |
| [`docs/QLNS.xlsx`](file:///home/admin/ai-stack/docs/QLNS.xlsx) | Bảng dữ liệu thông tin nhân viên công ty (dùng để đồng bộ và phân quyền tài khoản). |
| [`docs/evidence/`](file:///home/admin/ai-stack/docs/evidence) | Thư mục chứa các bằng chứng đối soát thực tế mới nhất: Đợt kiểm toán mở rộng 76 câu hỏi UI ngày 09/11/2026 (`ERP-FULL-20261109`, `ERP-UI-20261109`), đợt nghiệm thu Stored Procedure 07/11/2026 (log chat UI Playwright `ERP-UI-AUDIT-20261107`, test 18 câu Sales `ERP-18-QUESTIONS-20261107`, test baseline 12 câu `ERP-VERIFICATION-20261107`, test ngẫu nhiên 5 câu `ERP-RANDOM-TEST-20261107`, và metadata cột UI `ERP-MAP-20261107`). |
| [`docs/research/`](file:///home/admin/ai-stack/docs/research) | Các báo cáo nghiên cứu lý thuyết chuyên sâu về cơ chế suy luận của mô hình Qwen 14B và kiến trúc AI tự học. |

---

## 3. THƯ MỤC MÃ NGUỒN LÕI ERP AI (`erp_ai/`)

Đây là module Python đóng vai trò là "bộ não" thực thi nghiệp vụ ERP, được Open WebUI gọi vào:

| Tên File | Chức năng & Nội dung chính |
| :--- | :--- |
| [`erp_ai/procedure_catalog.py`](file:///home/admin/ai-stack/erp_ai/procedure_catalog.py) | **Danh mục Stored Procedure & Query Hợp nhất (64 Báo cáo):** Khai báo metadata 64 báo cáo chuẩn của Fast ERP 3S & MES bao phủ toàn diện cả 8 phân hệ doanh nghiệp: IN (Kho, Tồn kho, Lô, HSD, Tuổi hàng, Vị trí máy/kệ, Sức chứa), SO (Bán hàng, Báo giá, Tiến độ, Lệnh TO2, Bảng giá bán, Dự báo tiêu thụ), PO (Mua hàng, NCC, Giá mua hạt nhựa, Tình trạng đơn mua, Phiếu nhập, Xuất trả), GL (Sổ cái TK 111-642, Bảng cân đối phát sinh Trial Balance, Sổ quỹ thu chi, Chi phí SXKD dở dang & quản lý, Công nợ 131/331), MES (Work Order, OEE, Đóng thùng, Gộp tách thùng, Bổ sung shot, Thay khuôn, Dừng máy Downtime, Setup máy, NG linh kiện), MF (Lệnh sản xuất LSX, Thống kê sản xuất, Tiêu hao NVL theo LSX, NXT công đoạn, BOM), QC (IQC/IPQC chi tiết, Tem kiểm định, Phế phẩm NG, Lỗi NVL, Lỗi thành phẩm), VS (Hồ sơ khuôn, Sửa chữa bảo trì khuôn, Cảnh báo bảo dưỡng định kỳ). |
| [`erp_ai/generic_procedure_executor.py`](file:///home/admin/ai-stack/erp_ai/generic_procedure_executor.py) | **Bộ thực thi Procedure Tổng quát (Dual-Path Engine):** Tự động trích xuất thực thể động (vật tư, kho, khách hàng, NCC, tiểu khoản kế toán 3-5 số như TK 1521, 1311, 3311, máy ép `DUC-xxxx`, khuôn `K_xxxx`, Lệnh SX `\d{3}-\d{4}-\d{6}`), thiết lập mặc định kiểu dữ liệu an toàn tránh lỗi ép kiểu PL/pgSQL, cơ chế guard chống quá tải quét bảng triệu dòng, gọi DB an toàn qua rollback. Thực thi kết hợp 2 tầng: Stored Procedure PL/pgSQL chuẩn (đã tháo gỡ lỗi `DROP TABLE` trong transaction) và Direct Structural SQL Handlers cho các bảng nghiệp vụ gốc (`ct00`, `dmtk0`, `phiqc`, `ctlsx`, `phlsx`, `dmgiamuact`, `dmbanggiact`, `dmhosokhuon`, `mfdmfc1`, `cdbsp`, `cdvt13`, `mes_oi_van_hanh_khuon`, `mes_oi_bo_shot`, `intem_carton_log`), tích hợp tính toán tổng hợp cấp cơ sở dữ liệu (Database-level Aggregation) chống ảo giác cắt dòng và render bảng Markdown chuẩn hóa. |
| [`erp_ai/native_tools.py`](file:///home/admin/ai-stack/erp_ai/native_tools.py) | Định nghĩa 16 công cụ nghiệp vụ chuẩn được đăng ký vào Open WebUI (bổ sung: `lookup_qc_lot_status`, `lookup_mes_ng`, `lookup_mes_packing`, `lookup_delivery_orders`), tích hợp động cơ **Universal Entity 360 Resolver** (`_get_material_360`, `_get_partner_360`) nạp đầy đủ danh tính, đối tác, đóng gói, đơn giá và tồn kho vị trí máy/kệ `cdvt13` trong 1 lần truy vấn. |
| [`erp_ai/entities.py`](file:///home/admin/ai-stack/erp_ai/entities.py) | Bộ bóc tách thông minh: nhận diện mã vật tư, mã kho, mã khách hàng, mã NCC, khoảng thời gian. |
| [`erp_ai/context.py`](file:///home/admin/ai-stack/erp_ai/context.py) | Bộ nhớ hội thoại (Conversation Store): kế thừa ngữ cảnh khi người dùng hỏi tiếp các câu hỏi ngắn ("còn mã này thì sao?", "tháng trước thế nào?"). |
| [`erp_ai/router.py`](file:///home/admin/ai-stack/erp_ai/router.py) | Định tuyến câu hỏi tự nhiên tới đúng handler nghiệp vụ tương ứng. |
| [`erp_ai/validator.py`](file:///home/admin/ai-stack/erp_ai/validator.py) & [`contracts.py`](file:///home/admin/ai-stack/erp_ai/contracts.py) | Kiểm duyệt tính an toàn, bảo vệ dữ liệu và chặn các câu trả lời sai lệch trước khi trả về chat. |
| [`erp_ai/export_files.py`](file:///home/admin/ai-stack/erp_ai/export_files.py) & [`rich_ui.py`](file:///home/admin/ai-stack/erp_ai/rich_ui.py) | Sinh mã HTML Rich UI, vẽ biểu đồ Chart.js và tạo file Excel/CSV tải trực tiếp trên chat. |
| [`erp_ai/incident_log.py`](file:///home/admin/ai-stack/erp_ai/incident_log.py) & [`incidents_page.html`](file:///home/admin/ai-stack/erp_ai/incidents_page.html) | Module ghi nhận và giao diện theo dõi các sự cố tra cứu ERP của người dùng. |
| [`erp_ai/semantic_query.py`](file:///home/admin/ai-stack/erp_ai/semantic_query.py) | Adapter truy vấn ngữ nghĩa cho các bảng tra cứu. |

---

## 4. CÁC PLUGIN & CUSTOM TOOLS TRÊN OPEN WEBUI (`functions/`)

Các file được nạp trực tiếp vào cơ sở dữ liệu và giao diện Open WebUI:

| Tên File | Chức năng & Nội dung chính |
| :--- | :--- |
| [`functions/htmp_postgres_query.py`](file:///home/admin/ai-stack/functions/htmp_postgres_query.py) | **Tool Native Chính (`Tra cứu PostgreSQL ERP`):** Cầu nối trực tiếp giữa giao diện chat Open WebUI với bộ Stored Procedure trong `erp_ai/`. |
| [`functions/htmp_fast_rag.py`](file:///home/admin/ai-stack/functions/htmp_fast_rag.py) | **Filter Tiền xử lý (`HTMP Fast RAG`):** Làm sạch prompt, bóc tách ký tự rác và điều hướng nhanh cho model `HTMP ERP`. |
| [`functions/htmp_technical_rag.py`](file:///home/admin/ai-stack/functions/htmp_technical_rag.py) | **Filter Tra cứu Kỹ thuật:** Phục vụ hỏi đáp tài liệu kỹ thuật nội bộ qua Qdrant vector DB. |
| `htmp_erp_agent.py` & `htmp_erp_agent_filter.py` | Tool và Filter phụ trợ cho profile staging. |

---

## 5. BẢN VÁ HỆ THỐNG MOUNT VÀO DOCKER

### Backend Patches (`backend-patches/`)
Được mount đè vào bên trong container `open-webui` (`/app/backend/...`):
- `openai.py`: Patch router API OpenAI để hỗ trợ streaming mượt mà và route `/api/v1/erp/incidents`.
- `middleware.py`: Chống lặp vô tận khi gọi tool (`max_tool_call_iterations=1`).
- `models.py`: Quản lý hiển thị danh sách model trên giao diện theo chính sách nội bộ.
- `images.py`: Xử lý hiển thị và bảo vệ hình ảnh nội bộ.

### UI Patches (`ui-patches/`)
Được mount đè vào giao diện web tĩnh của Open WebUI:
- `index.html`: Khung trang web chính.
- `custom.css`: Tùy biến giao diện bảng dữ liệu ERP, theme sáng/tối.
- `chart.umd.min.js`: Thư viện Chart.js để vẽ biểu đồ Cột, Đường, Tròn trong khung chat.
- `bulk-chat-delete.js`: Tiện ích xóa hàng loạt đoạn chat cũ.
- Các file bundle JS (`2.Czbv28Xq.js`, `D5GoHi-U.js`, `DoNOBSZH.js`, `Cskhiuvj.js`): Giao diện đăng nhập nhân viên, cuộn khung chat mượt mà.

---

## 6. CÁC THƯ MỤC CÒN LẠI

| Thư mục | Mục đích sử dụng |
| :--- | :--- |
| [`config/`](file:///home/admin/ai-stack/config) | Chứa [erp_metadata_dictionary.json](file:///home/admin/ai-stack/config/erp_metadata_dictionary.json) (~2.8 MB từ điển metadata ERP) và cấu hình Apache Tika. |
| [`data/`](file:///home/admin/ai-stack/data) | Nơi lưu trữ 2 file CSDL SQLite cục bộ: `local_webui.db` (bản sao DB WebUI) và `erp-incidents.db` (lịch sử sự cố tra cứu). |
| [`nginx/`](file:///home/admin/ai-stack/nginx) | Cấu hình reverse proxy Nginx cổng 80/443, SSL certs và rate limit chống spam. |
| [`scripts/`](file:///home/admin/ai-stack/scripts) | Bộ script vận hành: `backup.sh`, `restore.sh`, `resource_status.sh`, `manage_gpt_users.py`, `import_users_from_qlns.py`. |
| [`backups/`](file:///home/admin/ai-stack/backups) | Thư mục lưu các bản sao lưu tự động hàng ngày (tự động dọn dẹp các bản quá 30 ngày). |
| [`scratch/`](file:///home/admin/ai-stack/scratch) | Thư mục chứa các bộ script kiểm định nghiệp vụ: [`run_full_corners_ui_test.py`](file:///home/admin/ai-stack/scratch/run_full_corners_ui_test.py) (Kiểm thử tự động 17 ca toàn bộ ngóc ngách nghiệp vụ trực tiếp trên giao diện Open WebUI qua CDP đạt 100%), [`run_enterprise_all_departments_verification.py`](file:///home/admin/ai-stack/scratch/run_enterprise_all_departments_verification.py) (40 test case toàn diện 8 phân hệ doanh nghiệp đạt 100%), [`run_full_expanded_verification.py`](file:///home/admin/ai-stack/scratch/run_full_expanded_verification.py) (23 test case kiểm thử Stored Procedures và tools native), [`sync_expanded_to_webui.py`](file:///home/admin/ai-stack/scratch/sync_expanded_to_webui.py) (Đồng bộ tool và specs vào `webui.db`). |
| [`open-webui-dev/`](file:///home/admin/ai-stack/open-webui-dev) | Toàn bộ mã nguồn Open WebUI upstream (dùng khi cần build lại Docker image). |
| [`tests/`](file:///home/admin/ai-stack/tests) | Bộ unit test tự động cho module `erp_ai` và export file. |

