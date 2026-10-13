# ERP catalog mapping — sales and inventory screens

Date: 2026-10-13

## Method

The ERP PostgreSQL catalog was queried through the configured read-only
account. The check inspected relation columns and function definitions only;
it did not execute an ERP report or read business rows.

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
