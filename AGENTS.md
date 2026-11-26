# Hướng dẫn làm việc với repo chatbot HTMP

Đọc [README.md](README.md) để nắm kiến trúc và [RUNBOOK.md](RUNBOOK.md) khi công việc liên quan vận hành. Với thay đổi ERP/MES, xem [quy trình kiểm tra](docs/ERP_CHANGE_CHECKLIST.md). Khi sửa, giới hạn phạm vi theo model, profile và đường xử lý đã xác định.

## Kiến trúc và điểm vào

- [docker-compose.yml](docker-compose.yml) mô tả Nginx, Open WebUI, vLLM, Tika, Qdrant, Redis và Langfuse. PostgreSQL của Langfuse phục vụ quan sát hệ thống. Kết nối PostgreSQL ERP/MES nằm trong adapter của luồng ERP. [Dockerfile.openwebui-speed-runtime](Dockerfile.openwebui-speed-runtime) mô tả build Open WebUI tùy biến. Bản vá backend và UI nằm ở `backend-patches/` và `ui-patches/`.
- Luồng ERP hiện hành dùng duy nhất profile `htmp-erp-agent-staging` (đã gỡ `htmp-nhanh` và bộ lập kế hoạch SQL tự do):
  - Điểm vào Open WebUI là Pipe trực tiếp [htmp_erp_agent_pipe.py](functions/htmp_erp_agent_pipe.py), cấu hình tại [htmp-erp-agent-profile.json](config/htmp-erp-agent-profile.json) và [model-picker-policy.json](config/model-picker-policy.json) (không dùng LLM bọc ngoài).
  - [agent_runtime.py](erp_ai/agent_runtime.py) nối `vLLM` (`qwen2.5-14b`) và adapter PostgreSQL chỉ đọc với [agent.py](erp_ai/agent.py) và [agent_backend.py](erp_ai/agent_backend.py).
  - [semantic_catalog.py](erp_ai/semantic_catalog.py), [semantic_retriever.py](erp_ai/semantic_retriever.py), [semantic_query.py](erp_ai/semantic_query.py), [semantic_executor.py](erp_ai/semantic_executor.py), [semantic_normalizer.py](erp_ai/semantic_normalizer.py) và [context_hints.py](erp_ai/context_hints.py) thực thi 62 hợp đồng semantic đã duyệt (kèm ghép nối đa bảng an toàn qua `query_semantic_join` theo đồ thị thực thể chung và kiểm tra bất biến cột tự động) và 20 báo cáo tra cứu trong [erp-agent.json](config/erp-agent.json), tự động nối metadata lưới/báo cáo 3SERP từ [erp_metadata_dictionary.json](config/erp_metadata_dictionary.json), phủ 34/34 chứng từ `sys_dmct` có dữ liệu và 131/202 bảng có dữ liệu trên `3SERP_HTMP_DATA`. Khi số dataset vượt 16, `retrieve()` đặt `context_hints` (kèm `available_joins`) lên trước, dùng BM25 + metadata 3SERP + tách vế câu hỏi chọn top-6 `recommended_datasets`, thu gọn `other_datasets` và hỗ trợ `search_semantic_datasets(query=...)`. Manifest và mẫu SQL báo cáo nằm ở [config/erp-reports](config/erp-reports) (18 file) và [sql/erp-reports](sql/erp-reports) (20 file).
- Giữ phạm vi sửa ERP tách khỏi GPT. Luồng GPT (`gpt-5.6-luna`) đi qua [openai.py](backend-patches/openai.py) và [images.py](backend-patches/images.py). Với ERP, kiểm tra ngữ cảnh và thực thể trong [context_hints.py](erp_ai/context_hints.py), [entities.py](erp_ai/entities.py), kiểm tra kết quả trong [validator.py](erp_ai/validator.py) và phần hiển thị/xuất file trong [presentation.py](erp_ai/presentation.py), [rich_ui.py](erp_ai/rich_ui.py), [export_files.py](erp_ai/export_files.py).

