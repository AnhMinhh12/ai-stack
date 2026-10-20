# Đối soát và tích hợp Qwen local — 20/10/2026

**Kết luận:** đã bổ sung lát cắt chạy được cho dòng phiếu xuất bán, vòng native tool
calling có ngân sách và quyền backend, adapter Open WebUI và profile staging riêng.
Đã kiểm thử Qwen thật bằng dữ liệu giả và SQL bằng PostgreSQL tạm cô lập. Chưa
nghiệm thu end-to-end trên ERP staging/UI, chưa triển khai profile vào runtime.
Không sửa dữ liệu production hoặc cấu hình chat đang dùng.

## 1. Bản đồ hiện trạng

| Phần | File/bằng chứng | Nhận xét |
|---|---|---|
| UI → tool → Qwen | `config/htmp-rag-models.json`, `functions/htmp_fast_rag.py`, `functions/htmp_postgres_query.py` | Profile htmp-nhanh gắn tool ask_erp, prompt yêu cầu đúng một call; router/handler cố định trước, planner SQL dự phòng sau |
| Model server | `docker-compose.yml` | Qwen/Qwen2.5-14B-Instruct; alias qwen2.5-14b; revision/tokenizer cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8; vLLM parser hermes, native auto tool choice; endpoint nội bộ http://vllm:8000/v1 |
| Probe thực tế | `docs/evidence/ERP-AGENT-20261020/probe.json`, `scripts/probe_qwen_tool_calls.py` | tool_calls[].function.arguments là JSON string; id liên kết role tool được server chấp nhận; probe đầu chưa chứng minh parallel calls; evaluation sau có nhiều calls trong một message, được chạy tuần tự |
| Context/tài nguyên | `docker-compose.yml` | Config max-model-len 32768, FP8 weight/KV, KV cache 64 GiB, max-num-seqs 20; đây là cấu hình, không phải đo capacity. nvidia-smi từ host thất bại kết nối driver trong phiên này; không suy ra RAM/VRAM trống |
| Hội thoại | `erp_ai/context.py`, `erp_ai/entities.py`, filter nhanh | Store in-memory có RLock, LRU 2000; key conversation_id/chat_id, chưa namespace theo user; có caller-provided conversation_id. Filter kế thừa mã/ngày theo câu hỏi trước |
| Streaming/hủy | `scratch_middleware.py`, `scratch_openai.py`, Compose Redis | Snapshot source có streaming và lưu stream; Redis giữ event. Không xác minh snapshot bằng phiên bản runtime/UI. Tool ERP dùng psycopg/urllib đồng bộ nên chưa chứng minh hủy xuyên suốt |
| Timeout/retry | `functions/htmp_postgres_query.py` | SQL default 15s, planner urllib 75s, tối đa 3 lần; có retry đổi SQL khi rỗng. Không có deadline chung của vòng nghiệp vụ |
| Log | `functions/htmp_fast_rag.py`, `functions/htmp_technical_rag.py` | Có request_id ở retrieval metadata; một số lỗi planner trả str(exc), chưa có thống kê ngân sách theo request |
| Tri thức | `functions/htmp_technical_rag.py` | Open WebUI get_sources_from_items, UserModel, BGE-M3/Qdrant; hybrid BM25 weight .5, k=10, rerank=5, threshold=.3. Profile htmp-ky tách khỏi ERP |

### Nhóm dữ liệu và quyền

`config/erp-reports/*.json`, `sql/erp-reports/*.sql`,
`docs/erp-screen-mapping.md` cung cấp metadata nguồn và mapping màn hình:

- Bán hàng: ph64/ct64 (đơn), ph96/ct96/ctkhgh (lệnh giao), ph81/ct81 (xuất bán).
- Mua hàng: ph91/ct91, ph94/ct94, ph77/ct77, dmgiamua/dmgiamuact.
- Kho: chứng từ nhập/xuất, tồn kho/lô/vị trí; nhật ký vận hành có manifest riêng.
- MES/khuôn/chất lượng: report sản xuất, khuôn, IQC/IPQC/OQC; không bật trong pilot.
- Header/detail thường nối stt_rec; cần ln để định danh dòng, không nối bằng số CT.
- `trusted_erp_user_id` dùng map ID/email phía server nhưng có shared-user fallback.
  Một số handler có userinfo/ds_branchs/kho; một số master-data và planner không
  nhận identity. SQL chỉ đọc không thay thế quyền bảng/hàng.

Schema kỹ thuật (tên bảng/cột/join) không chứng minh định nghĩa “đã giao”, “doanh
thu”, trạng thái ghi sổ hoặc hạt tổng hợp. Manifest và đối chiếu UI phải xác nhận
riêng. Không quảng bá các report pending_ui_validation là đã nghiệm thu.

### Markdown và thứ tự tin cậy

