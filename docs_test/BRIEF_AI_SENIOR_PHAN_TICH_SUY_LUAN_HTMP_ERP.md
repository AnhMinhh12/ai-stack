# Brief độc lập cho AI senior: nâng chất lượng suy luận của HTMP ERP

**Ngày lập:** 22/10/2026 (UTC)  
**Mục đích:** Giao cho một AI senior không có sẵn ngữ cảnh dự án phân tích kiến trúc, chẩn đoán nguyên nhân và đề xuất giải pháp có thể kiểm chứng.  
**Phạm vi ban đầu:** Phân tích và thiết kế; chưa sửa code hoặc cấu hình production.

## 1. Vai trò và nhiệm vụ của bạn

Bạn là senior AI engineer kiêm kiến trúc sư ứng dụng dữ liệu doanh nghiệp. Hãy đánh giá hệ thống **HTMP ERP**, một ứng dụng chat tiếng Việt trên Open WebUI, truy vấn PostgreSQL ERP và tài liệu nội bộ. Người dùng nhận thấy hệ thống thường trả lời ngay sau một lượt tool, thiếu khả năng lập kế hoạch, truy vấn bổ sung, kiểm tra số liệu và xử lý câu hỏi nối tiếp. Mục tiêu là tìm nguyên nhân thực sự và đưa ra phương án cải tiến khả thi cho dự án hiện có.

**Đừng mặc định lỗi nằm ở model.** Phải phân biệt rõ:

1. Năng lực và cấu hình model local.
2. Prompt, giới hạn số bước và cách điều phối tool.
3. Chọn sai intent hoặc bảng ERP, thiếu tham số, SQL sai/ngữ nghĩa sai.
4. Dữ liệu không có, không được phép xem, kết quả bằng 0, lỗi kỹ thuật, kết quả bị cắt và report chưa đối chiếu UI.
5. LLM diễn giải sai dù tool đã trả dữ liệu đúng.
6. UI hiển thị làm người dùng không thấy bằng chứng hoặc trạng thái các bước.

Nếu được cung cấp repository, hãy đọc mã thật và ghi đường dẫn/dòng cho mọi kết luận quan trọng. Nếu chỉ có file này, hãy dùng nó làm bối cảnh ban đầu, nêu rõ điều gì phải xác minh tiếp; đừng giả vờ đã đọc mã hoặc dữ liệu không được cung cấp.

## 2. Kỳ vọng sản phẩm

Một trợ lý ERP tốt cần:

- Hiểu yêu cầu, xác định thực thể, kỳ, kho, quyền, định nghĩa nghiệp vụ và độ mơ hồ.
- Chọn đúng **báo cáo/nguồn có nghĩa nghiệp vụ phù hợp**, không dùng một cột trùng tên làm bằng chứng cho khái niệm khác.
- Gọi thêm tool khi kết quả thiếu trường bắt buộc hoặc có mâu thuẫn; dừng có giới hạn và hỏi làm rõ khi không thể suy ra an toàn.
- Phân biệt **không tìm thấy dòng**, **giá trị SQL NULL**, **số 0**, **không có quyền**, **query lỗi**, **kết quả bị cắt**, **dữ liệu chưa đối chiếu UI**.
- Trả lời có mã hàng, đại lượng, đơn vị, ngày tham chiếu, phạm vi kho/đơn vị và nguồn khi có thể. Không biến ước đoán thành số liệu xác nhận.
- Xử lý câu hỏi nối tiếp mà không kế thừa nhầm mã hoặc khoảng ngày của câu trước.
- Giữ thời gian phản hồi chấp nhận được, giới hạn số tool/query/token và bảo toàn quyền truy cập dữ liệu.

Người dùng nói “không suy luận” để mô tả **chất lượng quyết định và kiểm chứng**, không yêu cầu hiển thị chuỗi suy nghĩ riêng tư của model. Hãy đề xuất các bước làm việc quan sát được (ví dụ “đã tra tồn kho sổ sách đến ngày X”) và kết quả có thể kiểm tra, thay vì đòi in chain-of-thought.

