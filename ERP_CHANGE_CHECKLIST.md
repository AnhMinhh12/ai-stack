# Checklist thay đổi nghiệp vụ ERP

Tag file này vào đầu chat mới khi yêu cầu sửa, bổ sung hoặc triển khai một nghiệp vụ ERP.

## Chỉ dẫn cho Codex

Khi xử lý thay đổi ERP, không chỉ sửa để câu hỏi hiện tại trả lời đúng. Phải rà soát và đồng bộ toàn bộ chuỗi: **định nghĩa nghiệp vụ → nguồn dữ liệu → truy vấn → quyền truy cập → output → kiểm thử → tài liệu → triển khai → đối chiếu UI**.

Không được kết luận hoàn tất nếu thay đổi mới chỉ nằm trong source code hoặc mới chạy đúng ở môi trường local.

## 1. Xác nhận yêu cầu nghiệp vụ

- Ghi lại câu hỏi thực tế của người dùng và các cách diễn đạt tương đương.
- Xác định rõ khái niệm nghiệp vụ, ví dụ:
  - “giao gần nhất” là phiếu xuất bán, lệnh giao hàng hay lịch giao trên đơn hàng;
  - “số lượng” là số lượng từng dòng, tổng trong một chứng từ hay tổng trong ngày;
  - có chỉ lấy chứng từ đã ghi sổ/hoàn thành hay không.
- Xác định phạm vi thời gian: ngày cụ thể, kỳ được chọn trên UI hay toàn bộ dữ liệu được phép xem.
- Xác định cách xử lý khi cùng một mã xuất hiện nhiều dòng trong một chứng từ.
- Không suy luận nguồn dữ liệu chỉ từ tên gọi. Phải đối chiếu màn hình ERP, catalog hoặc mapping đã xác nhận.

## 2. Xác định nguồn và hạt dữ liệu

- Ghi rõ bảng header, bảng detail và khóa nối.
- Xác định hạt kết quả: dòng, chứng từ, ngày, khách hàng, vật tư hoặc lô.
- Kiểm tra các trường ngày có thể dùng: ngày chứng từ, ngày hạch toán, ngày giao thực tế.
- Kiểm tra trạng thái chứng từ và điều kiện loại trừ chứng từ hủy/nháp/chưa ghi sổ.
- Kiểm tra mã giao dịch và các loại nghiệp vụ phải loại trừ.
- Kiểm tra điều kiện phân quyền theo `userinfo.ds_branchs`, kho và ĐVCS.
- Nếu có nhiều dòng cùng mã trong một chứng từ, xác định rõ có dùng `SUM(so_luong)` hay trả từng dòng.

## 3. Cập nhật đủ artifact nghiệp vụ

Rà soát tất cả vị trí sau, không mặc định chỉ cần sửa một file:

- `config/erp-business-intents.json`
  - thêm/sửa intent, từ khóa, nguồn, quyền và trường kết quả;
  - tăng version khi thay đổi hợp đồng nghiệp vụ.
- `functions/htmp_postgres_query.py`
  - thêm/sửa handler và thứ tự định tuyến;
  - bảo đảm intent cụ thể chạy trước các intent rộng dễ bắt nhầm;
  - truy vấn chỉ đọc và có statement timeout.
- `erp_ai/`
  - cập nhật router, entity extraction, contracts hoặc conversation state nếu thay đổi liên quan.
- `config/erp-reports/<report>.json`
  - cập nhật nguồn, filters, aliases, columns, metrics, computed fields và permission scope.
- `sql/erp-reports/<report>.sql`
  - ưu tiên fixed SQL khi nghiệp vụ thuộc một report/màn hình đã quản lý;
  - tham số SQL phải khớp manifest và code gọi;
  - không gọi function ERP động từ đường truy vấn AI nếu contract yêu cầu fixed SQL.
- `tests/erp-reports/<report>.json`
  - ghi case đối chiếu UI cụ thể và expected result;
  - không để toàn bộ case ở dạng placeholder nếu đã có bằng chứng thật.
- `tests/test_erp_report_contract.py` và test liên quan
  - thêm regression test cho câu hỏi gây lỗi;
  - thêm test nguồn, aggregation, permission, routing và fail-closed.
- `config/htmp-rag-models.json` hoặc prompt/profile liên quan
  - cập nhật khi output mới cần quy tắc diễn đạt đặc biệt.
- Tài liệu nghiệp vụ:
  - `docs/erp-screen-mapping.md`;
  - `docs/erp-ui-validation-guide.md`;
  - file evidence/catalog liên quan trong `docs/evidence/`;
  - checklist trạng thái UI nếu dự án đang theo dõi tại `docs/check-ui-erp.md`.

Không hard-code kết quả dữ liệu thật vào logic sản phẩm. Giá trị cụ thể chỉ nên nằm trong test fixture hoặc hồ sơ evidence khi cần tái kiểm chứng.

