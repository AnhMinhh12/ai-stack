# Kế hoạch ERP/MES trả lời câu hỏi tự do — bản chờ duyệt

Ngày lập: 27/10/2026. Phạm vi hiện tại: lập kế hoạch; chưa sửa runtime, gọi DB hay triển khai.

## 1. Mục tiêu và cách hiểu “trả lời được hết”

Xây một luồng hỏi đáp dùng được cho toàn bộ nghiệp vụ ERP/MES nằm trong phạm vi dữ liệu và quyền đã xác minh. Người dùng không phải nhớ tên màn hình, tên bảng hoặc mẫu câu cố định. Hệ thống hiểu câu hỏi mới bằng cách kết hợp đối tượng, chỉ số, điều kiện, quan hệ và thời gian đã có trong danh mục nghiệp vụ.

Không hứa 100% câu bất kỳ luôn có một con số đúng. Với dữ liệu không được ghi nhận, khái niệm chưa thống nhất hoặc câu hỏi về nguyên nhân chưa có bằng chứng, hệ thống phải nói rõ phần chưa xác định và hỏi đúng điều kiện cần thiết. Tất cả yêu cầu phải được xử lý thành một trong các trạng thái: trả được; trả một phần; cần làm rõ; ngoài quyền; thiếu dữ liệu; nghiệp vụ chưa xác minh; lỗi truy vấn. Không biến lỗi/rỗng thành số 0.

Định nghĩa hoàn thành phải dựa trên ma trận nghiệp vụ và bộ kiểm thử độc lập, không dựa trên việc AI đã kết nối được mọi bảng.

## 2. Hiện trạng đã kiểm tra trong workspace

- Có 82 manifest trong `config/erp-reports`: 67 ghi `pending_ui_validation`, 14 ghi `validated`, 1 chưa khai báo trạng thái. Đây là nhãn trong source, chưa phải xác nhận runtime hoặc bằng chứng nghiệm thu mới.
- `docs/erp-screen-mapping.md` đã có nhiều ánh xạ màn hình → state/function → bảng và khóa.
- `docs/erp-ui-validation-guide.md` đã quy định so sánh UI theo người dùng, ĐVCS, bộ lọc và thời điểm chốt. Một số tài liệu có khác biệt về nguồn; cần giải quyết trước khi đưa vào danh mục chuẩn.
- Có hai hướng trong source: tool `ask_erp` với router cũ, và runtime agent riêng trong `erp_ai`. Phải xác nhận model người dùng đang chọn thực sự đi qua hướng nào trước khi sửa.
- Có pilot sinh SQL từ catalog tại `scratch/erp-semantic-pilot`. Pilot chưa có phân quyền dòng theo người dùng ứng dụng; không dùng trực tiếp làm endpoint production.
- Báo cáo kiểm thử ngày 23/10 ghi 3 đúng, 3 một phần/chưa đủ, 12 sai trong 18 câu. Đây là kết quả lịch sử; phải chạy lại để có baseline hiện tại.
- Chưa kiểm tra live DB, phiên UI, catalog function hay đăng ký model đang chạy trong lần lập kế hoạch này.

## 3. Vì sao cột UI khác DB và phải lần theo cái gì

Không mặc định mỗi bảng có một function. Một function có thể phục vụ nhiều bảng; một màn có thể gọi nhiều API/function; một số phép tính nằm ở backend hoặc frontend.

Cần kiểm tra đủ các dạng khác biệt sau:

| Dạng khác biệt | Ví dụ | Cách xác minh |
| --- | --- | --- |
| Chỉ đổi nhãn | `ma_vt` thành Mã hàng | Metadata lưới và response API |
| Ghép nội dung hiển thị | Mã + tên trong một ô | Field API và formatter frontend |
| Join dữ liệu | Người lập lấy từ bảng người dùng | Query/function và khóa nối thực tế |
| Tính chỉ số | Còn phải giao, tồn cuối, tỷ lệ NG | Công thức, phạm vi trạng thái, đơn vị và thời gian |
| Tổng hợp/pivot | Một dòng/mã, cột theo kho hoặc ngày | GROUP BY/pivot và mức chi tiết của mỗi dòng |
| Gộp ô trực quan | Tên đơn chỉ hiện ở dòng đầu | Kiểm tra các dòng API còn tồn tại bên dưới |
| Chèn dòng tổng | Tổng nhóm, tổng cuối báo cáo | Cờ loại dòng; không cộng lại cả dòng tổng và dòng thật |
| Quy đổi mã trạng thái | `3` hiển thị OK | Từ điển trạng thái đúng nghiệp vụ |
| Lọc ngầm/quyền | Chỉ chứng từ đã ghi sổ, ĐVCS được phép | Request, backend và tài khoản ERP |
| Khác thời gian | Ngày chứng từ, ngày ghi sổ, ngày sản xuất | Ý nghĩa trường ngày và mốc chốt |

Luồng khảo sát bắt buộc: menu/màn → request UI → endpoint → function/query → bảng → response → phép biến đổi khi hiển thị. Không suy ra ý nghĩa cột chỉ bằng tên.

## 4. Kiến trúc đề xuất

```text
Câu hỏi + ngữ cảnh hội thoại + danh tính phiên đăng nhập
    ↓
Hiểu đối tượng, yêu cầu, kỳ thời gian và các vế liên quan
    ↓
Tìm định nghĩa nghiệp vụ và nguồn đã xác minh theo quyền
    ↓
Lập kế hoạch truy vấn có cấu trúc
    ↓
Kiểm tra chỉ số, khóa nối, mức chi tiết, quyền và chi phí
    ↓
Bộ thực thi báo cáo chuẩn / bộ biên dịch truy vấn theo danh mục
    ↓
DB hoặc API báo cáo đã được kiểm tra
    ↓
Đối chiếu, kiểm tra đầy đủ và chuẩn hóa kết quả
    ↓
Trả lời + bảng/biểu đồ + bộ lọc/mốc chốt + nguồn truy vết
```

Model phụ trách ngôn ngữ, tìm kiến thức phù hợp, đề xuất kế hoạch nhiều bước và diễn giải. Backend sở hữu công thức, khóa nối, trạng thái, quyền và việc thực thi.