## 3. Hệ thống hiện tại: hai luồng ERP khác nhau

### 3.1. Luồng HTMP ERP đang dùng rộng rãi (`htmp-nhanh`)

Open WebUI phục vụ chat; model `htmp-nhanh` có tên hiển thị “HTMP ERP”, dựa trên `qwen2.5-14b`, temperature 0, `max_tokens` khoảng 800, native function calling, gắn filter `htmp_fast_rag` và tool `htmp_postgres_query`. Cấu hình nguồn nằm trong `config/htmp-rag-models.json`. Runtime thực tế cần đối chiếu với DB của Open WebUI vì profile/tool/filter được đăng ký và lưu trong DB, không tự đồng bộ theo file repo.

Filter ở `functions/htmp_fast_rag.py` hiện ép quy trình: **mỗi lượt người dùng gọi đúng một lần `ask_erp` trước; sau kết quả thì trả lời ngay, không gọi lần hai trong cùng lượt**. Nó còn cố gắng kế thừa mã/điều kiện từ lịch sử cho follow-up và hướng dẫn model sao chép kết quả đã xác nhận. Đây là một quyết định sản phẩm có thể trực tiếp hạn chế khả năng thu thập thêm bằng chứng trong câu hỏi nhiều bước. Cần đánh giá lợi ích latency/ổn định của ràng buộc này trước khi nới.

Tool `functions/htmp_postgres_query.py` có các tầng: nhận câu hỏi tự nhiên → phát hiện một số report/intent cố định → trích thực thể và trạng thái hội thoại → router `erp_ai/router.py` → handler SQL xác định → fallback lập kế hoạch SQL từ catalog/schema khi không khớp. `erp_ai/entities.py` và `erp_ai/context.py` tham gia kế thừa mã/ngày. Một số handler dùng `userinfo` và scope quyền; một số master-data/planner không nhận identity. Cần rà toàn bộ đường đi, không suy từ một handler ra cả hệ thống.

Khi hỏi số liệu, prompt/filter yêu cầu tin tool. Nhưng prompt không bảo đảm model chọn đúng tool hoặc nhận biết rằng dữ liệu tool thiếu số lượng. Tool trả JSON hoặc Rich UI tùy bản code; model có thể diễn giải sai dữ liệu, bỏ qua `summary`, bỏ qua `has_more`, hoặc tạo kết luận không có trong kết quả.

### 3.2. Luồng agent nhiều lượt riêng (`htmp-erp-agent-staging`)

Repository còn có **một phương án staging**, không nên đánh đồng với `htmp-nhanh`:

- `erp_ai/agent.py`: vòng model → tool → xác minh → model, có giới hạn lượt/tool/DB/thời gian/context, chống lặp và giữ `verified_results`.
- `erp_ai/agent_backend.py`: công cụ có allowlist như `search_schema`, `search_knowledge`, `query_inventory_balance`, `query_receipt_lines`, `query_allowed_records` và các report khác. Model không được gửi SQL tự do, đường dẫn hoặc user ID trực tiếp cho backend này.
- `erp_ai/agent_runtime.py`: transport async, tài khoản PostgreSQL staging chỉ đọc (SELECT-only) theo tài liệu vận hành, deadline và timeout.
- `functions/htmp_erp_agent.py` và `functions/htmp_erp_agent_filter.py`: adapter/tool/filter Open WebUI, lấy identity và lịch sử do server inject, có thể trả Rich UI.
- `config/htmp-erp-agent-profile.json`, `config/erp-agent.json`: profile, nguồn và giới hạn; cấu hình Compose để `HTMP_AGENT_ENABLED` mặc định `0`, DSN/grants staging riêng. Cần **kiểm tra runtime** để biết profile nào đã đăng ký/đang bật; sự tồn tại của code không chứng minh đang phục vụ người dùng.

