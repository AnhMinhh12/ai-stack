# BAS-20260909 — host/runtime baseline

**UTC:** 2026-09-09T03:26:48Z  
**Owner/approver:** TBD / TBD  
**Host:** `edgexpert-f3a2`  
**Git:** `154673586bf6dc971606ba8c3f12f0a067d23cb0` (worktree sau đó có thay đổi)  
**Expiry:** 2026-09-16T03:26:48Z hoặc sớm hơn nếu image/model/config/schema đổi.

## Commands và kết quả

| Command | Exit | Raw result tóm tắt |
| --- | ---: | --- |
| `uname -a` | 0 | Linux 6.17.0-1031-nvidia, `aarch64` |
| `nvidia-smi --query-gpu=name,driver_version,memory.total,temperature.gpu,power.draw --format=csv,noheader` | 0 | NVIDIA GB10; driver 580.173.02; memory `N/A`; 44 C; 11.42 W |
| `docker version --format '{{.Server.Version}}'` | 0 | 29.2.1 |
| `docker compose version` | 0 | v5.0.2 |
| `docker compose config --quiet` | 0 | pass sau khi pin digest |
| `docker compose ps --all` | 0 | 8 services Up; 7 healthy; Tika Up nhưng chưa có healthcheck |
| `free -h` | 0 | 121 GiB total; 103 GiB used; 17 GiB available; swap 15 GiB |
| `df -h .` | 0 | 3.7T total; 232G used; 3.3T available; 7% |
| `df -i .` | 0 | inode usage 1% |
| `/proc/pressure/memory` | 0 | avg10/60/300 đều 0.00 tại thời điểm đo |
| `curl -fsS http://127.0.0.1:8000/v1/models` | 0 | root `Qwen/Qwen2.5-14B-Instruct`; alias `qwen2.5-14b`; max model len 16384 |

## Baseline identity

- vLLM đang chạy model alias `qwen2.5-14b`, FP8 weight/KV, context 16K và max 64 sequences theo Compose; model snapshot runtime là `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`.
- Embedding được cấu hình là `BAAI/bge-m3`, nhưng revision/dimension/schema chưa được xác minh từ runtime; không coi là verified.
- Public host exposure vẫn là Nginx `0.0.0.0/[::]:80,443`; kiểm tra LAN/VPN, IPv4/IPv6 và firewall chưa thực hiện trong evidence này.
- Không ghi lại giá trị `.env`; secret chỉ được xác nhận là có các key runtime.
- Kernel log có nhiều lỗi NVIDIA `Out of memory (NV_ERR_NO_MEMORY)` vào 2026-08-31, 2026-09-04 và 2026-09-07; chưa xác định nguyên nhân/ảnh hưởng, phải điều tra trước khi phê duyệt capacity.

## Kết luận

Baseline host/runtime đã thu thập được nhưng **chưa đạt điều kiện qua bước 0** vì owner/approver, pilot acceptance, SLO/RPO/RTO và risk register chưa được ký; ngoài ra còn NVRM OOM cần điều tra.
