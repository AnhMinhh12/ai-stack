# Checklist thay đổi nghiệp vụ ERP

Tag file này vào đầu chat mới khi yêu cầu sửa, bổ sung hoặc triển khai một nghiệp vụ ERP.

## Chỉ dẫn thực hiện

Khi xử lý thay đổi ERP, không chỉ sửa để câu hỏi hiện tại trả lời đúng. Phải rà soát và đồng bộ toàn bộ chuỗi: **đối chiếu màn hình 3SERP thật → hợp đồng dữ liệu → truy vấn & quyền → hiển thị Rich UI → kiểm thử & Golden Eval → tài liệu → triển khai (`bootstrap` + `restart open-webui`) → đối chiếu UI**.

Không kết luận hoàn tất nếu mới sửa file trên đĩa hoặc mới qua test mock mà chưa nạp lại vào runtime `open-webui`.

## 1. Xác nhận yêu cầu nghiệp vụ & đối chiếu màn 3SERP thật

- Ghi lại câu hỏi thực tế của người dùng và các cách diễn đạt tương đương.
- **Mở màn hình 3SERP thật** (hoặc chụp bảng + đối chiếu SQL DB chỉ đọc) trước khi viết/sửa hợp đồng; không suy đoán cột chỉ từ tên gọi:
  - Kiểm tra đầy đủ các cột ngày trên cả **header** và **lưới chi tiết** (ví dụ `ph91.ngay_ct` là *Ngày lập* còn `ct91.ngay_yc` là *Ngày nhận hàng \**).
  - Kiểm tra cách ghi mã biến thể so với mã gốc (ví dụ `dmhosokhuonsp` dùng `425-00107-2`, còn `mfkhsx_po_fc` dùng mã gốc `425-00107`).
  - Kiểm tra định dạng giá trị thật trong DB (`'0'`/`'1'` vs boolean, trạng thái chứng từ hủy/nháp `14`/`15`, tiểu khoản/đơn vị tính).

## 2. Xác định nguồn, hạt dữ liệu và quyền

- Ghi rõ bảng header, bảng detail, khóa nối và hạt dữ liệu (dòng chứng từ, chứng từ, ngày, máy, vật tư).
- Kiểm tra điều kiện phân quyền `userinfo.is_super`, `userinfo.ds_branchs` và `userinfo.ds_stocks` ngay trong SQL tham số hóa hoặc `curated_scoped_subquery`.
- Phân biệt rõ **trạng thái rỗng (`empty`)**, **số `0`**, **thiếu giá trị (`missing` / `NULL`)**, **cắt dòng (`partial` + `total_rows`)** và **lỗi (`error`)**.
- Nếu câu hỏi đòi hỏi phép tính tổng hợp/ước lượng liên phân hệ mà chưa có công thức backend, **không để LLM tự chia nhẩm từ các dòng mẫu**; hoặc bổ sung công thức xác định ở backend, hoặc chỉ trả các bảng số liệu đã xác minh.

## 3. Cập nhật artifact đúng chỗ (không vá đặc thù theo dataset)

- `config/erp-agent.json` (nguồn sự thật duy nhất của hợp đồng & báo cáo `htmp-erp-agent-staging`):
  - Với `semantic_contracts`: khai báo `source_sql`, `dimensions`, `metrics`, `filters`, `cues`/`secondary_cues`, `field_labels`, `notes`; dùng các thuộc tính chung (`default_dimensions`, `default_metrics`, `bounded_date_fields`, `alternate_date_field`, `alternate_date_label`, `value_aliases`, `parent_prefix_fallback`) thay vì thêm `if/else` hay luật đặc thù trong `erp_ai/*.py`.
  - Với `reports`: khai báo `tool_name`, `tool_description`, `cues`, `param_schema`, `max_date_span_days`, `status_message`, `field_labels`, `next_step_note` trực tiếp trong JSON để `ReportBackend` và `presentation.py` tự động sinh spec, validate tham số và render bảng không cần sửa Python.
