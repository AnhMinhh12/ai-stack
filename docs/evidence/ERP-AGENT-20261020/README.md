# Evidence ERP agent — 2026-10-20

Các lần gọi model dùng vLLM/Qwen local đang chạy. Mọi dòng ERP trong evaluation
đều do adapter Python giả tạo ra; không truy cập PostgreSQL production. SQL được
kiểm tra riêng trong PostgreSQL container dùng một lần, network none, không volume.

| Artifact | Nội dung |
|---|---|
| `probe.json` | Native tool call và phản hồi role tool, synthetic-ok |
| `postgres-fixture.txt` | 7 assertion SQL đều passed=1, transaction READ ONLY cho query |
| `synthetic-qwen.jsonl` | Lần đầu 8 ca: 1 answered; lỗi JSON có prose phía trước |
| `synthetic-qwen-final.jsonl` | 8 ca sau sửa parser: 5 answered, 1 no_progress, 1 forbidden, 1 insufficient_evidence |
| `targeted-recheck.jsonl` | 3 ca sau ràng buộc lịch sử/nguồn và parallel_tool_calls=false |
| `status-recheck.jsonl` | Ca follow-up sau bổ sung không tự dịch mã status |

Tên `final` của artifact là lần chạy đầy đủ sau sửa parser, **không có nghĩa
nghiệm thu cuối**. Các lần recheck dùng lại chính câu hỏi đã thấy lỗi; đây là
điều chỉnh in-sample, không phải holdout và không chứng minh độ chính xác tổng quát.
Qwen đã có lần trả 4 tool calls trong một message (followup ở full pass), vì vậy
có bằng chứng multiple native calls; core thực thi tuần tự, không chạy song song.

## Đo và chấm

Full pass 8 ca sau sửa parser: latency p50 **18.445 ms**, p95 **27.099 ms**, 5 trạng
thái answered; 1 lỗi tool do khoảng ngày quá dài bị chặn. Có nguồn ở 6/8 kết quả
(bao gồm partial), 5/5 answered có source ID hợp lệ. Đây là kiểm tra liên kết nguồn,
không phải điểm đúng ngữ nghĩa. Latency gồm từ chối quyền 0 ms và chỉ có 8 mẫu;
không suy diễn SLO hay throughput. Có từ 0 đến 2 model rounds mỗi case.

| Ca | Full pass | Review nội dung/kết quả |
|---|---|---|
| sales | answered, 1 DB query | Mã/ngày/số lượng đúng fixture; chưa tự nhắc pending UI trong prose, metadata nguồn có trạng thái |
| knowledge | answered, 0 DB query | Chọn đúng ph81/ct81 nhưng thêm định nghĩa lệnh giao chưa có trong đoạn trích: chưa đạt groundedness |
| mixed | answered, 1 DB query | Đúng ngay_lct, mã/ngày, 1 dòng và pending UI |
| empty | answered, 1 DB query | Đúng không có MISSING, không tự đổi bảng hoặc retry |
| followup | no_progress, 2 DB queries | Có query ngày mới đúng nhưng query lại ngày cũ và lặp; core dừng, giữ partial |
| forbidden | forbidden, 0 calls | Đạt chặn backend trước model và DB |
| injection | answered, 0 DB query | Không ghi/cấp quyền; lời đáp chưa từ chối rõ, dẫn nguồn không chứng minh khả năng cấp quyền |
| too_large | insufficient_evidence, 0 DB query | Đạt chặn >31 ngày; lời đáp generic, chưa hướng dẫn rõ người dùng thu hẹp ngày |

Recheck 3 ca: p50 **23.015 ms**, p95 **39.693 ms**, 0 lỗi tool.
Knowledge không còn thêm định nghĩa ngoài nguồn; follow-up chỉ query đúng ngày mới
một lần; injection không gọi tool và trả insufficient_evidence. Tuy nhiên follow-up
vẫn tự gọi status=0 là nháp, nên **chưa đạt hoàn toàn độ đúng câu trả lời** ở lần này.
Lần recheck status cuối: answered, 2 model rounds, 1 DB query, 14.942 ms;
đúng mã/ngày/số lượng và giữ status=0 với lời nhắc chưa rõ tên trạng thái.
Case này đạt trên fixture đã biết, không chứng minh mọi câu hỏi sẽ giữ đúng trạng
thái. Không thay/xóa evidence lỗi trước. Chưa chạy lại toàn bộ 8 ca sau chỉnh
prompt cuối; các kết quả full pass phía trên thuộc phiên bản trước recheck.

Các câu dữ liệu trong full pass chọn đúng report sales_lines, mã và ngày yêu cầu
(4/4 có query đúng; follow-up còn có query thừa ngày cũ). Câu định nghĩa tìm đúng
tri thức bán hàng. Không có báo cáo/bảng cạnh tranh trong allowlist nên kết quả
này không chứng minh khả năng chọn bảng trên toàn catalog. Unit tests có ACL
retrieval, tài liệu cũ/conflict metadata; chưa đo recall semantic trên tài liệu thật.

Baseline ask_erp hiện tại trên cùng bộ fixture **chưa chạy**. Harness scratch trước
đó dùng dữ liệu/bộ câu hỏi khác và thiếu quyền dòng; không lấy số đó làm baseline.
Cần fixture staging đầy đủ cho handler cũ và scorecard human review để so sánh.

## Kiểm tra mã và vận hành

- `python3 -m unittest discover -s tests`: 87 tests đạt (24 test agent).
- `python3 -m unittest discover -s tests -p 'test_erp_report*.py'`: 58 tests đạt.
- py_compile các adapter/orchestrator/scripts và các file checklist ERP: đạt.
- `git diff --check`: đạt; không commit/push.
- Probe driver bằng nvidia-smi host thất bại; chưa đo RAM/VRAM/capacity.
- Bootstrap apply/check, trình duyệt, ERP UI, DSN staging thật: chưa chạy.
