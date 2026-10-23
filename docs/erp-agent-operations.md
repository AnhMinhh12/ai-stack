# Vận hành ERP agent nhiều lượt — staging

Phiên bản 0.1, 2026-10-20. Luồng hiện tại không tự chuyển sang agent mới.
`functions/htmp_erp_agent.py` là adapter Open WebUI riêng; `erp_ai/agent_runtime.py`
là entrypoint Python async có thể gọi trực tiếp. Không có endpoint HTTP vô danh.

## Cấu hình

Runtime cần Python >=3.11, httpx và psycopg 3 (đã dùng trong stack hiện tại).
Mount/copy cây asset dưới một thư mục chỉ đọc, giữ nguyên đường dẫn tương đối:
`config/erp-agent.json`, `docs/knowledge/erp-sales-agent.md`,
`sql/erp-reports/agent-sales-lines.sql`. Đặt `HTMP_AGENT_ROOT` trỏ tới thư mục đó.
Package `erp_ai` phải ở PYTHONPATH; Compose hiện đã bind mount package này.

Các biến do quản trị viên cấu hình trong **staging**:

| Biến | Ý nghĩa |
|---|---|
| `HTMP_AGENT_ENABLED=1` | Bật luồng riêng; mặc định tắt |
| `HTMP_AGENT_ROOT` | Root của asset đã review |
| `HTMP_AGENT_DB_DSN` | PostgreSQL staging, tài khoản SELECT-only; bắt buộc khi bật agent, không fallback DB production |
| `HTMP_AGENT_GRANTS` | JSON server-owned: `{"<OpenWebUI user id>":{"erp_user_id":123,"reports":["sales_lines"]}}` |
| `HTMP_AGENT_MODEL_URL` | Mặc định `http://vllm:8000/v1/`; chỉ trỏ endpoint nội bộ tin cậy |
| `HTMP_AGENT_MODEL` | Mặc định `qwen2.5-14b` |
| `VLLM_API_KEY` | Secret hiện có, không ghi vào source/log |

Grant dùng ID phiên đăng nhập, không dùng user ID hoặc conversation ID model tự gửi.
Không dùng fallback `HTMP_ERP_SHARED_USER_ID`. Danh sách grant pilot là lớp quyền
báo cáo bổ sung; quyền dòng được kiểm tra lại bằng userinfo trong từng query.
SQL pilot cố ý chặn scope rỗng (trừ `is_super=1`); cần xác minh ý nghĩa `ds_stocks`
với quản trị ERP trước khi cấp quyền thật. Không thay đổi handler cũ.

## Đăng ký trên staging

Cấu hình riêng `config/htmp-erp-agent-profile.json` chỉ chứa tool/profile mới.
Có thể dùng `scripts/openwebui_bootstrap_runtime.py` trong container staging sau
khi copy profile, `functions/htmp_erp_agent.py`, `functions/htmp_erp_agent_filter.py` và runtime script vào cùng thư mục:

```bash
docker exec open-webui mkdir -p /tmp/erp-agent
docker cp scripts/openwebui_bootstrap_runtime.py open-webui:/tmp/erp-agent/
docker cp config/htmp-erp-agent-profile.json open-webui:/tmp/erp-agent/
docker cp functions/htmp_erp_agent.py open-webui:/tmp/erp-agent/
docker cp functions/htmp_erp_agent_filter.py open-webui:/tmp/erp-agent/
# Thay email bằng tài khoản quản trị sở hữu profile trên staging.
docker exec open-webui python /tmp/erp-agent/openwebui_bootstrap_runtime.py \
  --config /tmp/erp-agent/htmp-erp-agent-profile.json \
  --source-dir /tmp/erp-agent --owner-email '<staging owner>'
docker exec open-webui python /tmp/erp-agent/openwebui_bootstrap_runtime.py \
  --config /tmp/erp-agent/htmp-erp-agent-profile.json \
  --source-dir /tmp/erp-agent --owner-email '<staging owner>' --check
```

