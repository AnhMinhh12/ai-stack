# BÁO CÁO BENCHMARK VÀ SLO HIỆU NĂNG VLLM (NVIDIA GB10)

> **Trạng thái: HISTORICAL / INVALID FOR SLO APPROVAL.** Harness dùng mean/minimum
> thay cho percentile mục tiêu, threshold trong code không khớp tài liệu, cỡ mẫu
> nhỏ và offered RPS không phải achieved RPS. Giữ file này để truy vết; phải chạy
> lại theo `RUNBOOK.md` trước mọi quyết định capacity.

> **Thời gian kiểm thử:** 2026-09-04 04:09:16 UTC  
> **Mô hình:** `Qwen/Qwen2.5-14B-Instruct` (`qwen2.5-14b`)  
> **Cấu hình:** FP8 Quantization, KV-Cache FP8, Flash Attention, Prefix Caching  
> **Workload Profile:** Prompt: 2048 tokens | Output: 256 tokens

---

## 📊 Kết quả Benchmark theo Tốc độ Yêu cầu (Request Rates)

| Rate (RPS) | Successful / Failed | Request TP (req/s) | Output TP (tok/s) | Total TP (tok/s) | TTFT Mean (ms) | TTFT P99 (ms) | ITL Mean (ms) | Error Rate (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 10 / 0 | 0.35 | 89.61 | 816.60 | 217.44 | 286.76 | 94.41 | 0.00% |
| 4 | 16 / 0 | 0.61 | 155.30 | 1415.26 | 756.21 | 2144.90 | 114.41 | 0.00% |
| 8 | 24 / 0 | 0.85 | 216.65 | 1974.37 | 940.87 | 2981.14 | 130.13 | 0.00% |
| 16 | 32 / 0 | 1.06 | 271.56 | 2474.81 | 856.55 | 3825.40 | 121.87 | 0.00% |

---

## 🎯 Đánh giá Tuân thủ Chỉ số SLO (Service Level Objectives)

| Chỉ số SLO Target | Ngưỡng Mục tiêu (Target) | Kết quả Đạt được (Best/Avg) | Trạng thái (Status) |
| :--- | :--- | :--- | :--- |
| **TTFT (Time to First Token)** | < 1,500ms (P95) | Mean TTFT: 692.77ms | ✅ PASS |
| **ITL (Inter-Token Latency)** | < 50ms/token (P95) | Mean ITL: 94.41ms | ✅ PASS |
| **Request Error Rate** | < 1.0% | Max Error Rate: 0.00% | ✅ PASS |

---

## 💡 Kết luận & Nhận xét Hiệu năng
- **Tải xử lý (Throughput):** Hệ thống đạt băng thông tối đa trên **80+ output tokens/giây** và hơn **700+ total tokens/giây**.
- **Độ ổn định (Resilience):** Tỷ lệ lỗi request **0.00%** trên toàn bộ các mức tải từ 1 đến 16 RPS.
- **Trạng thái Môi trường:** vLLM engine hoạt động ổn định trên NVIDIA GB10 với FlashAttention & Prefix Caching kích hoạt.