Tài liệu `docs/erp-agent-audit-20261020.md` và `docs/erp-agent-operations.md` mô tả thử nghiệm synthetic, fixture PostgreSQL và nhiều điều kiện chưa nghiệm thu: E2E staging ERP/UI, quyền, browser, tải đồng thời và so sánh baseline cùng bộ dữ liệu. Một số dòng tài liệu là ảnh chụp trạng thái tại ngày viết, có thể đã thay đổi; luôn đối chiếu runtime.

**Câu hỏi kiến trúc quan trọng:** Có nên cải tiến dần `htmp-nhanh`, dùng agent staging theo từng nhóm report đã nghiệm thu, hay kết hợp router xác định cho câu đơn giản với agent nhiều bước có kiểm soát cho câu phức tạp? Đưa tiêu chí quyết định dựa trên độ đúng, quyền, latency, vận hành và chi phí, không chỉ dựa trên cảm giác hội thoại “thông minh”.

## 4. Sự cố thực tế dùng làm ca điều tra

Người dùng đã hỏi trong cùng một cuộc chat:

> “Mã hàng 1003947-1 tồn kho bao nhiêu trên hệ thống”  
> Kết quả cũ: không có số lượng tồn kho ghi nhận.

> “Mã hàng BGTD0193 tồn kho bao nhiêu trên hệ thống”  
> Kết quả cũ: có trong kho, đơn vị là PCS.

> “Mã hàng BGTD0193 còn bao nhiêu trong kho?”  
> Kết quả cũ: không có số lượng cụ thể được ghi nhận.

Chẩn đoán bằng mã nguồn và chạy truy vấn đọc vào 22/10/2026:

- `erp_ai/router.py` trước bản sửa đã cho câu có mã hàng nhưng không có ngày rơi vào `material_master` **trước khi kiểm tra ý định tồn kho**. `material_master` đọc `public.dmvt`; có thể trả `dvt=PCS` nhưng **không có số lượng tồn**.
- Mã `1003947-1` có phần số và dấu gạch ngang từng bị hai bộ nhận diện thực thể trong tool và `erp_ai/entities.py` bỏ sót; filter follow-up cũng không nhận diện đầy đủ. Tool có thể rơi xuống SQL planner và chọn đại lượng không đúng hoặc trả NULL.
- Bản sửa ngày 22/10/2026 thêm intent `inventory_balance`, trích mã đủ, dùng SQL tồn đầu kỳ `cdvt.ton00` cộng phát sinh `ct70.sl_nhap - ct70.sl_xuat` đến ngày tham chiếu, trong phạm vi quyền ERP đang dùng. Truy vấn trực tiếp trả **BGTD0193 = 0 PCS** và **1003947-1 = 560 PCS** tính đến **2026-10-22**. Đây là kết quả sổ sách tại thời điểm kiểm tra; không phải khẳng định tồn tem thực tế, tồn khả dụng, tồn theo từng kho, hoặc số liệu hiện tại ở ngày đọc file này.
- Report tồn kho liên quan vẫn có nhãn `pending_ui_validation` trong config. SQL thực thi thành công không thay thế việc đối chiếu màn hình ERP theo cùng ngày, quyền và phạm vi kho.
- Tool/filter đăng ký trong DB Open WebUI đã được cập nhật có chọn lọc để sửa sự cố, giữ các phần khác của code đang chạy. Bản trong DB có thể khác file repo ở các thay đổi chưa phát hành; kiểm tra drift trước khi đề xuất deploy.

Đây là ví dụ về **sai tuyến truy vấn + sai nhận diện mã + thiếu kiểm tra tính đầy đủ của kết quả**, không tự nó chứng minh Qwen2.5-14B không có khả năng suy luận. AI senior cần tìm thêm các loại lỗi tương tự trên những nghiệp vụ khác.