| Nguồn | Phạm vi/tin cậy |
|---|---|
| `docs/erp-screen-mapping.md`, `danh-sach-bang-tra-cuu.md` | Mapping/catalog có nguồn; ngày cập nhật trong tài liệu; không phải bằng chứng mọi query đúng UI |
| `config/erp-reports/*.json` + SQL | Contract do repo quản lý; validation label cần giữ nguyên |
| `docs/check-ui-erp.md`, `tests/erp-reports/*.json` | Case UI cụ thể; trạng thái có thể lệch manifest, không tự nâng cấp mức tin cậy |
| `docs/evidence/*` | Bằng chứng theo thời điểm và bộ lọc; không dùng thay định nghĩa nghiệp vụ |
| `README.md`, `RUNBOOK.md`, `PLAN.md` | Kiến trúc/vận hành; có mô tả lịch sử khác cấu hình Compose hiện tại |
| `scratch/erp-semantic-pilot/*`, `docs/archive/*`, transcript | Thử nghiệm/lịch sử, không tự ingest thành chỉ dẫn hoặc policy |

Ví dụ lệch đã thấy: README còn dòng nói Compose chưa enforce revision, trong khi
Compose đã pin revision; dashboard UI ghi có report đã xong nhưng manifest có thể
còn pending; hai tài liệu chỉ rõ việc này. Bản thử nghiệm scratch tự ghi không có
quyền dòng. Không coi việc SQL execute thành công là độ đúng nghiệp vụ.

## 2. Phần đã tích hợp và quyết định

- `erp_ai/agent.py`: vòng async model → validate tool → backend → role tool → model;
  giới hạn lượt/call/DB/thời gian/context, dừng lặp, giữ verified_results, bỏ kết quả
  muộn, log không chứa prompt/dữ liệu. Tuần tự tool calls để tránh giả định độc lập.
- `erp_ai/agent_backend.py`: retrieval từ khóa tiếng Việt có ACL, schema chọn theo
  câu hỏi, describe report, query_allowed_records. Không cho model gửi SQL/path/user ID.
- `erp_ai/agent_runtime.py`: httpx và psycopg async, staging DSN riêng, read-only
  transaction, statement/lock timeout, không fallback credential production.
- `config/erp-agent.json`, `docs/knowledge/erp-sales-agent.md`: allowlist nguồn có
  version/ngày/nhóm/quyền/đoạn trích; revision theo SHA-256, conflict_group có chủ đích.
- `sql/erp-reports/agent-sales-lines.sql`: tái dùng bảng/khóa/hạt của bảng kê xuất bán;
  parameterized query, hạn ngày, branch AND warehouse, field allowlist, LIMIT.
- `functions/htmp_erp_agent.py`, `functions/htmp_erp_agent_filter.py`,
  `config/htmp-erp-agent-profile.json`: adapter/tool/filter/profile staging, không
  thay profile hiện hữu. Identity và lịch sử do server inject, không có conversation_id
  tự do; không lưu state chung nên tránh kế thừa qua user.

Lát cắt được chọn từ mapping thực của dự án: ph81 JOIN ct81, từng dòng xuất bán,
ngày ngay_lct, ma_gd != 4. Trả status gốc, không tự gọi là giao thực tế/đã ghi sổ.
Danh sách quyền rỗng chặn trừ superuser: bảo thủ hơn handler cũ, cần nghiệm thu
ý nghĩa ds_stocks. Không query bảng ngoài lát cắt hay tự đổi sang bảng snapshot.
Không sinh link bản ghi; cần route map đã xác nhận mới bổ sung sau.

Mở rộng report qua config và SQL đã review với cùng hợp đồng bộ lọc, không sửa
vòng điều phối. Bộ lọc/tool mới cần adapter và test riêng. SQL config là code tin
cậy; không phải sandbox SQL tự do. Chưa nối semantic retrieval hiện có vì chưa
có bridge ACL kho tài liệu ↔ quyền report. Keyword retrieval đủ cho pilot một report,
không có bằng chứng để tuyên bố tối ưu cho toàn bộ catalog.

## 3. Kiểm thử và giới hạn nghiệm thu

| Hạng mục | Trạng thái |
|---|---|
| Native tool probe trên Qwen thật | Đạt; synthetic, call đầu 1,462s |
| Unit/integration fake model cho agent | Đạt: 24 tests, gồm budgets, lỗi arguments, ACL, context, empty, repeat, cancel, late result, nguồn giả, conflict metadata |
| Regression ERP hiện có | Đạt: 58 tests `test_erp_report*.py`; toàn suite 87 tests đạt |
| SQL trên PostgreSQL cô lập | Đạt: 7 assertions, branch AND warehouse, empty scope, superuser, unknown user, kho khác, mã không tồn tại, LIMIT |
| Qwen thật + DB giả | 8 ca và các recheck; follow-up cuối giữ đúng status=0; chưa có holdout/full rerun sau prompt cuối, xem `docs/evidence/ERP-AGENT-20261020/README.md` |
| PostgreSQL ERP staging + tài khoản SELECT-only thực | Chưa chạy; chưa cung cấp DSN/grants staging |
| So sánh baseline ask_erp bằng cùng fixture/database | Chưa chạy; không có fixture đầy đủ cho schema/handler baseline; không so số liệu scratch khác bộ câu hỏi |
| Browser, UI parity, hủy từ UI | Chưa chạy |
| Bootstrap apply/check | Chưa chạy; chưa deploy profile mới |
| Capacity/RAM/VRAM/concurrent load | Chưa chạy; latency synthetic đơn luồng không phải SLO |

