## Cập nhật giao diện HTMP Speed — 2026-09-10

- Open WebUI chạy image nội bộ `open-webui-htmp:speed-selector`. Component chọn model được thay bằng `HTMP` kèm dropdown `Speed`; chọn `Nhanh` ánh xạ tới `htmp-nhanh`, chọn `Kỹ` ánh xạ tới `htmp-ky`. Hai profile dùng cùng Qwen và knowledge `htmp`, không tải thêm model GPU.
- Source patch có thể tái tạo ở `scripts/patch_openwebui_speed_selector.pl`; Dockerfile runtime ở `Dockerfile.openwebui-speed-runtime`. Build/frontend đã xác nhận và container Open WebUI healthy sau rollout.

## Cập nhật hai chế độ RAG — 2026-09-10

- Đã tạo hai workspace model dùng chung `qwen2.5-14b` và knowledge `htmp`:
  - `HTMP Nhanh` (`htmp-nhanh`): vector-only, lấy tối đa 6 đoạn ngữ cảnh, không chạy hybrid/reranker; giới hạn output 600 token.
  - `HTMP Kỹ` (`htmp-ky`): giữ hybrid search + local reranker hiện hữu; giới hạn output 1,200 token. Đây là lựa chọn ưu tiên khi cần đối chiếu kỹ tài liệu nội bộ và chấp nhận thời gian chờ lâu hơn.
- `HTMP Nhanh` dùng filter theo từng model (`htmp_fast_rag`), không phải sửa cấu hình RAG dùng chung. Filter gọi helper có kiểm tra quyền truy cập của Open WebUI, rồi loại attachment đã xử lý để ngăn pipeline global chạy lại hybrid search lần hai. Vì vậy mode Nhanh và Kỹ không làm thay đổi nhau.
- Đã kiểm tra sau restart: 8/8 service healthy; hai model active, knowledge gắn sẵn và filter nạp được. Chưa coi đây là kết quả SLO: cần người dùng thử cùng một câu hỏi đại diện ở cả hai mode, ghi TTFT/E2E và đánh giá câu trả lời trước khi chốt ngưỡng cho khoảng 50 người dùng.

## Router truy vấn ERP theo thực thể và ngữ cảnh chat — 2026-09-16

**Mục tiêu:** người dùng hỏi theo ngôn ngữ tự nhiên và follow-up trong cùng chat;
không cấu hình theo từng câu hỏi, không để LLM tự sinh SQL/kết luận dữ liệu ERP.

### Quyết định kỹ thuật

- Router chung trích `mã vật tư`, `số chứng từ`, ngày, kho, khách hàng và chỉ tiêu
  từ câu hiện tại. Mọi cặp `mã vật tư + số chứng từ` phải dùng truy vấn SQL cố định,
  tham số hóa; không rơi vào SQL planner.
- Tool nhận thêm `context` do model truyền từ các lượt trước. Với câu follow-up chỉ
  có “chi tiết”, “thì sao”, “của nó”, model phải hợp nhất context thành một câu truy
  vấn hoàn chỉnh trước khi gọi tool. Không hỏi lại các điều kiện đã xuất hiện trong chat.
- Manifest vẫn là cấu hình một lần theo màn hình ERP. Từ điển thực thể, resolver
  ngữ cảnh và router dùng chung cho mọi report; không thêm nhánh theo cách diễn đạt
  cụ thể của người dùng.
- Kết quả tool mang metadata nguồn, filter hiệu lực, hàng chi tiết và aggregate.
  LLM chỉ trình bày kết quả; không được thay thế hoặc phủ nhận kết quả tool.

### Hạng mục thực hiện và acceptance

| ID | Hạng mục | Điều kiện pass | Trạng thái |
| --- | --- | --- | --- |
| ERP-R1 | Entity extractor chung | Nhận mã chữ-số/hyphen, số chứng từ, ngày, tên vật tư và các cột UI không phụ thuộc câu chữ | `partial — unit test pass; exact-name resolver runtime pass` |
| ERP-R2 | Context resolver | Follow-up kế thừa mã/số CT/ngày/kho từ context đã truyền; thiếu dữ kiện thật mới hỏi lại | `partial — runtime tool + injected chat_id pass` |
| ERP-R3 | Deterministic router | Có `ma_vt + so_ct` hoặc `ma_vt + ngày` thì chỉ chạy SQL cố định đúng điều kiện; không gọi planner | `partial — runtime query pass` |
| ERP-R4 | Output contract | Trả detail + aggregate + filter hiệu lực; không xuất JSON/tool instruction cho người dùng | `partial — validated payload runtime pass` |
| ERP-R5 | Eval regression | Fixture gồm VGU1A423, VGU1A527, VGW1A610-1, tên vật tư, chứng từ tồn tại/không tồn tại và follow-up | `partial — 10 unit tests pass; runtime name/date test pass` |
| ERP-R6 | Runtime rollout | Bootstrap, test tool thật read-only, kiểm thử UI multi-turn và rollback artifact | `partial — bootstrap + tool state test pass; UI binding pending` |

**Không chấp nhận:** sửa code/manifest chỉ để nhận một câu hỏi mới. Nếu câu hỏi mới
không qua router, bổ sung rule ở entity extractor/router chung và fixture regression.
**Giới hạn còn mở:** `chat_id` đã được Open WebUI inject server-side vào tool và runtime state test đã pass. Cần kiểm thử UI multi-turn thực tế, persistence qua restart và thay thế in-memory state bằng Redis trước khi chạy nhiều replica.
**Sửa nguồn dữ liệu 2026-09-16:** `Mã VV` của Nhật ký nhập xuất tồn là `ct70.ma_vv`, không phải `dmvt.ma_vv`. Câu hỏi theo cột UI nay chọn cột từ manifest và truy vấn nguồn giao dịch; khi thiếu ngày/số chứng từ, kết quả trả các giá trị phân biệt kèm số dòng và nêu rõ không thể kết luận một dòng duy nhất.

**Cập nhật 2026-09-16 — danh mục vật tư:** Bổ sung intent `material_master` chung: một mã vật tư không kèm ngày/chứng từ trả toàn bộ record `dmvt` bằng SQL read-only cố định. Vì vậy các cột như mã vụ việc, tên, tài khoản, đơn vị tính… dùng cùng một luồng, không tạo handler theo từng cột. Runtime đã xác minh `VGU1A532Z` có `ma_vv = 5197210103000S`.

**Cập nhật 2026-09-16 — tên vật tư + ngày:** Bổ sung resolver danh mục dùng chung `tên vật tư → ma_vt` theo đối sánh chính xác (0 kết quả hoặc nhiều mã trả trạng thái rõ ràng, không đoán). Cặp `ma_vt + ngày` luôn vào SQL read-only cố định và giữ lại trong state chat. Runtime ERP đã xác minh `FRONTAL COVER 6 PUSHBUTTON 4,3` → `1014082003`, ngày 03/09/2026 trả 6 dòng, tổng xuất `2.661 PCS`; follow-up cùng chat giữ nguyên mã/ngày.

**Cập nhật 2026-09-16:** Router semantic đã chạy cho cặp `ma_vt + so_ct`; Open WebUI inject `__chat_id__` vào tool nên follow-up cùng chat kế thừa filter tự động. Runtime read-only đã xác minh VGY1A053/001-2609-000008 trả 2 dòng, tổng xuất 66 PCS.

## Cập nhật ERP schema discovery — 2026-09-14