## 5. Dữ liệu ERP và những khó khăn nghiệp vụ

Các nguồn chính gồm manifest `config/erp-reports/*.json`, SQL `sql/erp-reports/*.sql`, mapping màn hình `docs/erp-screen-mapping.md`, tri thức `docs/knowledge/*.md`, catalog `danh-sach-bang-tra-cuu.md`. Chúng có mức tin cậy khác nhau. Tên bảng/cột hoặc mô tả trong tài liệu **không chứng minh** một con số khớp báo cáo UI.

- **Kho:** tồn sổ sách (`cdvt` + `ct70`), tồn theo vị trí/kho, tồn tem/khuôn (`intem_log`) và tồn khả dụng có thể khác nhau. Câu “còn bao nhiêu trong kho” cần quy định mặc định rõ và có thể phải hỏi thêm kho/ngày/loại tồn nếu không an toàn để đoán.
- **Bán hàng/giao hàng:** `ph64/ct64` (đơn), `ph96/ct96/ctkhgh` (lệnh giao), `ph81/ct81` (xuất bán) khác hạt dữ liệu và ý nghĩa. Không được gọi một lệnh giao là phiếu xuất bán hoặc cộng dòng chi tiết làm doanh thu khi chưa có định nghĩa nghiệp vụ.
- **Mua hàng/giá:** PO lịch sử khác báo giá nhà cung cấp, giá trước VAT khác sau VAT, hiệu lực bảng giá/MOQ và trạng thái duyệt phải được giữ đúng.
- **Sản xuất/khuôn/QC:** shot, tem OQC, trạng thái NG và kế hoạch PO/FCST có nguồn riêng; không được suy từ một bảng tồn kho chung.
- Header/detail thường nối bằng `stt_rec`; `so_ct` là số hiển thị, cần `ln` để định danh dòng. Cộng trùng khi join sai là rủi ro lớn.
- Tổng toàn kỳ phải lấy từ `summary`/aggregate của SQL; không cộng trang đầu khi `has_more=true`.
- Kết quả trống có nhiều nghĩa: không có record, số dư bằng 0, không thuộc kho được xem, user chưa được map, ngày ngoài kỳ, report lỗi, SQL timeout hoặc nguồn chưa được đối soát. Mỗi trạng thái cần output khác nhau.
- Nhiều report có `validation: pending_ui_validation`. Yêu cầu AI phân loại độ tin cậy theo report và đề xuất kế hoạch so sánh cùng bộ lọc/quyền trên UI ERP.

## 6. Quyền, an toàn và vận hành

ERP là dữ liệu nội bộ. `HTMP_ERP_USER_ID_MAP` ánh xạ Open WebUI identity sang user ERP; hiện có thể có `HTMP_ERP_SHARED_USER_ID` làm fallback ở luồng cũ. Một số SQL dùng `userinfo.ds_branchs`, `ds_stocks`, `is_super`, kho/ĐVCS; cách áp dụng chưa đồng nhất ở mọi handler. Agent staging có grants riêng và chủ đích không fallback shared user. Cần xác minh ý nghĩa thực tế của branch/warehouse scope với quản trị ERP trước khi mở rộng tool.

Không đề xuất cho model sinh SQL tùy ý rồi chạy trên production như giải pháp mặc định. Nếu cần planner SQL, phải có allowlist bảng/cột/report, tham số hóa, validation AST/statement, READ ONLY, timeout, row limit, scope quyền và kiểm thử truy cập chéo. Prompt đơn thuần không là cơ chế phân quyền.

Stack dùng Docker Compose, Open WebUI, vLLM/Qwen, Redis, Qdrant, Tika, Nginx và PostgreSQL ERP bên ngoài. Model local trong Compose được cấu hình context khoảng 32K và native tool calling; cấu hình này không phải bằng chứng hiệu năng thực tế. Tool cũ dùng nhiều I/O đồng bộ và planner có thể tốn thời gian/retry; agent staging có budget nhưng chưa có SLO tải thật. Cần đo p50/p95, lỗi, timeout và tải đồng thời trên cùng hardware trước khi tăng số bước.

