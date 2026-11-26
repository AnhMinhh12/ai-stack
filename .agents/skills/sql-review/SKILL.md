---
name: sql-review
description: "Rà SQL hoặc procedure ERP/MES do chatbot HTMP sinh hay thực thi, tập trung vào nguồn dữ liệu, JOIN, bộ lọc, quyền và tính đầy đủ của kết quả."
---

# Rà SQL và quyền dữ liệu ERP/MES

Mọi đường dẫn tính từ gốc repo. Bắt đầu bằng rà tĩnh và test cục bộ. Áp dụng giới hạn truy cập trong `AGENTS.md`.

1. Xác định profile và đường thực thi. Với legacy, lần qua `functions/htmp_postgres_query.py`, manifest trong `config/erp-reports/`, mẫu SQL trong `sql/erp-reports/` và `erp_ai/generic_procedure_executor.py` nếu nhánh gọi procedure. Với staging, xem `erp_ai/agent_backend.py` và adapter `erp_ai/agent_runtime.py`. Với semantic pilot, xem `config/erp-semantic-pilot.json`, `erp_ai/semantic_query.py` và `erp_ai/semantic_executor.py`. Phân biệt đối tượng được khai báo, đối tượng đã kiểm chứng và pilot.
2. Đối chiếu bảng, cột, khóa ghép, grain và cardinality với hợp đồng báo cáo hoặc bằng chứng ERP đã kiểm chứng. Kiểm tra bản ghi nhân lên hoặc biến mất qua JOIN, điều kiện trên bảng tùy chọn, ngày nghiệp vụ và biên kỳ, trạng thái chứng từ, đơn vị và tiền tệ. Ghi rõ chỗ thiếu bằng chứng thay vì suy từ tên cột.
3. Kiểm tra định danh từ allowlist và tham số giá trị đã bind. Truy nguồn danh tính ERP từ ngữ cảnh server và kiểm tra phạm vi báo cáo, chi nhánh, kho theo hợp đồng. Xác nhận cách xử lý mapping thiếu, phạm vi rỗng và quyền mở rộng. Rà quyền DB và điểm đặt transaction read-only, statement timeout và giới hạn dòng trong đúng adapter. Với procedure, kiểm tra quyền thực thi và side effect; rollback hoặc tên procedure chỉ cung cấp một phần bằng chứng.
4. Kiểm tra thứ tự/paging, `has_more` hoặc tín hiệu cắt dữ liệu, và tổng tính trên tập đủ thay vì số dòng đã giới hạn. Phân biệt số 0, NULL, tập rỗng, lỗi và thiếu quyền. Dùng các test trong `tests/test_erp_agent.py` và `tests/test_erp_semantic_query.py` theo nhánh, xem checklist tại `docs/ERP_CHANGE_CHECKLIST.md`.
5. Báo phát hiện kèm file/vị trí, điều kiện kích hoạt, tác động và kết quả test. Nếu chưa có bằng chứng về JOIN, công thức, quyền hoặc kết quả ERP cho cùng bộ lọc, giữ trạng thái chưa xác minh.