Lệnh apply ghi DB Open WebUI staging; `--check` chỉ đọc và xác nhận content,
tool specs, model params/tool/filter IDs. Nếu giao diện còn giữ profile cũ,
tải lại trang; cần thiết mới `docker restart open-webui` (giữ nguyên env của
container hiện tại). Không dùng `docker compose up -d` khi chưa cấu hình lại
`HTMP_AGENT_ENABLED`, DSN và grants trong môi trường Compose: Compose mặc định
tắt agent.
Runtime bootstrap hiện cấp quyền nhìn thấy tool cho mọi user; backend vẫn chặn
mọi người chưa có grant. Chỉ cài profile vào staging, không dùng bootstrap chính
để nghiệm thu: script bootstrap chính có thao tác copy/xóa asset cả khi `--check`.
Cần kiểm tra model/profile trên UI cùng injected `__user__`/`__messages__`, hủy
request qua UI, nguồn trích dẫn và quyền của hai user trước khi phát hành.

## Giới hạn và nguồn

`config/erp-agent.json`: tối đa 6 lượt model, 10 tool calls, 2 DB queries,
60 giây toàn request, 50 dòng, 12.000 ký tự/result, 48.000 ký tự context.
Đây là **giới hạn pilot**, chưa phải SLO đo tải. Context dùng giới hạn ký tự
bảo thủ, không phải phép đo token chính xác. HTTP timeout 30 giây; SQL timeout
10 giây, lock timeout 1 giây. Mỗi query tối đa 31 ngày. Không retry ngầm khi rỗng.
Adapter model gửi parallel_tool_calls=false; core vẫn kiểm tra được nhiều calls
trong một response và thực thi tuần tự. Không stream token model ra UI; chỉ trả kết quả đã qua vòng kiểm tra.

Tool trả `blocks` có cấu trúc và `display_markdown` làm dự phòng. Với
`query_receipt_lines`, backend dựng bảng 7 cột từ dòng SQL đã xác minh, tổng từ
window aggregate và nguồn theo report. Bảng giữ thứ tự ngày giảm dần, hiển thị
tối đa giới hạn `rows`; `has_more` cảnh báo khi còn dòng. Chưa có nút phân trang
hoặc xuất CSV. Bảng có nút tải Excel, Word và PDF; các file chỉ chứa những dòng
đã được trả về và ghi chú rõ khi báo cáo còn dòng chưa xuất. Khi có ít nhất hai nhóm và cùng đơn vị, bộ dựng biểu đồ tự chọn
cột cho nhiều kho trong cùng ngày, đường cho nhiều ngày, tròn cho câu hỏi tỷ
trọng theo kho khi dữ liệu đầy đủ (2–8 kho). Không gọi thêm model để chọn loại.
Rich UI có nút Cột / Đường / Tròn để đổi loại ngay trong trình duyệt, không
truy vấn lại; nút Tròn bị khóa khi dữ liệu chỉ là trang đầu hoặc không đủ điều
kiện tính tỷ trọng.
Khi bảng bị cắt, biểu đồ ghi rõ chỉ dùng các dòng đang hiển thị và không vẽ
biểu đồ tròn; khi đủ dòng, tổng biểu đồ phải khớp tổng tool. Agent trả
ngay kết quả nhập kho đã xác minh sau một lượt model và một truy vấn DB; không
gọi model lần hai chỉ để viết lại bảng, tránh timeout sau khi truy vấn thành công.
Adapter tool trả `HTMLResponse` với `Content-Disposition: inline` để Open WebUI hiển thị bảng và
Chart.js trong Rich UI iframe. HTML lấy từ block đã xác minh; model ngoài chỉ
nhận status và cờ Rich UI đã hiển thị (không nhận lại số liệu hoặc nguồn để
tránh lặp câu trả lời). Embed gửi `iframe:height` theo chiều cao thực để không
cắt bảng. Frontend riêng profile ERP neo vị trí ở câu hỏi khi gửi và khi embed
xuất hiện, không tự cuộn xuống cuối; người dùng cuộn trang chat để đọc toàn bộ
bảng/biểu đồ. Chart.js được ghim phiên bản 4.5.1 qua CDN;
Nếu trình duyệt không tải được, embed vẫn hiển thị thanh CSS và số liệu. Mã
nguồn `records:*` và trạng thái đối chiếu UI vẫn ở metadata nội bộ, không in
thành dòng dưới bảng. Cần nghiệm thu trên trình duyệt thực tế, gồm network/CSP
và màn hình hẹp.