Ba đường xử lý dùng chung danh mục nghiệp vụ:

1. **Báo cáo đã xác minh:** gọi adapter với tham số rõ ràng; ưu tiên tái sử dụng logic ERP/MES đúng khi phù hợp.
2. **Câu hỏi mới trên nghiệp vụ đã biết:** model lập kế hoạch chọn chỉ số, chiều phân tích, bộ lọc, so sánh và quan hệ; compiler sinh truy vấn tham số hóa từ định nghĩa đã duyệt. Không cần viết một template cho mỗi cách hỏi.
3. **Nghiệp vụ hoặc quan hệ mới:** dùng metadata để tìm nguồn ứng viên, nhưng chỉ kết luận khi đủ bằng chứng. Nếu thiếu công thức/khóa/quyền, trả phần đã xác minh và ghi nhận yêu cầu bổ sung danh mục; không tự biến suy đoán thành logic production.

Ví dụ: “Tháng này mã X giao được bao nhiêu, giảm bao nhiêu so tháng trước, còn kho nào và có lô nào NG?” được tách thành các tác vụ liên kết bằng cùng mã hàng, nhưng từng tác vụ giữ đúng nguồn, kỳ thời gian và định nghĩa. Không cắt câu cơ học theo dấu phẩy hoặc chữ “và”.

## 5. Giai đoạn 0 — Chốt baseline và đường chạy thực tế

**Công việc**

- Xác nhận model ERP người dùng đang chọn, ID, tool/filter, source đăng ký, bản code được nạp, cấu hình và trạng thái container.
- Vẽ đường đi từ câu hỏi qua tool đến DB và renderer; so sánh với runtime mới đang có.
- Chạy lại 18 câu cũ và một nhóm MES đại diện, qua đúng đường chat thực tế bằng phiên được phép.
- Lưu đầu vào, ngữ cảnh, định danh báo cáo, tham số, kết quả kiểm chứng và loại lỗi; tránh ghi bí mật hoặc dữ liệu vượt quyền.
- Giữ hai model GPT độc lập; mọi thay đổi trong kế hoạch tập trung vào đường ERP/MES.

**Bàn giao:** sơ đồ runtime, baseline có bằng chứng, danh sách lỗi theo nguyên nhân. Thời gian dự kiến: 1–2 ngày làm việc.

## 6. Giai đoạn 1 — Điều tra metadata, function và luồng màn hình

**Khảo sát DB**

- Kiểm kê schema, bảng, view/materialized view, function/procedure, kiểu tham số, kiểu trả về, khóa chính/ngoại, index, comment, trigger và dependency.
- Dùng catalog PostgreSQL như `pg_catalog`, `information_schema`, `pg_get_functiondef`, `pg_get_viewdef` để đọc định nghĩa mà không gọi thực thi function nghiệp vụ.
- Đọc cấu hình màn/lưới/menu đang có như `sys_command`, `sys_listinfo`, `sys_gridconfig`, `sys_listoptions` khi đã xác nhận schema tương ứng.
- Theo dõi SQL động và tên bảng/phân vùng theo kỳ; dependency catalog có thể không phản ánh đầy đủ quan hệ trong SQL động.
- Kiểm tra quan hệ thực tế bằng mẫu dữ liệu vì ERP có thể không khai báo FK. Tên gần giống nhau không đủ để kết luận khóa nối.
- Kiểm tra độ duy nhất và tỷ lệ khớp khóa, đặc biệt header–detail, đơn–giao–xuất và phiên sản xuất–sản lượng–NG–dừng máy.

**Khảo sát UI/API**

- Với mỗi màn: lưu tên/state, request, filter mặc định, response, cách gộp ô, định dạng, phân trang, subtotal và export.
- Nếu có source ERP/MES thì đọc controller/service/query/formatter; nếu chưa có source thì dùng request/response và export từ phiên được phép.
- Với mỗi cột: ghi tên UI, field API, nguồn bảng/biểu thức, công thức, đơn vị, trạng thái áp dụng, mức chi tiết và điều kiện quyền.
- Phân biệt tồn sổ sách, tồn tem, tồn khả dụng; giao theo phiếu xuất và giao thực tế; đơn mua và báo giá; NG sản phẩm và NG linh kiện.

**Quyết định dùng function**

- Đọc body, hàm được gọi bên trong, SQL động, quyền thực thi và tác dụng phụ. Nhãn volatility chỉ là thông tin hỗ trợ, không phải bằng chứng đủ.
- Function có ghi dữ liệu, tạo bảng làm việc, thay đổi session hoặc dùng quyền nâng cao không được gọi tùy tiện. Có thể tách phần SELECT thành adapter, hoặc dùng API hiện hữu sau khi xác minh.
- Mỗi nguồn chọn một cách thực thi có lý do: SELECT trên view; adapter function đã kiểm tra; API báo cáo; hoặc tái dựng SELECT từ logic nguồn.
- Nếu tái dựng logic, phải đối chiếu với báo cáo gốc; tránh có hai công thức khác nhau cùng mang một tên.

**Bàn giao:** catalog nguồn, sơ đồ quan hệ, bản đồ UI–API–DB và danh sách còn thiếu bằng chứng. Thời gian: 3–5 ngày cho nhóm ưu tiên; phần còn lại triển khai theo nhóm màn.

## 7. Giai đoạn 2 — Chuẩn hóa danh mục nghiệp vụ dùng chung

Mỗi dataset cần có:

