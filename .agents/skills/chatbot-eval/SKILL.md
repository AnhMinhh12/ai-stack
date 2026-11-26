---
name: chatbot-eval
description: "Chạy test và đánh giá hồi quy chatbot HTMP, so đáp án ERP/MES trước và sau thay đổi, ghi nhận độ đúng nghiệp vụ và phần chưa kiểm chứng."
---

# Đánh giá chatbot HTMP

Mọi đường dẫn tính từ gốc repo. Chọn model/profile, nhóm câu hỏi và tiêu chí đáp án trước khi chạy.

- Bắt đầu với các lệnh test cục bộ đã xác minh trong `AGENTS.md`. Chọn thêm module bằng `-p` và ca bằng `-k` theo phạm vi. Trước khi chạy cả suite hoặc nhóm incident, kiểm tra các ca bị chặn ghi trong `AGENTS.md` và cô lập mọi đường gọi DB. Báo lỗi và skip theo nguyên nhân, dùng cùng phạm vi test khi so baseline.
- `scripts/evaluate_erp_agent.py` chạy các ca tổng hợp của staging, với adapter DB giả lập và endpoint Qwen thật. Chỉ chạy khi được phép dùng endpoint đó và môi trường đã có `httpx` cùng cấu hình xác thực. Chấm nội dung đáp án theo fixture. Số lượt `answered`, số nguồn và độ trễ chỉ là số đo vận hành.
- `tests/erp_agent_postgres_fixture.py` sinh SQL với DDL/DML tổng hợp, dành cho PostgreSQL trống dùng riêng và có thể hủy. `scripts/evaluate_sales_workbook.py` có đường gọi DB thật. Kiểm tra chế độ và đích kết nối trước khi chạy, tuân theo giới hạn trong `AGENTS.md`.
- Dùng danh sách ca trong `docs/evidence/ERP-FULL-20261109/suite.json` làm nguồn câu hỏi cho kiểm thử UI ERP được phép. Xác lập lại đáp án tham chiếu theo dữ liệu, thời điểm và quyền của lần chạy. Ca có UI response chỉ được tính đạt khi câu trả lời khớp nguồn độc lập theo cùng bộ lọc, trạng thái chứng từ và đơn vị, hoặc đáp ứng đúng hành vi từ chối/thiếu dữ liệu mong đợi.
- Ghi mỗi ca bằng ID, profile, kỳ lọc, kết quả kỳ vọng, kết quả tool và câu trả lời đã ẩn dữ liệu. So các lượt trước/sau với cùng đầu vào và phạm vi. Tổng hợp số đạt, sai, bị chặn và chưa chạy. Ghi riêng ca thiếu oracle độc lập, thiếu fixture hoặc thiếu môi trường UI. Bộ test cục bộ chỉ xác nhận phạm vi fixture của nó.
