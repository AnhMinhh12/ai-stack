---
name: chatbot-debug
description: "Truy vết lỗi chatbot HTMP khi trả sai, gọi sai tool, mất ngữ cảnh, truy vấn lỗi hoặc hiển thị thiếu kết quả ERP/MES."
---

# Chẩn đoán chatbot HTMP

Mọi đường dẫn tính từ gốc repo.

1. Ghi câu hỏi và lượt trước cần thiết bằng dữ liệu đã ẩn, model/profile, phạm vi người dùng, kết quả mong đợi và hiện tượng. Bắt đầu từ binding trong `backend-patches/middleware.py`. Khi được phép xem runtime, đối chiếu model người dùng thực sự chọn và phiên bản tool đã đăng ký với checkout.
2. Với `htmp-nhanh`, lần từ `functions/htmp_fast_rag.py` đến `Tools.ask_erp` và `_ask_erp_data` trong `functions/htmp_postgres_query.py`. Kiểm tra ngữ cảnh trong `erp_ai/context.py` và thực thể trong `erp_ai/entities.py`. Xác định nhánh lookup, báo cáo hay planner đã chạy. Với báo cáo, lần manifest trong `config/erp-reports/` sang `sql/erp-reports/` hoặc procedure. Với planner, đối chiếu schema candidate, JSON kế hoạch, SQL và tham số đã bind. Ghi rõ nếu nhánh thực tế bỏ qua một bước.
3. Với `htmp-erp-agent-staging`, lần theo `functions/htmp_erp_agent_filter.py`, `functions/htmp_erp_agent.py`, `erp_ai/agent_runtime.py`, `erp_ai/agent.py` và `erp_ai/agent_backend.py`. Chỉ truy sâu semantic pilot khi trace xác nhận nhánh đó. Với vấn đề GPT, xem router tương ứng trong `backend-patches/` và giữ phạm vi sửa theo model.
4. Xác định điểm sai đầu tiên bằng câu hỏi → ngữ cảnh/thực thể → tool và bộ lọc → truy vấn hoặc procedure → trạng thái/số dòng/phạm vi → câu trả lời. Với lỗi hiển thị, đối chiếu payload trước và sau `erp_ai/validator.py`, `erp_ai/rich_ui.py` hoặc `erp_ai/export_files.py` theo nhánh. Kiểm tra dữ liệu rỗng, bị cắt, lỗi quyền và lỗi thực thi riêng.
5. Ưu tiên tái hiện bằng mock/fixture và test có liên quan trong `tests/`. Khi nhiệm vụ cho phép chạy UI, dùng lượt chat mới để so câu trả lời, kết quả tool và bằng chứng nghiệp vụ độc lập. Báo điểm sai đầu tiên, bằng chứng, kết quả sau sửa và các lớp chưa xác minh.

Theo giới hạn truy cập và xử lý bí mật trong `AGENTS.md`.
