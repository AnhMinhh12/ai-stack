# BAS-20260909-r2 — recheck bước 0

**UTC:** 2026-09-09T04:55:22Z  
**Host:** `edgexpert-f3a2`  
**Git baseline:** `154673586bf6dc971606ba8c3f12f0a067d23cb0`; worktree vẫn có thay đổi chưa commit  
**Owner/approver:** TBD / TBD  
**Trạng thái:** `blocked`.

## Kết quả runtime

| Kiểm tra | Kết quả |
| --- | --- |
| `docker compose config --quiet` | exit 0 |
| `docker compose ps --all` | 8 service Up; vLLM, Open WebUI, Qdrant, Redis, PostgreSQL, Langfuse, Nginx và Tika healthy |
| Host | ARM64, NVIDIA GB10, driver 580.173.02, Docker 29.2.1, Compose 5.0.2 |
| Model | Qwen2.5-14B snapshot `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`, alias `qwen2.5-14b`, context 16K |
| Tokenizer/chat template | tokenizer config và chat template tồn tại trong cùng model snapshot |
| Embedding | `BAAI/bge-m3`, revision `5617a9f61b028005a4858fdac845db406aefb181` |
| Backup | `backup_20260909_042815`, checksum pass, GPG decrypt-all pass, `COMPLETE` pass |
| Host exposure | chỉ gateway Nginx bind host 80/443 (IPv4/IPv6); service nội bộ không bind host port |
| Tika | healthcheck mới pass; read-only/tmpfs/cap-drop/resource limit đã áp dụng |

## Đánh giá bước 0

Đã có pilot scope draft 1–2 phòng ban, quota/SLO/RPO/RTO/abort threshold và baseline
artifact. Tuy nhiên chưa có người cụ thể ký owner/approver, workload acceptance,
risk register, retention/legal approval hoặc business risk acceptance. Ngoài ra
kernel baseline trước đây có NVRM `NV_ERR_NO_MEMORY`, cần owner chấp thuận sau điều tra.

**Gate bước 0: `blocked`.**

Evidence hết hạn sau 2026-09-16T04:55:22Z hoặc khi host/image/model/config/schema đổi.