- `htmp_postgres_query` không còn gửi catalog theo thứ tự cố định cho model. Với mỗi câu hỏi, tool tự đọc metadata schema `public`, chuẩn hóa tiếng Việt không dấu, mở rộng một từ điển nghiệp vụ chung (nhập/xuất/kho/tồn/số lượng/vật tư/sản xuất) và chỉ gửi tối đa 12 bảng phù hợp nhất cho SQL planner. Không đọc giá trị dữ liệu để xếp hạng và không cần khai báo thủ công từng cột hoặc tab ERP.
- Khi planner thấy khái niệm chưa đủ rõ, ví dụ `giao hàng` chưa xác định là xuất bán hay chuyển kho, tool trả câu hỏi làm rõ thay vì chạy truy vấn đoán. Các truy vấn vẫn bị giới hạn một `SELECT/WITH`, transaction read-only, timeout và số dòng tối đa.
- Đây là baseline connector DB read-only cho từng khách ERP. Bước kế tiếp là test trên bộ câu hỏi thật của từng ERP và bổ sung học mapping đã được người dùng xác nhận, nhưng không đưa toàn bộ schema hoặc dữ liệu mẫu vào prompt.

## Kiến trúc cấu hình báo cáo ERP theo màn hình — 2026-09-15

**Quyết định:** không cấu hình chatbot theo từng bảng PostgreSQL và không để model tự đoán bảng/cột từ tiếng Việt. Đơn vị cấu hình là một **màn hình hoặc nghiệp vụ ERP**. Một màn hình có thể lấy dữ liệu từ nhiều bảng, cột tính toán và các quy tắc nghiệp vụ riêng.

### Bố cục mục tiêu

```text
config/erp-reports/
  nhat-ky-nhap-xuat-ton.json
  bao-gia-nha-cung-cap.json
  bao-cao-hang-nhap-mua.json
  ton-kho.json
sql/erp-reports/
  nhat-ky-nhap-xuat-ton.sql
  bao-gia-nha-cung-cap.sql
  bao-cao-hang-nhap-mua.sql
  ton-kho.sql
tests/erp-reports/
  nhat-ky-nhap-xuat-ton.json
  ...
```

Mỗi manifest khai báo: `id`, các cụm từ nghiệp vụ tiếng Việt, tham số đầu vào (ngày, mã vật tư, kho, đơn vị cơ sở), danh sách nguồn DB, SQL template đã kiểm chứng, mapping cột output và dữ liệu kiểm thử. Tool chung chỉ làm ba việc: nhận diện report, trích điều kiện, rồi thực thi SQL template tham số hóa. Khi thêm report mới chỉ thêm manifest, SQL và test; không thêm nhánh xử lý theo từng câu hỏi vào tool.

### Report đầu tiên đã đối chiếu: Nhật ký nhập xuất tồn

- UI gọi `POST /INAPI/api/Reports/INBCNhatKyNXTAPI/GetData` với `gridid=INBCNhatKyNXT`, khoảng ngày, mã vật tư, mã kho, đơn vị cơ sở và phân trang.
- Backend ERP gọi function `public.inbcnknxt(params)`. Function dùng `ct70` làm nguồn chính, join `dmvt`, `dmkh`, `userinfo`, `sys_dmtt`, `ph74`, `ph84`; đồng thời tính cột ngoại tệ, dòng tổng cộng, phân trang và quyền UI.
- Connector hiện có truy vấn read-only trực tiếp các nguồn đã đối chiếu cho câu hỏi Nhật ký nhập xuất tồn. Khi refactor sang manifest, SQL của report này phải giữ các mapping đã xác nhận: `ct70` cho giao dịch, `dmvt` cho tên vật tư/TK doanh thu, `dmkh` cho khách hàng, `userinfo` cho người tạo/sửa, `sys_dmtt` cho tên trạng thái, `ph74/ph84` cho mã loại nhập xuất.
- Phân biệt rõ output: `STT`, `total`, `gia_nt`, `tien_nhap_nt`, `tien_xuat_nt` là cột tính; `NT` nghĩa là **ngoại tệ**, `TK GV` là tài khoản giá vốn và `TK DT` là tài khoản doanh thu.

### Quy tắc an toàn và kiểm thử

- SQL chỉ đọc, tham số hóa; không ghép input người dùng vào SQL.
- Không mượn hoặc hard-code quyền của tài khoản UI. Connector DB sử dụng tài khoản read-only đã cấp; nếu cần mô phỏng chính xác quyền UI thì dùng service account được phê duyệt riêng.
- Mỗi report phải có fixture từ request/response UI thực tế, tối thiểu gồm: một dòng giao dịch, một cột join, một cột tính toán, trường hợp 0 dòng và kiểm tra tổng số lượng/giá trị.
- Với đại từ tham chiếu như “mã này/của nó”, resolver chỉ mang identifier từ lịch sử chat; không tự bịa điều kiện còn thiếu. Nếu report cần khoảng ngày mà không có, trả câu hỏi làm rõ ngắn.

## Cập nhật pilot-ready — 2026-09-11

**Kết luận:** các kiểm soát có thể xây/kiểm tra trong workspace cho Bước 0–7 đã được triển khai hoặc kiểm tra lại; **không có bước nào được promotion**. Mọi dependency ngoại vi và approval vẫn `blocked` fail-closed. Evidence: [PILOT-20260911](docs/evidence/PILOT-20260911/steps0-7.md), [REL-20260911](docs/evidence/REL-20260911/step1.md).

- **Bước 0:** baseline/runtime staging vẫn healthy; owner, scope/risk acceptance, SLO/RPO/RTO và capacity approval đều `TBD`, nên gate `blocked`.
- **Bước 1:** Registry OCI nhẹ chạy trên chính host tại localhost:5443, TLS/auth/Robot Account/healthcheck pass; image Registry được tải qua IPv4 và checksum xác minh do Docker daemon không có IPv6 egress. Image Open WebUI hiện hành đã được push/pull theo rollback digest sha256:9b03fd56826d76cd503a5f4c126db919537dc5ea7490265fdd5bb12c6ba63cdd. Evidence: docs/evidence/REG-20260911/step1-registry.md. Custom candidate build/publish, SBOM/CVE/license scan, signed tag, Security approval và staging rollback test vẫn là blocker.
- **Bước 2:** thêm `config/pilot-contract.env.example` và checker để từ chối secret reference/backup/alert/on-call/retention trống hoặc placeholder. Secret manager, rotation record, firewall/certificate và off-host immutable storage chưa có; `blocked`.
- **Bước 3:** scope đã đổi sang một kho tri thức chung cho toàn công ty; phân quyền chi tiết, OIDC/MFA và RAG ACL được hoãn, không bỏ. Public signup vẫn khóa và tài khoản nội bộ được quản trị thủ công. Không được đưa dữ liệu cần phân quyền vào kho chung. Xem docs/company-wide-access-scope.md.
- **Bước 4:** request ID gateway/RAG profile smoke có pass; hai filter RAG chỉ chuyển opaque request ID và profile, không đưa prompt/tài liệu/header xác thực/email vào hook. Observability contract cấm các dữ liệu đó. Chưa có Langfuse trace E2E, retention enforcement, notification endpoint hay on-call owner; `blocked`.
- **Bước 5:** thêm clean-room archive verifier chỉ dùng `RESTORE_MODE=clean-room` và Docker volume tạm, không ghi production. Negative test chặn do thiếu `BACKUP_GPG_RECIPIENT`; không tạo backup không mã hóa. Clean-room service recovery, off-host immutable copy và DR approval chưa có; `blocked`.
- **Bước 6:** giữ GPU-load lock; dry-run 48 case đã pass, nhưng không chạy benchmark thật/soak. Cần window, workload, SLO/headroom và abort threshold được duyệt; `blocked`.
- **Bước 7:** staging smoke pass Compose, 8 service, auth, bootstrap và cả HTMP Nhanh/Kỹ với citation config. Upload→parse→retrieve→generate bằng dữ liệu clean-room, citation content assertion, context-limit, trace/authorization E2E và promotion đều chờ upstream gates; `blocked`.

**Recheck cuối:** 2026-09-11T03:10:49Z — bootstrap apply/check, RAG profile, staging smoke và `git diff --check` đều pass sau khi đồng bộ hook request-ID.

