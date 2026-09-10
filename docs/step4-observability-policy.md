# Bước 4 — Observability, audit và trực vận hành

**Trạng thái:** `partial — gateway baseline implemented; end-to-end instrumentation pending`

## Correlation contract

- Gateway sinh `request_id` server-side và gửi `X-Request-ID` tới Open WebUI.
- Application phải giữ request ID khi gọi retrieval, Tika, Qdrant, vLLM và Langfuse.
- Trace fields tối thiểu: pseudonymous subject/tenant, request ID, route/action,
  model revision, retrieval outcome, latency, token counters và error class.
- Không dùng request ID do client tự đặt làm bằng chứng identity; nếu nhận header từ
  client thì gateway phải ghi đè bằng ID server-side.

## Redaction và retention

Không được ghi vào access log, metric label hoặc trace: prompt, model output, file
content, embedding/vector, Authorization/API key, cookie/session token, email nguyên
dạng hoặc tenant name nhạy cảm. Dùng pseudonymous subject/tenant và resource ID.

Mọi retention phải được Data/Legal duyệt riêng cho access log, audit event, trace,
chat, file, vector và backup. Khi chưa có approval, không coi retention mặc định là
đã được chấp nhận; áp dụng giới hạn kỹ thuật và ghi owner còn thiếu.

## Tín hiệu và alert baseline

| Signal | Alert condition | Severity | Runbook/owner |
| --- | --- | --- | --- |
| Gateway | 5xx/429 tăng, upstream latency, TLS expiry | P1/P2 | Network/Platform |
| Open WebUI | 5xx, auth/ACL deny spike, upload/index failure | P1/P2 | Platform/Security |
| vLLM | queue, TTFT/ITL, KV pressure, OOM/preemption | P1/P2 | AI Platform |
| RAG/Tika/Qdrant | parse/search error, filter deny, stale/orphan data | P1/P2 | Data/AI Quality |
| Redis/PostgreSQL/Langfuse | memory/AOF/DB/trace ingestion failure | P1/P2 | Operations |
| Host/DR | disk/inode, GPU memory, backup age/restore failure | P0/P1 | Operations |

Mỗi alert trước production phải có owner, severity, escalation, runbook và test
notification. Healthcheck chỉ chứng minh process sống; không chứng minh trace, metric
hay alert đã hoạt động.

## Trạng thái dependency

- Nginx request ID và log redaction đã triển khai.
- Langfuse container/health endpoint đang healthy nhưng chưa có SDK/OTel hoặc middleware
  nối request AI; chưa có trace end-to-end để xác nhận.
- Chưa có dashboard/alert backend, owner on-call hoặc test notification trong workspace.
