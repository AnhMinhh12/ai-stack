# SEC-20260909 — bước 2: secret và network hardening

**UTC:** 2026-09-09T04:55:22Z  
**Host:** `edgexpert-f3a2`  
**Git baseline:** `154673586bf6dc971606ba8c3f12f0a067d23cb0` (worktree recheck sau hardening cổng)  
**Owner/approver:** TBD / TBD  
**Trạng thái:** `blocked` — core controls pass; governance/network verification remains.

## Kết quả đã xác minh

| Hạng mục | Command/điều kiện | Kết quả |
| --- | --- | --- |
| Compose | `docker compose config --quiet` | exit 0 |
| Nginx syntax | `docker exec nginx-gateway nginx -t` | exit 0 |
| Current-tree secret fallback scan | `rg` trên scripts | pass; không còn fallback literal/default |
| `.env` permission | `stat -c %a .env` | `600` |
| Qdrant auth | missing/wrong/correct key từ network ứng dụng | `401/401/200` |
| vLLM auth | missing/wrong/correct key từ network ứng dụng | `401/401/200` |
| RAG test fail-closed | chạy khi thiếu env | exit 1; yêu cầu `QDRANT_URL` và `QDRANT_API_KEY` |
| Backup encryption | backup_20260909_042815; SHA256 + GPG decrypt-all + COMPLETE | pass; 0 plaintext state files |
| Runtime | `docker compose up -d --no-build --pull never` | network segmentation áp dụng; 8/8 service healthy sau model warmup; chỉ Nginx bind host 80/443 |

## Thay đổi

- `scripts/rag_leakage_test.py` chỉ nhận credential từ runtime environment/secret
  mechanism; không đọc `.env` và không có fallback.
- `scripts/backup.sh` không sao chép `.env`; chỉ lưu tên key/mode, yêu cầu
  `BACKUP_GPG_RECIPIENT` + GPG, mã hóa state artifacts trước checksum và ghi
  `COMPLETE` sau khi thành công.
- Xoay Qdrant key từng có trong fallback, Redis/vLLM key sau khi phát hiện output
  chẩn đoán chứa runtime value; không ghi giá trị vào evidence.
- Compose có các network `frontend`, `inference`, `ingestion`, `data` và
  `observability`; chỉ Nginx bind host ports 80/443, service nội bộ không bind host
  port; vLLM chạy offline (`HF_HUB_OFFLINE=1`).
- Nginx có request ID, rate limit, connection limit, security headers và map
  WebSocket `Connection` đúng theo Upgrade.

## Blocker còn lại

- Các `env.bak` plaintext cũ đã secure-delete; cần owner xác nhận retention/deletion
  evidence nếu muốn đóng hoàn toàn audit trail.
- GPG encrypted backup đã pass; `restore.sh` đã hỗ trợ giải mã GPG vào thư mục tạm.
  Private recovery key hiện còn local trong `.secrets/`, chưa có bản sao immutable/
  off-host và chưa có secret-manager ownership.
- Secret DB/Redis/Langfuse/TLS chưa rotation qua secret manager.
- Chưa có LAN/VPN IPv4/IPv6 scan, firewall evidence, TLS SAN/renewal test hoặc
  egress test toàn bộ service.
- Tika đã có healthcheck/resource/read-only/tmpfs/cap-drop; quarantine/malware
  control vẫn chưa có. `ipc: host` vẫn cần risk review.
- Negative-auth chứng minh service-level auth cho vLLM/Qdrant, chưa chứng minh IAM/RAG
  authorization end-to-end qua Open WebUI.

Evidence hết hạn khi image/model/config/schema đổi hoặc sau 2026-09-16T04:55:22Z.
