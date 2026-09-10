# Shared platform architecture — bước 8

**Trạng thái:** `target architecture — not approved for implementation`

## Mục tiêu

Shared platform chỉ được thiết kế sau khi pilot đạt gate. Single-host Compose hiện tại
không phải HA và không được gọi là shared platform.

## Kiến trúc mục tiêu

```text
Users/IdP + MFA
      |
Enterprise CA / canonical DNS
      |
HA gateway/LB + WAF + rate/token admission
      |
Stateless Web/API replicas ---- OTel/metrics/log/audit
      |                         \---- Langfuse/observability HA
      +--> model router/admission --> N+1 GPU inference pool
      +--> RAG service --> Qdrant replicated + ACL metadata
      +--> ingestion queue --> sandboxed Tika workers + quarantine/DLQ
      +--> external DB/object storage/session/cache
```

## Bắt buộc trước khi xây dựng

- Canonical hostname, enterprise CA, certificate renewal/expiry alert và WAF policy.
- OIDC/SAML + MFA, group/tenant mapping, quota, token budget và admission control.
- Stateless application; database, uploads/object storage, sessions và cache externalized.
- Qdrant replication/sharding, payload index/ACL schema, reindex và failover drill.
- Redis HA/ACL/noeviction; PostgreSQL HA/PITR/pool/migration rollback.
- Tika worker sandbox: queue, concurrency/quota, timeout/cancellation, quarantine,
  malware/content control, dead-letter và deny egress.
- OTel/metrics/log/audit pipeline có redaction, pseudonymization, retention/RBAC và
  alert owner/on-call.
- N+1 GPU/failover, capacity model, cost forecast và failure matrix.

## Không được triển khai như sau

- Không gọi hai container cùng host là HA.
- Không dùng API key service-level thay cho per-user/tenant authorization.
- Không dùng local volume làm shared durable state.
- Không mở traffic trước khi pilot, DR, capacity và security gates pass.

## Điều kiện chuyển bước 8

Bước 8 chỉ chuyển sang implementation khi bước 7 đã đạt pilot acceptance, có business
case, availability/SLO/RPO/RTO/cost target được ký và có owner cho từng control plane/data
plane.