**Lệnh tái kiểm tra:** `bash -n scripts/{backup,restore,clean_room_verify,build_release_image,supply_chain_scan}.sh`; `python3 -m py_compile scripts/*.py functions/*.py`; `python3 scripts/staging_smoke_check.py`; `env -i PATH=/usr/local/bin:/usr/bin:/bin python3 scripts/pilot_contract_check.py --strict --oidc` (phải exit 2 khi chưa có handoff); `python3 scripts/release_gate.py --manifest docs/evidence/REL-TEMPLATE/release-manifest.yaml --evidence-dir docs/evidence/REL-TEMPLATE` (phải exit 2 khi artifact/approval thiếu).



# Kế hoạch triển khai Local AI Stack

> Căn cứ: `README.md` và `RUNBOOK.md`  
> Ngày lập: 2026-09-09  
> Trạng thái hiện tại: lab/pilot đang hoạt động; chưa được phép rollout toàn công ty

> **Cập nhật recheck 2026-09-09:** Runtime 8/8 service đang healthy và Compose/Nginx hardening đã được áp dụng. Bước 0 vẫn `blocked`; bước 1 đã xác minh model,
> tokenizer, embedding revision và image registry digest nhưng vẫn `blocked` vì
> custom Open WebUI/SBOM/scan/approval. Bước 2 đã pass core secret/network controls và chỉ gateway còn expose host port;
> governance và kiểm thử LAN/VPN còn `blocked`. Bước 3 đã có technical baseline (khóa
> signup, policy IAM/data và policy checker), nhưng IdP/application ACL/E2E còn `blocked`.
> Bước 4 đã pass gateway log/request-ID baseline; tracing end-to-end, dashboard/alert và
> on-call còn `blocked`. Bước 9 đã có wave manifest và rollout gate fail-closed; chưa mở traffic
> vì upstream gate/approval còn thiếu. Evidence: [BAS-r2](docs/evidence/BAS-20260909-r2/baseline.md), [REL-r2](docs/evidence/REL-20260909-r2/release-manifest.yaml), [SEC](docs/evidence/SEC-20260909/step2.md), [IAM-20260909](docs/evidence/IAM-20260909/step3.md), [OBS-20260909](docs/evidence/OBS-20260909/step4.md), [WAVE-20260909](docs/evidence/WAVE-20260909/step9.md).

## Kết quả kiểm thử tổng hợp gần nhất

**UTC:** 2026-09-09T08:48:25Z  
**Phạm vi:** read-only runtime smoke, policy/unit test, auth negative test, dry-run và gate validation.

| Nhóm kiểm tra | Kết quả |
| --- | --- |
| `docker compose config --quiet` | PASS |
| Bash syntax backup/restore, Python compile, `git diff --check` | PASS |
| Step 3 policy checker | PASS |
| Step 4 observability checker | PASS |
| Benchmark dry-run | PASS; 48 cases, không tạo tải GPU |
| Benchmark parser unit test | PASS; 3/3 |
| Runtime staging smoke | PASS; 8/8 service healthy |
| Nginx syntax | PASS |
| Qdrant negative-auth | `401/401/200` |
| vLLM negative-auth | `401/401/200` |
| Host exposure | Chỉ còn `80/443` |
| Compose secret rendering | `RISK` — `docker compose config`/inspect có thể hiển thị secret runtime; chưa có secret manager |
| Frontend egress | `OPEN` — Network `frontend` chưa `internal`; Open WebUI còn đường egress cần kiểm thử/khóa |
| Pilot gate | `BLOCKED` đúng dự kiến vì upstream approval/evidence thiếu |
| Rollout gate `WAVE-001` | `BLOCKED` đúng dự kiến vì còn `TBD/pending` và upstream gate thiếu |
| Clean-room restore preflight | Fail-closed đúng; backup cũ có Open WebUI artifact giải mã chỉ 87 bytes |

Chưa chạy và không được coi là pass: benchmark GPU thật, soak 24 giờ, backup mới,
clean-room restore thành công, production restore, pilot traffic và rollout traffic.
Các thao tác này cần approval/cửa sổ vận hành riêng hoặc còn phụ thuộc blocker ở các
bước trước. Kết quả trên xác nhận runtime đang hoạt động và các guard đang từ chối
đúng các promotion/restore không đủ điều kiện; chưa xác nhận production readiness.

## 1. Mục tiêu và nguyên tắc

Mục tiêu là đưa stack từ trạng thái lab hiện tại đến pilot có dữ liệu được kiểm
soát, sau đó phát triển thành shared service có thể mở rộng. Không chuyển sang
production toàn công ty khi còn bất kỳ P0 nào ở trạng thái `blocked`.

Mỗi bước chỉ được coi là hoàn tất khi có evidence gồm: test ID, UTC timestamp,
owner/approver, host, Git commit, image digest, model/embedding revision, config
đã redact, command, exit code, raw result, kết luận và ngày hết hạn.

## 2. Vai trò cần chỉ định trước khi bắt đầu

- Platform: Compose, host, GPU, network, release và rollback.
- Security: secret, IAM, network exposure, threat model và security approval.
- Data: phân loại dữ liệu, ACL, retention, lineage và deletion.
- Operations: SLO, alert, on-call, incident response và DR.
- AI Quality: bộ eval tiếng Việt/RAG, chất lượng và acceptance criteria.
- Business owner: use case, nhóm pilot, quota, workload và risk acceptance.

Gán owner/approver cho từng hạng mục và tạo thư mục evidence theo test ID trước
khi thực hiện thay đổi.

## 3.1. Theo dõi blocker và lý do chưa đóng

Các mục dưới đây được giữ `blocked` có chủ đích. Không tự đánh dấu hoàn tất khi
chưa có bằng chứng, owner hoặc phê duyệt tương ứng.

