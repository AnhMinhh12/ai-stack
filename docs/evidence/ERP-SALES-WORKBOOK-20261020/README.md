# Test sales_question.xlsx và đối chiếu DB — 20/10/2026

**Kết luận: luồng ERP nhiều lượt vừa bổ sung chưa đạt bộ 18 câu này.**
Theo tiêu chí đúng nguồn, đúng dữ liệu, đúng hạt/phạm vi và trả lời đủ ý:
**0 câu đạt đầy đủ; 2 khớp một phần; 9 sai/lệch nghiệp vụ; 7 chưa trả lời.**
Đây là kết quả của agent mới với allowlist duy nhất `sales_lines`, không phải
kết luận rằng toàn bộ handler `ask_erp` đang có đều sai, và không phải kết luận
DB thiếu dữ liệu. Phần lớn câu hỏi cần dataset chưa được tích hợp vào agent mới.

Bàn giao:

- [Excel đối chiếu 18 câu](sales_question_doi_chieu.xlsx): câu hỏi, câu đã điền tham
  số, đáp án model, trạng thái kỹ thuật, kết luận, DB, nhận xét, số lượt và latency.
  Có thêm sheet SQL/DB và điều kiện kiểm thử. File gốc được giữ nguyên.
- [Bảng đối chiếu Markdown](comparison.md), [CSV](comparison.csv).
- [Kết quả model và tool đầy đủ](agent-results.jsonl).
- [22 truy vấn DB đối chiếu độc lập](db-reference.jsonl); tất cả chạy thành công.
- [Chấm từng câu](review.json).

## Phạm vi và phương pháp

Đọc đủ 18 câu từ cột B của `sales_question.xlsx`. Cột C là ghi chú màn hình/
nghiệp vụ của người dùng, chỉ dùng chấm bài, **không đưa cho model**. Không sửa
prompt/core/SQL của agent trong lúc chạy, không bổ sung tool để giúp một câu đỗ.
Model không được xem SQL tham chiếu, kết quả gold, hay tổng kiểm toán bên dưới.

Các câu đều là template, thiếu tham số cụ thể. Đã kiểm tra DB trước và bổ sung
tham số phù hợp riêng từng câu:

| Tham số | Giá trị |
|---|---|
| Mã hàng | QC7-5146-000 |
| Khách khai báo của mã | KH0015 — Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long |
| Khuôn đã xác minh liên kết mã hàng | K_QC5-2919-000-V1 |
| Lệnh giao cụ thể cho câu 13 | 001-2610-001811 |
| Kỳ mặc định cho câu cần khoảng ngày | 01–20/10/2026 |
| Kỳ so sánh câu 10 | 01–20/09 với 01–20/10/2026 |
| Ngày tham chiếu | 20/10/2026 |

Không truyền khuôn/khách/ngày không liên quan vào mọi câu. Câu “gần nhất” không
được mặc định giới hạn tháng; nếu model tự bó về một ngày thì ghi nhận trong chấm.
Câu tên khách dùng tên đầy đủ từ DB, không dùng tên viết tắt mơ hồ. Bộ thực thể
này khác fixture không liên kết ở thử nghiệm scratch trước đó; không so tỷ lệ giữa
hai bài như cùng một benchmark.

Bài test gọi **Qwen local thật + PostgreSQL thật**, dùng core `run_agent`, adapter
`ReportBackend` và query SQL cố định hiện tại trong harness riêng. Không chạy qua
browser hoặc profile Open WebUI; chưa chấm thêm bước outer model hiển thị tool.
Không bật `HTMP_AGENT_ENABLED`, không sửa DB cấu hình WebUI hay cấp thêm quyền.

Runtime hiện không có map/grants cá nhân mới, chỉ có shared ERP identity đã cấu
hình. Preflight xác nhận identity này tồn tại và là ERP superuser. Harness dùng
đúng scope hiện có, không bịa user ID khác. Reference rộng sẽ fail closed nếu
identity cấu hình không phải superuser. **Đây là kiểm toán bởi operator, không phải
nghiệm thu ACL của một người dùng bị giới hạn.** Tài khoản kết nối DB hiện có,
transaction READ ONLY; không gọi stored function hoặc SQL sinh tự do bởi model.
Mọi giá trị lọc được bind parameters. Timeout SQL 10–15 giây, lock timeout 1 giây.

22 truy vấn tham chiếu chạy trong một snapshot READ ONLY REPEATABLE READ lúc
**20/10/2026 10:44:06.726773 +07:00**. Model chạy sau đó trên DB đang hoạt động;
không dùng chung snapshot dài cho cả đợt. Mỗi query agent có một aggregate độc lập
trong **cùng snapshot của query đó** để kiểm tra toàn bộ số dòng/số lượng trước
LIMIT; tổng này chỉ ghi vào evidence, không đưa lại cho model.

## Kết quả kỹ thuật khác với đúng nghiệp vụ

| Chỉ số | Kết quả |
|---|---:|
| Câu đã chạy | 18/18 |
| status=answered | 11 |
| invalid_final | 5 |
| insufficient_evidence | 1 |
| backend_error | 1 |
| Tổng model rounds | 39 |
| Tổng tool calls | 21 |
| Truy vấn DB của agent | 13 |
| Lỗi arguments/tool được chặn | 2 |
| Latency p50 / p95 | 21,481 / 59,899 giây |
| Câu answered có source IDs hợp lệ | 11/11 |
| Đạt đầy đủ nghiệp vụ theo tiêu chí trên | 0/18 |

