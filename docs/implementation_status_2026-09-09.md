# Đánh giá triển khai bước 0–1

**Ngày evidence:** 2026-09-09T03:26:48Z  
**Git baseline:** `154673586bf6dc971606ba8c3f12f0a067d23cb0`  
**Trạng thái:** `blocked` — core bước 2 đã harden/pass; chưa được phép promotion/pilot dữ liệu nhạy cảm.

## Kết quả

| Bước | Kết quả | Lý do |
| --- | --- | --- |
| 0 — phạm vi, tiêu chí, baseline | `blocked` | Đã có draft scope và baseline evidence, nhưng owner/approver, SLO/RPO/RTO/risk acceptance chưa được người có thẩm quyền ký. |
| 1 — release/supply chain | `blocked` | Đã pin 7 image registry và base image; image Open WebUI custom còn local tag, embedding revision đã xác minh; SBOM/CVE/license scan chưa chạy. |

## Đã thực hiện

- Pin digest cho vLLM, Qdrant, Redis, PostgreSQL, Langfuse, Nginx và Tika trong `docker-compose.yml`.
- Pin base image Open WebUI trong `Dockerfile.openwebui` bằng digest.
- Tạo [pilot scope và tiêu chí draft](pilot-scope.md).
- Tạo [baseline evidence](evidence/BAS-20260909/baseline.md) và [release manifest](evidence/REL-20260909/release-manifest.yaml).
- `docker compose config --quiet` pass sau thay đổi.

## Việc còn thiếu trước khi qua gate

1. Business owner, Platform, Security, Data, Operations và AI Quality ký owner/approver; duyệt pilot scope, quota, workload, SLO tạm thời, abort threshold, RPO/RTO và risk register.
2. Build/publish custom Open WebUI từ Dockerfile đã pin, lấy registry digest của final image; không dùng `open-webui-htmp:libreoffice` local tag cho release.
3. Đã xác minh immutable revision của `BAAI/bge-m3`, tokenizer/chat template; vẫn cần chốt dimension/schema collection trong manifest.
4. Chạy SBOM + CVE/license scan trên toàn bộ final images và custom package build; lưu raw output, policy, owner và expiry.
5. Điều tra và xử lý các lỗi NVIDIA `NV_ERR_NO_MEMORY` trong kernel log trước khi chạy capacity gate.
6. Commit các thay đổi, tạo release tag/commit bất biến và chạy lại manifest, compose validation, smoke test và rollback command theo digest.

Các P0 khác trong RUNBOOK (secret fallback/backup plaintext, network/IAM/RAG authorization, observability, DR và capacity harness) vẫn mở; không được coi bước 0–1 là production readiness.