Vòng dừng khi lặp cùng tool/tham số, hết lượt hoặc hết ngân sách. Kết quả tool
thành công được giữ trong `verified_results`; `status` chỉ rõ timeout/giới hạn.
Cancellation lan xuống async HTTP/psycopg; kết quả đến sau deadline bị bỏ.
Không ghi prompt, arguments, rows, secret hay lỗi transport nguyên văn vào log.
Logger `erp_ai.agent` có request_id, tool, source_ids, elapsed_ms và error code.

Nguồn Markdown chỉ được nạp từ allowlist config, có title/section, path,
updated, domain, access, status, excerpt và SHA-256 revision. Retrieval từ khóa
chuẩn hóa tiếng Việt; tối đa 3 đoạn và 3 schema. Không đọc toàn repository.
Nguồn `superseded` được xếp sau `current`; `conflict_group` báo mâu thuẫn đã
được biên tập đánh dấu. Chưa tự phát hiện mâu thuẫn ngữ nghĩa chưa gắn metadata.
Hybrid RAG hiện có của Open WebUI được giữ riêng vì ACL kho tri thức chưa có
bridge tới report grants. Không reuse index bỏ qua quyền để tăng recall.

Final answer nhận một JSON duy nhất ở cuối (loại bỏ prose/Markdown ngoài JSON) và source IDs đã có trong request. IDs lạ hoặc URL
model sinh bị từ chối. Kiểm tra nguồn không chứng minh mọi câu diễn giải là đúng;
cần chấm nội dung và đối chiếu UI. Không sinh deep link bản ghi trong pilot.

## Mở rộng

Thêm report trong `erp-agent.json`: ID, title, bảng/khóa nối/fields, đường dẫn
manifest và SQL cố định, thứ tự parameters, validation. Chỉ query_file được
admin review mới được thực thi. Giữ hợp đồng parameter hiện có (`user_id`,
`material`, `date_from`, `date_to`, `row_limit`) để thêm report không sửa vòng lặp.
Cần hợp đồng bộ lọc mới thì thêm adapter/spec và test, không để model tự đưa SQL.
Mỗi SQL mới phải tự kiểm tra quyền trước LIMIT, dùng bind parameters, transaction
READ ONLY, danh sách trường xuất allowlist và test âm về ACL. Runtime không phải
sandbox cho SQL config độc hại; config/SQL là code tin cậy do admin quản lý.

Thêm tài liệu vào allowlist với metadata quyền và hiệu lực. Đánh dấu tài liệu
cũ hoặc conflict_group; không tự coi ghi chú scratch/evidence là tri thức chuẩn.
Không thêm tool ghi, cấp quyền hoặc sinh URL từ chuỗi tự do của model.

## Chạy lại kiểm thử

```bash
python3 -m unittest discover -s tests -p 'test_erp_agent.py'
python3 -m unittest discover -s tests -p 'test_erp_report*.py'
bash scripts/test_erp_agent_postgres.sh
python3 scripts/build_erp_agent_eval_bundle.py > /tmp/erp-agent-eval.py
docker exec -i open-webui python - < /tmp/erp-agent-eval.py
```

Lệnh cuối gọi Qwen thật nhưng adapter DB hoàn toàn giả. Có thể chọn case bằng
`docker exec -e HTMP_AGENT_EVAL_CASES=sales,followup ...`.
`tests/erp_agent_postgres_fixture.py` sinh setup và assertions SQL **chỉ dành cho
PostgreSQL rỗng dùng một lần**, không chạy trên DB dự án. Evidence có kết quả
7 assertions trong container `--network none`, không volume, tự xóa.
