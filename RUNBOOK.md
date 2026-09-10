# RUNBOOK TRIỂN KHAI VÀ VẬN HÀNH LOCAL AI STACK

> Cập nhật: **2026-09-09**
>
> Trạng thái: **P0 còn mở; chưa được phép qua production gate toàn công ty**
>
> Bối cảnh và kiến trúc: [`README.md`](./README.md)

## 1. Quy tắc vận hành

### Nguồn sự thật

1. Runtime đã kiểm tra: image digest, model root/revision, startup log, metric và test.
2. `docker-compose.yml`: topology, port, volume và tham số dự kiến.
3. Secret manager/`.env`: chỉ chứa giá trị môi trường, không commit hoặc đưa vào artifact.
4. `README.md` và file này: quyết định, quy trình, SLO và tiêu chí nghiệm thu.
5. Tài liệu chính thức đúng với phiên bản/digest đã pin.

### Trạng thái bằng chứng

| Trạng thái | Ý nghĩa |
| --- | --- |
| `target` | Mục tiêu chưa triển khai |
| `configured` | Có trong config nhưng chưa chứng minh runtime/end-to-end |
| `verified` | Test đúng tầng đã pass và artifact còn hiệu lực |
| `blocked` | Thiếu điều kiện bắt buộc để đi tiếp |

Một checkbox chỉ được đánh dấu `[x]` khi artifact có test ID, UTC timestamp,
owner/approver, host, Git commit, image digest, model/embedding revision, config
đã redact, command, exit code, raw result, kết luận và ngày hết hiệu lực. Parser
không đọc được metric hoặc thiếu artifact phải làm test fail.

## 2. Baseline ngày 2026-09-09

| Hạng mục | Trạng thái | Bằng chứng/giới hạn |
| --- | --- | --- |
| Compose syntax | `verified` tại thời điểm rà soát | `docker compose config --quiet` pass; không lưu output render vào log/evidence nếu chưa redact secret |
| Runtime | `verified` tại thời điểm rà soát | 8/8 container Up và healthy, gồm Tika; đây không phải security/SLO evidence |
| Model identity | `configured` | Runtime trả root Qwen2.5-14B, alias `qwen2.5-14b`, context 16K; revision được ghi trong evidence/backup metadata nhưng Compose chưa enforce |
| Backend binding | `configured` | Backend bind loopback/inner network; chưa có LAN/VPN IPv4/IPv6 scan |
| Secret file | `partial` | `.env` quyền `0600`, Git ignore; fallback/backup plaintext đã sửa, nhưng secret vẫn vào rendered Compose/process và chưa có secret manager |
| Immutable release | `blocked` | Digest đã pin cho registry images; Open WebUI vẫn local tag, model revision/embedding và SBOM/CVE/license evidence chưa đủ |
| Langfuse tracing | `blocked` | Service healthy nhưng chưa có trace end-to-end |
| RAG isolation | `blocked` | Test gọi thẳng Qdrant, không đi qua user/group/application |
| Backup/restore | `blocked` | Hardening/preflight đã pass; chưa có backup mới, off-host copy hoặc clean-room restore |
| Performance SLO | `partial` | Harness/parser dry-run/unit pass; chưa chạy GPU load, quality hoặc soak |

Snapshot này hết hiệu lực sau bất kỳ thay đổi image/model/config/data schema hoặc
sau thời hạn evidence do owner quy định.

## 3. Backlog bắt buộc

### P0 - Trước pilot dữ liệu nhạy cảm hoặc rollout lớn

- [ ] **OWN-01:** Gán owner/approver cho Platform, Security, Data, Operations và AI Quality.
- [ ] **EVD-01:** Tạo `evidence/<test-id>/manifest` và quy tắc expiry/fail-closed.
- [x] **SEC-01 (current tree):** Xóa credential fallback, scan working tree và rotate runtime secret từng lộ; Git history cũ vẫn cần xử lý/revoke theo approval.
- [ ] **SEC-02:** Chuyển secret sang secret manager; mã hóa và tách secret khỏi backup dữ liệu; thêm preflight fail-closed cho mọi secret bắt buộc (không cho phép giá trị rỗng).
- [ ] **REL-01:** Pin image bằng digest, model/embedding bằng revision; tạo SBOM,
  scan CVE/license và promotion manifest.
