# Pilot scope — bản draft chờ phê duyệt

**Ngày:** 2026-09-09  
**Trạng thái:** `target`, chưa phải approval.

## Phạm vi đề xuất

- Pilot giới hạn **1–2 phòng ban**, tối đa 30 người dùng được cấp quyền.
- Use case: chat nội bộ, tóm tắt tài liệu và RAG trên tài liệu đã phân loại.
- Không cho phép `restricted`, dữ liệu có legal hold, dữ liệu khách hàng chưa được phê duyệt, secret/credential, dữ liệu HR nhạy cảm hoặc upload tự do từ Internet.
- Tạm thời chỉ dùng trong mạng/VPN doanh nghiệp qua gateway; single-host là giới hạn và không cam kết HA.

## Tiêu chí tạm thời cần owner ký

| Hạng mục | Draft để duyệt |
| --- | --- |
| Giờ cao điểm | 09:00–11:00 và 14:00–16:00 UTC, cần thay bằng giờ nghiệp vụ địa phương |
| Quota | 20 request/phút/user; 200 request/phút/pilot; batch bị giới hạn riêng |
| SLO tạm thời | TTFT p95 < 1,5 s; ITL p95 < 50 ms/token; success ≥ 99% |
| Availability | 99,0% trong pilot; không gọi single-host là HA |
| RPO/RTO | Draft RPO ≤ 24 h, RTO ≤ 4 h; phải được Operations/Data duyệt |
| Abort | Cross-tenant leak, secret exposure, backup/restore fail, OOM loop, hoặc SLO fail trong 2 cửa sổ đo liên tiếp |
| Retention | Chưa chốt; Data/Legal phải duyệt riêng cho chat, file, vector, trace và backup |

## Owner/approver bắt buộc

| Vai trò | Người cụ thể | Trạng thái |
| --- | --- | --- |
| Platform | TBD | `blocked` |
| Security | TBD | `blocked` |
| Data | TBD | `blocked` |
| Operations | TBD | `blocked` |
| AI Quality | TBD | `blocked` |
| Business owner | TBD | `blocked` |

Không dùng các giá trị draft làm cam kết vận hành nếu chưa có chữ ký/phê duyệt và evidence có expiry.
