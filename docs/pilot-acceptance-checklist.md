# Pilot acceptance checklist — bước 7

**Trạng thái:** `blocked — checklist ready, approval/evidence pending`

## Gate trước staging

- [ ] Release manifest đã freeze: Git commit/tag, image digest, model/embedding revision, config hash.
- [ ] Backup mới checksum/encryption/COMPLETE pass; rollback command và owner đã duyệt.
- [ ] Owner, Security, Data, Operations, AI Quality và Business owner ký pilot scope.
- [ ] Dữ liệu pilot chỉ `public`/`internal` đã duyệt; quota, retention, RPO/RTO và abort threshold đã ký.
- [ ] IAM/IdP/MFA/group mapping và break-glass đã test.

## Staging smoke

- [ ] `docker compose config --quiet`, deployment và all-health pass.
- [ ] Model root/alias/revision đúng; streaming và non-streaming pass.
- [ ] Context 4K/8K/16K có hành vi đúng; request quá giới hạn fail rõ ràng.
- [ ] Upload → Tika parse → index → retrieve → generate → delete pass với dữ liệu test.
- [ ] User ngoài group bị deny list/retrieve/generate/delete; deny có audit redacted.
- [ ] Client disconnect giải phóng generation/slot; dependency outage fail closed.

## Security/quality/capacity

- [ ] Cross-tenant matrix hai user/hai group đạt 0 leak.
- [ ] Trace/log/metric/audit cùng request ID; prompt/output/secret được redacted.
- [ ] Benchmark matrix và soak đạt SLO với headroom đã duyệt.
- [ ] Clean-room restore và rollback đạt RPO/RTO.

## Pilot operation

- [ ] Theo dõi 24 giờ và 7 ngày; có on-call/escalation.
- [ ] Review SLO, ACL, incident, orphan data, trace/redaction, chi phí và feedback.
- [ ] Không có P0 mới hoặc abort threshold violation.

Không coi `docker compose ps` healthy là pilot acceptance; mọi checkbox cần evidence
ID, UTC timestamp, owner, raw result, expiry và approval.