Hai request model chạy đồng thời. Giữ nguyên limit pilot: 6 rounds, 10 calls,
2 DB queries, 60 giây/request, 50 dòng, 12.000 ký tự/result; HTTP 30 giây,
max_tokens=900. Các query rộng fetch 51 dòng rồi adapter còn rút xuống 41 dòng do
ngân sách ký tự; `has_more=true` đã được truyền cho model. Latency này có điều kiện
riêng, không phải SLO hay phép so sánh baseline. `backend_error` ở câu 6 không có
chi tiết exception trong log hiện tại; không tự quy là lỗi DB hay transport.

## Những sai lệch quyết định

1. **MOQ:** model lấy min lượng xuất = **420 PCS**, nhưng bảng giá quy định
   **sl_min=1 PCS, gia=0,08563 USD**, hiệu lực 25/09–31/12/2026. Sai nguồn nghiệp vụ.
2. **Tổng xuất kỳ:** model trả **14.400 PCS**; 41 dòng nó nhận chỉ cộng được
   **11.880**, còn toàn bộ 303 dòng là **82.380 PCS**. Vừa sai phép cộng, vừa bỏ
   `has_more=true`. `SUM(tien2)` tham chiếu là **157.711.964,104 nội tệ**.
3. **So sánh kỳ:** model trả cả hai kỳ **12.300 PCS**, nói tương đương. DB là
   **84.840 → 82.380 PCS** và `SUM(tien2)` **175.446.405,12 → 157.711.964,104**.
4. **Tồn kho:** model trả **2.520 PCS**, là lượng xuất bán ngày 20/10. DB có
   tồn sổ **6.280 PCS** và tem hoạt động **16.660 PCS**; đây là hai chỉ tiêu khác nhau.
5. **Khách hàng:** model nói không tìm thấy theo tên, trong khi dmkh có **KH0015**.
   Không tìm thấy trong schema/Markdown hạn chế không đồng nghĩa DB không có.
6. **Trạng thái lot:** model nhìn `ph81.status=2`, nhưng QC phải tra
   `intem_log.status_qc`. Các lot mẫu đang có **status_qc=3 — OK**; không tự ánh xạ
   status chứng từ sang trạng thái QC.

Hai câu khớp một phần: câu 3 trả các phiếu thật cùng ngày nhưng chưa chọn lần
cuối và không giải thích lot trống; câu 5 trả đúng mã KH0015 nhưng suy từ giao dịch
xuất trong ngày thay vì khách khai báo ở dmvt/dmkh, thiếu tên khách. Vì vậy không
đếm thành hai case nghiệm thu đầy đủ.

Một số câu cần thêm hợp đồng nghiệp vụ dù DB có một phần dữ liệu: lịch sử revision
DO/FCST; tuổi thọ khuôn (không đồng nhất shot bảo hành với tuổi thọ tối đa); quy đổi
pallet với hệ số đang 0; mapping die_no → khuôn; “giá 0” và “chưa link giá”; NG so
với giao thiếu cùng mã giao dịch 10 và yêu cầu trả so với nhập trả thực tế. Không
chấm công thức suy đoán là đáp án chuẩn chỉ vì SQL chạy được.

## Việc cần sửa trước khi mở rộng sử dụng

- Route theo capability/metric của dataset: câu BOM, MOQ, tồn, QC không được đưa
  vào tool xuất bán. Ngoài phạm vi phải nói rõ tool chưa hỗ trợ, không nói DB rỗng.
- Aggregate/count/so sánh phải tính ở backend trên toàn bộ scope; không để model
  cộng trang rows. Chặn kết luận tổng kỳ từ kết quả `has_more=true` bằng kiểm tra
  có thể thực thi, không chỉ bằng prompt.
- Tái dùng handler/SQL hiện có có quyền đã xác minh; lần lượt tích hợp BOM, bảng
  giá, master khách, kho/tem/QC, đơn/lệnh. Thêm expected metric/grain/source vào
  contract để không coi source ID hợp lệ là đủ xác nhận câu trả lời.
- Chạy lại cùng fixture và thêm holdout sau sửa; so sánh riêng với handler hiện
  hữu. Không triển khai production dựa trên bộ kết quả hiện tại.

## Tái chạy

```bash
python3 scripts/evaluate_sales_workbook.py --bundle > /tmp/erp-workbook-run.py
docker exec -e ERP_WORKBOOK_MODE=references -i open-webui python - \
  < /tmp/erp-workbook-run.py > /tmp/workbook-db-reference.jsonl
docker exec -i open-webui python - \
  < /tmp/erp-workbook-run.py > /tmp/workbook-agent-results.jsonl
```

Có thể thêm `-e ERP_WORKBOOK_CASES=2,4,14` để chọn câu. Mỗi lần chạy lại cần lưu
thư mục evidence mới và chấm lại dữ liệu thay đổi. Không ghi đè lần chạy này.
`python3 scripts/report_sales_workbook.py` dựng lại XLSX/CSV/Markdown từ evidence
và review đã lưu. XLSX đã kiểm tra cấu trúc ZIP/XML, 3 sheet, đủ 18 dòng đối chiếu;
chưa mở bằng ứng dụng Excel/browser. Chưa commit/push.