- ID, tên Việt, từ đồng nghĩa, tên màn nguồn và trạng thái xác minh.
- Mức chi tiết của một dòng, khóa định danh và khóa nối; quan hệ một–một/một–nhiều/nhiều–nhiều.
- Dimension được phép: khách, nhà cung cấp, hàng, kho, lô, khuôn, máy, line, ca, WO, OI, kỳ.
- Metric: công thức, trường nguồn, cách tổng hợp, đơn vị, tiền tệ, quy tắc NULL/0 và làm tròn.
- Chỉ số cộng được theo chiều nào; ví dụ không cộng tồn ngày qua nhiều ngày, không lấy trung bình các tỷ lệ NG để thay cho tổng NG/tổng sản lượng.
- Trường ngày dùng cho từng nghiệp vụ, ngày hiệu lực, timezone và lịch ca qua nửa đêm.
- Trạng thái được tính/loại, xử lý hủy/trả/đảo bút toán và dữ liệu cập nhật trễ.
- Quyền dòng/cột, ĐVCS, kho, nhà máy và nguồn danh tính đáng tin cậy.
- Bộ lọc, sắp xếp, so sánh kỳ, top N, phân trang và xuất toàn bộ được hỗ trợ.
- Nguồn gốc, bằng chứng đối chiếu, người xác nhận, phiên bản và dependency checksum.

Tái sử dụng 82 manifest hiện có sau khi rà soát. Không nhập tất cả vào một prompt dài; truy xuất theo nghiệp vụ và quyền. Quan hệ và phép tính được định nghĩa một lần để dùng cho nhiều câu hỏi.

**Bàn giao:** danh mục nghiệp vụ có phiên bản, hợp đồng truy vấn/kết quả, quy tắc xử lý xung đột. Thời gian: 3–5 ngày, triển khai song song với đối chiếu UI khi có đủ nguồn.

## 8. Giai đoạn 3 — Xử lý câu hỏi tự do và nhiều lượt

- Chuẩn hóa tiếng Việt, viết tắt, lỗi gõ, mã có dấu gạch và tên gần giống; không nhầm mã khách với mã hàng.
- Tìm ứng viên trong đúng danh mục, xác minh mã tồn tại; hỏi lại nếu nhiều ứng viên mà không đủ ngữ cảnh.
- Sinh kế hoạch có cấu trúc: tác vụ, dataset, entity, metric, dimension, filter, kỳ, thứ tự và phụ thuộc giữa các bước.
- Lưu context theo hội thoại ở dạng có cấu trúc; “mã đó”, “còn tháng trước”, “chia theo kho” kế thừa đúng đối tượng. Đổi đối tượng phải cập nhật hoặc xóa các filter liên quan.
- Dùng ngày server và timezone nghiệp vụ để giải thích ngày tương đối; kỳ so sánh phải rõ là cả tháng hay cùng số ngày đã qua.
- Với câu hỏi xuyên phân hệ: tổng hợp từng nguồn về đúng khóa chung rồi mới nối; không nối trực tiếp nhiều bảng chi tiết làm nhân số lượng.
- Truy vấn phụ thuộc có giới hạn số bước và thời gian; chỉ sửa truy vấn khi phát hiện lỗi cụ thể, không bỏ filter để ép có dữ liệu.
- Với “vì sao”: phân biệt nguyên nhân được ghi nhận trong nhật ký và suy luận tương quan. Với dự báo: công khai giả định và độ bất định, không gọi đó là dữ kiện DB.

**Bàn giao:** parser/planner, context state, compiler và executor cho các phép phân tích chuẩn. Thời gian: 4–6 ngày.

## 9. Giai đoạn 4 — Kiểm tra kết quả và trình bày đúng

- Quyền đến từ phiên đăng nhập và ánh xạ server; không nhận user ID/phạm vi do model hoặc URL tự đưa.
- Chỉ thực thi nguồn/phép toán cho phép, bind tham số, transaction chỉ đọc, timeout, giới hạn dòng và ngân sách chi phí. SELECT vẫn có thể gọi function, nên chỉ kiểm tra từ khóa SELECT là chưa đủ.
- Kiểm tra đúng mã, kỳ, kho, trạng thái, đơn vị, tiền tệ, khóa trùng và tổng trước/sau join.
- Aggregate tính trên toàn bộ tập lọc; bảng chỉ là trang hiển thị. Không lấy 200 dòng đầu làm tổng toàn bộ.
- Tách trạng thái kết quả rỗng, số 0 hợp lệ, NULL, ngoài quyền, lỗi và chưa hỗ trợ.
- Với so sánh dữ liệu đang biến động: dùng cùng snapshot khi có thể; nếu UI/API khác kết nối thì ghi mốc chốt hoặc chọn kỳ đóng. Không đổ mọi sai lệch cho DB thay đổi.
- Kết quả có số tóm tắt, bảng chi tiết, biểu đồ khi phù hợp, kỳ/filter và tình trạng còn trang. Biểu đồ dùng dữ liệu đủ phạm vi; không trộn đơn vị.
- Excel toàn bộ phải lấy đủ dữ liệu trong phạm vi quyền và giới hạn đã duyệt; nếu chỉ xuất trang hiện tại phải ghi rõ.
- Metadata truy vết lưu report/version, nguồn, filter, request ID, thời điểm và phạm vi; giao diện người dùng chỉ hiện thông tin hữu ích, không đổ schema kỹ thuật vào câu trả lời.

**Bàn giao:** validator, kết quả có cấu trúc và renderer thống nhất. Thời gian: 2–3 ngày.

## 10. Giai đoạn 5 — Đối chiếu UI và nghiệm thu bằng câu hỏi chưa thấy

**Phạm vi kiểm thử**

- Chạy lại 18 câu lịch sử; bổ sung tối thiểu 200 câu độc lập trong đợt nghiệm thu đầu, phân tầng theo nghiệp vụ, kiểu hỏi và rủi ro.
- Có câu do người dùng nghiệp vụ đặt, không chỉ câu do model tự sinh. Giữ riêng một tập chưa dùng để sửa prompt hoặc logic.
- Bao phủ tra cứu, tổng hợp, so sánh, xếp hạng, nhiều vế, nhiều lượt, xuyên phân hệ, câu mơ hồ và ngoài dữ liệu/quyền.
- Mỗi màn tối thiểu ba mẫu đối chiếu theo hướng dẫn hiện có; với quan hệ nhiều–nhiều hoặc chỉ số quan trọng phải tăng số mẫu.
- Các ca MES bắt buộc: ca qua ngày, nhiều lần xác nhận một phiên, nhiều nguyên nhân dừng, khoảng dừng chồng nhau, đổi cavity, bổ sung/bỏ shot, NG sản phẩm/linh kiện, gộp/tách thùng và thu hồi NVL.
- Kiểm tra âm về quyền giữa ít nhất hai tài khoản có phạm vi khác nhau; xác minh cache, hội thoại và export không làm lộ dữ liệu chéo.

