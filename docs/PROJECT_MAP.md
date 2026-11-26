# BẢN ĐỒ CẤU TRÚC DỰ ÁN (PROJECT CODEBASE MAP)

> **Dành cho:** Thành viên mới tham gia dự án, kỹ sư bảo trì và lập trình viên AI.
> **Cập nhật:** 25/11/2026 (Sau khi chuyển `htmp-erp-agent-staging` sang Pipe trực tiếp và gỡ bỏ `htmp-nhanh` / nhánh sinh SQL tự do).
> **Vị trí file:** [`docs/PROJECT_MAP.md`](file:///home/admin/ai-stack/docs/PROJECT_MAP.md)

---

## 1. THƯ MỤC GỐC (ROOT DIRECTORY)

| Tên File / Thư mục | Chức năng & Nội dung chính |
| :--- | :--- |
| [`README.md`](file:///home/admin/ai-stack/README.md) | **Cổng thông tin tổng quan:** Bối cảnh, kiến trúc 8 service Docker trên NVIDIA GB10, rủi ro và lộ trình production. |
| [`AGENTS.md`](file:///home/admin/ai-stack/AGENTS.md) | **Hướng dẫn cộng tác cho agent/kỹ sư:** Điểm vào chính, lệnh kiểm thử, quy tắc an toàn và đối soát. |
| [`RUNBOOK.md`](file:///home/admin/ai-stack/RUNBOOK.md) | **Sổ tay vận hành:** Bật/tắt container, xử lý sự cố, sao lưu và kiểm tra production gate. |
| [`docker-compose.yml`](file:///home/admin/ai-stack/docker-compose.yml) | **Topology chính:** Nginx, Open WebUI, vLLM (`Qwen2.5-14B-Instruct` FP8), Tika, Qdrant, Redis, Langfuse và PostgreSQL Langfuse. |
| [`docker-compose.dev.yml`](file:///home/admin/ai-stack/docker-compose.dev.yml) | Chế độ phát triển live-reload cho frontend Open WebUI. |
| [`Dockerfile.openwebui-speed-runtime`](file:///home/admin/ai-stack/Dockerfile.openwebui-speed-runtime) | Dockerfile build image Open WebUI tùy biến. |

---

## 2. THƯ MỤC TÀI LIỆU (`docs/`)

| Tên File / Thư mục | Chức năng & Nội dung chính |
| :--- | :--- |
| [`docs/ERP_MES_COVERAGE.md`](file:///home/admin/ai-stack/docs/ERP_MES_COVERAGE.md) | **Ma trận độ phủ ERP/MES hiện hành:** Tổng hợp 16 hợp đồng semantic đã duyệt, 18 báo cáo tra cứu và khoảng trống đối soát. |
| [`docs/ERP_CHANGE_CHECKLIST.md`](file:///home/admin/ai-stack/docs/ERP_CHANGE_CHECKLIST.md) | **Checklist kiểm thử nghiệp vụ:** Quy trình rà soát khi thêm/sửa nghiệp vụ tra cứu ERP/MES. |
| [`docs/ERP-COMPLETE-MAPPING-66-TABLES.md`](file:///home/admin/ai-stack/docs/ERP-COMPLETE-MAPPING-66-TABLES.md) | **Từ điển ánh xạ bảng ERP/MES:** Chi tiết các bảng gốc (`ph64`, `ct64`, `ph81`, `ct81`, `ph91`, `ph94`, `ct00`...), khóa nối và ý nghĩa nghiệp vụ. |
| [`docs/erp.md`](file:///home/admin/ai-stack/docs/erp.md) | Nguyên tắc kiến trúc: không để LLM sinh SQL tự do, truy vấn theo hợp đồng xác định. |
| [`docs/PLAN.md`](file:///home/admin/ai-stack/docs/PLAN.md) | Nhật ký các mốc triển khai theo thời gian. |
| [`docs/TONG_QUAN_KHAO_SAT_ERP_MES_VA_HUONG_CHATBOT.md`](file:///home/admin/ai-stack/docs/TONG_QUAN_KHAO_SAT_ERP_MES_VA_HUONG_CHATBOT.md) | Tài liệu khảo sát tổng quan ERP 3S & MES và định hướng ban đầu. |
| [`docs/DANH_SACH_CAU_HOI_TEST_ERP_VA_BAO_CAO.md`](file:///home/admin/ai-stack/docs/DANH_SACH_CAU_HOI_TEST_ERP_VA_BAO_CAO.md) | Bộ câu hỏi kiểm thử nghiệp vụ tham chiếu. |
| [`docs/freecad-mcp-local.md`](file:///home/admin/ai-stack/docs/freecad-mcp-local.md) | Ghi chú tích hợp FreeCAD MCP bridge chạy ngoài repo qua Tailscale. |
| [`docs/knowledge/`](file:///home/admin/ai-stack/docs/knowledge) | Tài liệu nghiệp vụ có metadata nguồn phục vụ `search_knowledge`. |
| [`docs/evidence/`](file:///home/admin/ai-stack/docs/evidence) | Bằng chứng kiểm thử UI/SQL và bản đồ màn hình `ERP-MAP-20261107`. |

---

## 3. MÃ NGUỒN LÕI ERP AI (`erp_ai/`)

| Tên File | Chức năng & Nội dung chính |
| :--- | :--- |
| [`erp_ai/agent_runtime.py`](file:///home/admin/ai-stack/erp_ai/agent_runtime.py) | Nối `QwenClient` (`vLLM`), cấu hình `erp-agent.json`, quyền `erp_user_id` và kết nối PostgreSQL chỉ đọc (`SET TRANSACTION READ ONLY`). |
| [`erp_ai/agent.py`](file:///home/admin/ai-stack/erp_ai/agent.py) | Vòng điều phối bounded tool-calling (`run_agent`, `parse_final`, `Limits`), chặn vòng lặp và bảo vệ tính toàn vẹn dữ liệu rỗng/cắt dòng/thiếu giá trị. |
| [`erp_ai/agent_backend.py`](file:///home/admin/ai-stack/erp_ai/agent_backend.py) | Thực thi tool tra cứu có tham số hóa (`ReportBackend`), lọc tập tool theo ngữ cảnh (`model_specs`) và gợi ý fallback theo metadata hợp đồng. |
| [`erp_ai/semantic_query.py`](file:///home/admin/ai-stack/erp_ai/semantic_query.py) | Trình biên dịch SQL an toàn (`compile_query`) từ JSON plan với whitelist cột/chỉ tiêu, lọc không dấu `contains` và phân quyền `erp_user_id`. |
| [`erp_ai/semantic_executor.py`](file:///home/admin/ai-stack/erp_ai/semantic_executor.py) | Thực thi truy vấn semantic giới hạn dòng, phát hiện cắt dòng (`has_more`, `total_rows`) và tách biệt trạng thái `empty` / `missing` / `partial`. |
| [`erp_ai/semantic_normalizer.py`](file:///home/admin/ai-stack/erp_ai/semantic_normalizer.py) | Chuẩn hóa cấu trúc plan từ model (`parse_plan_arguments`, `normalize_semantic_plan`) dựa theo metadata khai báo trong `erp-agent.json`. |
| [`erp_ai/semantic_request.py`](file:///home/admin/ai-stack/erp_ai/semantic_request.py) | Bảo vệ ràng buộc kỳ thời gian (`require_explicit_month`) để model không tự bỏ/sửa tháng người dùng hỏi. |
| [`erp_ai/context_hints.py`](file:///home/admin/ai-stack/erp_ai/context_hints.py) | Trích xuất xác định ngày ISO, mốc tháng, thực thể và gợi ý dataset từ câu hỏi + lịch sử không cần gọi DB. |
| [`erp_ai/presentation.py`](file:///home/admin/ai-stack/erp_ai/presentation.py) & [`rich_ui.py`](file:///home/admin/ai-stack/erp_ai/rich_ui.py) | Tạo block tóm tắt/bảng/biểu đồ xác định từ kết quả DB, dựng Rich UI HTML embed (`Chart.js`) và Markdown fallback. |
| [`erp_ai/export_files.py`](file:///home/admin/ai-stack/erp_ai/export_files.py) & [`system_dictionary.py`](file:///home/admin/ai-stack/erp_ai/system_dictionary.py) | Xuất file CSV/XLSX tải về từ Rich UI và ánh xạ nhãn cột/trạng thái ERP tiếng Việt. |
| [`erp_ai/entities.py`](file:///home/admin/ai-stack/erp_ai/entities.py), [`validator.py`](file:///home/admin/ai-stack/erp_ai/validator.py), [`identity.py`](file:///home/admin/ai-stack/erp_ai/identity.py), [`incident_log.py`](file:///home/admin/ai-stack/erp_ai/incident_log.py) | Trích xuất thực thể, kiểm tra toàn vẹn tồn kho, ánh xạ danh tính và ghi nhận sự cố UI (`/erp-incidents`). |

---

## 4. PLUGIN & HÀM OPEN WEBUI (`functions/`)

| Tên File | Chức năng & Nội dung chính |
| :--- | :--- |
| [`functions/htmp_erp_agent_pipe.py`](file:///home/admin/ai-stack/functions/htmp_erp_agent_pipe.py) | **Điểm vào duy nhất của `htmp-erp-agent-staging`:** Pipe trực tiếp gọi `erp_ai.agent_runtime.answer`, phát Rich UI `embeds` và trả tóm tắt xác định không qua LLM bọc ngoài. |

---

## 5. CẤU HÌNH, SQL, BẢN VÁ & KIỂM THỬ

- **`config/`**: [erp-agent.json](file:///home/admin/ai-stack/config/erp-agent.json) (nguồn sự thật khai báo cho 18 `reports` + 16 `semantic_contracts` đã duyệt), [htmp-erp-agent-profile.json](file:///home/admin/ai-stack/config/htmp-erp-agent-profile.json), [model-picker-policy.json](file:///home/admin/ai-stack/config/model-picker-policy.json) (`htmp-erp-agent-staging`, `gpt-5.6-luna`), `erp-reports/` (16 manifest).
- **`sql/erp-reports/`**: 18 truy vấn SQL tham số hóa phục vụ 18 báo cáo tra cứu.
- **`backend-patches/` & `ui-patches/`**: Mount đè vào container `open-webui` để tách luồng GPT (`openai.py`, `images.py`), cố định binding (`middleware.py`), lọc model picker (`models.py`) và tùy biến Rich UI (`custom.css`, `chart.umd.min.js`, JS bundle).
- **`scripts/`**: [eval_erp_golden.py](file:///home/admin/ai-stack/scripts/eval_erp_golden.py) (Golden E2E Eval 17 ca kèm đối soát SQL thật), [openwebui_bootstrap_runtime.py](file:///home/admin/ai-stack/scripts/openwebui_bootstrap_runtime.py), `test_erp_agent_postgres.sh`, `backup.sh`, `restore.sh`, `resource_status.sh`.
- **`tests/`**: 7 bộ kiểm thử ERP & UI (`test_erp_agent.py`, `test_erp_semantic_query.py`, `test_erp_semantic_retrieval.py`, `test_erp_export.py`, `test_erp_incident_changes.py`, `test_erp_golden_pipeline.py`, `test_openwebui_speed_selector_patch.py`).
