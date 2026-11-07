# Điểm bắt đầu phát triển ERP/MES

Cập nhật: 07/11/2026. Mục đích: chỉ dẫn tới hiện trạng, bằng chứng và hướng phát triển; không thay thế nghiệm thu nghiệp vụ.

## Hiện trạng cần ghi nhớ

- Luồng người dùng cần kiểm tra là model `htmp-nhanh` trên Open WebUI. Các model GPT/API đang được sử dụng và phải giữ độc lập khi phát triển ERP.
- Kiểm thử giao diện ngày 07/11/2026: [báo cáo 12 câu](evidence/ERP-UI-20261107/ket-qua.md). Các công cụ native ít nhất ở đơn bán, tồn và khuôn lỗi import; hai câu MES từng suy diễn sai tháng thành mã. Chốt tạm đã ngăn hai câu đó kết luận dữ liệu rỗng, nhưng chưa tạo được báo cáo theo kỳ. [Kết quả chạy lại](evidence/ERP-UI-20261107/mes-guard-rerun.jsonl).
- Các khẳng định hoàn tất hoặc 100% trong tài liệu lịch sử, gồm `PLAN.md` và `TONG_QUAN_KHAO_SAT_ERP_MES_VA_HUONG_CHATBOT.md`, không phải bằng chứng nghiệm thu hiện tại. Mục 17 và 20 của tài liệu khảo sát nêu kết quả tồn khác nhau; quan hệ UI–API–DB, giờ chốt, quyền và nguyên nhân chênh lệch chưa được xác nhận đầy đủ.
- `config/erp-semantic-pilot.json` có nhãn `approved` nhưng nhãn không chứng minh nghiệp vụ đã duyệt. `erp_ai/semantic_query.py` và `erp_ai/semantic_executor.py` chỉ là nền thử nghiệm có phạm vi thực thi hạn chế, không phải toàn bộ ERP/MES.

## Hướng phát triển

1. Xây dựng một lớp hiểu yêu cầu chung: nghiệp vụ, chỉ tiêu, đối tượng, khoảng thời gian, đơn vị và ngữ cảnh nhiều lượt.
2. Xây dựng hợp đồng dữ liệu theo nhóm nghiệp vụ: nguồn chuẩn, công thức, trạng thái, đơn vị, quyền và bằng chứng đối chiếu với ERP. Backend sở hữu các quy tắc đó; model không tự tạo SQL, phép nối hoặc quyền.
3. Bộ thực thi chỉ đọc, tham số hóa, giới hạn tài nguyên, phân quyền theo danh tính được máy chủ xác thực; phân biệt lỗi, thiếu quyền, không dữ liệu và số 0, kiểm tra tính đầy đủ và đơn vị.
4. Kiểm thử xuyên suốt model → công cụ → dữ liệu → câu trả lời trên UI; đối chiếu ERP/API/DB cùng điều kiện và quyền, cùng bộ câu hỏi độc lập và người phụ trách nghiệp vụ xác nhận.
5. Thực hiện trước một luồng đơn bán và giao hàng; tồn kho chỉ được đưa vào khi thống nhất được công thức và đối chiếu cùng điều kiện. Mở rộng mua hàng, kho, sản xuất, BOM, khuôn và chất lượng trên cùng cơ chế, không tạo handler cho từng câu ví dụ.

## Vị trí cần giữ

- `erp_ai/`, `functions/`, `config/erp-reports/`, `sql/erp-reports/`, `tests/` là các thành phần ERP hoặc nền thử nghiệm; cần kiểm tra phụ thuộc và trạng thái trước khi sửa/xóa.
- `backend-patches/`, `ui-patches/`, cấu hình OpenAI/model và `docker-compose.yml` có thể đang phục vụ GPT hoặc giao diện chung; không thay đổi trong công việc ERP nếu chưa đánh giá ảnh hưởng và kiểm tra đường chạy.
- `docs/evidence/`, `test2/`, các kết quả và script trong `scratch/` có bằng chứng nghiệp vụ, đối chiếu hoặc script vận hành. Tên cũ không đủ căn cứ kết luận rác; bảo toàn đến khi lập được danh mục thay thế và xác minh tham chiếu.
- `backups/`, `local_webui.db`, `exports/`, `.env`, `.secrets/`, `image/` có thể chứa dữ liệu, sao lưu hoặc tài liệu của người dùng; không xóa theo tuổi tệp.