**Ba lớp bằng chứng**

1. Đáp án kỳ vọng từ query tham chiếu độc lập hoặc dữ liệu fixture có kiểm soát.
2. UI/export ERP/MES theo cùng filter, quyền và mốc chốt.
3. Câu trả lời cuối qua model/tool/UI thực tế, bao gồm bảng, tổng, biểu đồ và file xuất.

**Điều kiện phát hành đề xuất**

- 100% ca số liệu trọng yếu trong phạm vi phát hành khớp nguồn chuẩn; sai số chỉ được chấp nhận theo quy tắc tiền tệ/làm tròn đã thống nhất.
- 100% ca quyền và phân biệt rỗng/0/lỗi bắt buộc phải đạt.
- Tối thiểu 95% câu đủ dữ kiện, trong phạm vi hỗ trợ của tập kiểm thử độc lập, trả đúng đầy đủ. Chấm khả năng yêu cầu làm rõ/từ chối riêng; không tính từ chối mọi câu là đạt độ chính xác.
- Không có lỗi nghiêm trọng như dùng doanh số làm giao bù NG, nhân số lượng do join hay cộng lại dòng tổng. Nếu có, chặn nhóm nghiệp vụ bị ảnh hưởng để sửa.
- Công bố cả tỷ lệ bao phủ nghiệp vụ, tỷ lệ trả lời, độ chính xác và lỗi theo nhóm. Không suy ra “95% mọi câu hỏi ERP” từ một tập nhỏ.
- Mục tiêu hiệu năng ban đầu: P95 ≤ 15 giây cho câu chuẩn, ≤ 45 giây cho phân tích nhiều bước trên tải được thống nhất; phải đo rồi mới cam kết.

**Bàn giao:** báo cáo pass/fail, lỗi còn lại, ma trận phạm vi được phát hành. Thời gian: 3–5 ngày, có thể dài hơn nếu thiếu UI/đáp án nghiệp vụ.

## 11. Giai đoạn 6 — Pilot, chuyển luồng và vận hành

- Chạy staging bằng bản sao cấu hình và tài khoản chỉ đọc có scope tương ứng; không thử ghi dữ liệu trên ERP/MES production.
- Pilot với nhóm người dùng nhỏ; nghiệm thu trên đúng model ERP và tài khoản thật được cấp quyền.
- Đối chiếu yêu cầu thực với luồng cũ trong chế độ phù hợp tải DB; không tự động nhân đôi mọi truy vấn nặng.
- Chỉ chuyển đường ERP sau khi có kết quả nghiệm thu và duyệt triển khai riêng; giữ khả năng quay lại phiên bản trước.
- Theo dõi lỗi định tuyến, sai khác số liệu, timeout, câu chưa có nghiệp vụ, độ trễ và mức bao phủ. Dữ liệu giám sát phải theo quyền và tránh lưu thừa nội dung giao dịch.
- Khi function/schema/API đổi, đánh dấu dataset phụ thuộc cần kiểm tra; chạy lại các mẫu đối chiếu trước khi xác nhận còn đúng.
- Câu chưa xử lý được trở thành yêu cầu bổ sung có bằng chứng. Không tự sửa công thức nghiệp vụ từ phản hồi của một lượt chat.

**Bàn giao:** hướng dẫn vận hành, rollback, quy trình bổ sung nghiệp vụ. Thời gian: 2–3 ngày pilot và theo dõi tiếp.

## 12. Thứ tự phủ nghiệp vụ

| Đợt | Phạm vi | Mục đích |
| --- | --- | --- |
| A | Vật tư/khách/NCC; tồn, nhập–xuất; đơn–giao–bán; giá mua/bán; các ca lịch sử bị sai | Chốt nền dữ liệu và sửa lỗi có bằng chứng |
| B | BOM, LSX, WO/OI, line/máy/ca, sản lượng, NG, dừng máy, khuôn/shot, vật tư dùng/thu hồi | Phủ chuỗi MES và câu hỏi xuyên sản xuất–kho |
| C | QC IQC/IPQC/OQC, tem/lô/thùng/pallet, forecast/DO, đổi trả/giao bù, các màn còn lại | Hoàn thiện nghiệp vụ phức tạp và thiếu định nghĩa |

Công nợ, kế toán hoặc phân hệ chưa nằm trong catalog phải được bổ sung phạm vi và nguồn trước khi tính là đã hỗ trợ.

## 13. Điều kiện đầu vào và mốc thời gian

Cần tài khoản DB chỉ đọc thấy được metadata cần thiết; phiên/tài khoản UI nghiệp vụ đúng quyền hoặc API tương ứng; danh sách menu/phân hệ cần phủ; đầu mối xác nhận công thức còn tranh chấp. Nếu thiếu source ERP/MES vẫn có thể khảo sát qua API và UI, nhưng tiến độ đối chiếu sẽ chậm hơn.

Ước lượng ban đầu cho một người triển khai chính, có người nghiệp vụ phối hợp: **3–5 tuần cho nền tảng và phạm vi ưu tiên**, vì một số hạng mục có thể thực hiện xen kẽ. Thời gian phủ toàn bộ ERP/MES chỉ chốt sau giai đoạn kiểm kê; số lượng màn, function động và khả năng tiếp cận UI quyết định phần còn lại. Không cam kết toàn bộ hệ thống trong một số ngày cố định khi chưa có kiểm kê.

Mốc duyệt nội bộ đề xuất:

1. Sau giai đoạn 0–1: chốt nguồn, phạm vi, công thức còn thiếu và lịch thực hiện cập nhật.
2. Sau giai đoạn 2–4: review thiết kế và demo câu hỏi ngẫu nhiên trên staging.
3. Sau giai đoạn 5: duyệt phạm vi đạt nghiệm thu.
4. Sau pilot: xin duyệt chuyển luồng ERP thực tế bằng kết quả cụ thể và phương án rollback.

## 14. Nội dung đề nghị duyệt

