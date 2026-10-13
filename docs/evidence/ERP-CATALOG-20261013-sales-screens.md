# ERP catalog mapping — sales and inventory screens

Date: 2026-10-13

## Method

The ERP PostgreSQL catalog and business rows were queried through the
configured read-only account. Screen captures supplied from the ERP UI were
then compared with the same keys, date periods and aggregates.

## Confirmed mappings

| ERP screen | State/function | Physical sources | Key / grain |
| --- | --- | --- | --- |
| Danh mục bảng giá | catalog relation | `dmbanggia`, `dmbanggiact` | `ma_bang_gia`, then item/customer or customer-group, MOQ (`sl_min`) and effective range |
| Tổng hợp bán hàng | `SOBCTongHopBH` / `sobctonghopbh` | `ph81`, `dmkh`, state/config tables | function-defined aggregate; UI validation required for money metric |
| Doanh số bán hàng theo khách hàng | `SOBCDSTheoKH` / `sobcdskh` | `ph81`, `ct81`, `ph76`, `dmkh`, `dmvt` | customer → item → reporting period |
| Bảng kê đơn hàng bán | `SOBKDonHang` / `sobkdonhang` | `ph64`, `ct64`, `ctkhgh`, `dmkh`, `dmvt` | sales-order line (`stt_rec`, `ln`) |
| Danh mục khách hàng | catalog relation | `dmkh` | `ma_kh` |
| Phiếu yêu cầu đổi, trả hàng bán | `SOBKYCDoitra` / `sobkycdoitra` | `ph66`, `ct66`, `dmkh`, `dmvt`, `dmvv` | return-request line (`stt_rec`, `ln`) |
| Báo cáo tồn kho theo số khuôn | `InBCTonKhoTheoSoKhuon` / `inbctonkhotheosokhuon` | `intem_log`, `dmvt`, `dmlo`, `dmkho`, `dmvitri` | material–lot–warehouse–location–mold |
| Báo cáo tồn kho theo trạng thái tem | `InBCTKTheoTTTem` / `inbctktheotttem` | `intem_log`, `dmvt`, `sys_listoptions`, `sys_gridconfig` | material–lot–warehouse–location–QC status |

## Relevant confirmed columns

- `dmbanggiact`: `ma_vt`, `ma_kh`, customer groups, `sl_min`, price before/after tax, currency, and effective dates/times.
- `ct66`: material, warehouse, quantity, selling price, amount, tax, discount, linked sales order/invoice fields.
- `ph66`: customer, document status/dates, currency, header totals, actual receipt/return dates.
- `ct81`: material, warehouse/location, quantity, selling price/amount, discount, tax, delivery dates, and `quy_cach_dong_goi`.
- `intem_log`: label identifier, warehouse/location, lifecycle status, `status_qc`, and serialized label payload.

## Confirmed UI parameter contracts

The screen metadata in `sys_command` and `sys_reportparams` confirms these
states and filters. This is configuration metadata, not business-row data.

| State | Confirmed filters |
| --- | --- |
| `SOBCTongHopBH` | Required report type and start date; optional period count, customer/customer groups, branch, and grouping. |
| `SOBCDSTheoKH` | Date range; customer/customer groups, material/material groups, branch, and grouping. |
| `SOBKDonHang` | Date range; document-number range, customer, salesperson, material/material groups, branch, transaction and status. |
| `SOBKYCDoiTra` | Date/time range; document-number range, customer, material/material groups, branch and status (`RQ1`). |
| `INBCTonKhoTheoSoKhuon` | Date range, material/material groups, Die No, lot, warehouse, location, warehouse type, status and mold. |
| `INBCTKTheoTTTem` | Warehouse, material/material groups, QC status, lot and location. |

## Implementation gate

The fixed-SQL artifacts must use these catalog-confirmed sources and reproduce
the relevant UI filter, aggregate, and permission behavior. Report functions
remain reference-only; they must not be called by the AI query path.

## UI comparisons performed on 2026-10-13

| ERP screen | Exact UI route | Reproducible case | Result |
| --- | --- | --- | --- |
| Danh mục bảng giá | Bán hàng → Chính sách bán hàng → Danh mục bảng giá | `001` / `BGC` / Bảng giá 2026 / Giá bán buôn / Bảng giá chuẩn / Sử dụng | PASS |
| Tổng hợp bán hàng theo tuần/tháng | Bán hàng → Báo cáo đặc thù → Báo cáo tổng hợp bán hàng theo tuần/tháng | Tuần 1, 01–07/10/2026; `KH0015`; SL `1,188,691`, tỷ lệ `25.7700%` | PASS |
| Doanh số bán hàng theo khách hàng | Bán hàng → Báo cáo → Doanh số bán hàng theo khách hàng | 10/2026; `KH0007`; SL `80,900`, doanh số `313,835,449` | PASS |
| Bảng kê đơn hàng bán | Bán hàng → Bảng kê → Bảng kê đơn hàng bán | `001-2610-000001`; SL đơn `353,150`, SL giao chi tiết `208,610`, trạng thái Đóng | PASS |
| Danh mục khách hàng | Bán hàng → Danh mục khai báo → Danh mục khách hàng | `KH0007`; AS-VN-HN CO., LTD; điện thoại `094 189 9134`; Sử dụng | PASS |
| Phiếu yêu cầu đổi, trả hàng bán | Bán hàng → Bảng kê → Bảng kê phiếu yêu cầu đổi trả hàng bán | `001-2610-000024`; `KH0062`; `11,816 PCS`; Hoàn thành | PASS |
| Báo cáo tồn kho theo số khuôn | Kho vận → Báo cáo → Báo cáo tồn kho theo số khuôn | `003-M69-101-2`; tổng UI `15,399 PCS` | PASS |
| Báo cáo tồn kho theo trạng thái tem | Kho vận → In tem QR code → Báo cáo tồn kho theo trạng thái tem | `003-M69-101-2`; tổng `16,599 PCS`; 4 dòng OK và 1 dòng NG | PASS |

Each report manifest remains `pending_ui_validation`: the project contract
requires three UI cases per artifact, while the table above documents the
first successful case for each screen.