| ID | Phạm vi | Việc còn lại | Lý do hiện chưa đóng | Điều kiện đóng | Owner cần chỉ định | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| B0-01 | Bước 0 | Chỉ định Platform/Security/Data/Operations/AI Quality/Business owner và approver | Chưa có người chịu trách nhiệm/phê duyệt trong workspace | Ghi tên, vai trò, ngày duyệt vào pilot scope/evidence | Business + Platform | `blocked — chờ quyết định` |
| B0-02 | Bước 0 | Chốt pilot scope, dữ liệu được phép, quota, SLO, RPO/RTO, abort threshold, risk acceptance | Đây là quyết định nghiệp vụ và rủi ro, không thể tự suy đoán | Có approval và risk register được ký | Business + Security + Operations | `blocked — chờ phê duyệt` |
| B0-03 | Bước 0 | Điều tra cảnh báo NVIDIA `NV_ERR_NO_MEMORY` | Cần kiểm tra/capacity decision trên host GPU | Có phân tích nguyên nhân, mitigation và approval | Platform + AI Quality | `blocked — cần điều tra host` |
| B1-01 | Bước 1 | Build/publish Open WebUI custom image và lấy registry digest | Hiện chỉ có local image `open-webui-htmp:libreoffice` | Image nằm trong registry tin cậy, digest ghi vào manifest | Platform/Release | `blocked — cần registry` |
| B1-02 | Bước 1 | Chạy SBOM, CVE và license scan | Chưa có scan artifact/policy/CI evidence | Raw output, policy, owner và expiry được lưu | Security/Release | `blocked — cần pipeline/policy` |
| B1-03 | Bước 1 | Tạo release commit/tag và rollback target | Worktree còn thay đổi; chưa có release approval | Commit/tag bất biến, rollback command và test evidence | Platform/Release | `blocked — chờ release gate` |
| B2-01 | Bước 2 | Đưa secrets vào secret manager; chuyển recovery key ra immutable/off-host | Workspace chỉ có runtime `.env` 0600 và GPG key local | Secret-manager reference, rotation record và recovery drill | Security/Operations | `blocked — cần hạ tầng` |
| B2-02 | Bước 2 | Rotation chính thức cho DB/Langfuse/TLS secrets | Chưa có secret-manager ownership và lịch rotation | Rotation có kiểm chứng, không downtime ngoài kế hoạch | Security/Operations | `blocked — cần hạ tầng` |
| B2-03 | Bước 2 | Kiểm thử LAN/VPN IPv4/IPv6, firewall, TLS SAN/renewal và egress | Cần quyền truy cập mạng/certificate/firewall ngoài workspace | Test evidence pass và rule được phê duyệt | Network/Security | `blocked — cần quyền ngoài workspace` |
| B2-04 | Bước 2 | Risk review `ipc: host`, malware quarantine Tika và IAM/RAG ACL end-to-end | Đây là thay đổi kiến trúc/chính sách, không chỉ sửa Compose | Threat-model decision, quarantine control và application-level authorization tests | Security + Data + Platform | `blocked — cần thiết kế/phê duyệt` |
| B3-01 | Bước 3 | OIDC/SAML + MFA và tắt public signup | IdP doanh nghiệp chưa được kết nối; signup đã khóa ở runtime | IdP/MFA evidence và login/deny audit test | Security/Platform | `partial — signup pass, IdP blocked` |
| B3-02 | Bước 3 | Group mapping, admin/break-glass, provisioning/offboarding, access review | Chưa có group/owner/lifecycle thật | Mapping matrix, expiry/revoke và access review evidence | Security/Data/Operations | `blocked — cần IdP` |
| B3-03 | Bước 3 | Metadata contract và data classification | Policy/contract đã tạo; chưa tích hợp vào application/storage path | Schema enforcement và invalid-metadata fail-closed test | Data/Platform | `partial — policy pass, enforcement blocked` |
| B3-04 | Bước 3 | Hai user/hai group E2E RAG authorization matrix | Chưa có application middleware/identity context trong workspace | 0 cross-tenant leak; deny có audit không chứa dữ liệu nhạy cảm | Security/Data/AI Quality | `blocked — cần application/IdP` |
| B4-01 | Bước 4 | Request ID gateway → app → retrieval → vLLM → Langfuse | Gateway đã forward ID; chưa có application SDK/middleware | Trace thành công/lỗi có cùng ID và không chứa secret/content | Platform/AI Quality | `partial — gateway pass, E2E blocked` |
| B4-02 | Bước 4 | Metrics/dashboard/alert/on-call và notification test | Chưa có backend/dashboard/owner/escalation trong workspace | Alert có test notification và runbook | Operations/Platform | `blocked — cần vận hành` |
| B4-03 | Bước 4 | Redaction, pseudonymous identity, retention và RBAC | Policy đã tạo; chưa có trace/audit backend để enforce | Sample trace/log/metric pass redaction và retention review | Security/Data | `partial — policy pass, enforcement blocked` |
| B5-01 | Bước 5 | Resolve volume/path từ container/Compose và tạo manifest | Script đã chuyển sang resolve runtime volume; backup format mới chưa chạy trên dữ liệu thật | Backup mới có manifest, model/embedding revision và volume mapping | Platform/Operations | `partial — code pass, artifact pending` |
| B5-02 | Bước 5 | Encrypted backup/checksum/size/complete/retention | Script đã thêm size check và GPG; tạo backup thật bị chặn cần approval side effect | Artifact mới pass checksum/decrypt/size/COMPLETE và retention review | Operations/Security | `partial — approval pending` |
| B5-03 | Bước 5 | Clean-room restore và RPO/RTO | Restore default đã chuyển sang preflight; backup cũ chứa archive 87 bytes nên bị từ chối đúng | Backup format mới restore trên clean-room volume/project, smoke flow và RPO/RTO pass | Operations/Platform | `blocked — cần artifact sạch` |
| B5-04 | Bước 5 | Collection snapshot/ACL/RAG verification | Mapping collection mới xử lý được tên có dấu gạch dưới; chưa có clean-room restore thực tế | Record/vector/ACL/sample RAG/trace đối chiếu pass | Data/AI Quality | `blocked — cần clean-room` |
| B6-01 | Bước 6 | Benchmark parser/command/metric fail-closed và p50/p95/p99 | Harness mới đã sửa; chưa chạy tải GPU | Unit fixture pass; missing metric/command fail | AI Platform | `partial — harness pass, load blocked` |
| B6-02 | Bước 6 | Workload matrix 4K/8K/16K × concurrency 8/16/32/64 | Dry-run đã tạo 48 cases; workload/arrival approval chưa có | Approved run với token distribution/RAG ratio/cache state | AI Quality/Operations | `partial — dry-run pass` |
| B6-03 | Bước 6 | TTFT/ITL/E2E/queue/goodput/error/KV/OOM/power/quality | Chưa có artifact runtime và telemetry window | Result JSON + host/GPU telemetry + quality score | Platform/AI Quality | `blocked — cần cửa sổ đo` |
| B6-04 | Bước 6 | Soak 24h, cold/warm prefix cache và headroom | Chưa có approval chạy tải dài; GPU có lịch sử OOM | Soak/abort evidence, SLO/headroom approval | Operations/Platform | `blocked — cần approval` |
| B7-01 | Bước 7 | Freeze release, staging/pilot smoke và rollback | Các gate 0–6 còn blocked; chưa có approval pilot | Acceptance checklist, release/backup/rollback evidence | Platform/Operations | `blocked — gate upstream` |
| B7-02 | Bước 7 | Pilot 24h/7d, ACL/security/quality/capacity review | Chưa có IdP/E2E RAG/trace/capacity/DR pass | Pilot report không có P0 và owner ký | Business/Operations | `blocked — gate upstream` |
| B8-01 | Bước 8 | Shared-platform target architecture | Đã tạo target architecture; chưa có business case/approval | Architecture review và owner từng control plane/data plane | Platform/Security/Operations | `partial — design ready, implementation blocked` |
| B8-02 | Bước 8 | HA, external state, router, replicated data, sandbox workers | Single-host Compose chưa đáp ứng; cần đầu tư/hạ tầng mới | Failover/DR/capacity/cost evidence pass | Platform/Operations | `blocked — cần kiến trúc/hạ tầng` |
| B9-01 | Bước 9 | Wave manifest: user/data/owner/quota/ACL/release/rollback | Template WAVE-001 đã tạo nhưng owner/approval còn TBD | Wave manifest hoàn chỉnh và signed approvals | Business/Data/Security/Operations | `blocked — chờ phê duyệt` |
| B9-02 | Bước 9 | Canary traffic và review 24h/7d | Upstream IAM/DR/capacity/observability gates chưa pass | 24h/7d review không P0, SLO/ACL/headroom pass | Operations/Platform | `blocked — gate upstream` |
| B9-03 | Bước 9 | Rollout gate fail-closed | Script đã tạo; không mở traffic nếu còn evidence blocked/TBD | Gate pass và operator approval | Platform/Operations | `partial — gate ready` |

Quy tắc theo dõi: mỗi lần tiếp tục triển khai phải cập nhật owner, evidence link,
gày kiểm tra, điều kiện pass/fail và blocker kế tiếp. Chỉ chuyển `blocked` sang
`done` khi điều kiện đóng tương ứng đã được kiểm chứng; nếu phụ thuộc hệ thống
ngoài workspace thì ghi rõ dependency và người chịu trách nhiệm.

## 3. Các bước triển khai

### Bước 0 — Chốt phạm vi, tiêu chí và baseline

1. Xác nhận giai đoạn đầu là pilot 1–2 phòng ban, không phải rollout toàn công ty.
2. Chốt use case, loại dữ liệu được phép đưa vào, số user, giờ cao điểm, quota,
   retention, SLO tạm thời và ngưỡng abort.
3. Chốt RPO/RTO và availability target; ghi rõ single-host là giới hạn hiện tại.
4. Kiểm tra baseline host bằng `uname`, `nvidia-smi`, Docker/Compose, disk/inode,
   memory, PSI, nhiệt độ, power và kernel OOM log.
5. Ghi Git commit, cấu hình đã redact, trạng thái container, model root/alias,
   image hiện tại và các P0 đang `blocked`.

### Bước 1 — Đóng băng release và xử lý supply chain