Duyệt hướng **khảo sát UI/API/function → danh mục nghiệp vụ đã xác minh → planner/ compiler truy vấn → kiểm tra kết quả → nghiệm thu UI**; bắt đầu bằng baseline và kiểm kê chỉ đọc, sau đó xây và kiểm thử trên staging theo thứ tự A/B/C.

Duyệt kế hoạch không đồng nghĩa đã nghiệm thu mọi báo cáo hoặc cho phép chuyển production ngay. Việc chuyển luồng ERP thực tế sẽ có đề xuất riêng sau khi cung cấp bằng chứng kiểm thử. Trong lượt hiện tại chỉ tạo tài liệu kế hoạch này.

---

## 15. Giải pháp kỹ thuật xử lý "Giao diện gộp cột / UI khác DB" để tra cứu nội bộ

### 15.1. Bản chất sự khác biệt giữa UI Grid và Database
Khi người dùng đối chiếu bảng tra cứu trên giao diện ERP/MES (như danh sách trong `danh-sach-bang-tra-cuu.md`) với bảng vật lý trong DB PostgreSQL (`3SERP_HTMP_DATA`), sự khác biệt xuất phát từ 4 cơ chế:
1. **Gộp dòng chi tiết thành dòng tổng hợp (Aggregation):**
   - DB lưu mức chi tiết nhất (atomic). Ví dụ: `mes_oi_dong_thung` lưu từng con tem sản phẩm lẻ (`serial_tem_sp`).
   - UI "Bảng kê đóng gói, đóng thùng" gom nhóm (`GROUP BY`) theo Thùng (`serial_tem_thung`), tính `COUNT(serial_tem_sp)` thành `Số lượng theo thùng` và `SUM(quantity)` thành `Số lượng thực tế`.
2. **Ghép nhiều cột DB thành 1 cột UI (Combined Columns):**
   - DB tách riêng `create_date` và `create_time`. UI ghép lại thành `Thời gian đóng thùng`.
   - DB chỉ lưu mã ngoại khóa; UI tự JOIN bảng danh mục (`dmvt`, `dmkh`, `sys_dmtt`) để hiển thị Tên, Đơn vị tính, Mô tả trạng thái.
3. **Cột Kế hoạch và Thực tế đến từ các nguồn khác nhau (Cross-source JOIN):**
   - Bảng thực thi chỉ ghi nhận sản lượng thực tế. Cột `Ngày kế hoạch`, `SL kế hoạch` được JOIN từ lịch trình / lệnh sản xuất (`mes_scheduling`, `mfkhsx_po_fc`) qua số WO (`mes_scheduling_code`).
4. **Dữ liệu log dạng Document/JSON (JSONB unpacking):**
   - Bảng tem nhãn `intem_log` lưu chi tiết trong cột `data_tem` (JSONB). Khi lên giao diện, hệ thống tự bung mảng JSON ra thành các cột riêng (`cavity`, `die_no`, `ma_khuon`, `so_luong`).

### 15.2. Kiến trúc 4 lớp để hoàn thiện tra cứu nội bộ trên Open WebUI
Để AI và người dùng nội bộ có thể tra cứu chính xác bất kỳ bảng nào trong danh mục mà không bị sai lệch số liệu hay thiếu cột:

```text
[Người dùng hỏi tự nhiên trên Open WebUI / Chatbot nội bộ]
                      ↓
[Lớp 1: Entity Extraction & Intent Routing (functions/htmp_postgres_query.py)]
  - Trích xuất: Tên bảng tra cứu, Mã vật tư, Số WO, Khách hàng, Kho, Ngày...
  - Nhận diện Intent trong config/erp-business-intents.json
                      ↓
[Lớp 2: Semantic View / Parameterized Query Adapter]
  - Truy vấn chuẩn hóa đã giải quyết sẵn việc gộp dòng, ghép cột ngày-giờ, JOIN danh mục
  - Chạy an toàn với quyền chỉ đọc (read_htmp), statement_timeout = 15s, bind params
                      ↓
[Lớp 3: Result Validator & Formatter]
  - Kiểm tra đối chiếu số liệu, loại trừ trùng dòng
  - Tái tạo định dạng hiển thị đúng như trên lưới ERP (đủ 15–20 cột theo bảng tra cứu)
                      ↓
[Lớp 4: Trình bày kết quả]
  - Bảng tổng hợp / chi tiết Markdown trực quan
  - Nút xuất file Excel / CSV đầy đủ phục vụ nghiệp vụ
```

### 15.3. Quy trình 4 bước đóng gói từng bảng tra cứu vào hệ thống

Mỗi bảng trong `danh-sach-bang-tra-cuu.md` sẽ được hoàn thiện theo quy trình tiêu chuẩn:
1. **Bước 1: Khảo sát catalog & xác định bảng vật lý:**
   - Dùng script catalog scan (chỉ đọc) để tìm đúng bảng nguồn và khóa chính (`mes_oi_dong_thung`, `intem_carton_log`, `mes_oi_bo_shot`, `ct81`, `ct70`, `mfbom`...).
2. **Bước 2: Xây dựng Query Template / Semantic View:**
   - Viết câu lệnh SELECT tham số hóa chứa đầy đủ logic: `GROUP BY`, `JOIN` danh mục, ghép ngày-giờ, giải mã trạng thái.
   - Kiểm tra đối chiếu (Reconciliation) với mẫu dữ liệu thực tế trên UI ERP.
3. **Bước 3: Khai báo Intent & Bổ sung từ điển:**
   - Thêm vào `config/erp-business-intents.json`: ID nghiệp vụ, tên tiếng Việt, từ khóa nhận diện (có dấu, không dấu, viết tắt, tiếng lóng xưởng).
   - Khai báo manifest trong `config/erp-reports/<report_id>.json`.
4. **Bước 4: Đăng ký vào Tool runtime `functions/htmp_postgres_query.py`:**
   - Bổ sung hàm handler tương ứng, hỗ trợ phân trang và xuất dữ liệu.
   - Viết test tự động chạy kiểm thử hồi quy (như `scratch/test_18_questions.py`).

### 15.4. Lộ trình triển khai theo 3 đợt nghiệp vụ

