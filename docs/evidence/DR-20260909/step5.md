# DR-20260909 — bước 5: backup/restore và kiểm thử DR

**UTC:** 2026-09-09  
**Host:** `edgexpert-f3a2`  
**Trạng thái:** `blocked` — hardening code pass; artifact/clean-room drill pending.

## Đã kiểm tra

| Kiểm tra | Kết quả |
| --- | --- |
| `bash -n scripts/backup.sh scripts/restore.sh` | pass |
| Backup hiện có | `backup_20260909_042815` checksum pass trước preflight |
| `RESTORE_MODE=clean-room bash scripts/restore.sh ...` | fail closed đúng |
| Lý do fail | decrypted `open_webui_data.tar.gz` chỉ 87 bytes, bị size check từ chối |
| Production safety | Không drop schema, không ghi volume trong preflight |

## Thay đổi

- Backup resolve volume runtime, tạo manifest và mapping collection; không còn giả định tên
  volume hoặc parse collection bằng phần trước dấu gạch dưới.
- Backup kiểm tra kích thước bất thường trước encryption.
- Restore mặc định là clean-room preflight; production restore cần hai cờ xác nhận explicit.
- Restore kiểm tra checksum, GPG decrypt, kích thước, gzip và tar trước khi thực hiện.

## Chưa thể đóng

- Backup mới theo format này chưa chạy do cần approval cho side effect tạo snapshot/encryption/retention.
- Backup hiện có chứa artifact bất thường 87 bytes, nên không đủ điều kiện restore.
- Chưa có clean-room project/volume, application smoke flow, record/vector/ACL comparison và RPO/RTO evidence.

Không dùng evidence này để tuyên bố DR đã đạt; preflight fail đúng là điều kiện an toàn,
nhưng clean-room restore thành công vẫn còn bắt buộc.