1. Chọn model revision Qwen, tokenizer/chat template, quantization và revision
   embedding `BAAI/bge-m3` cố định.
2. Pin digest cho toàn bộ image; loại `latest`, `main`, major tag và package build
   không bất biến khỏi release production.
3. Tạo release manifest gồm Git commit, digest, platform/architecture, driver/CUDA,
   vLLM arguments, schema/migration, backup ID và rollback target.
4. Sinh SBOM, scan CVE/license và lưu kết quả cùng manifest.
5. Chạy `docker compose config --quiet` với config đã redact; tạo staging project
   hoặc port riêng.

**Điều kiện qua:** release candidate có manifest bất biến, scan đạt policy và có
rollback command theo digest/revision.

### Bước 2 — Khóa secret và harden network

1. Xóa credential fallback trong `scripts/rag_leakage_test.py`; scan working tree
   và Git history.
2. Rotate mọi secret đã lộ hoặc từng nằm trong artifact; chuyển secret sang secret
   manager, giữ `.env` chỉ là giá trị runtime quyền `0600`.
3. Không sao chép `.env` plaintext vào backup; mã hóa backup và tách recovery key.
4. Tách network frontend, inference, ingestion, data và observability theo nguyên
   tắc tối thiểu quyền.
5. Chỉ gateway được expose; kiểm tra IPv4/IPv6 từ LAN/VPN, firewall, negative-auth
   với credential thiếu/sai/đúng cho vLLM, Qdrant và các data service.
6. Rà soát `ipc: host`, egress/Hugging Face access, TLS, certificate SAN/renewal,
   request ID, body/token/connection/rate limit và log redaction.

**Điều kiện qua:** không còn secret fallback/tracked, rotation pass, chỉ gateway
được công bố và các luồng authorization-sensitive fail closed.

**Cập nhật thực hiện 2026-09-09 — trạng thái: `blocked` (partial implementation):**

Đã hoàn thành/đã kiểm tra:

- Xóa credential fallback khỏi `scripts/rag_leakage_test.py`; test thiếu
  `QDRANT_URL`/`QDRANT_API_KEY` fail closed. Current-tree scan không còn fallback.
- Xoay Qdrant key từng xuất hiện trong fallback; sau khi phát hiện output chẩn đoán
  chứa runtime value, xoay lại Qdrant/Redis/vLLM. `.env` vẫn giữ quyền `0600`, không
  đưa giá trị vào Git/evidence.
- Bật vLLM API authentication; từ network ứng dụng: thiếu/sai key trả `401`,
  đúng key trả `200` cho cả vLLM và Qdrant.
- Không còn sao chép `.env` vào backup mới; 3 `env.bak` cũ đã secure-delete. Backup
  `backup_20260909_042815` đã mã hóa GPG, checksum/decrypt-all/COMPLETE đều pass;
  `restore.sh` đã cập nhật để giải mã GPG vào thư mục tạm và tự dọn plaintext.
- Tách Compose thành frontend, inference, ingestion, data và observability network;
  chỉ Nginx expose host ports 80/443, các service nội bộ không còn host port mapping.
  Áp dụng runtime thành công. vLLM chuyển `HF_HUB_OFFLINE=1` để chặn egress Hugging
  Face; Nginx có request ID, rate/connection limit, security headers và không ép
  WebSocket Upgrade cho request thường.
- `docker compose config --quiet`, `nginx -t`, healthcheck service và negative-auth
  đã chạy; evidence chi tiết ở `docs/evidence/SEC-20260909/step2.md`.

Thiếu sót/blocker còn lại:

- Backup encrypted đã pass, nhưng private recovery key hiện còn local trong
  `.secrets/`; chưa có bản sao immutable/off-host và chưa có secret-manager ownership.
- DB/Langfuse/TLS secrets chưa được rotation qua secret manager; Qdrant, Redis và
  vLLM đã được xoay runtime, nhưng Redis chưa có secret-manager governance.
- LAN/VPN IPv4/IPv6, firewall, certificate SAN/renewal và egress của mọi service
  chưa được kiểm thử độc lập. `ipc: host` của vLLM vẫn cần risk review.
- Tika đã có healthcheck/resource/read-only/tmpfs/cap-drop; quarantine/malware
  control vẫn thiếu. Network segmentation chưa thay thế IAM/RAG ACL end-to-end.
- Git history vẫn còn commit cũ chứa fallback; không rewrite history/remote khi chưa
  có approval. Bước 0–1 vẫn thiếu owner/approver, SBOM/CVE/license scan, custom image
  digest và release commit/rollback evidence; không được mở pilot dữ liệu nhạy cảm.
- Compose hiện chỉ fail-closed rõ ràng với `VLLM_API_KEY`; Qdrant/Redis/DB/WebUI secret chưa được khai báo bắt buộc nên cần preflight kiểm tra không rỗng.
- Lần audit này cũng xác nhận `docker compose config` render secret vào environment/command; không lưu output chưa redact vào evidence/log và phải rotate nếu đã ra ngoài vùng tin cậy.
- `docker compose config` cho thấy secret được render vào environment/command. Đây là rủi ro vận hành: Docker inspect, process/diagnostic output, log hoặc người có quyền Docker có thể đọc secret. Cần secret manager/Docker secrets hoặc tương đương và rotation sau mọi lần lộ.
- Network `frontend` chưa `internal`; Open WebUI multi-homed nên segmentation chưa đủ để kết luận egress deny. Cần egress policy và SSRF/file-ingestion test độc lập.

### Bước 3 — Hoàn thiện IAM và quản trị dữ liệu

1. Tích hợp IdP OIDC/SAML với MFA; tắt public signup.
2. Map group doanh nghiệp vào role/knowledge base; tách admin và break-glass,
   bật alert/audit, đặt SLA provision/deprovision và lịch access review.
3. Chốt phân loại `public/internal/confidential/restricted`, use case được phép,
   retention, legal hold, data residency, egress và acceptable-use.
4. Thiết kế metadata bắt buộc cho document/chunk: tenant, owner, classification,
   source ACL, version, retention và deletion status.
5. Bảo đảm identity/filter được tạo server-side; không tin `tenant_id` từ client.
6. Chạy test end-to-end qua application với tối thiểu hai user/hai group cho
   upload, list, search, retrieve, chat, share/export, delete, revoke, IDOR,
   filter tampering, semantic query, prompt injection và cache/trace/backup.

**Điều kiện qua:** deny-by-default, không có cross-tenant leak trong matrix đã
duyệt, mọi deny có audit mà không ghi dữ liệu nhạy cảm.

**Cập nhật thực hiện 2026-09-09 — trạng thái: `blocked` (technical baseline partial):**

Đã hoàn thành:

- Tắt public signup bằng cấu hình bất biến `ENABLE_SIGNUP=False`; không còn cho phép
  bật signup tùy ý qua `.env` runtime.
- Tạo [IAM/data-governance policy](docs/step3-iam-data-governance.md) với deny-by-default,
  phân loại dữ liệu, use-case pilot, metadata contract bắt buộc, role baseline và
  quy tắc legal hold/deletion.
- Thêm `scripts/step3_policy_check.py`; static policy check pass.

Còn thiếu/blocker:

- OIDC/SAML, MFA, group mapping, provisioning/deprovisioning và access review cần
  IdP doanh nghiệp, owner và thông tin group thật.
- Open WebUI custom image chưa có middleware ACL trong workspace; chưa chứng minh
  identity/filter được tạo server-side qua application path.
- Chưa chạy được ma trận hai user/hai group cho upload, list, search, retrieve, chat,
  share/export, delete, revoke, IDOR, filter tampering, semantic query, prompt
  injection và cache/trace/backup.

Evidence: [IAM/data policy](docs/step3-iam-data-governance.md). Bước 3 không được
coi là hoàn tất cho đến khi có IdP/application evidence và mọi deny đều audit được
mà không ghi dữ liệu nhạy cảm.

### Bước 4 — Nối observability end-to-end