`tests/erp_agent_postgres_fixture.py` chỉ tạo dữ liệu giả trong DB tạm; không ghi
production. Test model transport và query ACL tách biệt; chưa kiểm chứng async
psycopg cancellation thực tế qua mạng PostgreSQL hay việc WebUI inject history.

Toàn suite ban đầu phát hiện assertion cũ yêu cầu đúng 3 case trong khi fixture
`bang-ke-phieu-nhap-kho.json` đã có 4. Đã sửa
`tests/test_all_pending_erp_report_artifacts.py` thành ít nhất required_comparisons,
giữ yêu cầu tối thiểu 3 và mọi kiểm tra SQL/manifest khác. Không sửa fixture cũ.

Bộ câu hỏi Qwen có: dòng xuất bán (join hai bảng), định nghĩa Markdown/phân biệt
lệnh giao, tài liệu+kết quả, mã không tồn tại, follow-up ngày, user bị chặn,
prompt injection yêu cầu DELETE/cấp quyền và khoảng ngày quá lớn. Unit tests bổ sung
nhiều calls, arguments sai, conflict/stale metadata, timeout, kết quả muộn.
Hỏi dữ liệu một bảng thuộc nhóm khác và tự phát hiện mâu thuẫn chưa gắn metadata
nằm ngoài lát cắt; cần bổ sung trước khi tuyên bố bao phủ đa nghiệp vụ.

## 4. Điều kiện phát hành còn lại

Cấp DSN staging SELECT-only và map user ID staging (không gửi secret trong chat),
xác minh ds_stocks, chạy cùng bộ câu hỏi với baseline trên snapshot giả/staging
đầy đủ, chấm đúng dữ liệu và source, bootstrap profile riêng, kiểm tra UI ít nhất
ba case cùng quyền/bộ lọc. Cần thêm user bị hạn chế, chứng từ nhiều dòng, trạng thái
nháp/hủy và test hủy qua UI. Sau đó mới quyết định triển khai production.

Hướng dẫn cấu hình, thêm bảng/tài liệu và xem log:
[`erp-agent-operations.md`](erp-agent-operations.md).
Các file scratch/evidence đã có trước nhiệm vụ được giữ nguyên; không commit/push.

## 5. Bổ sung định dạng nhập kho theo prompt archive

`erp_ai/presentation.py` tạo hợp đồng `blocks` (`summary`, `table`, `chart`,
`warning`) từ `verified_results`, kèm `display_markdown` dạng bảng GFM để profile
Open WebUI hiện tại hiển thị. Bảng có 7 cột theo yêu cầu, số dòng toàn kỳ,
`has_more`, bộ lọc, thứ tự, nguồn; ô dữ liệu được escape. Biểu đồ thanh tự sinh
theo ngày hoặc kho khi có ít nhất hai nhóm cùng đơn vị; trường hợp bảng bị cắt
chỉ dùng dòng đang hiển thị và ghi rõ phạm vi. `agent-receipt-lines.sql` thêm
`ln` và `dvt`; backend bỏ giới hạn cứng 5 dòng nhập kho, giữ trần cấu hình và
cảnh báo phần bị cắt. Đầu ra cuối cho nhập kho dùng số liệu do tool xác minh,
không dùng lời kể của model để dựng bảng/biểu đồ.

Compose nay để agent tắt mặc định; DSN staging và grants phải được cấu hình riêng,
không lấy lại credential ERP chung. Kiểm thử hiện tại: 93 unit tests đạt,
13 assertions SQL trên PostgreSQL cô lập đạt, Compose syntax và `git diff --check`
đạt. Probe Qwen thật bằng dữ liệu giả chạy lại ngày 20/10: tool_calls chứa
`function.arguments` là JSON string, role tool được nhận, latency 1,453 giây.
Chưa chạy browser, câu hỏi nhập kho end-to-end trên Qwen sau thay đổi định dạng,
hoặc DB staging. UI vẫn
phụ thuộc model ngoài sao chép `display_markdown`; chưa có renderer tùy biến đảm bảo
hiển thị block JSON trực tiếp, nút xem thêm, hay kiểm tra trên màn hẹp.

## 6. Rich UI embed thử nghiệm

`erp_ai/rich_ui.py` và `functions/htmp_erp_agent.py` hiện trả bảng cùng biểu đồ
Chart.js bằng `HTMLResponse` inline từ các block đã xác minh. Nếu Chart.js CDN
không tải được, iframe vẫn hiển thị thanh CSS và số liệu. Profile/tool staging
trong Open WebUI đã được cập nhật bằng bootstrap; `bootstrap check: PASS`,
`max_tokens=6000`. Handoff `HTMLResponse` qua middleware của container đã đạt
với dữ liệu giả. Toàn suite 94 tests đạt. Chưa kiểm tra chart bằng browser hoặc
truy vấn ERP thật sau thay đổi này; không coi handoff backend là nghiệm thu UI.
