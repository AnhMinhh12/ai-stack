# Ma trận độ phủ trợ lý ERP/MES

Ảnh chụp hiện trạng ngày **25/11/2026** từ bản đồ khảo sát, cấu hình agent và bộ kiểm thử Golden Eval. Dùng ma trận này làm backlog cho các câu hỏi mới của người dùng.

## Tài sản theo phân hệ

| Phân hệ | Mục khảo sát đã mở / tổng | Báo cáo tra cứu (`reports`) | Hợp đồng semantic (`approved`) | Ghi chú & ưu tiên đối soát |
| --- | ---: | --- | --- | --- |
| Bán hàng và giao nhận | 52 / 63 (`SO`) | `sales_lines`, `sales_orders`, `sales_order_price_gaps`, `delivery_order`, `price_list`, `replacement_orders` | `sales_delivery_lines`, `sales_order_lines` | Liên kết đơn $\rightarrow$ lệnh giao $\rightarrow$ phiếu xuất, giao bù NG, bảng giá/MOQ |
| Mua hàng | 32 / 38 (`PO`) | — | `purchase_requests` (`ph91`/`ct91`), `purchase_order_lines` (`ph94`/`ct94`), `purchase_receipt_lines` | Hỗ trợ cả `day` (`ngay_ct` ngày lập) và `required_date` (`ngay_yc` ngày nhận hàng), người đề nghị/lập (`HP2843`/`user_name`), giá mua |
| Kho | 76 / 85 (`IN`) | `inventory_balance`, `inventory_by_warehouse`, `receipt_lines` | `inventory_movements` | Tồn tại ngày chốt (index `ct70_ma_vt`/`cdvt_ma_vt`), tồn từng kho, điều chuyển |
| Kế toán và công nợ | 2 / 3 (`GL`) | — | `gl_account_movements` (`ct00`) | `ct00` hiện chỉ có phát sinh khác 0 đến `2024-09-06`; bảng số dư đầu kỳ `cdkh`/`cdtk` trống |
| Kế hoạch và định mức | 22 / 28 (`MF`) | `product_structure`, `forecast_po` | `production_forecast_demand` | Snapshot mới nhất `mfkhsx_po_fc`; hỗ trợ fallback mã gốc (`425-00107`) |
| Sản xuất MES | 2 / 2 (`MES`) | — | `mes_production_output`, `mes_work_orders`, `mes_oee_daily`, `mes_downtime_lines`, `mes_ng_defects`, `mes_material_usage` | Sản lượng theo ca/WO, OEE (`cycle_time` + `cavity`), dừng máy, NG, tiêu hao NVL |
| Chất lượng | 1 / 1 (`QC`) | `qc_label_status` | `qc_iqc_lines` | Kiểm tra IQC (`phiqc`) và trạng thái tem OQC (`intem_log`) |
| Khuôn và thiết bị | — | `mold_profile`, `mold_label_stock` | `mold_cavity_specs` | Liên kết khuôn $\leftrightarrow$ sản phẩm $\leftrightarrow$ cavity, chu kỳ, shot lũy kế và shot bảo hành còn lại |
| Danh mục | — | `customer_master`, `employee_master`, `material_customer`, `packaging_spec` | — | Tìm không dấu khách hàng/NCC, nhân viên (`dmkh.nv_yn=1` + `userinfo`), quy cách đóng gói |
| Hệ thống và nhóm cần phân loại | 9 / 34 (`SYS`, `ERP`, `NM` và chưa gán) | — | — | Rà lọc màn nghiệp vụ vs màn quản trị trong 254 mục khảo sát |

Tổng hợp tài sản hiện hành (đã gỡ toàn bộ nhánh sinh SQL tự do và mã nguồn `htmp-nhanh` lỗi thời):
- **16 manifest** trong [config/erp-reports](file:///home/admin/ai-stack/config/erp-reports) và **18 file SQL** trong [sql/erp-reports](file:///home/admin/ai-stack/sql/erp-reports).
- **18 báo cáo tra cứu (`reports`)** và **16 hợp đồng semantic (`approved`)** trong [erp-agent.json](file:///home/admin/ai-stack/config/erp-agent.json) (tự động điều phối tool, gợi ý dataset, kiểm tra tham số và nhãn Rich UI từ metadata).
- Các liên kết UI $\rightarrow$ API $\rightarrow$ function và quy tắc phê duyệt trong 254 mục khảo sát (nguồn [bản đồ màn hình](evidence/ERP-MAP-20261107/README.md)) cần tiếp tục đối soát khi mở thêm hợp đồng/báo cáo mới.

## Phần cần xây và duy trì chung

| Phần | Trạng thái hiện tại | Điều kiện nghiệm thu |
| --- | --- | --- |
| Đường ống Open WebUI | Đã chuẩn hóa `htmp-erp-agent-staging` chạy Pipe trực tiếp [htmp_erp_agent_pipe.py](file:///home/admin/ai-stack/functions/htmp_erp_agent_pipe.py), gỡ hoàn toàn module cũ. | Chat nhiều lượt giữ nguyên mốc ngày/thực thể, hiển thị Rich UI `embeds` và không rò CJK. |
| Chuẩn hóa và hợp đồng | [agent_backend.py](file:///home/admin/ai-stack/erp_ai/agent_backend.py), [context_hints.py](file:///home/admin/ai-stack/erp_ai/context_hints.py), [semantic_normalizer.py](file:///home/admin/ai-stack/erp_ai/semantic_normalizer.py) và [presentation.py](file:///home/admin/ai-stack/erp_ai/presentation.py) đọc toàn bộ cấu hình (`cues`, `param_schema`, `field_labels`, `default_dimensions`, `value_aliases`, `parent_prefix_fallback`) từ [erp-agent.json](file:///home/admin/ai-stack/config/erp-agent.json). | Thêm hợp đồng hoặc báo cáo mới chỉ khai báo trong `erp-agent.json`, không thêm `if/else` theo tên dataset/report trong Python. |
| Kiểm thử & Golden Eval | 90 unit test cục bộ + [eval_erp_golden.py](file:///home/admin/ai-stack/scripts/eval_erp_golden.py) (17 ca E2E có đối soát SQL thật; chạy live đạt 16/17 = `94.1%`, `0 tool_errors`). | Mọi thay đổi prompt/schema/code phải đạt `>= 90%` trên `--live`, `100%` trên `--dry-run`, và phải restart `open-webui` trước khi test UI. |

## Lệnh kiểm thử chuẩn

```bash
python3 -B -m unittest tests.test_erp_agent tests.test_erp_semantic_query tests.test_erp_semantic_retrieval tests.test_erp_export tests.test_erp_incident_changes tests.test_erp_golden_pipeline tests.test_openwebui_speed_selector_patch
python3 -B scripts/eval_erp_golden.py --dry-run
bash scripts/test_erp_agent_postgres.sh
```