Code tool/filter của Open WebUI được lưu trong DB ứng dụng; source repository có thể khác runtime. `docker-compose.yml` còn có các bind mount/hotfix backend/UI và release image theo digest. Đề xuất triển khai phải bao gồm cách phát hiện drift, rollback và kiểm tra version thực chạy, không chỉ sửa file Python trong repo.

Không đưa secret, DSN, bản ghi nhạy cảm, prompt người dùng hay auth header vào log/báo cáo. Khi làm evaluation, ưu tiên fixture giả có cấu trúc tương đương và staging SELECT-only. Nếu dùng dữ liệu thật, giữ nguyên quyền người dùng và chỉ xuất số liệu tối thiểu phục vụ đối soát.

## 7. Vấn đề cần phân tích sâu

### 7.1. Nhận diện ý định và thực thể

Kiểm tra mã thuần số, chữ+số, dấu `-`/`/`, revision `/V1`, mã chứng từ giống mã hàng, câu nhiều mã, tên vật tư gần giống, câu không dấu và câu follow-up “mã này”, “còn bao nhiêu”, “vậy tuần trước?”. Xác định nơi trích mã trùng lặp giữa filter, tool và package `erp_ai`; đề xuất một hợp đồng chung có test và phân biệt nguồn/độ chắc chắn.

### 7.2. Lập kế hoạch và dùng tool

Rà luật “đúng một `ask_erp` rồi trả lời”, giới hạn `max_tokens=800`, prompt dài và thứ tự giữa router xác định với fallback SQL planner. Thiết kế một controller cho phép các trạng thái: cần làm rõ → tra cứu → kiểm tra tính đầy đủ/đúng nguồn → tra bổ sung/đối chiếu khi cần → tổng hợp câu trả lời. Nêu rõ khi nào được trả ngay để giữ latency tốt; khi nào phải dùng thêm lượt; khi nào dừng vì budget hoặc quyền.

### 7.3. Hợp đồng kết quả và kiểm chứng

Đề xuất schema output có `status`, `intent`, `filters_resolved`, `metric`, `value`, `unit`, `date_as_of`, `scope`, `source`, `validation_state`, `total_rows`, `returned_rows`, `has_more`, `error_code`. Tách “verified value” khỏi văn bản model tự viết. Xem xét render câu trả lời và bảng trực tiếp từ dữ liệu đã xác minh cho các chỉ số số học, để model chỉ diễn giải phần được phép.

### 7.4. Hội thoại và quyền

`erp_ai/context.py` dùng state trong bộ nhớ theo conversation ID và có thể nhận ID từ caller trong luồng cũ; cần kiểm tra namespace theo user, nhiều replica, TTL, xóa phiên, việc model rút gọn/sai mã và rò điều kiện từ chat khác. So sánh với agent staging dùng lịch sử/identity server-injected, không nhận conversation ID tự do. Đề xuất migration an toàn.

### 7.5. Đánh giá model và trải nghiệm người dùng

Thiết kế benchmark **cùng dữ liệu, cùng quyền, cùng câu hỏi** cho baseline hiện tại, router/hợp đồng mới, agent nhiều lượt và nếu cần một model khác. Đo tool choice, answer accuracy, source faithfulness, tỷ lệ hỏi làm rõ đúng, false certainty, latency/cost. Không dựa vào một vài câu chat hoặc điểm benchmark tổng quát để chọn model. UI cần cho người dùng thấy nguồn, ngày/phạm vi và trạng thái “đang kiểm tra/thiếu dữ liệu” mà không hiển thị chain-of-thought.

## 8. Bộ ca kiểm thử bắt buộc đề xuất

Hãy mở rộng thành bộ eval có expected tool/report, bộ lọc và đáp án nguồn xác minh, ít nhất gồm:

