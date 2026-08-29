# TÀI LIỆU KỸ THUẬT: TRIỂN KHAI VÀ VẬN HÀNH HỆ THỐNG LOCAL AI
## TRÊN NỀN TẢNG MÁY CHỦ UBUNTU (MSI EDGEXPERT - NVIDIA GRACE BLACKWELL GB10)

---

## 📋 NỘI DUNG CHÍNH
1. [Tổng Quan & Cấu Hình Phần Cứng Chuyên Sâu](#1-tổng-quan--cấu-hình-phần-cứng-chuyên-sâu)
2. [Kiến Trúc Hệ Thống & Luồng Dữ Liệu](#2-kiến-trúc-hệ-thống--luồng-dữ-liệu)
3. [Chuẩn Bị Môi Trường Nền Tảng (Ubuntu ARM64)](#3-chuẩn-bị-môi-trường-nền-tảng-ubuntu-arm64)
4. [Triển Khai AI Core Engine (vLLM High-Throughput Engine)](#4-triển-khai-ai-core-engine-vllm-high-throughput-engine)
5. [Quản Lý & Tối Ưu Mô Hình AI trên 128GB Unified Memory](#5-quản-lý--tối-ưu-mô-hình-ai-trên-128gb-unified-memory)
6. [Triển Khai Giao Diện Người Dùng & RAG (Open WebUI)](#6-triển-khai-giao-diện-người-dùng--rag-open-webui)
7. [Cấu Hình Mạng, Nginx Reverse Proxy & An Ninh Bảo Mật](#7-cấu-hình-mạng-nginx-reverse-proxy--an-ninh-bảo-mật)
8. [Tối Ưu Hàng Đợi, Giám Sát Tài Nguyên & Xử Lý Sự Cố](#8-tối-ưu-hàng-đợi-giám-sát-tài-nguyên--xử-lý-sự-cố)
9. [Phụ Lục: Mẫu Docker-Compose & Tra Cứu Nhanh](#9-phụ-lục-mẫu-docker-compose--tra-cứu-nhanh)

---

## 1. TỔNG QUAN & CẤU HÌNH PHẦN CỨNG CHUYÊN SÂU

Tài liệu này hướng dẫn chi tiết quy trình triển khai và vận hành hệ thống AI Local phục vụ nội bộ doanh nghiệp trên máy chủ chuyên dụng **MSI EdgeXpert-55SVN**. Hệ thống kết hợp giữa nền tảng phần cứng kiến trúc **NVIDIA Grace Blackwell (GB10 Superchip)** và giải pháp phần mềm mã nguồn mở chuẩn Doanh nghiệp (vLLM, Open WebUI, Qdrant, Redis, Langfuse, Docker, Nginx).

### 1.1. Bảng Thông Số Kỹ Thuật Chi Tiết

| Thành phần | Thông số chi tiết | Đánh giá & Vai trò trong hệ thống Local AI |
| :--- | :--- | :--- |
| **Model Máy chủ** | MSI EdgeXpert-55SVN (`9S6-C9311-55S`) | Thiết kế Mini Server công nghiệp (150mm x 150mm x 50.5mm), hoạt động bền bỉ 24/7. |
| **Vi xử lý (CPU)** | Arm 20-core CPU | Đảm nhiệm tác vụ hệ điều hành, điều phối container, xử lý logic RAG và dữ liệu đầu vào. |
| **Hệ thống AI (GPU)** | NVIDIA GB10 Grace Blackwell Superchip | Kiến trúc Blackwell thế hệ mới, đạt **1 PFLOPS hiệu năng FP4 AI**, tối ưu cho LLM thế hệ mới. |
| **Bộ nhớ (RAM/VRAM)** | **128GB Coherent Unified System Memory** | **Điểm mấu chốt:** Bộ nhớ đồng nhất (Unified Memory) cho phép CPU và GPU chia sẻ toàn bộ 128GB. Giúp load các mô hình AI lớn đến **70B - 72B Parameters** trực tiếp mà không bị giới hạn PCIe bus. |
| **Ổ cứng lưu trữ** | **4TB NVMe M.2 SSD** (Self-Encrypting - SED) | Tốc độ đọc/ghi dữ liệu siêu nhanh, hỗ trợ mã hóa phần cứng bảo vệ trọng số AI Model và CSDL nội bộ. |
| **Card mạng (NIC)** | **NVIDIA ConnectX-7 SmartNIC** + Wi-Fi/BT | Chuẩn kết nối băng thông siêu cao, sẵn sàng cho hạ tầng mạng doanh nghiệp / RDMA clustering. |
| **Cổng giao tiếp** | 4x USB-C, 1x HDMI | Hỗ trợ kết nối thiết bị ngoại vi và hiển thị màn hình giám sát trực tiếp. |
| **Hệ điều hành & License** | **NVIDIA DGX OS** (Nền Ubuntu Server 22.04 LTS ARM64) + 90 ngày NVIDIA AI Enterprise | Tích hợp sẵn bộ driver NVIDIA CUDA, NeMo & Container Toolkit chuẩn hóa cho Grace Blackwell. |

---

## 2. KIẾN TRÚC HỆ THỐNG & LUỒNG DỮ LIỆU

Hệ thống được thiết kế theo mô hình kiến trúc Enterprise AI Agent 5 tầng độc lập, khép kín hoàn toàn trong mạng nội bộ Doanh nghiệp, kết hợp giữa AI Core Engine và Hệ sinh thái Hạ tầng Production (Qdrant, Langfuse, Celery + Redis, WebSocket):

### 2.1. Sơ Đồ Khối Trực Quan (Visual Architecture Diagram)

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. TẦNG NGƯỜI DÙNG & GIAO TIẾP (CLIENTS & REAL-TIME INTERACTION)                       │
│    [🖥️ Web App / Mobile]      [⚙️ ERP / CRM API]      [🔌 WebSocket Client]              │
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │ (Kết nối HTTP / HTTPS & Real-time WebSockets qua LAN)
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. TẦNG MẠNG & CỔNG GIAO TIẾP (GATEWAY & AN NINH)                                      │
│    [🔒 UFW Firewall]  ──►  [🌐 Nginx Reverse Proxy (SSL, WebSocket Upgrades & Buffering Off)]│
└───────────────────────────────────┬────────────────────────────────────────────────────┘
                                    │ (Định tuyến API & Stream Token real-time)
                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. TẦNG ĐIỀU PHỐI AGENT & XỬ LÝ BẤT ĐỒNG BỘ (AGENT ECOSYSTEM & TASK QUEUE)             │
│    [💬 Open WebUI / Agent API] ◄──► [⚡ Celery Workers + Redis (Queue, Cache, Session)] │
└─────────┬───────────────────────────────┬───────────────────────────────┬──────────────┘
          │                               │                               │
          ▼                               ▼                               ▼
┌───────────────────┐           ┌───────────────────┐           ┌───────────────────┐
│ 4A. VECTOR SEARCH │           │ 4B. OBSERVABILITY │           │ 4C. AI INFERENCE  │
│ [🔍 Qdrant DB]    │           │ [📊 Langfuse]     │           │ [🧠 vLLM Engine]  │
│ (Rust Vector DB,  │           │ (Trace LLM Calls, │           │ (LLM 72B AWQ/FP8  │
│  RAG & Memory)    │           │  Latency & Cost)  │           │  PagedAttention)  │
└───────────────────┘           └───────────────────┘           └─────────┬─────────┘
                                                                          │
                                                                          ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 5. TẦNG PHẦN CỨNG & BỘ NHỚ ĐỒNG NHẤT (HARDWARE LAYER)                                  │
│    [🚀 Grace Blackwell GPU (1 PFLOPS)]  ◄───►  [💾 128GB Unified Memory / 4TB NVMe SSD]  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2. Sơ Đồ Luồng Dữ Liệu Xử Lý (Enterprise Agent Data Flow)

```mermaid
flowchart TD
    A["💻 Người dùng / ERP Client"] -->|1. Gửi Yêu cầu / Stream WS| B["🌐 Nginx Proxy (WebSocket/HTTPS)"]
    B -->|2. Forward Request| C["💬 Agent Service / Open WebUI"]
    
    subgraph Async_Queue["⚡ Task Queuing & Caching Layer"]
        C -->|3a. Check Cache / Queue Task| D["🔴 Redis Cache & Message Broker"]
        D -->|3b. Pick Task| E["⚙️ Celery Worker (Async Agent Execution)"]
    end
    
    subgraph Knowledge_Retrieval["🔍 Vector Search & RAG"]
        E -->|4. Query High-Speed HNSW| F["🦀 Qdrant Vector Database"]
        F -->|5. Trả về Context/Memory| E
    end

    subgraph LLM_Inference["🧠 Hardware Inference Engine"]
        E -->|6. Gửi Prompt + Context| G["🧠 vLLM High-Throughput Engine"]
        G -->|7. Phục vụ trên GPU 1 PFLOPS| H["⚡ Grace Blackwell (128GB RAM)"]
        H -->|8. Stream Tokens trả về| E
    end

    subgraph Observability_Tracing["📊 LLMOps & Monitoring"]
        E -.->|9. Log Trace, Tokens, Latency| I["📊 Langfuse Server"]
    end

    E -->|10. Stream Tokens qua WebSocket| B
    B -->|11. Real-time Output trên màn hình| A
```

---

## 3. CHUẨN BỊ MÔI TRƯỜNG NỀN TẢNG (UBUNTU ARM64)

### 3.1. Cập Nhật Hệ Thống & Cài Đặt Package Cơ Bản
Truy cập qua SSH vào server DGX OS / Ubuntu ARM64 và thực hiện cập nhật toàn bộ package:

```bash
# Cập nhật danh sách gói tin và nâng cấp hệ thống
sudo apt update && sudo apt upgrade -y

# Cài đặt các công cụ bổ trợ hệ thống cần thiết
sudo apt install -y curl wget git build-essential htop nvtop net-tools ufw ca-certificates gnupg lsbrelease
```

### 3.2. Cấu Hình Tối Ưu Kernel Cho Kiến Trúc Grace Blackwell 128GB RAM
Bổ sung các tham số tối ưu cho bộ nhớ và tiến trình xử lý nặng:

```bash
# Mở file sysctl.conf
sudo nano /etc/sysctl.d/99-ai-performance.conf
```

Chèn nội dung cấu hình:
```ini
# Tăng giới hạn số lượng tiến trình và kết nối mạng
fs.file-max = 2097152
vm.max_map_count = 1048576
net.core.somaxconn = 4096

# Tối ưu hóa việc giải phóng RAM (Swapiness thấp để ưu tiên RAM/Unified Memory)
vm.swappiness = 10
```

Áp dụng cấu hình ngay lập tức:
```bash
sudo sysctl --system
```

### 3.3. Cài Đặt Docker Engine & NVIDIA Container Toolkit (ARM64)

Máy chủ MSI EdgeXpert chạy kiến trúc **ARM64 (`aarch64`)**. Tiến hành cài đặt Docker chuẩn ARM64:

```bash
# Khởi tạo GPG Key và Repository cho Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Cài đặt Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Phân quyền cho User hiện tại chạy Docker không cần sudo
sudo usermod -aG docker $USER
sudo systemctl enable --now docker
```

Kiểm tra NVIDIA Driver & CUDA Container Toolkit:
```bash
# Kiểm tra nhận diện GPU Grace Blackwell
nvidia-smi

# Cấu hình NVIDIA Container Runtime cho Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

---

## 4. TRIỂN KHAI AI CORE ENGINE (vLLM HIGH-THROUGHPUT ENGINE)

Để phục vụ môi trường Production đa người dùng với hiệu năng cao nhất, hệ thống sử dụng **vLLM** — AI Inference Engine chuẩn Enterprise tích hợp công nghệ **PagedAttention** và **Continuous Batching**, giúp tận dụng tối đa 1 PFLOPS hiệu năng GPU Grace Blackwell.

### 4.1. Cài Đặt vLLM Engine Native / Container trên Linux ARM64

Triển khai vLLM Server thông qua Python venv hoặc Docker Container chuyên dụng cho NVIDIA Grace Blackwell:

```bash
# 1. Cài đặt HuggingFace CLI để tải model weights
pip install -U "huggingface_hub[cli]" vllm

# 2. Tạo thư mục chứa Model Weights từ HuggingFace trên SSD 4TB
sudo mkdir -p /var/lib/vllm/models
sudo chown -R $USER:$USER /var/lib/vllm
```

### 4.2. Cấu Hình & Khởi Chạy vLLM OpenAI API Server

Khởi chạy vLLM API Server tương thích với chuẩn OpenAI API (`http://0.0.0.0:8000/v1`):

```bash
# Lệnh khởi chạy vLLM tối ưu cho Qwen2.5 72B AWQ từ local weights
python3 -m vllm.entrypoints.openai.api_server \
    --model /var/lib/vllm/models/Qwen2.5-72B-Instruct-AWQ \
    --quantization awq \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.85 \
    --max-model-len 32768 \
    --max-num-seqs 32 \
    --served-model-name qwen2.5-72b
```

> **📌 Phân Tích Cấu Hình Tối Ưu Cho Grace Blackwell 128GB RAM:**
> * `--quantization awq`: Khai báo chính xác phương pháp định lượng AWQ (INT4) giúp tối ưu bộ nhớ VRAM/Unified Memory.
> * `--gpu-memory-utilization 0.85`: Tối ưu dành 85% bộ nhớ Coherent Unified Memory cho VRAM/KV Cache của vLLM.
> * `--max-model-len 32768`: Mở rộng cửa sổ ngữ cảnh (Context Window) 32K tokens cho RAG văn bản dài.
> * `--max-num-seqs 32`: Giới hạn tối đa 32 câu thoại xử lý đồng thời trong 1 batch mà không làm bùng nổ latency hoặc ngắt kết nối client.
> * `Continuous Batching & PagedAttention`: vLLM tự động gộp hàng chục câu hỏi từ các nhân viên khác nhau vào 1 batch duy nhất để xử lý đồng thời.

---

## 5. QUẢN LÝ & TỐI ƯU MÔ HÌNH AI TRÊN 128GB UNIFIED MEMORY (vLLM & HUGGINGFACE)

Khác với máy chủ thông thường bị giới hạn bởi VRAM GPU ngắn, **MSI EdgeXpert Grace Blackwell GB10 có 128GB Coherent Unified Memory**. Điều này cho phép vLLM nạp mượt mà mô hình 72B tham số và quản lý hàng nghìn KV Cache PagedAttention cùng lúc.

### 5.1. Bảng Khuyến Nghị Lựa Chọn Mô Hình Chuẩn Enterprise (AWQ / FP8)

| Tên Mô Hình (HuggingFace ID) | Định dạng Weights | Dung lượng RAM chiếm | Thế mạnh & Ứng dụng thực tế |
| :--- | :--- | :--- | :--- |
| **`Qwen/Qwen2.5-72B-Instruct-AWQ`** | AWQ (INT4) | ~42 GB | **Mô hình Doanh nghiệp Toàn diện (Chính):** Vua Tiếng Việt, RAG văn bản pháp lý, gọi tool agent. |
| **`Qwen/Qwen2.5-32B-Instruct-AWQ`** | AWQ (INT4) | ~20 GB | **Siêu Tốc Độ (High-Speed):** Nhanh gấp 2.5 lần bản 72B, thích hợp làm Trợ lý Chat tức thì. |
| **`deepseek-ai/DeepSeek-R1-Distill-Qwen-32B`** | FP8 / AWQ | ~22 GB | **Mô hình Suy luận (Reasoning):** Phân tích dữ liệu kỹ thuật, lập kế hoạch multi-step Agent. |
| **`BAAI/bge-m3`** | FP32 / FP16 | ~1.2 GB | **Embedding Model:** Đa ngôn ngữ (Phục vụ tra cứu Vector RAG trên Qdrant). |

### 5.2. Lệnh Tải Trọng Số Mô Hình Về SSD 4TB Local

Tải trước các model trọng tâm từ HuggingFace để chạy offline hoàn toàn:

```bash
# 1. Tải mô hình Qwen2.5-72B AWQ (Tối ưu cho vLLM)
huggingface-cli download Qwen/Qwen2.5-72B-Instruct-AWQ --local-dir /var/lib/vllm/models/Qwen2.5-72B-Instruct-AWQ

# 2. Tải mô hình siêu tốc Qwen2.5-32B AWQ
huggingface-cli download Qwen/Qwen2.5-32B-Instruct-AWQ --local-dir /var/lib/vllm/models/Qwen2.5-32B-Instruct-AWQ

# 3. Tải mô hình suy luận DeepSeek-R1 32B
huggingface-cli download deepseek-ai/DeepSeek-R1-Distill-Qwen-32B --local-dir /var/lib/vllm/models/DeepSeek-R1-32B
```

---

## 6. TRIỂN KHAI GIAO DIỆN NGƯỜI DÙNG & HỆ SINH THÁI PRODUCTION (FULL ENTERPRISE STACK)

Để hệ thống vận hành chuẩn Production, ngoài giao diện Open WebUI, cần triển khai bộ dịch vụ bổ trợ bao gồm: **Qdrant** (Vector Search hiệu năng cao), **Redis** (Celery Broker & Caching), và **Langfuse** (Tracing & Observability).

### 6.1. Cấu Hình Docker Compose Cho Enterprise AI Stack

Tạo thư mục làm việc cho dịch vụ:
```bash
mkdir -p ~/ai-stack && cd ~/ai-stack
nano docker-compose.yml
```

Dán nội dung `docker-compose.yml` tối chuẩn bên dưới:

```yaml
version: '3.8'

services:
  # 1. vLLM Inference Engine (High-Throughput OpenAI API Compatible Engine)
  vllm:
    image: vllm/vllm-openai:latest
    container_name: vllm-engine
    restart: always
    ipc: host
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - /var/lib/vllm/models:/root/.cache/huggingface
    environment:
      - HF_HUB_OFFLINE=1
    command: >
      --model mesolitica/Qwen2.5-72B-Instruct-FP8
      --host 0.0.0.0
      --port 8000
      --gpu-memory-utilization 0.85
      --max-model-len 16384
      --max-num-seqs 16
      --enable-prefix-caching
      --served-model-name qwen2.5-72b
      --enable-auto-tool-choice
      --tool-call-parser hermes

  # 2. Giao diện Người dùng & Quản lý RAG (Open WebUI)
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    restart: always
    ports:
      - "127.0.0.1:3000:8080"
    environment:
      - OPENAI_API_BASE_URLS=http://vllm:8000/v1
      - OPENAI_API_KEY=EMPTY
      - WEBUI_SECRET_KEY=EnterpriseSuperSecretKey2026_GB10
      - ENABLE_RAG_WEB_SEARCH=False
      - VECTOR_DB=qdrant
      - QDRANT_URI=http://qdrant:6333
      - REDIS_URL=redis://:EnterpriseRedisSecret2026@redis:6379/0
      - ENABLE_SIGNUP=True
      - DEFAULT_USER_ROLE=user
    volumes:
      - open-webui-data:/app/backend/data
    depends_on:
      - vllm
      - qdrant
      - redis

  # 3. Qdrant Vector Database (Vector Search hiệu năng cao bằng Rust)
  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant-vector-db
    restart: always
    ports:
      - "127.0.0.1:6333:6333"
      - "127.0.0.1:6334:6334"
    volumes:
      - qdrant-data:/qdrant/storage

  # 4. Redis Server (Message Broker cho Celery & Semantic LLM Cache)
  redis:
    image: redis:7-alpine
    container_name: redis-broker-cache
    restart: always
    command: redis-server --appendonly yes --requirepass EnterpriseRedisSecret2026
    ports:
      - "127.0.0.1:6379:6379"
    volumes:
      - redis-data:/data

  # 5. Langfuse Postgres Database (Lưu dữ liệu Tracing LLM)
  langfuse-db:
    image: postgres:15-alpine
    container_name: langfuse-db
    restart: always
    environment:
      - POSTGRES_USER=langfuse
      - POSTGRES_PASSWORD=LangfuseSecretPassword2026
      - POSTGRES_DB=langfuse
    volumes:
      - langfuse-db-data:/var/lib/postgresql/data

  # 6. Langfuse Web Server (Giao diện Observability & Trace LLM Agent)
  langfuse-web:
    image: ghcr.io/langfuse/langfuse:2
    container_name: langfuse-server
    restart: always
    ports:
      - "127.0.0.1:3001:3000"
    environment:
      - DATABASE_URL=postgresql://langfuse:LangfuseSecretPassword2026@langfuse-db:5432/langfuse
      - NEXTAUTH_SECRET=EnterpriseNextAuthSecretKey2026
      - SALT=EnterpriseLangfuseSaltKey2026
      - ENCRYPTION_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
      - NEXTAUTH_URL=http://localhost:3001
      - TELEMETRY_ENABLED=false
    depends_on:
      - langfuse-db

volumes:
  open-webui-data:
    driver: local
  qdrant-data:
    driver: local
  redis-data:
    driver: local
  langfuse-db-data:
    driver: local
```

Khởi chạy toàn bộ Container Stack:
```bash
docker compose up -d
```

Kiểm tra trạng thái container:
```bash
docker compose ps
docker logs -f open-webui
```

### 6.2. Cấu Hình Tài Khoản Admin & Hệ Thống RAG Trực Quan
1. Mở trình duyệt truy cập: `http://<IP-SERVER-UBUNTU>` (hoặc `http://ai.yourcompany.local` qua Nginx Reverse Proxy).
2. **Tài khoản khởi tạo đầu tiên** sẽ tự động trở thành **Admin (Quản trị viên)**.
3. Trong **Admin Panel -> Settings -> Connections**: Xác nhận kết nối OpenAI API Endpoint chỉ đến `http://vllm:8000/v1`, hệ thống hiển thị model `qwen2.5-72b`.
4. **Tải tài liệu RAG:** Vào mục **Documents**, tải lên các file PDF/Word quy trình công ty. Khi nhân viên chat chỉ cần gõ `#Tên_Tài_Liệu`, Open WebUI sẽ tự động kích hoạt pipeline Vector Search với model `BAAI/bge-m3` để tra cứu ngữ cảnh chính xác.

### 6.3. Quản Lý Vị Trí Lưu Trữ & Giới Hạn Tải Lên Dữ Liệu RAG

#### 1. Vị Trí Lưu Trữ Dữ Liệu RAG Trực Tiếp Trên Server
Khi người dùng tải tài liệu (PDF, DOCX, Excel...) lên Open WebUI, dữ liệu được lưu trữ hoàn toàn nội bộ trên máy chủ Ubuntu tại các đường dẫn:
* **File gốc & Vector Database (Qdrant DB):**
  Lưu trữ trong Docker Volume `qdrant-data` và `open-webui-data` trên Host Ubuntu:
  * Thư mục file gốc WebUI: `/var/lib/docker/volumes/open-webui-data/_data/uploads/`
  * Thư mục Qdrant Vector Storage & HNSW Index: `/var/lib/docker/volumes/qdrant-data/_data/`
* **Mô hình Embedding (`bge-m3`):**
  Model băm nhỏ văn bản thành Vector được Open WebUI tải và lưu trữ trực tiếp trong cache container Open WebUI: `/var/lib/docker/volumes/open-webui-data/_data/cache/huggingface/`

#### 2. Phân Tích Giới Hạn Dung Lượng & Khả Năng Tải Lên
Do là hệ thống Local AI hoàn toàn độc lập, khả năng tải dữ liệu **không bị giới hạn bởi dịch vụ bên thứ 3 hay chi phí Cloud**. Tuy nhiên, khả năng vận hành thực tế phụ thuộc vào 2 nhóm giới hạn:
* **Giới hạn cấu hình Phần mềm (Có thể tùy chỉnh nâng lên):**
  * **Cấu hình Nginx (`client_max_body_size`):** Mặc định trong tài liệu thiết lập `500M` (Mục 7.2) cho mỗi file upload. Bạn có thể sửa thành `2G` hoặc `0` (không giới hạn) trong file Nginx config nếu cần upload các file cực lớn.
  * **Timeout xử lý (`proxy_read_timeout`):** Cấu hình `600s` (10 phút) để đảm bảo kết nối không bị ngắt khi GPU nạp model `bge-m3` phân tích các bộ tài liệu hàng nghìn trang.
* **Giới hạn Phần cứng Máy chủ (Vật lý):**
  * **Ổ cứng 4TB NVMe SSD:** Đủ dung lượng lưu trữ hàng triệu trang tài liệu nội bộ và hệ thống Vector DB.
  * **128GB Unified Memory & Grace Blackwell GPU:** Đảm bảo nạp toàn bộ Vector Index vào RAM để truy vấn siêu tốc và không lo sập dịch vụ do tràn bộ nhớ (Out of Memory).

---

## 7. CẤU HÌNH MẠNG, NGINX REVERSE PROXY & AN NINH BẢO MẬT

### 7.1. Cấu Hình Firewall UFW Bảo Vệ Máy Chủ
Áp dụng nguyên tắc bảo mật tối thiểu (**Zero Trust / Least Privilege**): Chỉ mở các cổng giao tiếp thực sự cần thiết, khóa trực tiếp các cổng backend `8000` (vLLM API), `6333` (Qdrant), `6379` (Redis) khỏi mạng bên ngoài để tránh bị truy cập trái phép. Tất cả kết nối của người dùng đều bắt buộc đi qua Nginx Reverse Proxy (Cổng 80/443).

```bash
# 1. Chặn toàn bộ kết nối đi VÀO (Incoming) mặc định để bảo vệ hệ thống
sudo ufw default deny incoming

# 2. Cho phép kết nối đi RA (Outgoing) để cập nhật hệ thống, tải Docker Image và AI Models
sudo ufw default allow outgoing

# 3. Cho phép SSH quản trị hệ thống từ xa (Cổng 22)
sudo ufw allow 22/tcp

# 4. Cho phép lưu lượng Web Nginx Proxy (HTTP Cổng 80 & HTTPS Cổng 443)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 5. Kích hoạt UFW Firewall (Tự khởi động cùng hệ thống)
sudo ufw enable

# 6. Kiểm tra bảng trạng thái tường lửa chi tiết
sudo ufw status verbose
```

> **🔒 Phân Tích Bảo Mật, Chống Bỏ Qua UFW & Chống Tràn GPU:**  
> * **Lưu ý Cực Kỳ Quan Trọng về Docker & UFW:** Mặc định Docker tự động can thiệp vào `iptables` của Linux, bỏ qua (bypass) toàn bộ quy tắc chặn cổng của UFW. Nếu trong `docker-compose.yml` bạn khai báo `ports: "8000:8000"`, cổng vLLM sẽ bị công khai ra ngoài mạng LAN bất chấp UFW! Do đó, tất cả dịch vụ backend trong `docker-compose.yml` bắt buộc phải bind vào `127.0.0.1:` (ví dụ: `127.0.0.1:8000:8000`, `127.0.0.1:3000:8080`).
> * **Nếu mở trực tiếp cổng 8000 (API vLLM):** Cổng này không có xác thực mặc định. Bất kỳ máy nào trong LAN cũng có thể gửi request trực tiếp, làm rò rỉ dữ liệu hoặc chiếm dụng tài nguyên GPU.  
> * **Khi bắt buộc truy cập qua Nginx -> Open WebUI (Cổng 80 / 443):**  
>   1. **Định danh & Kiểm soát:** Người dùng bắt buộc phải đăng nhập tài khoản. Admin dễ dàng kiểm duyệt log và khóa tài khoản nếu phát hiện bất thường.  
>   2. **Cơ chế Hàng Đợi & Continuous Batching:** Kết hợp tham số `--max-num-seqs 32` của vLLM, khi có hàng chục người cùng gửi câu hỏi, vLLM tự động xếp hàng và batch các request một cách tối ưu. GPU Grace Blackwell luôn hoạt động đạt đỉnh hiệu năng mà **tuyệt đối không bị tràn RAM/VRAM**.

### 7.2. Triển Khai Nginx Reverse Proxy & Mã Hóa SSL/TLS
Nginx là một phần mềm máy chủ web (web server) mã nguồn mở cực kỳ phổ biến, nổi tiếng với hiệu suất cao, tốc độ xử lý nhanh, độ ổn định và khả năng tiêu thụ tài nguyên cực kỳ tiết kiệm.

Nginx đóng vai trò làm **Reverse Proxy (Trạm trung chuyển truy cập)** đứng ở trước Open WebUI. Giải pháp này giúp chuyển đổi địa chỉ IP:Port khó nhớ thành tên miền nội bộ thân thiện (`http://ai.yourcompany.local`), đồng thời quản lý việc upload file RAG dung lượng lớn và tối ưu luồng hiển thị gõ chữ thời gian thực (Streaming SSE) từ AI.

#### 1. Cài Đặt Nginx & Khởi Tạo File Cấu Hình
```bash
# Cài đặt dịch vụ Nginx Web Server
sudo apt install -y nginx

# Tạo file cấu hình Virtual Host riêng cho AI Server
sudo nano /etc/nginx/sites-available/ai-local.conf
```

#### 2. Chi Tiết File Cấu Hình Nginx Tối Ưu Cho AI Stack (HTTP & HTTPS SSL)
Dán nội dung cấu hình bên dưới:

```nginx
server {
    listen 80;
    server_name ai.yourcompany.local;
    return 301 https://$host$request_uri; # Tự động chuyển hướng HTTP sang HTTPS
}

server {
    listen 443 ssl;
    server_name ai.yourcompany.local;

    # Cấu hình Chứng chỉ SSL/TLS (Self-signed hoặc CA Doanh nghiệp)
    ssl_certificate /etc/ssl/certs/ai-local.crt;
    ssl_certificate_key /etc/ssl/private/ai-local.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Cho phép tải lên file dữ liệu RAG tối đa 500MB (Tránh lỗi "413 Request Entity Too Large")
    client_max_body_size 500M; 

    location / {
        # Điều hướng toàn bộ truy cập từ Nginx sang Open WebUI đang chạy ở port 3000 (bind 127.0.0.1)
        proxy_pass http://127.0.0.1:3000;
        
        # Bắt buộc sử dụng HTTP 1.1 và duy trì kết nối WebSocket thời gian thực
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        
        # Giữ nguyên thông tin tên miền và IP gốc của người dùng để Open WebUI ghi log chính xác
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # --- 🚀 TỐI ƯU CỰC KỲ QUAN TRỌNG CHO AI CHAT ---
        # Tắt bộ đệm (Buffering) để phản hồi được Streaming từng từ một (Hiệu ứng gõ chữ real-time như ChatGPT)
        proxy_buffering off;
        
        # Nâng thời gian chờ lên 10 phút (600s) tránh bị ngắt kết nối khi AI suy luận các câu hỏi khó (Lỗi 504 Gateway Timeout)
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

> **💡 Mẹo Khởi Tạo SSL Self-Signed Nhanh:**
> ```bash
> sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
>   -keyout /etc/ssl/private/ai-local.key \
>   -out /etc/ssl/certs/ai-local.crt \
>   -subj "/CN=ai.yourcompany.local"
> ```

#### 3. Kích Hoạt Cấu Hình & Khởi Động Dịch Vụ
```bash
# Tạo liên kết để kích hoạt cấu hình site vào danh sách đang chạy
sudo ln -s /etc/nginx/sites-available/ai-local.conf /etc/nginx/sites-enabled/

# Kiểm tra cú pháp cấu hình Nginx xem có bị lỗi không trước khi reload
sudo nginx -t

# Khởi động lại Nginx để áp dụng ngay cài đặt mới
sudo systemctl restart nginx
```

---

## 8. TỐI ƯU HÀNG ĐỢI, GIÁM SÁT TÀI NGUYÊN & XỬ LÝ SỰ CỐ

### 8.1. Cơ Chế Giới Hạn Hàng Đợi (Queue Concurrency) & Multi-Model Routing
Khi nhiều người dùng cùng tạo câu hỏi, vLLM Engine trên GPU Grace Blackwell sẽ xử lý song song nhờ thuật toán PagedAttention và Continuous Batching (giới hạn `--max-num-seqs 32`).

- **Trường hợp quá tải yêu cầu:** Các request vượt quá giới hạn concurrency tự động được vLLM xếp hàng chờ (Memory Queue Buffer) mà không bị sập container hay tràn RAM.
- **Multi-Model Routing (Chuyển luồng mô hình):** Để phục vụ đồng thời nhiều mô hình (VD: Qwen2.5-72B cho công việc chung và DeepSeek-R1-32B cho suy luận chuyên sâu), có thể chạy thêm container `vllm-engine-reasoning` ở cổng `8001` hoặc sử dụng **LiteLLM Proxy** làm trạm điều phối trung gian phía trước Open WebUI.

### 8.2. Lệnh Giám Sát Tài Nguyên Thực Thời (Real-time Monitoring & Observability)

```bash
# 1. Giám sát GPU NVIDIA Grace Blackwell (Xung nhịp, Nhiệt độ, Điện năng, VRAM)
watch -n 1 nvidia-smi

# 2. Giám sát trực quan CPU 20 Cores và 128GB RAM
htop

# 3. Giám sát Log hệ thống vLLM Inference Core
docker logs -f vllm-engine

# 4. Giám sát trạng thái toàn bộ Enterprise Stack Containers
docker compose ps

# 5. Giám sát Tracing LLM & Latency trên giao diện Langfuse UI
# Truy cập trình duyệt: http://<IP-SERVER-UBUNTU>:3001

# 6. Xem Log thời gian thực của từng dịch vụ trong Stack
docker logs -f open-webui       # WebUI & Agent Interface
docker logs -f qdrant-vector-db  # Qdrant Vector Search Engine
docker logs -f redis-broker-cache# Redis Queue & Cache
docker logs -f langfuse-server  # Langfuse Observability Server
```

### 8.3. Xử Lý Sự Cố Thường Gặp (Troubleshooting Guide)

#### ❓ Sự cố 1: vLLM Container ngắt ngẫu nhiên hoặc báo lỗi CUDA Memory / Out of Memory (OOM)
* **Nguyên nhân:** Tham số `--gpu-memory-utilization` quá cao (vượt quá dung lượng RAM khả dụng khi các dịch vụ khác như Qdrant/Langfuse khởi chạy) hoặc Context Length (`--max-model-len`) đặt quá xa.
* **Cách khắc phục:**
  ```bash
  # 1. Kiểm tra log chi tiết của vLLM
  docker logs --tail 100 vllm-engine
  
  # 2. Hạ --gpu-memory-utilization từ 0.85 xuống 0.75 - 0.80 trong docker-compose.yml
  # 3. Chạy lại container:
  docker compose up -d vllm
  ```

#### ❓ Sự cố 2: Langfuse Container báo lỗi "ENCRYPTION_KEY must be set"
* **Nguyên nhân:** Langfuse v2+ yêu cầu chuỗi Hex 256-bit để mã hóa credentials lưu trong PostgreSQL.
* **Cách khắc phục:** Đảm bảo biến môi trường `ENCRYPTION_KEY` đã được khai báo trong `docker-compose.yml` (như mẫu ở Mục 6.1).

#### ❓ Sự cố 3: Không kết nối được WebUI từ máy tính nhân viên trong LAN
* **Nguyên nhân:** UFW chưa cho phép cổng 80/443 hoặc Nginx Reverse Proxy chưa khởi chạy.
* **Cách khắc phục:**
  ```bash
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo systemctl status nginx
  ip a # Kiểm tra lại IP tĩnh của máy chủ
  ```

---

## 9. PHỤ LỤC: MẪU DOCKER-COMPOSE & TRA CỨU NHANH

### 9.1. Bảng Tra Cứu Câu Lệnh Thường Dùng (Quick Cheat Sheet)

```bash
# --- vLLM ENGINE & HUGGINGFACE ---
huggingface-cli download Qwen/Qwen2.5-72B-Instruct-AWQ # Tải model AWQ từ HuggingFace
docker logs -f vllm-engine                             # Xem log inference thực tế của vLLM
curl http://localhost:8000/v1/models                   # Kiểm tra API models đang serve trên vLLM

# --- SYSTEM & SERVICES ---
sudo systemctl restart nginx   # Khởi động lại Web Reverse Proxy Nginx
watch -n 1 nvidia-smi          # Giám sát GPU Grace Blackwell (VRAM, GPU Usage)

# --- DOCKER ENTERPRISE STACK ---
docker compose up -d           # Khởi chạy toàn bộ Enterprise AI Stack ngầm
docker compose down            # Dừng toàn bộ hệ thống
docker compose ps              # Trạng thái các container (vllm, open-webui, qdrant, redis, langfuse)
docker logs --tail 100 open-webui # Xem 100 dòng log mới nhất của WebUI
```

### 9.2. Tổng Kết Quy Trình Đưa Vào Vận Hành Doanh Nghiệp
1. **Thiết lập phần cứng:** Đặt máy chủ MSI EdgeXpert-55SVN tại phòng Server, cắm dây mạng LAN RJ45/ConnectX-7, gán **IP Tĩnh (Static IP)** trên Router.
2. **Khởi tạo OS & Core:** Chạy toàn bộ lệnh ở **Mục 3 & 4** để cài đặt NVIDIA Container Runtime & sẵn sàng vLLM API Engine.
3. **Tải AI Models:** Nạp các mô hình chuẩn AWQ/FP8 (`Qwen2.5-72B-Instruct-AWQ`, `Qwen2.5-32B-Instruct-AWQ`) về SSD 4TB theo **Mục 5**.
4. **Khởi chạy Enterprise Stack:** Chạy Docker Compose **Mục 6** để bật đồng thời `vLLM`, `Open WebUI`, `Qdrant Vector DB`, `Redis Broker`, `Langfuse Tracing`.
5. **Ủy quyền & Phân quyền:** Phân quyền Admin/User trên Open WebUI, cung cấp địa chỉ IP/Domain cho các phòng ban truy cập và khai thác hiệu quả.

---
*Tài liệu được biên soạn chuẩn hóa cho hệ thống AI Local Doanh nghiệp trên nền tảng MSI EdgeXpert GB10 Grace Blackwell 128GB RAM.*