- [ ] **NET-01:** Đã tách các network và chỉ gateway được công bố; còn phải khóa/kiểm thử egress frontend, LAN/VPN IPv4/IPv6, firewall và certificate.
- [ ] **NET-02:** Test Qdrant/vLLM/data service với credential thiếu/sai/đúng; luồng
  authorization-sensitive phải fail closed.
- [ ] **IAM-01:** Tích hợp IdP, MFA/group mapping, provisioning/offboarding,
  admin/break-glass và access review.
- [ ] **GOV-01:** ACL RAG deny-by-default và test cross-tenant end-to-end qua ứng dụng.
- [ ] **OBS-01:** Nối request ID từ gateway/app/inference/retrieval tới Langfuse,
  metric/log/audit; áp dụng redaction và retention.
- [ ] **DR-01:** Hardening/preflight đã có; vẫn phải tạo backup mới và chạy clean-room restore đạt RPO/RTO.
- [ ] **PERF-01:** Harness đã sửa; vẫn phải benchmark/soak theo workload thật và phê duyệt
  achieved goodput còn đạt đồng thời SLO/headroom.

### P1 - Reliability và vận hành

- [ ] Graceful shutdown, cold boot, restart từng dependency và host reboot test.
- [ ] Gateway HA, canonical hostname, enterprise CA, renewal, request ID, rate/
  connection/token limit và SSE/WebSocket load test.
- [ ] Open WebUI stateless/multi-replica design; external database/object storage.
- [ ] Tika worker isolation, healthcheck, queue, resource/concurrency limit,
  quarantine và malware/content controls.
- [ ] Qdrant replication/snapshot/index/capacity policy và reindex test.
- [ ] Redis ACL, `noeviction` cho auth/session state, memory alert và HA; tách cache/queue.
- [ ] PostgreSQL HA/PITR/pool/migration; Langfuse upgrade theo official deployment.
- [ ] Log rotation, dashboards, alerts, on-call, incident/change/rollback process.
- [ ] Failure matrix, soak test và cost/capacity forecast theo phòng ban.

## 4. Release manifest và chuẩn phiên bản

Không deploy tag moving trực tiếp vào production. Manifest cho mỗi release phải có:

- Git commit và `docker compose config` đã redact;
- repository, tag, image digest, platform/architecture của từng image;
- model root, immutable revision, tokenizer, chat template, quantization format;
- embedding model/revision/dimension và collection schema version;
- vLLM arguments, environment ảnh hưởng, driver/CUDA và host profile;
- database migration version, backup ID và rollback target;
- kết quả smoke, security, RAG, benchmark và restore còn hiệu lực.

“Latest” trong doanh nghiệp nghĩa là **latest approved digest/revision**, không
phải tag `latest`, `main`, major tag hoặc nội dung mới nhất trên registry.

## 5. Preflight và triển khai

### Host preflight

Trước `docker compose config`, kiểm tra mọi biến bắt buộc (`VLLM_API_KEY`, `QDRANT_API_KEY`, `REDIS_PASSWORD`, `WEBUI_SECRET_KEY`, PostgreSQL/Langfuse secrets, backup recipient) tồn tại và không rỗng; thiếu biến phải dừng, không chạy với giá trị mặc định hoặc secret rỗng.

```bash
uname -m
cat /etc/os-release
nvidia-smi
docker version
docker compose version
docker info
df -h
df -i
free -h
```

Xác minh ARM64/GB10 được nhận, NVIDIA runtime hoạt động, disk/inode và unified
memory đủ cho weights, KV cache, data service, spike và backup. Ghi PSI memory,
temperature/power và kernel OOM log source. Không coi 128 GB unified memory là
128 GB riêng cho GPU.

### Trước thay đổi

1. Freeze manifest/digest/revision và định nghĩa abort threshold.
2. Backup tất cả state bị ảnh hưởng, xác minh manifest/checksum/decryption.
3. Triển khai trên staging hoặc Compose project/port riêng.
4. Ghi rollback command và xác nhận schema/data backward compatibility.