1. `BGTD0193 tồn kho bao nhiêu?` — phân biệt 0 với thiếu dữ liệu.
2. `1003947-1 tồn kho bao nhiêu?` — mã số có dấu gạch ngang.
3. `BGTD0193 còn bao nhiêu trong kho?` sau một câu về mã khác — mã mới phải thắng ngữ cảnh cũ.
4. `Mã này còn bao nhiêu?` sau một câu có mã duy nhất; và sau câu có hai mã (phải làm rõ).
5. Cùng mã hỏi tồn sổ sách, tồn theo khuôn/tem, tồn theo kho và tồn khả dụng — không trộn khái niệm.
6. Hỏi ngày cụ thể, không ghi ngày, ngày không hợp lệ và ngày ở năm trước.
7. Hai kho khác quyền; user không map, user hạn chế, superuser và shared fallback.
8. Mã không tồn tại trong master; mã có master nhưng không có dòng cân đối; tồn đúng 0; trường quantity NULL; DB lỗi/timeout.
9. Một câu yêu cầu nhiều mã và nhiều metric; tránh mất một vế hoặc dùng sai đơn vị.
10. Kết quả hơn row limit; `has_more=true`; tổng toàn kỳ khác tổng trang đầu.
11. Giá PO lịch sử so với báo giá NCC trước/sau VAT và trạng thái duyệt.
12. Đơn hàng, lệnh giao, xuất bán cùng mã/kỳ nhưng số lượng khác nhau; chọn đúng nghĩa câu hỏi.
13. Câu follow-up đổi ngày/kho nhưng giữ mã; câu đổi mã nhưng không giữ bộ lọc không liên quan.
14. Mã chứng từ `so_ct` gần giống mã vật tư; revision `/V1`.
15. Tool trả dữ liệu mâu thuẫn với tài liệu mô tả hoặc report chưa đối chiếu UI.
16. Prompt injection nằm trong tên vật tư/tài liệu/kết quả tool yêu cầu bỏ qua quyền hoặc ghi DB.
17. Người dùng hủy request giữa truy vấn; tool trả muộn; retry; hai câu đồng thời trong một chat.
18. Model nhận kết quả có `dvt=PCS` nhưng không có quantity — tuyệt đối không khẳng định có hàng hoặc số lượng bằng 0.

Với mỗi ca, ghi **nguồn expected answer** (fixture, query đã review hoặc ảnh chụp UI ERP cùng quyền/ngày); không tự lấy đáp án từ chính model đang được đánh giá.

## 9. Đầu ra bắt buộc của phân tích

Trả bằng tiếng Việt, có cấu trúc rõ:

1. **Bản đồ runtime thực tế:** UI → model/profile → filter → tool → router/agent → DB/knowledge → validator → renderer, kèm vị trí file và khác biệt DB/runtime nếu được phép kiểm tra.
2. **Bảng nguyên nhân:** hiện tượng, bằng chứng, nguyên nhân gốc, mức chắc chắn, ảnh hưởng và cách tái hiện. Phân loại lỗi do model, điều phối, tool, SQL/nghiệp vụ, quyền, dữ liệu và UI.
3. **Ba phương án kiến trúc** khả thi (cải tiến luồng cũ; agent staging theo report; hybrid), có sơ đồ, ưu/nhược, độ khó, latency, rủi ro dữ liệu/quyền, khả năng rollback. Đề xuất một phương án và nói rõ lý do.
4. **Thiết kế chi tiết:** state machine cho một lượt hỏi, điều kiện gọi thêm tool, stopping/budget, xác minh dữ liệu, output schema, xử lý follow-up, scope quyền và lỗi.
5. **Kế hoạch theo giai đoạn:** quick wins, pilot trên staging, so sánh A/B với baseline, nghiệm thu UI ERP, phát hành và giám sát. Mỗi giai đoạn có tiêu chí PASS/FAIL định lượng; ghi người cần xác nhận định nghĩa nghiệp vụ.
6. **Bộ eval** tối thiểu 18 ca ở trên, metric, dữ liệu fixture/holdout và cách chạy lại sau thay đổi prompt/router/model.
7. **Danh sách câu hỏi còn thiếu bằng chứng**, sắp theo mức độ chặn triển khai. Nêu rõ giả thuyết và cách kiểm chứng, không biến giả thuyết thành kết luận.