1. Nối correlation/request ID từ gateway → Open WebUI → retrieval → vLLM →
   Langfuse; xác nhận trace thực sự xuất hiện, không chỉ container healthy.
2. Thu metric gateway, app, vLLM, Tika/RAG, Qdrant, Redis, PostgreSQL/Langfuse,
   host/GPU và DR theo RUNBOOK.
3. Thiết lập redaction, pseudonymous user/tenant, retention, sampling và RBAC;
   không log prompt, output nhạy cảm, secret hoặc auth header ngoài policy.
4. Tạo dashboard và alert có owner, severity, runbook, escalation và test
   notification: latency, queue, KV, OOM, disk/inode, cert, backup, trace lag.

**Điều kiện qua:** một request thành công và một request lỗi đều truy vết được
đầy đủ, metric/log/audit nhất quán và alert test pass.

**Cập nhật thực hiện 2026-09-09 — trạng thái: `blocked` (technical baseline partial):**

Đã hoàn thành:

- Nginx sinh request ID server-side, forward `X-Request-ID` tới Open WebUI và ghi
  timing/request ID vào stdout; access log không ghi query string, referer, user-agent,
  request body hoặc auth header.
- Tạo [observability policy](docs/step4-observability-policy.md) cho correlation,
  redaction, pseudonymous identity, retention và alert ownership.
- Thêm `scripts/step4_observability_check.py`; static observability/redaction check pass.

Còn thiếu/blocker:

- Chưa có SDK/OTel hoặc middleware nối Open WebUI → retrieval/Tika/Qdrant → vLLM →
  Langfuse; Langfuse healthy chưa phải bằng chứng có trace.
- Chưa có dashboard, metric backend, alert rule, on-call owner, escalation và test
  notification trong workspace.
- Chưa có evidence request thành công/lỗi dùng cùng correlation ID và trace được redact
  qua toàn bộ pipeline.

Evidence: [Observability policy](docs/step4-observability-policy.md). Không chuyển
bước 4 sang `done` chỉ dựa trên healthcheck hoặc container Langfuse healthy.

### Bước 5 — Sửa backup/restore và kiểm thử DR

1. Resolve volume/path từ Compose hoặc manifest, không hard-code tên volume.
2. Tạo backup nhất quán cho Open WebUI DB/uploads, Qdrant, Langfuse/PostgreSQL và
   ACL source; lưu model/embedding revision trong manifest.
3. Thêm checksum, encryption, complete marker, kích thước bất thường check,
   retention, immutable/off-host copy và least privilege.
4. Khi backup/restore lỗi, thiếu artifact hoặc archive bất thường thì fail ngay;
   không drop/ghi đè production.
5. Restore mặc định vào clean-room project/volume mới; kiểm tra user/chat/file,
   record count, collection/vector/ACL, collection có dấu gạch dưới, sample RAG,
   trace và application smoke flow.
6. Đo thời gian từ lúc tuyên bố recovery đến khi hoàn thành smoke flow; đối chiếu
   RPO/RTO và sửa đến khi đạt.

**Điều kiện qua:** encrypted off-host backup và clean-room restore đạt RPO/RTO;
backup hỏng bị loại tự động.

**Cập nhật thực hiện 2026-09-09 — trạng thái: `blocked` (backup/restore hardening partial):**

Đã hoàn thành:

- `backup.sh` resolve Open WebUI volume từ container runtime thay vì hard-code tên volume;
  ghi manifest, model/embedding revision, volume và collection mapping.
- Thêm minimum-size check, per-collection snapshot mapping, GPG encryption, checksum và
  complete marker; artifact không hợp lệ phải fail.
- `restore.sh` mặc định chạy `RESTORE_MODE=clean-room`: checksum, decrypt tạm, size,
  gzip/tar validation và không ghi production volume. Production restore cần explicit
  `RESTORE_MODE=production` và `RESTORE_CONFIRM=I_UNDERSTAND_PRODUCTION_RESTORE`.
- Restore production dùng dynamic volume resolution và collection map thay vì tách tên
  collection bằng dấu gạch dưới.
- Clean-room preflight trên backup hiện có đã fail đúng vì `open_webui_data.tar.gz`
  giải mã chỉ có 87 bytes; artifact cũ không được phép restore.

Còn thiếu/blocker:

- Chưa tạo được backup mới theo format đã sửa vì thao tác tạo snapshot/mã hóa/retention
  cần approval side effect riêng.
- Chưa chạy restore trên clean-room volume/project mới; chưa đo RTO từ recovery declaration
  đến application smoke flow và chưa đối chiếu RPO.
- Chưa xác minh user/chat/file, record count, vector/ACL, collection có dấu gạch dưới,
  sample RAG, trace và application smoke flow sau restore.

Evidence: [DR-20260909](docs/evidence/DR-20260909/step5.md). Không restore production
trước khi có clean-room artifact và approval destructive rõ ràng.

### Bước 6 — Sửa harness và xác nhận capacity

1. Sửa benchmark fail-closed: parser/command/metric lỗi phải làm test fail; tính
   đúng p50/p95/p99, không dùng mean/minimum thay percentile.
2. Chuẩn bị workload đại diện: chat ngắn/dài, RAG, tóm tắt, agent/tool và batch;
   ghi token distribution, RAG ratio, cache state và arrival pattern.
3. Đo TTFT, ITL, E2E, queue, offered/achieved goodput, success/429/5xx, token
   throughput, KV, preemption, memory, OOM/restart, power/nhiệt độ và quality.
4. Chạy ma trận context 4K/8K/16K và concurrency 8/16/32/64; tăng đến khi SLO
   hoặc headroom fail. Xác minh Flash Attention bằng log/metric.
5. Đo cold/warm prefix cache; speculative decoding mặc định tắt, chỉ A/B khi có
   quality gate. Không so engine nếu model/revision/hardware/workload khác nhau.
6. Chạy soak tối thiểu 24 giờ bằng cùng release candidate và workload mix; định
   nghĩa abort threshold trước khi chạy, không đổi config giữa lần đo.

**Điều kiện qua:** achieved goodput đạt SLO tạm thời (TTFT p95 < 1,5 giây,
ITL p95 < 50 ms/token, success >= 99%, nếu owner phê duyệt) và còn headroom được
phê duyệt. Không dùng benchmark lịch sử 2026-09-04 làm capacity approval.

**Cập nhật thực hiện 2026-09-09 — trạng thái: `blocked` (harness partial; runtime capacity pending):**

Đã hoàn thành:

- Thay `scripts/benchmark_vllm.py` bằng harness fail-closed: command lỗi, result JSON
  thiếu metric, request count hoặc throughput đều làm test fail.
- Dùng đúng p50/p95/p99; parser tính nearest-rank từ request-level samples hoặc yêu cầu
  summary fields tương ứng, không dùng mean/minimum để thay percentile.
- Harness yêu cầu `--percentile-metrics ttft,itl,e2el`, `--metric-percentiles 50,95,99`,
  lưu detailed JSON và metadata workload/model.
- Ma trận mặc định gồm 48 case: input 4K/8K/16K × concurrency 8/16/32/64 × rate 1/4/8/16.
- Dry-run pass; unit test parser pass 3/3; real GPU execution mặc định bị khóa và cần
  `BENCHMARK_APPROVED=YES` cùng `--execute`.

Còn thiếu/blocker:

- Chưa chạy benchmark tải thật, nên chưa có achieved goodput, TTFT/ITL/E2E, queue,
  KV, OOM/restart, power/nhiệt độ hoặc quality evidence.
- Chưa có owner phê duyệt workload mix, arrival pattern, abort threshold và cửa sổ đo.
- Chưa chạy cold/warm prefix cache, A/B speculative decoding hoặc soak 24 giờ.
- Không dùng benchmark lịch sử 2026-09-04 làm capacity approval; lỗi NVIDIA OOM lịch sử
  vẫn cần điều tra trước khi mở capacity gate.