### Deploy và smoke

```bash
docker compose config --quiet
docker compose up -d
docker compose ps
# Chỉ gateway bind host; service nội bộ kiểm tra qua Docker network/container.
curl -kfsS https://127.0.0.1/health
# vLLM/Qdrant cần auth; không gọi qua host port.
docker compose exec -T vllm curl -fsS http://127.0.0.1:8000/health
docker compose exec -T qdrant bash -c 'exec 3<>/dev/tcp/127.0.0.1/6333 && echo -e "GET /healthz HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n" >&3 && cat <&3 | grep -q "200 OK"' 
```

Không chạy `pull` tag moving trong production. Sau healthcheck phải test:

1. Chat streaming và non-streaming; model root/alias/revision đúng.
2. Prompt bình thường, sát context limit và vượt limit có lỗi dự kiến.
3. Upload, parse, index, retrieve, generate và xóa một tài liệu test.
4. User trái group bị từ chối list/retrieve/generate/delete.
5. Request thành công/lỗi có trace, metric, log và correlation ID đúng.
6. Client ngắt stream giải phóng generation/slot trong timeout.

Rollback theo digest/revision đã ghi, không theo tag. Không tự hạ database schema
nếu migration không hỗ trợ; restore vào project/volume mới rồi smoke test trước
khi chuyển traffic.

## 6. Benchmark và capacity

### Workload phải tách riêng

| Profile | Điểm cần đo |
| --- | --- |
| Chat ngắn | TTFT, ITL, fairness |
| Chat dài | KV memory, preemption, context rejection |
| RAG | Parse/embed/search/generation latency, token budget, quality |
| Tóm tắt tài liệu | Prefill throughput, queue và timeout |
| Agent/tool | Nhiều vòng gọi, cancellation, tool error và E2E |
| Batch/offline | Throughput và ảnh hưởng tới interactive traffic |

### Metric bắt buộc

p50/p95/p99 của TTFT, ITL, E2E và queue; offered/achieved RPS; success/429/5xx;
input/output goodput; running/waiting; KV usage; cache hit; preemption; peak unified
memory; power/temperature; OOM/restart và quality score.

Target tạm thời kế thừa từ dự án: TTFT p95 <1,5 giây, ITL p95 <50 ms/token và
request success >=99%. Owner nghiệp vụ phải duyệt workload/cửa sổ đo trước khi
biến target thành SLO. Availability 99,9% không thể là HA guarantee trên một host.

### Ma trận tuning

- Context 4K/8K/16K và concurrency 8/16/32/64, tăng tới khi một SLO/headroom fail.
- FP8 weight/KV so với baseline chất lượng; calibrate KV scale nếu recipe yêu cầu.
- Continuous batching/scheduler theo arrival pattern thật; tách interactive/batch.
- Xác minh Flash Attention bằng startup log/metric.
- Prefix caching: cold, warm no-hit, warm hit; ghi hit rate và salt theo trust group.
- Speculative decoding: mặc định tắt; chỉ bật sau A/B latency/throughput/quality.
- So engine vLLM/SGLang/TensorRT-LLM chỉ khi cùng model, revision, hardware và workload.
- Đo gateway/network/serialization riêng khỏi model/inference latency.

Artifact benchmark 2026-09-04 chỉ là lịch sử. Offered 16 RPS đạt khoảng 1,06
request/s; report không đo đúng p95 và pass ITL bằng ngưỡng code sai. Không dùng
làm capacity approval.

## 7. IAM, RAG và quản trị dữ liệu

### Identity

- IdP/OIDC/SAML theo phiên bản đã pin; MFA do IdP cưỡng chế.
- Group doanh nghiệp map tới role/knowledge base; mặc định deny.
- Provision/deprovision có SLA; admin tách user; break-glass có alert/audit.
- Service account có scope, owner, expiry; access review định kỳ.

### RAG authorization test

Mỗi document/chunk phải mang tenant, owner, classification, source ACL, version,
retention và deletion status. Identity/filter phải được tạo server-side, không tin
`tenant_id` do client gửi.

