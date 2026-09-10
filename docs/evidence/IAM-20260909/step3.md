# IAM-20260909 — bước 3: IAM và quản trị dữ liệu

**UTC:** 2026-09-09T06:15:27Z  
**Host:** `edgexpert-f3a2`  
**Trạng thái:** `blocked` — technical baseline pass; IdP/application ACL evidence còn thiếu.

## Evidence đã kiểm tra

| Kiểm tra | Kết quả |
| --- | --- |
| `docker compose config --quiet` | pass |
| Runtime service health | 8/8 service healthy |
| Open WebUI public signup | `ENABLE_SIGNUP=False` trong container runtime |
| `python3 scripts/step3_policy_check.py` | pass toàn bộ policy baseline |
| Metadata contract | Có đủ tenant, owner, classification, source ACL, version, retention và deletion status trong policy |
| Deny-by-default/break-glass/legal hold | Đã định nghĩa trong policy |

## Đã triển khai

- Khóa public signup bằng cấu hình Compose bất biến; không còn lấy giá trị từ `.env`.
- Tạo [IAM/data-governance policy](../../step3-iam-data-governance.md) gồm classification, use-case pilot, metadata contract, role baseline, retention/legal hold và audit redaction.
- Tạo `scripts/step3_policy_check.py` để fail khi policy baseline hoặc signup hardening bị thiếu.

## Chưa thể xác nhận

- OIDC/SAML, MFA, group mapping, provisioning/deprovisioning và access review.
- Server-side identity/filter enforcement trong Open WebUI custom application path.
- Hai user/hai group E2E cho upload, list, search, retrieve, chat, share/export, delete, revoke, IDOR, filter tampering, semantic query, prompt injection và cache/trace/backup.

Không được dùng evidence này để tuyên bố bước 3 đã hoàn tất; cần IdP, application ACL và test matrix có user/group thật trước khi chuyển trạng thái.
