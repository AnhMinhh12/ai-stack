# Ma trận độ phủ và Bản đồ dữ liệu trợ lý ERP/MES

Ảnh chụp hiện trạng ngày **26/11/2026** sau khi đối soát toàn diện CSDL PostgreSQL `3SERP_HTMP_DATA` (`55` loại chứng từ `sys_dmct`, `525` trạng thái `sys_dmtt`, `103` bảng lõi / `4,074` cột UI-DB đã kiểm tra trên tổng `601` bảng/view và `202` bảng có dữ liệu) kết hợp [bản đồ màn hình 254 trạng thái UI](evidence/ERP-MAP-20261107/README.md).

## Bản đồ đối chiếu toàn bộ 40 Hợp đồng Semantic & 18 Báo cáo tra cứu

| Phân hệ | Báo cáo tra cứu (`reports`, 18) | Hợp đồng semantic (`approved`, 40) | Bảng DB nguồn & phạm vi dữ liệu đã xác minh |
| --- | --- | --- | --- |
| **Bán hàng & Giá bán (`SO`)** | `sales_lines`, `sales_orders`, `sales_order_price_gaps`, `delivery_order`, `price_list`, `replacement_orders` | `sales_delivery_lines`, `sales_order_lines`, `sales_delivery_orders`, `sales_quotations`, `sales_returns`, `sales_return_requests`, `sales_prices_current` | `ph81`/`ct81` (`HDA`), `ph64`/`ct64` (`SO1`), `ph96`/`ct96` (`TO2`), `ph61`/`ct61` (`SQ1`), `ph76`/`ct76` (`HDF`), `ph66`/`ct66` (`RQ1`), `dmbanggia`/`dmbanggiact`, `dmkh`, `dmvt`, `dmkho`, `sys_dmtt` |
| **Mua hàng & Giá mua (`PO`)** | — | `purchase_requests`, `purchase_order_lines`, `purchase_receipt_lines`, `supplier_quotations`, `purchase_prices_current`, `planning_pending_po` | `ph91`/`ct91` (`PR0`), `ph94`/`ct94` (`PO1`), `ph77`/`ct77` (`PR1`), `phbgncc`/`ctbgncc` (`BG0`), `dmgiamuact`, `mfkhsx_po_pending_linhkien`, `mfkhsx_po_nhua_pending`; hỗ trợ cả `day` (`ngay_ct`) và `required_date` (`ct91.ngay_yc`/`ct94.ngay_yc`), lọc `requester`/`creator_user` |
| **Kho vận & Tồn kho (`IN`)** | `inventory_balance`, `inventory_by_warehouse`, `receipt_lines` | `inventory_movements`, `inventory_stock_lots`, `warehouse_transfers`, `warehouse_internal_issues`, `warehouse_internal_receipts`, `warehouse_requests`, `planning_stock_snapshot` | `ct70`, `cdvt13`, `dmlo`, `ph85`/`ct85` (`PXB`/`PNF`, đã tối ưu scalar subquery), `ph84`/`ct84` (`PXA`), `ph74`/`ct74` (`PND`), `phdnv`/`ctdnv` (`DNV`), `phdxnvl`/`ctdxnvl` (`DXV`), `mfkhsx_ton_nhua`/`ton_linhkien`/`ton_kho_ok`/`ton_kho_ng` (chỉ lấy snapshot `max(date0)`) |
| **Kế hoạch, Lệnh SX & BOM (`MF`)** | `product_structure`, `forecast_po` | `production_forecast_demand`, `production_orders`, `bom_materials`, `ecn_and_bom_changes` | `mfkhsx_po_fc` (`FC` = FCST, `PO` = DO; hỗ trợ `value_aliases` và `parent_prefix_fallback`), `phlsx`/`ctlsx` (`PD1`), `mfbom`/`mfbom_material` (hỗ trợ tra ngược từ NVL lên SP mẹ), `phecn`/`ctecn`/`history_bom_change` (`date_change`) |
| **Sản xuất MES & Lịch điều độ (`MES`)** | — | `mes_production_output`, `mes_work_orders`, `mes_oee_daily`, `mes_downtime_lines`, `mes_ng_defects`, `mes_material_usage`, `mes_setup_and_mold_ops`, `mes_operators_output`, `mes_carton_packing`, `mes_shot_rejections`, `mes_scheduling_plan` | `mes_oi_confirm`, `mes_scheduling` + `mes_scheduling_output` (join `stt_rec`), `mes_oi_stop_line`/`dmnndungmay`, `mes_oi_ng_confirm`/`dmloi`, `mes_oi_material`, `mes_oi_setup_may`/`mes_oi_van_hanh_khuon`, `mes_oi_nv_dung_may` (`sl_th`), `mes_oi_dong_thung`, `mes_oi_bo_shot`, `mflist_line` |
| **Khuôn & Chất lượng (`QC`/`Mold`)** | `qc_label_status`, `mold_profile`, `mold_label_stock` | `qc_iqc_lines`, `qc_pqc_lines`, `mold_cavity_specs`, `mold_incident_status` | `phiqc`, `phpqc`, `dmhosokhuon`/`dmhosokhuonsp` (cavity, chu kỳ, `non_summable` shot/chu kỳ), `mfkhsx_thongtin_khuon` (chỉ lấy snapshot `max(date0)`); `intem_log` |
| **Kế toán & Công nợ (`GL`)** | — | `gl_account_movements` | `ct00`/`dmtk0`/`dmkh` (lưu ý dữ liệu thật trong `ct00` hiện chỉ có phát sinh khác 0 tới `2024-09-06`; bảng `cdkh`/`cdtk` trống) |
| **Danh mục (`DM`)** | `customer_master`, `employee_master`, `material_customer`, `packaging_spec` | — (hoặc ghép qua cột `*_name` không dấu trong 40 hợp đồng) | `dmkh` (`nv_yn=1` + KH/NCC), `userinfo`, `dmvt` |