## Lệnh chạy và kiểm thử

Thực hiện từ gốc repo.

| Lệnh | Trạng thái xác minh |
| --- | --- |
| `python3 -B -m unittest tests.test_erp_agent tests.test_erp_semantic_query tests.test_erp_semantic_retrieval tests.test_erp_export tests.test_erp_incident_changes tests.test_erp_golden_pipeline tests.test_openwebui_speed_selector_patch tests.test_erp_canonical_architecture` | Đã chạy, 100/100 test đạt. |
| `python3 -B scripts/eval_erp_golden.py --suite all --dry-run` | Đã chạy, 60/60 ca đạt (17 golden + 36 random + 7 holdout) với fixture tổng hợp. |
| `docker exec open-webui env HTMP_AGENT_ROOT=/app/backend python3 -B /tmp/eval_erp_golden.py --suite all --live --model-url http://vllm:8000/v1/` | Đã chạy sau restart `open-webui`, **58/60 ca đạt (`pass_rate: 0.967`, 16/17 golden + 35/36 random + 7/7 holdout, `p50_ms: 21599`, `p95_ms: 67441`)**. |
| `bash scripts/test_erp_agent_postgres.sh` | Kiểm thử SQL trên container PostgreSQL cô lập với dữ liệu tổng hợp. |
| `docker compose version`, `docker compose ps` | Đã xác minh trên Ubuntu. Chỉ vận hành/restart container theo phạm vi được phép. |

## Quy tắc làm việc

- Giữ bí mật ngoài tài liệu, test fixture và log. Tránh đọc `.env` thật, in biến môi trường hoặc render Compose ra terminal khi có cấu hình bí mật. Dùng fixture tổng hợp và bằng chứng đã ẩn dữ liệu.
- Mặc định bắt đầu bằng đọc code và test cục bộ. Xác định quyền trước khi truy cập ERP/DB thật, gọi endpoint nội bộ, đổi cấu hình, restart hoặc triển khai. Giữ nguyên thay đổi đang có của người dùng. Commit và push theo yêu cầu.
- Backend quyết định quyền, phạm vi dữ liệu và hợp đồng truy vấn; mọi quy ước chuẩn hóa và mở rộng (`cues`, `secondary_cues`, `param_schema`, `presentation`, `direct_render`, `person_lookup`, `alternate_filter_fields`, `field_labels`, `value_aliases`, `default_dimensions`, `default_metrics`, `bounded_date_fields`, `alternate_date_field`, `alternate_date_label`, `parent_prefix_fallback`, `next_step_note`, `notes`) khai báo trong [erp-agent.json](config/erp-agent.json), không thêm `if/else` đặc thù theo tên dataset/report trong code Python. Giữ riêng trạng thái rỗng, số 0, lỗi, thiếu quyền và dữ liệu bị cắt; không để LLM tự tính ước lượng khi chưa có công thức backend.
- Trước khi thêm/sửa hợp đồng hoặc báo cáo mới, phải đối chiếu màn hình 3SERP thật (kể cả các cột ngày trên lưới chi tiết như `ct91.ngay_yc` *Ngày nhận hàng* khác `ph91.ngay_ct` *Ngày lập*), thêm ca vào [eval_erp_golden.py](scripts/eval_erp_golden.py), và **bắt buộc `docker compose restart open-webui`** sau khi sửa `erp_ai/` hoặc `config/` (tiến trình `uvicorn` không tự nạp lại module Python đã import khi chạy qua bind mount). Không nhồi thêm luật đặc thù vào `SYSTEM` prompt để bù cho giới hạn suy luận đa bước của `qwen2.5-14b`.
- Dùng `$chatbot-debug` để truy vết lỗi, `$chatbot-eval` để đánh giá trước/sau, và `$sql-review` để rà truy vấn và quyền dữ liệu. Skill nằm trong `.agents/skills/`.