Test ít nhất hai user/hai group và bao phủ upload, list, search, retrieve, chat,
share/export, delete, quyền bị thu hồi, IDOR, filter bị bỏ/sửa, query semantic gần
dữ liệu bị cấm, prompt injection trong tài liệu, cache/trace/backup. Mọi deny phải
có audit nhưng không log nội dung nhạy cảm.

### Data lifecycle

- Phân loại public/internal/confidential/restricted và use case được phép.
- DLP/PII/secret scan trước ingestion và trước trace/log.
- Retention/xóa cho file gốc, chunk, vector, chat, feedback, trace và backup.
- Legal hold, lineage, data residency và egress policy.
- Model license/provenance và acceptable-use được Legal/Security/Data duyệt.

## 8. Hardening theo thành phần

### Gateway/network

- Chỉ 80/443 được mở cho subnet/VPN được phép; SSH chỉ admin network.
- vLLM, Tika, Qdrant, Redis, Langfuse và database nằm trên network tối thiểu cần thiết.
- Canonical hostname, certificate CA, SAN, TLS 1.2/1.3, renewal/expiry alert.
- Request ID, secure headers/cookie/CORS, rate/connection/body/token limit.
- Không ép `Connection: Upgrade` cho mọi request; test SSE/WebSocket/slow client.
- Không log prompt, secret, auth header hoặc query nhạy cảm.
- Risk-review `ipc: host` của vLLM và kiểm soát egress. vLLM đã đặt `HF_HUB_OFFLINE=1`, nhưng frontend/ứng dụng và đường upload vẫn cần egress test.

### Open WebUI

- Pin base image/digest; custom LibreOffice build có SBOM/CVE scan và package lock.
- Tắt public signup, cấu hình SSO/RBAC và hạn chế share/export/tool/admin.
- Muốn nhiều replica phải externalize database/uploads, migration và session state.

### Tika/LibreOffice

- File upload là dữ liệu hostile: MIME validation, archive/page/size/time/memory limit.
- Quarantine, antivirus/CDR theo policy; worker non-root/read-only, deny egress,
  queue/concurrency cap, cancellation/dead-letter và healthcheck.
- Test Word/Excel/PDF/PPT tiếng Việt, bảng, scan/OCR, file hỏng và decompression bomb.

### Qdrant

- API key/TLS service-to-service không thay thế per-user authorization.
- Collection/shard/payload index theo filter/tenant và schema version.
- Replication, snapshot/retention/capacity/compaction và restore/reindex test.
- File gốc và source ACL phải có source of truth ngoài vector store.

### Redis

- ACL, TLS tại trust boundary, `noeviction` cho auth/session state, memory/AOF alert.
- Tách session/token revocation, WebSocket, queue và response cache nếu policy khác.
- Nếu thêm semantic cache, key phải gồm tenant, model/revision, prompt/policy;
  có TTL, invalidation, encryption và leakage test.

### Langfuse/PostgreSQL

- Không nâng Langfuse v2 bằng cách chỉ đổi tag; test migration/rollback theo official stack.
- Trace có pseudonymous user/tenant, request ID, model revision, token, latency,
  retrieval/error; redact prompt/output/secret, đặt RBAC/retention/sampling.
- PostgreSQL có migration control, pool, HA/PITR và restore test.

## 9. Observability và trực vận hành

| Lớp | Tín hiệu tối thiểu |
| --- | --- |
| Gateway | RPS, connection/SSE, 4xx/429/5xx, upstream latency, TLS expiry |
| Open WebUI | Login/ACL deny, active user, 5xx, upload/index/WebSocket latency |
| vLLM | TTFT, ITL, E2E, queue, running/waiting, tokens/s, KV, preemption/OOM |
| RAG/Tika | Parse/embed/search latency/error, recall, empty/stale/orphan data |
| Qdrant | Query/filter latency, collection/shard size, replication, snapshot age |
| Redis | Memory, eviction, rejected connection, replication/AOF error |
| Langfuse/DB | Trace completeness, ingestion lag/error, DB/worker/storage growth |
| Host/GPU | CPU, PSI/unified memory, disk/inode, network, power/temperature |
| DR | Last complete backup/off-host copy/restore drill và RPO breach |