**Yêu cầu về chất lượng:** Không chỉ viết lại prompt để model “suy luận kỹ hơn”. Ưu tiên sửa hợp đồng dữ liệu, định tuyến, quyền và kiểm chứng đầu ra khi đó là nguyên nhân. Không đề xuất đào tạo hoặc thay model nếu chưa có eval so sánh. Mọi phép tính và kết luận số học phải dựa trên dữ liệu đã truy vấn đúng nguồn.

## 10. Các file nên đọc nếu có quyền truy cập repository

| Nhóm | File/đường dẫn |
| --- | --- |
| Kiến trúc/vận hành | `README.md`, `RUNBOOK.md`, `docker-compose.yml`, `docs/erp-agent-audit-20261020.md`, `docs/erp-agent-operations.md` |
| Profile/prompt | `config/htmp-rag-models.json`, `config/htmp-erp-agent-profile.json`, `functions/htmp_fast_rag.py`, `functions/htmp_erp_agent_filter.py` |
| Tool/agent | `functions/htmp_postgres_query.py`, `functions/htmp_erp_agent.py`, `erp_ai/agent.py`, `erp_ai/agent_backend.py`, `erp_ai/agent_runtime.py`, `erp_ai/context.py`, `erp_ai/entities.py`, `erp_ai/router.py`, `erp_ai/contracts.py`, `erp_ai/validator.py`, `erp_ai/presentation.py`, `erp_ai/rich_ui.py` |
| Nguồn ERP | `config/erp-agent.json`, `config/erp-reports/`, `sql/erp-reports/`, `docs/erp-screen-mapping.md`, `docs/knowledge/`, `danh-sach-bang-tra-cuu.md` |
| Kiểm thử/bằng chứng | `tests/test_erp_report_contract.py`, `tests/test_erp_agent.py`, `tests/erp_agent_postgres_fixture.py`, `docs/evidence/ERP-AGENT-20261020/` |
| Triển khai | `scripts/bootstrap_openwebui_rag.py`, `scripts/openwebui_bootstrap_runtime.py`, `scripts/deploy_erp_export_tools.py` |

Khi nhận repository, trước hết ghi snapshot Git diff và runtime version, vì workspace có thể có nhiều thay đổi chưa commit. Không ghi đè hoặc dọn các thay đổi đó khi chưa xác định chủ sở hữu. Nếu không có repository, hãy yêu cầu tối thiểu các file thuộc ba nhóm profile/prompt, tool/agent và nguồn ERP, rồi vẫn đưa phương án sơ bộ dựa trên brief này.

## 11. Giới hạn thao tác trong vòng phân tích

- Đọc code, kiểm tra cấu hình và chạy test chỉ đọc/fixture giả khi được cấp quyền.
- Không sửa production DB, profile/tool Open WebUI đang dùng, image, Compose hoặc secret.
- Không chạy SQL ghi dữ liệu; không thử vượt quyền thật.
- Không công bố danh sách người dùng, credentials, DSN, nội dung chat hoặc bản ghi ERP nhạy cảm trong báo cáo.
- Trước mọi đề xuất triển khai, đưa bản diff/thiết kế có thể review, kế hoạch rollback và kiểm thử quyền với tài khoản hạn chế.

**Bắt đầu bằng cách nêu 5 giả thuyết có thể kiểm chứng về lý do “trả lời luôn mà không suy luận”, sau đó đọc bằng chứng và cập nhật/xóa từng giả thuyết.**