Tổng hợp tài sản hiện hành (đã gỡ toàn bộ nhánh sinh SQL tự do và mã nguồn `htmp-nhanh` lỗi thời):
- **16 manifest** trong [config/erp-reports](file:///home/admin/ai-stack/config/erp-reports) và **18 file SQL** trong [sql/erp-reports](file:///home/admin/ai-stack/sql/erp-reports).
- **18 báo cáo tra cứu (`reports`)** và **40 hợp đồng semantic (`approved`)** trong [erp-agent.json](file:///home/admin/ai-stack/config/erp-agent.json) (mỗi hợp đồng đều hỗ trợ lọc tên không dấu `*_name` `contains`, trạng thái `sys_dmtt`, tên kho/vật tư/đối tác và gắn cờ `non_summable` cho chỉ tiêu trung bình/chu kỳ/cavity/shot/hệ số).
- Các hợp đồng mới thêm từ audit DB + UI được đánh dấu `"scope": "curated_scoped_subquery"` và đã kiểm tra thực thi SQL live `40/40`; đối chiếu giao diện 3SERP qua CDP cho phần màn chưa khảo sát trực tiếp hiện vẫn ở trạng thái `pending_ui_validation` do endpoint `127.0.0.1:19223` chưa mở trên máy chủ hiện tại.

## Phần kiến trúc mở rộng và kiểm soát ngưỡng ngữ cảnh

| Phần | Trạng thái hiện tại | Điều kiện nghiệm thu |
| --- | --- | --- |
| Đường ống Open WebUI | Chuẩn hóa `htmp-erp-agent-staging` chạy Pipe trực tiếp [htmp_erp_agent_pipe.py](file:///home/admin/ai-stack/functions/htmp_erp_agent_pipe.py), giữ trả lời làm rõ dạng text thuần (`insufficient_evidence`) khi người dùng thiếu kỳ dữ liệu. | Chat nhiều lượt giữ nguyên mốc ngày/thực thể, hiển thị Rich UI `embeds` và không rò CJK. |
| Truy hồi mở rộng 40+ contracts | [agent_backend.py](file:///home/admin/ai-stack/erp_ai/agent_backend.py) và [context_hints.py](file:///home/admin/ai-stack/erp_ai/context_hints.py) xếp `context_hints` lên trước, cấp lược đồ top-5 `recommended_datasets` trong `semantic_datasets` cùng mục lục gọn `other_datasets`, hỗ trợ `search_semantic_datasets(query=...)` và gợi ý fallback `X -> X_name` (`not isdigit`), bỏ cue nhầm làm bộ lọc (`PXA`/`PND`...), nêu rõ tên trường sai khi lỗi `PlanError`. | Kích thước `retrieve()` dưới giới hạn context (`< 26,000` chars với 40 hợp đồng), thêm hợp đồng mới chỉ khai báo trong [erp-agent.json](file:///home/admin/ai-stack/config/erp-agent.json). |
| Kiểm thử & Golden/Random Eval | **92/92** unit test cục bộ + **40/40** kiểm tra SQL live trên `3SERP_HTMP_DATA` + **13/13** kiểm thử phân quyền PostgreSQL cô lập + [eval_erp_golden.py](file:///home/admin/ai-stack/scripts/eval_erp_golden.py) (`--suite all`: 17 golden + 22 random đa phân hệ; dry-run đạt **39/39 = 100%**, live đạt **35/39 = 89.7%** (`15/17` golden + `20/22` random), `p50_ms: 12836`). | Mọi thay đổi prompt/schema/code phải đạt `>= 85%` trên `--suite all --live`, `100%` trên `--suite all --dry-run`, và bắt buộc `docker compose restart open-webui`. |

## Lệnh kiểm thử chuẩn

```bash
python3 -B -m unittest tests.test_erp_agent tests.test_erp_semantic_query tests.test_erp_semantic_retrieval tests.test_erp_export tests.test_erp_incident_changes tests.test_erp_golden_pipeline tests.test_openwebui_speed_selector_patch
python3 -B scripts/eval_erp_golden.py --suite all --dry-run --min-pass-rate 1.0
bash scripts/test_erp_agent_postgres.sh
```