Evidence: [capacity harness dry-run](docs/evidence/CAP-20260909/step6.md). Bước 6 chỉ
được qua khi runtime artifact, SLO và headroom được owner phê duyệt.

### Bước 7 — Deploy pilot và nghiệm thu

1. Freeze release manifest, backup và rollback; triển khai staging trước rồi mới
   pilot.
2. Chạy `docker compose config --quiet`, `up -d`, kiểm tra `ps` và health endpoint
   của vLLM, Open WebUI, Qdrant; xác nhận Tika có healthcheck/giám sát phù hợp.
3. Smoke test model root/alias/revision, streaming/non-streaming, context limit,
   upload → parse → index → retrieve → generate → delete.
4. Kiểm tra user trái group bị từ chối list/retrieve/generate/delete; client ngắt
   stream phải giải phóng generation/slot trong timeout.
5. Chạy security, RAG, trace, failure và capacity test trên release candidate.
6. Theo dõi pilot sau 24 giờ và 7 ngày; review lỗi, SLO, ACL, chi phí và feedback.

**Điều kiện qua:** pilot chỉ dùng dữ liệu đã phân loại, có quota/owner; không có
P0 mới, SLO pass và headroom không thấp hơn ngưỡng phê duyệt.

### Bước 8 — Nâng lên shared platform

Chỉ thực hiện sau pilot đạt gate:

1. Chọn kiến trúc shared platform: HA gateway/LB, canonical hostname, enterprise
   CA và N+1 GPU hoặc failover được phê duyệt.
2. Làm stateless web/API, externalize database/uploads/object storage và session
   state; không gọi hai container cùng host là HA.
3. Thêm model router/admission control hiểu queue, token budget và tenant quota;
   tách interactive khỏi batch.
4. Triển khai Qdrant replication, Redis HA/ACL/noeviction, PostgreSQL HA/PITR/pool;
   test failover, migration và reindex.
5. Tách Tika thành worker sandbox có queue, quota, concurrency, quarantine,
   malware/content control, dead-letter, cancellation và deny egress.
6. Hoàn thiện gateway rate/connection/token limit, SSE/WebSocket load test,
   log rotation, on-call, incident/change/rollback và cost forecast.

**Điều kiện qua:** failure matrix, soak, failover và DR pass theo availability,
RPO/RTO và cost/capacity target đã ký.

**Cập nhật thực hiện 2026-09-09 — bước 7: `blocked` (gate upstream chưa đạt):**

Đã hoàn thành:

- Tạo [pilot acceptance checklist](docs/pilot-acceptance-checklist.md) cho release freeze,
  staging smoke, IAM/RAG, observability, capacity, DR, rollback và theo dõi 24h/7d.
- Tạo `scripts/pilot_gate_check.py` để promotion fail-closed; script không mutate deployment.
- `scripts/staging_smoke_check.py` chạy read-only và pass: Compose, 8/8 healthy, Nginx,
  Open WebUI, vLLM auth/models, Qdrant auth, Tika và Langfuse health; đây vẫn chỉ là
  runtime smoke, không phải pilot acceptance.

Còn thiếu: owner/approval bước 0, release/scan bước 1, IAM E2E bước 3, trace/alert bước 4,
clean-room DR bước 5 và capacity/soak bước 6. Không triển khai pilot dữ liệu nhạy cảm.

**Cập nhật thực hiện 2026-09-09 — bước 8: `partial` (target design only):**

- Tạo [shared-platform target architecture](docs/shared-platform-architecture.md) với HA
  gateway/LB, stateless API, external state, model router, replicated Qdrant, Redis/Postgres
  HA, Tika sandbox/quarantine và observability plane.
- Chưa triển khai hạ tầng bước 8 vì pilot chưa đạt gate và chưa có business case,
  availability/SLO/RPO/RTO/cost target được ký.

Evidence/gate: `scripts/pilot_gate_check.py`, [pilot checklist](docs/pilot-acceptance-checklist.md)
và [shared-platform architecture](docs/shared-platform-architecture.md).

### Bước 9 — Rollout theo wave

1. Mỗi wave ghi rõ nhóm user, dữ liệu, owner, quota, ACL review, capacity headroom,
   release manifest và rollback plan.
2. Mở traffic từng đợt nhỏ; theo dõi 24 giờ rồi review trước khi giữ ổn định.
3. Sau 7 ngày kiểm tra lại SLO, incident, ACL, dữ liệu orphan, trace/redaction,
   chi phí và feedback.
4. Không mở wave tiếp theo nếu có P0 mới, SLO fail hoặc headroom dưới ngưỡng.
5. Khi tất cả gate đạt, Data/Security/Legal/Operations/AI Quality và business
   owner ký production approval.

**Cập nhật thực hiện 2026-09-09 — bước 9: `blocked` (rollout process ready, gates pending):**

Đã hoàn thành:

- Tạo [rollout wave plan](docs/rollout-wave-plan.md) với manifest template, canary, quota,
  ACL review, rollback, abort threshold và review 24h/7d.
- Tạo `docs/rollout-waves/WAVE-001.yaml` làm wave đầu tiên ở trạng thái `blocked`, không
  tự coi TBD là approval.
- Thêm `scripts/rollout_wave_gate.py`; gate fail-closed nếu evidence, owner, approval,
  release, DR, observability hoặc capacity còn `blocked`/`TBD`/`pending`. Script không đổi traffic.

Còn thiếu/blocker:

- WAVE-001 chưa có user group, owner, approver, quota, ACL review, backup hợp lệ, rollback
  command và headroom được ký.
- Các gate upstream bước 0–8 chưa pass; chưa mở traffic, chưa có review 24h/7d và chưa
  thể ký production approval.

Evidence: [WAVE-20260909](docs/evidence/WAVE-20260909/step9.md).

## 4. Production gate cuối cùng

Chỉ ghi nhận production-ready khi release candidate đồng thời đạt:

- artifact/model/embedding/config đã pin và rollback pass;
- SSO, MFA, group lifecycle, admin/break-glass và access review pass;
- không còn secret fallback/tracked; rotation và encrypted backup pass;
- chỉ gateway expose; IPv4/IPv6 scan và negative-auth pass;
- benchmark/soak đạt SLO tại achieved goodput với headroom;
- overload, cancellation, dependency, host, disk và certificate failure pass;
- trace, metric, log, audit, redaction, retention và alert pass;
- clean-room restore và rollback đạt RPO/RTO;
- HA/failover đúng availability cam kết hoặc có business acceptance bằng văn bản;
- các bên Data, Security, Legal, Operations và AI Quality phê duyệt.

## 5. Thứ tự thực thi ngắn gọn

```text
Owner + baseline
  -> release pinning + secret/network hardening
  -> IAM + RAG ACL
  -> observability
  -> backup/restore
  -> benchmark + soak
  -> pilot
  -> HA/shared platform
  -> rollout từng wave
```

Các bước sau không được bỏ qua gate của bước trước. Mọi thay đổi image, model,
embedding, schema, config hoặc data policy phải tạo release/evidence mới và có
đánh giá lại các test bị ảnh hưởng.


## Cập nhật thực hiện 2026-09-10 — Bước 0–1

**Phạm vi kiểm tra:** trực tiếp trên server `edgexpert-f3a2` đang vận hành stack, không phải máy local. Không restart hoặc recreate container trong đợt này.

### Bước 0 — baseline server

- `docker compose config --quiet` pass; runtime giữ nguyên và service healthy theo kiểm tra runtime gần nhất.
- Disk còn 3.3 TiB, inode còn 99%, memory PSI hiện 0.
- Kernel log vẫn có nhiều `NVRM: NV_ERR_NO_MEMORY` ngày 2026-09-09; chưa có capacity analysis/mitigation được owner phê duyệt. Gate bước 0 giữ `blocked`.
- Owner/approver, workload acceptance, SLO/RPO/RTO, retention và business risk acceptance vẫn `TBD`.

### Bước 1 — release/supply chain

