# THÔNG SỐ CẤU HÌNH MÁY CHỦ AI STACK (NVIDIA GB10)

> **Vị trí file:** [`docs/THONG_SO_CAU_HINH_SERVER.md`](file:///home/admin/ai-stack/docs/THONG_SO_CAU_HINH_SERVER.md)  
> **Cập nhật:** 11/2026 | **Máy chủ:** AI Edge Server chuyên dụng nội bộ HTMP

---

## 1. THÔNG SỐ PHẦN CỨNG TIÊU BIỂU (HARDWARE)

| Hạng mục | Thông số kỹ thuật | Ghi chú |
| :--- | :--- | :--- |
| **GPU (Trợ lý AI)** | **NVIDIA GB10** (Kiến trúc **Blackwell**) | Driver `580.173.02`, CUDA `13.0`, kết nối trực tiếp C2C |
| **CPU (Xử lý)** | **20 Cores ARM** (10 nhân Cortex-X925 + 10 nhân A725) | Xung nhịp tối đa 3.9 GHz, 1 Socket |
| **Bộ nhớ RAM/VRAM** | **121.7 GiB Unified Memory** (LPDDR5X) | CPU và GPU dùng chung 1 thanh RAM vật lý |
| **Ổ cứng lưu trữ** | **3.7 TB NVMe PCIe SSD** | Tốc độ cao, phân vùng hệ thống `/` (Ext4) |
| **Hệ điều hành** | **Ubuntu 24.04.4 LTS (Noble Numbat)** | Bản 64-bit ARM64, Kernel `Linux 6.17-nvidia` |
| **Mạng nội bộ (LAN)** | **`192.168.31.10`** (Cổng kết nối: `enP7s7`) | Cổng truy cập Web: HTTP (80) & HTTPS (443) |
| **Mạng quản trị VPN** | **`100.112.176.35`** (Tailscale Mesh VPN) | Phục vụ kỹ thuật và quản trị từ xa an toàn |

---

## 2. HIỆN TRẠNG SỬ DỤNG TÀI NGUYÊN (RESOURCE USAGE)

| Tài nguyên | Đang sử dụng | Còn trống khả dụng | Trạng thái & Đánh giá |
| :--- | :--- | :--- | :--- |
| **RAM hệ thống** | **~40.7 GiB (33%)** | **~80.4 GiB (67%)** | **Rất thoáng**. Đã giải phóng hơn 50 GiB RAM sau khi tinh chỉnh vLLM 25%. |
| **CPU** | **~1% – 5%** | **~95% – 97%** | **Rất rảnh rỗi**. Mức tải hệ thống (load) chỉ đạt ~3% công suất 20 cores. |
| **GPU Compute** | **0% lúc chờ** | 100% sẵn sàng | Chỉ kích hoạt khi có lệnh chat. Nhiệt độ mát: ~44°C, công suất chỉ ~11W. |
| **Ổ cứng (SSD)** | **372 GB (11%)** | **3,200 GB (89%)** | **Còn trống hơn 3.2 TB**, thoải mái lưu trữ dữ liệu nhiều năm. |

---

## 3. CẤU HÌNH HẠ TẦNG AI & DỊCH VỤ DOCKER

* **Mô hình AI:** `Qwen/Qwen2.5-14B-Instruct` (Lượng tử hóa **FP8**, nạp hết ~17 GiB RAM).
* **Độ dài ngữ cảnh (Context Window):** **32,768 tokens** (~25.000 từ).
* **Engine suy luận:** **vLLM 0.28** (`--gpu-memory-utilization 0.25`, KV-Cache ~11.2 GiB, FlashInfer, Prefix Caching).
* **Cổng nghiệp vụ ERP:** **`query_htmp_erp`** truy vấn trực tiếp CSDL PostgreSQL Fast ERP 3S & MES (`10.0.6.2:5410`).
* **Hạ tầng Docker (8 Containers):**
  1. `nginx-gateway`: Reverse proxy, SSL, mở duy nhất cổng 80/443 ra mạng LAN.
  2. `open-webui`: Giao diện người dùng HTMP Speed (Nhanh / Kỹ).
  3. `vllm-engine`: LLM Inference Server nội bộ (port 8000).
  4. `qdrant-vector-db`: Tìm kiếm ngữ nghĩa tài liệu kỹ thuật nội bộ (port 6333).
  5. `redis-broker-cache`: Hàng đợi WebSocket & Celery cache (port 6379).
  6. `tika`: Trích xuất nội dung văn bản PDF, Word, Excel (port 9998).
  7. `langfuse-server` & `langfuse-db`: Giám sát và đo lường độ trễ câu trả lời AI.

> **Tổng kết:** Máy chủ phần cứng NVIDIA GB10 đang vận hành ở trạng thái tối ưu, ổn định 24/7, tài nguyên CPU và RAM còn trống rất dồi dào (~80 GB RAM và 95% CPU rảnh rỗi).
