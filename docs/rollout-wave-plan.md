# Rollout theo wave — bước 9

**Trạng thái:** `blocked — process ready, production gates pending`

## Nguyên tắc

- Mỗi wave dùng một release candidate bất biến, có manifest, backup, rollback command
  và owner/approver cụ thể.
- Mở traffic theo canary nhỏ; không mở wave tiếp theo nếu P0, SLO, ACL, trace/redaction,
  DR hoặc headroom fail.
- Dữ liệu phải được phân loại và ACL review trước khi cấp quyền. Không đưa `restricted`,
  legal hold, secret/credential hoặc dữ liệu chưa duyệt vào wave.
- Review bắt buộc sau 24 giờ và 7 ngày; kết quả phải có UTC, raw metrics, incident,
  orphan-data review, cost và feedback.

## Wave template

Mỗi wave phải lưu file `docs/rollout-waves/<wave-id>.yaml` với tối thiểu:

```yaml
wave_id: WAVE-001
status: blocked
user_group: TBD
data_classification: TBD
owner: TBD
approvers: [TBD]
quota: TBD
acl_review: TBD
release_manifest: TBD
backup_id: TBD
rollback_command: TBD
capacity_headroom: TBD
abort_threshold: TBD
review_24h_utc: TBD
review_7d_utc: TBD
```

## Checklist mở wave

- [ ] `scripts/rollout_wave_gate.py --wave-id <id>` pass.
- [ ] Pilot/production approval có chữ ký của Data, Security, Legal, Operations, AI Quality
  và Business owner.
- [ ] Release, backup/restore, rollback, IAM/RAG, observability và capacity evidence pass.
- [ ] Canary scope, quota, on-call và abort action được thông báo.
- [ ] Traffic mở từng đợt; ghi timestamp bắt đầu/kết thúc và metric baseline.

## Review 24 giờ / 7 ngày

Review SLO, 4xx/5xx/429, latency, capacity/headroom, ACL denies/leak indicators, trace
redaction, orphan data, backup age, incidents, cost và feedback. Một P0 hoặc abort
threshold violation phải dừng wave, rollback theo manifest và tạo incident.