- Compose đã ép `--revision` và `--tokenizer-revision` cho Qwen2.5-14B revision `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`.
- Các secret runtime bắt buộc của WebUI, Qdrant, Redis, PostgreSQL và Langfuse đã dùng interpolation fail-closed (`:?`); thiếu giá trị sẽ làm Compose config không hợp lệ.
- Xác minh sau thay đổi: `docker compose config --quiet`, `git diff --check` và unit test hiện có 3/3 pass.
- Custom Open WebUI vẫn là image local `open-webui-htmp:libreoffice`, chưa có registry digest. `docker sbom`, `syft`, `grype` và `trivy` không khả dụng trên server; SBOM/CVE/license scan chưa chạy.
- Chưa có release commit/tag, rollback target đã duyệt, owner/approver hoặc signed risk acceptance. Gate bước 1 giữ `blocked`.


## Cập nhật điều tra B0-03 — 2026-09-10T01:39:38Z

**Host:** `edgexpert-f3a2` (server đang vận hành)  
**Trạng thái:** `partial — điều tra hoàn tất; mitigation/approval pending`.

- `NV_ERR_NO_MEMORY` lặp lại trong kernel log vào các đợt tạo/recreate Docker; ở lần 2026-09-09, lỗi xuất hiện khi vLLM đang load/warm-up model, trước khi engine báo ready. Không có Xid/ECC/thermal-throttling; GPU hiện 41°C, 0% utilization và service vẫn healthy.
- vLLM hiện giữ khoảng 92,045 MiB GPU memory. Startup cho biết weight/non-torch/activation/CUDA graph dùng khoảng 17.37 GiB, KV cache 72.43 GiB; cấu hình `--max-num-seqs 64` vượt maximum concurrency được engine ước tính ở 16K context (48.29x).
- `VLLM_ATTENTION_BACKEND=FLASH_ATTN` bị vLLM báo unknown; backend thực tế là FlashInfer. Không coi biến này là kiểm soát hiệu năng hợp lệ.
- Mitigation đề xuất, **chưa áp dụng vì sẽ restart inference và đổi capacity**: đặt ngân sách KV cố định thấp hơn (ví dụ 64 GiB) và đặt `--max-num-seqs` không vượt concurrency đã xác minh; sau đó chạy workload được phê duyệt và soak. Platform + AI Quality phải phê duyệt SLO/headroom trước khi mở pilot.
- Trong lúc đọc startup log, vLLM đã ghi API key vào log. Key phải được xem là đã lộ: không lưu raw log/evidence chứa key, rotate `VLLM_API_KEY`, rồi xác minh lại negative-auth và log redaction theo bước 2.

**Kết luận B0-03:** không có bằng chứng lỗi phần cứng đang hoạt động, nhưng chưa thể kết luận root cause hoặc đóng risk khi chưa áp dụng mitigation và đo lại tải. Bước 0 vẫn `blocked` do B0-01/B0-02 cần owner/approval và B0-03 cần quyết định capacity.


## Cập nhật sự cố gateway — 2026-09-10T02:15Z

- Triệu chứng: Open WebUI tại `https://192.168.31.10` trả trang trắng.
- Nguyên nhân: rate limit `10r/s`, `burst=20` được áp dụng ở server-level; trình duyệt tải song song nhiều JavaScript asset `/_app/immutable/*` và nhận `429`.
- Khắc phục: tách `/_app/` và `/static/` thành location không rate-limit; giữ `limit_req zone=per_ip burst=20 nodelay` và `limit_conn per_ip_conn 20` cho route động (API/chat/upload). Recreate riêng Nginx để bind mount cấu hình mới.
- Xác minh: Nginx healthy; 80 request đồng thời tới `/_app/version.json` đều `200`; 8/8 service healthy. Không restart Open WebUI, vLLM hoặc sửa/xóa knowledge data.


## Cập nhật rotation/capacity — 2026-09-10

- Scope do business xác nhận: toàn bộ khối văn phòng, dữ liệu nội bộ; ước tính khoảng 50 người dùng đồng thời. Đây là rollout nội bộ, không còn là pilot 1–2 phòng ban.
- Đã rotate `VLLM_API_KEY` trong `.env` (không ghi giá trị vào plan/log/evidence), đặt file quyền `0600`, và restart riêng vLLM rồi Open WebUI.
- Đã đổi vLLM từ `--gpu-memory-utilization 0.75`, `--max-num-seqs 64` sang `--kv-cache-memory 68719476736` (64 GiB), `--max-num-seqs 40`; tắt vLLM default logging configuration để giảm nguy cơ startup log lộ key. Sau restart GPU dùng khoảng 83.3 GiB, giảm từ khoảng 92 GiB.
- Xác minh: key sai trả `401`; key mới nội bộ từ Open WebUI sang vLLM trả `200`; gateway trả `200`; 8/8 service healthy.
- B0-03 còn `partial`: cần benchmark/soak theo workload 50 user để chứng minh SLO, headroom và không lặp `NV_ERR_NO_MEMORY` trước khi mở toàn bộ văn phòng.


## Cập nhật provider model — 2026-09-10

- Triệu chứng: WebUI báo `No models available` sau khi rotate `VLLM_API_KEY`.
- Nguyên nhân: WebUI lưu `openai.api_keys` trong SQLite; giá trị cũ ghi đè key mới từ `.env`. Ollama provider mặc định còn bật và trỏ tới `host.docker.internal:11434` không tồn tại.
- Khắc phục: đồng bộ key mới vào `openai.api_keys`, tắt `ollama.enable`, và lưu `ENABLE_OPENAI_API=True`/`ENABLE_OLLAMA_API=False` trong Compose. Không sửa knowledge/user data.
- Xác minh: key lưu trong WebUI khớp runtime key; Ollama disabled; vLLM/Open WebUI/Nginx cùng 8/8 service healthy.


## Cập nhật RAG/knowledge — 2026-09-10

- Triệu chứng: hỏi “giám đốc công ty htmp là ai” trong chat nhận trả lời chung chung, không dùng tài liệu nội bộ.
- Xác minh storage: WebUI có 2 knowledge base, 1,578 liên kết knowledge-file; Qdrant có `open-webui`, `open-webui_files` và `open-webui_knowledge`. Knowledge không bị mất.
- Nguyên nhân: knowledge trong Workspace không tự được đưa vào mọi chat. Chat `Greetings` không có knowledge attachment, nên vLLM chỉ trả lời theo kiến thức nền.
- Cách dùng hiện tại: tại ô chat gõ `#`, chọn knowledge base `htmp` (hoặc dùng nút `+` để đính knowledge), thấy biểu tượng file/knowledge xuất hiện rồi mới hỏi. Cần hỏi kèm yêu cầu “trả lời theo tài liệu nội bộ và nêu nguồn”.
- Việc còn lại: nếu toàn bộ văn phòng phải luôn tra cùng một knowledge base, gắn knowledge `htmp` vào model nội bộ trong Workspace > Models hoặc folder dùng chung; sau đó chạy test retrieval/permission giữa nhiều user trước khi rollout.


## Cập nhật RAG performance — 2026-09-10

- Đo request RAG thực tế: Qdrant trả kết quả sau khoảng 5 giây; local reranker hoàn tất khoảng 45 giây sau đó. Bottleneck là reranker CPU, không phải số lượng 1,500 tài liệu hoặc Qdrant.
- Cấu hình hiện tại: hybrid search bật, `top_k=20`, `top_k_reranker=10`, `chunk_size=1500`, `chunk_overlap=200`, local `BAAI/bge-reranker-v2-m3`.
- Đề xuất baseline latency: tắt hybrid reranking, giữ vector search `bge-m3` và giảm `top_k` xuống 8; đo lại bằng bộ câu hỏi nội bộ có đáp án. Nếu cần độ chính xác rerank cao, cần chuyển reranker sang GPU/service riêng thay vì CPU của Open WebUI.
Thiết kế và tiêu chuẩn triển khai ERP: [erp.md](docs/erp.md).