Mỗi alert có owner, severity, runbook, escalation và test notification. Đồng bộ
clock, dùng correlation ID, rotation/retention và audit log bất biến. Tracing
không được trở thành kho sao chép dữ liệu nhạy cảm không kiểm soát.

## 10. Backup và disaster recovery

Backup/restore hiện đã có hardening baseline; clean-room restore drill vẫn là điều kiện bắt buộc. Bản vận hành phải:

1. Resolve path/volume từ container/Compose/manifest, không hard-code `open-webui-data`; restore mặc định chạy `RESTORE_MODE=clean-room`.
2. Snapshot nhất quán Open WebUI DB/uploads, Qdrant, Langfuse stores và ACL source.
3. Có manifest version/timestamp/component/size/checksum/encryption/complete marker,
   model/embedding revision và retention class.
4. Fail khi command lỗi, thiếu artifact hoặc kích thước bất thường; không restore
   archive 87 byte từng xuất hiện trong backup hiện tại.
5. Mã hóa, least privilege, immutable/off-host copy và recovery key tách biệt.
6. Không backup `.env` plaintext cùng data artifact.
7. Restore mặc định chỉ preflight clean-room; production restore cần `RESTORE_MODE=production` và confirmation phrase, không drop/ghi đè production nếu thiếu approval.
8. Xử lý đúng collection có dấu gạch dưới và chọn rõ full/collection snapshot.
9. Sau restore đối chiếu user/chat/file, record count, vector/ACL, sample RAG,
   trace và application smoke test.

RPO do thời điểm dữ liệu cuối phục hồi được quyết định, không phải tên thư mục.
RTO đo từ lúc tuyên bố recovery tới khi người dùng hoàn thành smoke flow.

## 11. Failure matrix và soak test

| Case | Kết quả mong đợi |
| --- | --- |
| Overload trên capacity | Backpressure/429; không OOM; hồi phục về baseline |
| Prompt vượt context | 4xx rõ ràng; không 500/cắt im lặng |
| Client ngắt stream | Generation bị hủy và slot giải phóng đúng hạn |
| File rỗng/hỏng/bomb | Bị từ chối/quarantine; không index rác hoặc cạn tài nguyên |
| Mất Qdrant/Redis/DB/Langfuse | Hành vi fail-closed/approved; health và alert đúng |
| Restart host/service | Startup đúng thứ tự; data còn nguyên; request có policy rõ |
| Disk/inode gần đầy | Alert sớm; ingestion bị giới hạn có kiểm soát |
| Cert expiry/renewal fail | Alert/escalation trước outage |
| Backup hỏng | Bị loại; fallback restore đạt RPO/RTO |
| Cross-tenant attack | Không list/retrieve/generate/export được dữ liệu cấm |

Soak phải dài hơn peak business window (khởi đầu tối thiểu 24 giờ), dùng cùng
release candidate, workload mix/RAG ratio/token distribution/cache state đã ghi.
Định nghĩa abort threshold trước test và không chỉnh config giữa lần đo.

## 12. Xử lý sự cố nhanh

### vLLM OOM/kill hoặc latency tăng

1. Kiểm tra log, queue/running, PSI memory, kernel OOM, disk, power/temperature.
2. Phân tách queue time, TTFT, ITL và gateway/RAG latency.
3. Admission-control tải; giảm lần lượt sequence/context/memory utilization.
4. Quay về baseline không speculative/FP8 KV nếu nghi ngờ; mỗi lần chỉ đổi một biến.
5. Smoke + benchmark + quality test trước khi đóng incident.

### RAG sai hoặc nghi rò rỉ

Ngừng ingestion/share liên quan, bảo toàn audit, thu hồi access/token, xác định
file/chunk/vector/cache/trace bị ảnh hưởng. Xác minh identity/filter/ACL source,
embedding revision và dữ liệu orphan. Không reindex trước backup/forensic snapshot.

### Không có trace

