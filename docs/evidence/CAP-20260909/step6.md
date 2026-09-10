# CAP-20260909 — bước 6: benchmark và capacity

**UTC:** 2026-09-09  
**Host:** `edgexpert-f3a2`  
**Trạng thái:** `blocked` — harness/dry-run pass; runtime load/soak pending approval.

## Evidence đã kiểm tra

| Kiểm tra | Kết quả |
| --- | --- |
| `python3 scripts/benchmark_vllm.py` | dry-run pass; không tạo GPU load |
| Default matrix | 48 cases: 4K/8K/16K × concurrency 8/16/32/64 × rate 1/4/8/16 |
| `python3 tests/test_benchmark_vllm.py` | 3/3 pass |
| Parser missing percentile | fail-closed bằng `ValueError` |
| Real execution guard | từ chối nếu thiếu `BENCHMARK_APPROVED=YES` hoặc `--execute` |
| vLLM CLI | hỗ trợ lưu detailed JSON và p50/p95/p99 cho TTFT/ITL/E2E |

## Đã sửa

- Harness không còn default zero/mean/minimum khi thiếu metric.
- Ghi result JSON theo từng case, workload metadata, success/error và percentile.
- Có SLO gate: TTFT p95 < 1.5s, ITL p95 < 50ms/token, success >= 99%.

## Chưa thể xác nhận

- Chưa có runtime capacity result, achieved goodput, queue/KV/OOM/restart,
  power/temperature hoặc quality score.
- Chưa chạy ma trận thật, cold/warm prefix cache, speculative decoding A/B hoặc soak 24h.
- Chưa có owner approval cho workload, abort threshold, cửa sổ đo và headroom.

Không được dùng artifact benchmark lịch sử 2026-09-04 để đóng capacity gate.