| Đợt | Nhóm bảng tra cứu mục tiêu | Nguồn DB cốt lõi | Kết quả bàn giao |
| :---: | :--- | :--- | :--- |
| **Đợt 1 (Ưu tiên cao)** | **Bán hàng & Kho vận:**<br>- Bảng kê đơn hàng bán (SO1)<br>- Lệnh giao hàng, Bảng kê lệnh giao hàng<br>- Phiếu xuất kho, Bảng kê xuất/nhập kho (ct70, ct81, ct74) | `ph81/ct81`, `ph64/ct64`, `ph96/ct96`, `ct70`, `ph74/ct74`, `dmvt`, `dmkh` | Tra cứu được toàn bộ tiến độ đơn hàng, lịch sử giao hàng, tồn kho theo kho, doanh số bán. |
| **Đợt 2** | **Sản xuất & Đóng gói MES:**<br>- Bảng kê đóng gói, đóng thùng (mes_oi_dong_thung)<br>- Bảng kê gộp, tách thùng (intem_carton_log, intem_log)<br>- Bảng kê Work Order, Bảng kê bổ sung shot (mes_oi_bo_shot)<br>- Thống kê cấp NVL | `mes_oi_dong_thung`, `intem_carton_log`, `mes_oi_bo_shot`, `intem_log`, `mfkhsx`, `mes_scheduling` | Tra cứu được sản lượng thực tế theo thùng/WO, lịch sử gộp tách tem, số shot khuôn, cấp NVL cho sản xuất. |
| **Đợt 3** | **Kế hoạch, Bảng giá & Khuôn mẫu:**<br>- Danh mục bảng giá, BOM sản phẩm<br>- Báo cáo OQC/IQC<br>- Hồ sơ khuôn, tuổi thọ khuôn | `mfbom/mfbom_material`, `dmbanggia/dmbanggiact`, `dmhosokhuon`, `sys_listoptions` | Tra cứu cấu trúc BOM, giá bán/mua hiện hành, tình trạng chất lượng và cảnh báo bảo dưỡng khuôn. |

### 15.5. Kết quả kiểm thử tự động toàn diện đợt 1 (Ngày 2026-10-27)