Health Langfuse không đủ. Theo request ID kiểm tra instrumentation, endpoint/key,
worker/queue/store và redaction. Thực hiện policy inference khi telemetry mất và
phát alert; không để observability trở thành dependency auth ngoài thiết kế.

### Streaming/WebSocket chậm

Kiểm tra buffering, upgrade header, keepalive, proxy/upstream timeout, slow client,
CORS/cookie, cancellation và active connection. Đo gateway latency tách khỏi TTFT.

## 13. Production gate

Chỉ triển khai toàn công ty khi cùng một release candidate đáp ứng:

- [ ] Owner/approver, workload, SLO, RPO/RTO và risk acceptance đã ký.
- [ ] Image/model/embedding/config freeze bằng digest/revision và rollback pass.
- [ ] SSO/group lifecycle/admin/break-glass/access review pass.
- [ ] Cross-tenant RAG end-to-end đạt 0 incident trong matrix đã duyệt.
- [ ] Secret fallback trong current tree đã xử lý; vẫn thiếu history remediation, secret manager/rotation governance, off-host recovery key và encrypted backup drill.
- [ ] Chỉ gateway expose; IPv4/IPv6 scan và negative-auth pass.
- [ ] Benchmark/soak đạt SLO tại achieved goodput với capacity headroom.
- [ ] Overload/cancellation/dependency/host/disk/cert failure test pass.
- [ ] Trace/metric/log/audit/redaction/retention và alert test pass.
- [ ] Clean-room restore và release rollback đạt RPO/RTO.
- [ ] HA/failover đúng availability cam kết hoặc có business acceptance rõ ràng.
- [ ] Data, Security, Legal, Operations và AI Quality phê duyệt.

Review lại sau 24 giờ và 7 ngày mỗi rollout wave. Không mở wave tiếp theo nếu có
P0 mới, SLO fail hoặc headroom thấp hơn ngưỡng đã duyệt. Dùng
`scripts/rollout_wave_gate.py --wave-id <id>` trước khi mở traffic; gate không thay đổi
traffic và phải pass cùng approval ngoài hệ thống.

## 14. Tài liệu chính thức cần kiểm tra theo release

- [vLLM documentation](https://docs.vllm.ai/)
- [vLLM Docker deployment](https://docs.vllm.ai/en/stable/deployment/docker/)
- [vLLM engine arguments](https://docs.vllm.ai/en/latest/configuration/engine_args/)
- [vLLM security](https://docs.vllm.ai/en/latest/usage/security/)
- [vLLM benchmark CLI](https://docs.vllm.ai/en/latest/cli/bench/serve/)
- [Open WebUI environment configuration](https://docs.openwebui.com/reference/env-configuration/)
- [Open WebUI hardening](https://docs.openwebui.com/getting-started/advanced-topics/hardening/)
- [Open WebUI scaling](https://docs.openwebui.com/getting-started/advanced-topics/scaling/)
- [Langfuse self-hosting](https://langfuse.com/self-hosting)
- [Qdrant security](https://qdrant.tech/documentation/security/)
- [Qdrant distributed deployment](https://qdrant.tech/documentation/guides/distributed_deployment/)
- [Redis security](https://redis.io/docs/latest/operate/oss_and_stack/management/security/)
- [Apache Tika configuration](https://tika.apache.org/)
- [Docker Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)

Các URL `latest` chỉ dùng để đọc release notes. Cấu hình production phải bám
version/digest trong release manifest, vì nội dung trang và default có thể đổi.

## 15. Changelog tài liệu

| Ngày | Thay đổi |
| --- | --- |
| 2026-09-09 | Gộp bối cảnh, tài liệu mở rộng, canonical runbook và kế hoạch chi tiết thành `README.md` + `RUNBOOK.md`; cập nhật runtime 8 service và Tika |
| 2026-09-09 | Phân loại benchmark 2026-09-04 là historical evidence, không phải SLO proof; tách UI design reference khỏi tài liệu vận hành |
| 2026-09-04 | Audit hạ trạng thái benchmark, RAG isolation và backup/restore về blocked |
| 2026-09-03 | Loại Celery/semantic cache/fail-open khỏi kiến trúc hiện tại |
