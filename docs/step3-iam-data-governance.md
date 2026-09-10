# Bước 3 — IAM và quản trị dữ liệu

**Trạng thái:** `partial — technical baseline implemented; IdP/application ACL pending`

## Phạm vi và nguyên tắc

- Mặc định deny; không cho phép public signup. Tài khoản phải được provision từ
  IdP hoặc quy trình break-glass được phê duyệt.
- Identity, group và quyền truy cập phải được tạo từ server-side identity context;
  không tin `tenant_id`, `owner_id`, `classification` hoặc ACL do client gửi.
- Tài liệu/chunk không được truy cập nếu thiếu tenant, owner, classification hoặc
  source ACL hợp lệ. Metadata thiếu hoặc sai phải fail closed.
- Admin và break-glass là hai vai trò riêng; break-glass phải có thời hạn, lý do,
  người phê duyệt và audit event.
- Audit chỉ lưu pseudonymous subject/tenant, action, decision, request ID và
  resource ID; không ghi prompt, output, file content, secret hoặc Authorization header.

## Phân loại dữ liệu và use case pilot

| Classification | Cho phép trong pilot | Yêu cầu tối thiểu |
| --- | --- | --- |
| `public` | Có | Owner, source, version, retention |
| `internal` | Có nếu Business owner duyệt | Tenant/group ACL, retention, deletion status |
| `confidential` | Chưa mặc định; chỉ khi Security/Data duyệt | IdP/MFA, source ACL, legal basis, audit và egress review |
| `restricted` | Không trong pilot hiện tại | Phê duyệt riêng, residency/legal hold và kiểm soát tăng cường |

Use case pilot chỉ gồm chat nội bộ, tóm tắt và RAG trên `public`/`internal` đã
được duyệt. Không đưa dữ liệu `restricted`, secrets, credentials, dữ liệu cá nhân
nhạy cảm hoặc dữ liệu chịu legal hold vào pilot trước khi có approval.

## Metadata contract bắt buộc

Mỗi document và chunk phải có các trường sau trong source-of-truth và payload/index
được kiểm soát:

| Field | Quy tắc |
| --- | --- |
| `tenant_id` | Sinh từ authenticated identity/group server-side; không nhận tin từ client |
| `owner_id` | Subject/group sở hữu; phải tồn tại trong IdP/source-of-truth |
| `classification` | Một trong `public`, `internal`, `confidential`, `restricted` |
| `source_acl` | Danh sách group/subject được phép; rỗng nghĩa là deny, không phải public |
| `version` | Monotonic/versioned; cập nhật phải tạo audit event |
| `retention_until` | UTC timestamp hoặc policy reference; quá hạn phải được xử lý |
| `deletion_status` | `active`, `pending_delete`, `deleted`, `legal_hold` |

Invariant bắt buộc: `tenant_id` của request phải khớp metadata; group intersection
với `source_acl` phải khác rỗng; chỉ `active` và đúng retention mới được retrieve;
`legal_hold` chặn deletion tự động.

## Role/group baseline

| Role | Quyền mặc định |
| --- | --- |
| `user` | Chat/search trong knowledge base được cấp; không export/share/admin |
| `knowledge-owner` | Upload/update/delete tài nguyên thuộc owner/group sau audit |
| `security-auditor` | Đọc audit metadata, không đọc nội dung mặc định |
| `platform-admin` | Vận hành hệ thống, không mặc nhiên đọc nội dung tenant |
| `break-glass` | Quyền tạm thời, MFA, approval, expiry và audit bắt buộc |

## Dependency chưa thể đóng trong workspace

- OIDC/SAML, MFA, group mapping, provisioning/deprovisioning và access review cần
  IdP doanh nghiệp, metadata group và owner được chỉ định.
- Open WebUI custom image hiện không có source middleware ACL trong repository; policy
  này chưa chứng minh được authorization end-to-end qua upload/list/search/retrieve/chat
  và share/export/delete/revoke.
- Cần test với hai user/hai group thật, IDOR/filter tampering/prompt injection và
  kiểm tra cache/trace/backup không vượt tenant boundary.