## 4. Kiểm tra lỗi định tuyến và ngôn ngữ

- Kiểm tra cả tiếng Việt có dấu và không dấu.
- So khớp từ/cụm từ theo ranh giới từ; không dùng substring khiến `gia` khớp nhầm `giao`.
- Kiểm tra mã có dấu gạch ngang, dấu `/`, chữ và số ở nhiều vị trí.
- Mã được nêu trong câu hỏi mới phải ghi đè mã kế thừa từ context.
- Kiểm tra câu hỏi ngắn follow-up vẫn kế thừa đúng điều kiện.
- Kiểm tra intent mới không bị intent cũ bắt trước.

## 5. Kiểm thử trước triển khai

Chạy tối thiểu:

```bash
cd /home/admin/ai-stack
git diff --check
python3 -m py_compile \
  functions/htmp_postgres_query.py \
  scripts/bootstrap_openwebui_rag.py \
  scripts/openwebui_bootstrap_runtime.py
python3 -m unittest discover -s tests -p 'test_erp_report*.py'
```

Ngoài test tự động, phải kiểm tra trực tiếp:

- entity được trích xuất đúng;
- intent mới trả `true`;
- intent sai từng bắt nhầm phải trả `false`;
- SQL dùng đúng bảng, khóa, trạng thái và phép tổng hợp;
- kết quả không vượt phạm vi quyền người dùng.

## 6. Triển khai Open WebUI

`--check` chỉ dùng để xác minh. Muốn cập nhật function/tool phải chạy pha apply trước:

```bash
cd /home/admin/ai-stack

python3 scripts/bootstrap_openwebui_rag.py \
  --owner-email hoanhminhz@gmail.com

python3 scripts/bootstrap_openwebui_rag.py \
  --owner-email hoanhminhz@gmail.com \
  --check
```

Kết quả mong đợi:

```text
bootstrap apply: PASS
bootstrap check: PASS
```

Lưu ý:

- `/app/backend/erp_ai` có thể là bind mount chỉ đọc; bootstrap phải dùng mount hiện tại thay vì cố xóa/copy vào đó.
- Không coi việc copy file cấu hình vào container là đã triển khai xong; nội dung function/tool trong database Open WebUI phải được upsert.
- `--check` phải đối chiếu nội dung function/tool, không chỉ kiểm tra object có tồn tại.
- Nếu bootstrap dừng giữa chừng, trạng thái runtime có thể bị cập nhật một phần. Phải chạy lại apply đầy đủ rồi mới check.

## 7. Đối chiếu với ERP UI

So sánh cùng điều kiện, không chỉ nhìn dòng đầu tiên trên màn hình:

- cùng khoảng ngày;
- cùng mã hàng, khách hàng, kho, ĐVCS và trạng thái;
- cùng số chứng từ nếu đang kiểm tra một bản ghi;
- cùng cách sắp xếp tăng/giảm dần;
- cùng cách tổng hợp nhiều dòng;
- cùng quyền người dùng.

Với câu hỏi “gần nhất”:

- lọc đúng mã hàng trên UI;
- sắp xếp ngày giảm dần hoặc tìm trực tiếp số chứng từ do AI trả;
- xác nhận ngày, số chứng từ, số lượng, ĐVT, khách hàng, kho và trạng thái;
- ảnh dòng đầu của báo cáo sắp xếp tăng dần không phải bằng chứng về bản ghi mới nhất.

Ghi case đã xác nhận vào test fixture và tài liệu evidence. Không chỉ xác nhận trong chat.

## 8. Kiểm tra Git và bàn giao

- Chạy `git status --short` và `git diff --name-only`.
- Phân biệt thay đổi của nhiệm vụ với file người dùng đã sửa từ trước.
- Không commit file tạm, database local, scratch file hoặc thông tin nhạy cảm.
- Kiểm tra mọi artifact liên quan đã được cập nhật; nếu còn thiếu phải nói rõ.
- Chỉ báo “hoàn tất” khi:
  - source và config đã đồng bộ;
  - test đạt;
  - bootstrap apply đạt;
  - bootstrap check đạt;
  - UI đã đối chiếu;
  - evidence/docs đã cập nhật;
  - thay đổi cần lưu đã được commit/push theo yêu cầu.

## 9. Mẫu báo cáo hoàn tất

```text
Nghiệp vụ: <tên nghiệp vụ>
Nguồn: <header/detail và khóa nối>
Phạm vi: <thời gian, trạng thái, quyền>
Aggregation: <hạt dữ liệu và cách cộng>
Files đã cập nhật: <danh sách>
Tests: <số lượng/kết quả>
Bootstrap apply: PASS/FAIL
Bootstrap check: PASS/FAIL
UI comparison: PASS/FAIL — <case cụ thể>
Git status: <đã commit/chưa commit và file còn lại>
Việc còn thiếu: <không có hoặc danh sách>
```