- `sql/erp-reports/<report>.sql` & `config/erp-reports/<report>.json` (nếu thêm/sửa báo cáo tra cứu).
- `erp_ai/presentation.py` / `erp_ai/rich_ui.py` (chỉ chỉnh khi đổi layout Rich UI hoặc từ điển chung `SEMANTIC_FIELD_META` / `LOOKUP_FIELD_META`).
- `functions/htmp_erp_agent_pipe.py` & `config/htmp-erp-agent-profile.json` (khi thay đổi đường gọi Pipe hoặc cấu hình profile).
- `tests/` & `scripts/eval_erp_golden.py`: thêm unit test cho quy tắc chuẩn hóa/quyền/hiển thị và thêm ca đối soát SQL thật vào bộ Golden Eval.
- Tài liệu: cập nhật [AGENTS.md](../AGENTS.md), [ERP_MES_COVERAGE.md](ERP_MES_COVERAGE.md), [PROJECT_MAP.md](PROJECT_MAP.md) và [PLAN.md](PLAN.md) khi thay đổi phạm vi/quy tắc.

Không nhồi thêm luật đặc thù câu chat đơn lẻ vào `SYSTEM` prompt để bù cho giới hạn suy luận đa bước của `qwen2.5-14b`.

## 4. Kiểm thử trước triển khai

Chạy từ `/home/admin/ai-stack`:

```bash
python3 -B -m unittest tests.test_erp_agent tests.test_erp_semantic_query tests.test_erp_semantic_retrieval tests.test_erp_export tests.test_erp_incident_changes tests.test_erp_golden_pipeline tests.test_openwebui_speed_selector_patch
python3 -B scripts/eval_erp_golden.py --dry-run
bash scripts/test_erp_agent_postgres.sh
```

Khi được phép kiểm tra live trên vLLM + ERP DB chỉ đọc:

```bash
docker cp scripts/eval_erp_golden.py open-webui:/tmp/eval_erp_golden.py
docker exec open-webui env HTMP_AGENT_ROOT=/app/backend python3 -B /tmp/eval_erp_golden.py --live --model-url http://vllm:8000/v1/ --min-pass-rate 0.90
docker exec open-webui rm -f /tmp/eval_erp_golden.py
```

## 5. Triển khai lên Open WebUI & bắt buộc restart khi đổi code Python/config

- Nếu sửa `functions/htmp_erp_agent_pipe.py` hoặc `config/htmp-erp-agent-profile.json`: chạy `scripts/openwebui_bootstrap_runtime.py` để upsert vào `/app/backend/data/webui.db` và chạy lại với `--check` (`bootstrap check: PASS`).
- **Nếu sửa bất kỳ file nào trong `erp_ai/`, `config/` hoặc `backend-patches/`:** các thư mục này được bind-mount chỉ đọc vào `open-webui`, tiến trình `uvicorn` đang chạy **không tự nạp lại** module đã import. **Bắt buộc chạy `docker compose restart open-webui`** và đợi `/health` trả OK trước khi báo hoàn tất hoặc kiểm tra trên trình duyệt.

## 6. Đối chiếu với ERP UI

So sánh cùng điều kiện trên màn 3SERP:
- cùng khoảng ngày và **cùng loại ngày** (ngày chứng từ vs ngày nhận hàng/giao hàng);
- cùng mã hàng, đối tượng, kho, ĐVCS, trạng thái chứng từ và đơn vị tính;
- cùng quyền người dùng.

## 7. Mẫu báo cáo hoàn tất

```text
Nghiệp vụ: <tên nghiệp vụ>
Nguồn: <header/detail, khóa nối và trường ngày>
Phạm vi: <thời gian, trạng thái, quyền>
Files đã cập nhật: <danh sách>
Tests & Eval: <unittest + eval_erp_golden --dry-run/--live>
Open WebUI sync/restart: <bootstrap check + restart open-webui health>
UI comparison: PASS/FAIL — <case cụ thể>
Việc còn thiếu: <không có hoặc danh sách>
```