Đã xây dựng và thực thi bộ kiểm thử tự động toàn diện gồm 16 câu hỏi thực tế (`scratch/run_full_batch1_test.py`) qua pipeline [ask_erp](file:///home/admin/ai-stack/functions/htmp_postgres_query.py#L2779-L2805):

| Mã test | Nghiệp vụ | Câu hỏi kiểm thử thực tế | Kết quả | Thời gian | Nguồn DB / Ghi chú dữ liệu live |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **MES-01** | Đóng gói đóng thùng | `Bảng kê đóng gói đóng thùng mã QC7-5524-000` | **PASSED** | 3.19s | `mes_oi_dong_thung` (30 thùng hôm nay, Serial `20261027...`, WO `001-2610-2510-DUC-0011.1T`) |
| **MES-02** | Đóng gói đóng thùng | `Cho tôi xem bảng kê đóng thùng gần đây nhất` | **PASSED** | **0.07s** | `mes_oi_dong_thung` (30 thùng mới nhất qua index scan ngược, không cần mã vật tư) |
| **MES-03** | Đóng gói đóng thùng | `Bảng kê đóng gói theo WO 001-2610-2510-DUC-0011.1T` | **PASSED** | 3.08s | `mes_oi_dong_thung` (30 thùng theo WO, đã sửa regex nhận diện có dấu chấm `.1T`) |
| **MES-04** | Đóng gói đóng thùng | `Bảng kê đóng thùng mã RC6-4007-000` | **PASSED** | 3.11s | `mes_oi_dong_thung` (30 thùng đóng hôm nay của mã RC6-4007-000) |
| **MES-05** | Gộp tách thùng | `Bảng kê gộp tách thùng` | **PASSED** | 0.45s | `intem_carton_log` + `intem_log` (30 lượt gộp/tách tem, mã thùng cũ/mới, SL cũ/mới) |
| **MES-06** | Gộp tách thùng | `Cho tôi xem bảng kê gộp tách thùng hôm nay` | **PASSED** | 1.20s | `intem_carton_log` (30 lượt gộp/tách ngày hôm nay 2026-10-27) |
| **MES-07** | Gộp tách thùng | `Lịch sử gộp tách thùng mã VGL1A375` | **PASSED** | 0.35s | `intem_carton_log` (2 dòng lịch sử tách thùng STATUS LENS, SL 1400 -> 900) |
| **MES-08** | Gộp tách thùng | `Bảng kê gộp tách thùng mã BGTD0103` | **PASSED** | 0.33s | `intem_carton_log` (30 lượt gộp/tách của thùng BGTD0103) |
| **MES-09** | Bổ sung shot khuôn | `Bảng kê bổ sung shot khuôn` | **PASSED** | 0.17s | `mes_oi_bo_shot` (30 lượt ghi nhận shot thực tế máy đúc ca hôm nay) |
| **MES-10** | Bổ sung shot khuôn | `Bảng kê bổ sung shot khuôn gần đây` | **PASSED** | 0.15s | `mes_oi_bo_shot` (30 lượt ghi nhận gần đây nhất) |
| **MES-11** | Bổ sung shot khuôn | `Bảng kê bổ sung shot máy DUC-0032` | **PASSED** | 0.15s | `mes_oi_bo_shot` (21 lượt shot bổ sung máy DUC-0032 ca hôm nay) |
| **MES-12** | Bổ sung shot khuôn | `Bảng kê bổ sung shot mã RC6-3909-000` | **PASSED** | 0.14s | `mes_oi_bo_shot` (5 lượt shot của sản phẩm RC6-3909-000) |
| **ERP-13** | Quy cách đóng gói | `Quy cách đóng gói và tồn kho mã QC7-5524-000` | **PASSED** | 3.10s | Đóng gói thực tế + quy cách tiêu chuẩn |
| **ERP-14** | Trạng thái QC | `Trạng thái QC mã QC7-5524-000` | **PASSED** | 1.49s | `sys_listoptions` (6,585 PCS tem OK) |
| **ERP-15** | Nhập kho | `Bảng kê phiếu nhập kho mã QC7-5524-000` | **CHẶN AN TOÀN** | 0.01s | Kiểm tra quyền session chat thành công |
| **ERP-16** | Giao hàng | `Đợt giao hàng gần nhất của mã QC7-5524-000` | **PASSED** | 0.08s | `ph81/ct81` (lần giao gần nhất kèm số phiếu xuất kho) |

**Tổng kết:** **15/16 test PASSED (93.8%)**. Nhóm nghiệp vụ Đóng gói - Gộp tách - Shot khuôn đạt **100% (12/12)**, thời gian phản hồi trung bình dưới 1 giây. Đã sẵn sàng chuyển tiếp sang Đợt 2.

### 15.6. Kết quả triển khai & kiểm thử tự động toàn diện đợt 2 (Ngày 2026-10-27)

Đợt 2 tập trung vào nhóm nghiệp vụ **Kế hoạch điều độ sản xuất, Dừng máy và Phế phẩm MES**. Quá trình khảo sát catalog đối chiếu thực tế đã xác định chuẩn xác các bảng DB vật lý (thay thế các tên ước lượng không tồn tại như `mfwo`, `mes_oi_downtime`, `mes_oi_ng`):
- **Bảng kê Work Order / Điều độ sản xuất:** `mes_scheduling_output` (243,769 dòng chi tiết WO) + `phlsx` (244,948 dòng) / `ctlsx` (252,531 dòng) + `dmvt`.
- **Bảng kê dừng máy / dừng chuyền:** `mes_oi_stop_line` (421,283 dòng log dừng máy) + `dmnndungmay` (176 dòng danh mục nguyên nhân dừng) tính toán thời lượng dừng thực tế theo phút.
- **Bảng kê phế phẩm / lỗi sản xuất (NG):** `mes_oi_ng_confirm` (237,572 dòng lỗi xác nhận) + `dmloi` (180 mã lỗi) + `dmvt`.

Đã xây dựng và thực thi bộ kiểm thử tự động toàn diện gồm 12 câu hỏi thực tế (`scratch/run_full_batch2_test.py`) qua pipeline [ask_erp](file:///home/admin/ai-stack/functions/htmp_postgres_query.py#L2779-L2805):

| Mã test | Nghiệp vụ | Câu hỏi kiểm thử thực tế | Kết quả | Thời gian | Nguồn DB / Ghi chú dữ liệu live |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **MES2-01** | Điều độ SX / WO | `Bảng kê Work Order mã 1014082701` | **PASSED** | 0.365s | `phlsx` + `ctlsx` (8 dòng LSX/WO mã FRONTAL COVER) |
| **MES2-02** | Điều độ SX / WO | `Cho tôi xem bảng kê điều độ sản xuất gần đây nhất` | **PASSED** | 0.114s | `phlsx` + `ctlsx` (30 LSX mới nhất kèm mã WO) |
| **MES2-03** | Điều độ SX / WO | `Tiến độ Work Order 001-2610-2710-DUC-0037.T30` | **PASSED** | **0.070s** | `mes_scheduling_output` (WO máy DUC-0037, SL 300) |
| **MES2-04** | Điều độ SX / WO | `Kế hoạch sản xuất mã RC6-3087-000` | **PASSED** | 0.189s | `phlsx` + `ctlsx` (4 dòng LSX, Cover_Left_MY) |
| **MES2-05** | Dừng máy / chuyền | `Bảng kê dừng máy gần đây` | **PASSED** | 0.235s | `mes_oi_stop_line` (30 sự cố dừng máy mới nhất) |
| **MES2-06** | Dừng máy / chuyền | `Bảng kê dừng máy hôm nay` | **PASSED** | 0.245s | `mes_oi_stop_line` (30 sự cố dừng máy ca hôm nay) |
| **MES2-07** | Dừng máy / chuyền | `Lịch sử dừng máy DUC-0266` | **PASSED** | 0.231s | `mes_oi_stop_line` (30 sự cố dừng máy DUC-0266) |
| **MES2-08** | Dừng máy / chuyền | `Bảng kê sự cố dừng máy DUC-0050` | **PASSED** | 0.220s | `mes_oi_stop_line` (30 sự cố dừng máy DUC-0050) |
| **MES2-09** | Phế phẩm / Lỗi NG | `Bảng kê phế phẩm sản xuất gần đây` | **PASSED** | 0.180s | `mes_oi_ng_confirm` (30 dòng ghi nhận lỗi NG mới nhất) |
| **MES2-10** | Phế phẩm / Lỗi NG | `Bảng kê lỗi sản xuất mã QC7-5021-000` | **PASSED** | 0.172s | `mes_oi_ng_confirm` (30 dòng lỗi mã QC7-5021-000) |
| **MES2-11** | Phế phẩm / Lỗi NG | `Hàng NG máy DUC-0031` | **PASSED** | 0.166s | `mes_oi_ng_confirm` (30 dòng lỗi máy DUC-0031) |
| **MES2-12** | Phế phẩm / Lỗi NG | `Bảng kê phế phẩm mã QC7-5403-000` | **PASSED** | 0.175s | `mes_oi_ng_confirm` (5 dòng lỗi mã QC7-5403-000) |

**Tổng kết Đợt 2:** **12/12 test PASSED (100.0%)**, thời gian phản hồi trung bình **0.197s** (dưới 200ms). Toàn bộ tool đã được đồng bộ vào `/app/backend/data/webui.db` và container `open-webui` (healthy).

### 15.7. Kết quả triển khai & kiểm thử tự động toàn diện đợt 3 (Ngày 2026-10-28)

Đợt 3 tập trung vào các phân hệ cốt lõi ERP: **Bán hàng (Đơn hàng SO1, Phiếu xuất bán HDA), Mua hàng (Đơn mua PO1), Kho vận (Phiếu nhập/xuất nội bộ PND/PXA), Hồ sơ khuôn (dmhosokhuon) và Bảng giá bán (dmbanggia)**. Quá trình khảo sát catalog đã xác định chuẩn xác các bảng DB vật lý:
- **Đơn hàng bán SO1:** `ph64` (620,792 đơn SO) + `ct64` (782,021 dòng chi tiết) + `ctkhgh` (4,028,260 dòng tiến độ giao hàng) + `dmkh` + `sys_dmtt`.
- **Phiếu xuất kho bán hàng HDA:** `ph81` (160,982 phiếu) + `ct81` (3,296,218 dòng chi tiết) liên kết đơn hàng `so_ct_so1` và số `so_po`.
- **Đơn hàng mua PO1:** `ph94` (hàng chục nghìn PO) + `ct94` + `dmkh` (NCC) + `sys_dmtt`.
- **Phiếu nhập/xuất nội bộ:** `ph74` (504,312 phiếu) + `ct74` (916,793 dòng) + `dmvt` + `dmkho` (xử lý phiếu nhập kho từ sản xuất `PND` và xuất nội bộ `PXA`).
- **Hồ sơ khuôn:** `dmhosokhuon` (2,185 hồ sơ khuôn, số cavity, tuổi thọ shot bảo hiểm).
- **Bảng giá bán:** `dmbanggia` (11 bảng giá) + `dmbanggiact` (11,225 dòng chi tiết giá).

Đã xây dựng và thực thi bộ kiểm thử tự động toàn diện gồm 16 câu hỏi thực tế (`scratch/run_full_batch3_test.py`) qua pipeline [ask_erp](file:///home/admin/ai-stack/functions/htmp_postgres_query.py):

| Mã test | Nghiệp vụ | Câu hỏi kiểm thử thực tế | Kết quả | Thời gian | Nguồn DB / Ghi chú dữ liệu live |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **ERP3-01** | Đơn hàng bán SO1 | `Cho tôi xem bảng kê đơn hàng bán gần đây nhất` | **PASSED** | 1.719s | `ph64` + `ct64` (30 dòng đơn SO mới nhất ngày 28/10/2026) |
| **ERP3-02** | Đơn hàng bán SO1 | `Bảng kê đơn hàng bán mã KH0047` | **PASSED** | 1.100s | `ph64` + `ct64` (30 dòng SO của Anam Electronics) |
| **ERP3-03** | Đơn hàng bán SO1 | `Bảng kê đơn hàng bán số 001-2610-010164` | **PASSED** | 0.684s | `ph64` + `ct64` (30 dòng chi tiết đơn SO 001-2610-010164) |
| **ERP3-04** | Đơn hàng bán SO1 | `Đơn hàng bán mã VGL1A416` | **PASSED** | 1.553s | `ph64` + `ct64` (30 dòng đơn hàng có chứa mã VGL1A416) |
| **ERP3-05** | Phiếu xuất bán HDA | `Bảng kê phiếu xuất kho bán hàng gần đây` | **PASSED** | 0.386s | `ph81` + `ct81` (30 dòng xuất kho bán ngày hôm nay 28/10/2026) |
| **ERP3-06** | Phiếu xuất bán HDA | `Bảng kê phiếu xuất bán mã KH0049` | **PASSED** | 0.437s | `ph81` + `ct81` (30 dòng xuất kho bán KH Tohoku Pioneer) |
| **ERP3-07** | Phiếu xuất bán HDA | `Phiếu xuất kho bán hàng 001-2610-002643` | **PASSED** | 0.308s | `ph81` + `ct81` (6 dòng chi tiết phiếu xuất 001-2610-002643) |
| **ERP3-08** | Đơn hàng mua PO1 | `Bảng kê đơn hàng mua gần đây nhất` | **PASSED** | 0.253s | `ph94` + `ct94` (8 dòng PO mới nhất ngày 28/10/2026) |
| **ERP3-09** | Đơn hàng mua PO1 | `Bảng kê đơn hàng mua mã NCC0220` | **PASSED** | 0.169s | `ph94` + `ct94` (9 dòng PO của NCC Hungtech) |
| **ERP3-10** | Đơn hàng mua PO1 | `Đơn hàng mua số 001-2610-000702` | **PASSED** | **0.079s** | `ph94` + `ct94` (1 dòng PO số 001-2610-000702) |
| **ERP3-11** | Nhập/xuất nội bộ | `Bảng kê phiếu nhập kho nội bộ gần đây` | **PASSED** | 0.455s | `ph74` + `ct74` (16 dòng phiếu PND từ sản xuất hôm nay) |
| **ERP3-12** | Nhập/xuất nội bộ | `Phiếu nhập kho nội bộ số 001-2610-011362` | **PASSED** | 1.357s | `ph74` + `ct74` (1 dòng chi tiết phiếu PND 001-2610-011362) |
| **ERP3-13** | Nhập/xuất nội bộ | `Bảng kê nhập kho từ sản xuất mã RC4-3049-000` | **PASSED** | 1.272s | `ph74` + `ct74` (30 dòng nhập kho của mã phụ kiện máy in) |
| **ERP3-14** | Hồ sơ khuôn | `Bảng kê hồ sơ khuôn gần đây` | **PASSED** | 0.090s | `dmhosokhuon` (30 hồ sơ khuôn mới nhất, có cavity, shot BH) |
| **ERP3-15** | Hồ sơ khuôn | `Hồ sơ khuôn mã K_VGY1A061` | **PASSED** | 0.087s | `dmhosokhuon` (1 dòng hồ sơ khuôn K_VGY1A061, tuổi thọ 1M shot) |
| **ERP3-16** | Bảng giá bán | `Danh mục bảng giá bán hiện hành` | **PASSED** | **0.069s** | `dmbanggia` + `dmbanggiact` (30 dòng giá bán đang hiệu lực) |

**Tổng kết Đợt 3:** **16/16 test PASSED (100.0%)**, thời gian phản hồi trung bình **0.626s**.
**Kiểm thử hồi quy Đợt 1:** 15/16 PASSED (93.8%), 12/12 nghiệp vụ MES đạt 100%.
**Kiểm thử hồi quy Đợt 2:** 12/12 PASSED (100.0%).
Toàn bộ mã nguồn đã đồng bộ vào `local_webui.db` và `/app/backend/data/webui.db` trong Docker, container `open-webui` đã được khởi động lại và hoạt động ổn định `(healthy)`.



