# OBS-20260909 — bước 4: observability và trực vận hành

**UTC:** 2026-09-09T06:23:24Z  
**Host:** `edgexpert-f3a2`  
**Trạng thái:** `blocked` — gateway baseline pass; end-to-end instrumentation/alerting pending.

## Evidence đã kiểm tra

| Kiểm tra | Kết quả |
| --- | --- |
| `python3 scripts/step4_observability_check.py` | pass toàn bộ static checks |
| `docker exec nginx-gateway nginx -t` | pass |
| Gateway smoke `/health?step4_probe=redaction-test` | HTTP 200 |
| Gateway access log | Có method + URI không query string, timing và server-side request ID |
| Gateway log redaction | Không ghi query string, referer, user-agent, body hoặc auth header trong format mới |
| Runtime health | 8/8 service healthy trước/sau reload Nginx |
| Langfuse | Container/health endpoint healthy; chưa có trace end-to-end evidence |

## Đã triển khai

- Nginx ghi access log ra container stdout, error log ra stderr để có thể áp dụng log rotation; format chỉ giữ URI, status, timing và request ID.
- Nginx forward `X-Request-ID` server-side tới Open WebUI.
- Tạo [observability policy](../../step4-observability-policy.md) cho correlation, redaction, pseudonymous identity, retention, signal và alert ownership.
- Tạo `scripts/step4_observability_check.py` để kiểm tra fail khi mất request ID hoặc log có nguy cơ chứa query/body/auth data.

## Chưa thể xác nhận

- Chưa có SDK/OTel hoặc middleware nối Open WebUI → retrieval/Tika/Qdrant → vLLM → Langfuse.
- Chưa có request thành công/lỗi được truy vết cùng ID xuyên toàn pipeline.
- Chưa có dashboard/metric backend, alert rule, owner/on-call, escalation hoặc test notification.

Không được dùng evidence này để tuyên bố bước 4 đã hoàn tất; healthcheck Langfuse chỉ chứng minh process sống, không chứng minh trace ingestion.
