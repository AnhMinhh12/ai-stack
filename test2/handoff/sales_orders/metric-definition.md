# Metric Definition: Sales Order Header (`sales_order_header` / `sales_orders`)

## 1. Screen State and URL

- **Module**: Sales (`SO`)
- **Screen State**: `SO1` (registered in menu with `menuid: SO_a0_01_02`, `type: V`)
- **Controller & View**: `SO1Controller` / `/Areas3SERP/SO/Vouchers/SO1/SO1.html`
- **URL**: `http://10.0.6.2:1004/Solution/ERP/#/SO/SO1`
- **UI Title**: `Đơn hàng (Hợp đồng)` (Breadcrumb: `Bán hàng` > `Đơn hàng (Hợp đồng)`)
- **Detail Screen State**: `SO1Overview` (`/SO/SO1Overview` via `c.EditRowPage`)

---

## 2. API Request Loading Data

- **Method**: `HTTP GET`
- **Endpoint**: `/SOAPI/api/Vouchers/SO1API/GetData/`
- **Parameters Passing Convention**: Nested object passed via query string parameter `searchDynamic`:
  `GET /SOAPI/api/Vouchers/SO1API/GetData/?searchDynamic={...}`
- **Query Fields**:
  - `pindex`: Zero-based page index (e.g. `0`)
  - `plimit`: Page size limit (e.g. `20`)
  - `gridid`: Grid identifier (`"SO1"`)
  - `stateid`: Screen state identifier (`"SO1"`)
  - `keyword`: Search keyword string (default `""`)
  - `status`: Status filter (default `"*"` for all statuses)
  - `pwhere`: SQL filter clause (default `" 1 = 1 "`)
  - `user_id`: Authenticated user ID (integer `78`)
  - `search_dynamic_cols`: Advanced column search conditions (default `""`)
  - `cols_search`: Comma-delimited list of searchable columns extracted from grid config:
    `sys_dmtt.statusname,a.ngay_ct,a.so_ct,a.ma_gd,sys_dmmagd.ten_gd,a.so_po,a.ma_kh,dmkh.ten_kh,a.dia_chi,a.ong_ba,a.dien_thoai,a.ma_nvbh,a.dien_giai,a.ma_nt,a.ty_gia,a.t_so_luong,a.t_tien2,a.t_thue,a.t_ck,a.t_tt`
  - `search_dynamic_ph`: JSON string for voucher header search (default `""`)
  - `search_dynamic_ct`: JSON string for voucher detail search (default `""`)
- **Request Headers**:
  - `Token`: Active session authentication token
  - `state`: `"SO1"`
  - `user_name`: `"IT.ERP"`
  - `user_id`: `"78"`
  - `lang`: `"vi-VN"`
  - `ma_dvcs`: `""` (Empty string sent by client `CRUDServices.getdata`)
  - `module`: `"SO"`
  - `application`: `"ERP"`
  - `FROM`: `"web"`

---

## 3. Date Field and Time Basis

- **UI Column Header**: `Ngày chứng từ` (`ngay_ct`)
- **Physical Column**: `ph64.ngay_ct`
- **Date Type**: Document / Voucher date (`ngay_ct`). It is NOT posting date, receipt date, or production date.
- **Display Format**: `DD/MM/YYYY` (formatted client-side from ISO `YYYY-MM-DD`).
- **Audit Timestamps**: Returned in payload but hidden from primary grid:
  - `date0` / `time0`: Creation date and time (`YYYY-MM-DD`, `HH:mm:ss.ffffff`).
  - `date2` / `time2`: Last update / approval date and time.
  - `user_id0` / `user_name0`: Creator user ID and login username.
  - `user_id2` / `user_name2`: Approver / modifier user ID and login username.

---

## 4. Status Inclusion / Exclusion & Role Scoping

- **Status Field**: `ph64.status` joined with `sys_dmtt` on `status = status AND ma_ct = 'SO1'`.
- **Observed Status Values**:
  - `0`: `Lập chứng từ` (Draft)
  - `1`: `Chờ duyệt` (Pending Approval)
  - `2`: `Duyệt` (Approved)
  - `*`: All statuses (Default filter on grid view).
- **Inclusion / Exclusion**: Default grid view displays ALL active statuses (`status = "*"`), including both unapproved (`status = 1`) and approved (`status = 2`) records.
- **Role Scoping**: Evaluated server-side via `user_id` and branch unit (`001`). `Admin` role has `r_access: 1, r_add: 1, r_edit: 1, r_delete: 0`.

---

## 5. Row Grain

- **Row Grain**: **Voucher Header level (`ph64`)**.
- **Unique Primary Key**: `stt_rec` (e.g. `A1000000025227547SO1`).
- **Detail Line Grain**: Line items (`ct64`) are NOT flattened into the overview grid. Line items belong to `ct64` joined by `stt_rec` and line number `ln`, accessible when drilling down into `SO1Overview`.
- **Cardinality Warning for Machine A**: When joining `ph64` with `ct64` in reference SQL, do NOT sum header totals (`t_tt`, `t_so_luong`) across detail rows, as this will multiply amounts.

---

## 6. Total Calculation & Paging

- **Paging Limit**: 20 records per page (`plimit = 20`).
- **Paging Mechanism**: Infinite scroll / lazyload triggered on scroll down (`v.Paging()` increments `$sys.index` and appends rows).
- **Displayed Grand Total**: Total count displayed on UI header badge is `579 110` (formatted as `579,110`).
- **Total Scope**: **Server-side total across all pages**, returned in response as `res.Result.TotalItems: 579110` and on each row as `item.total: 579110`. The UI does NOT recalculate or truncate this to only the loaded page.

---

## 7. Post-API Formatting, Grouping & Transformations

- **Currency & Number Formatting**:
  - `t_so_luong`: Formatted with thousands separator (`#.##0`).
  - `t_tien2`, `t_tt`: Formatted with currency decimals according to `ma_nt` (`VND` has 0 decimals, `USD` has 2 decimals).
  - `ty_gia`: Formatted with exchange rate decimals (default 0 or 2, e.g. `23,080.0`).
- **Labels & Code Joins**:
  - `statusname`: Joined client-side/API from `sys_dmtt` (`ma_ct = 'SO1'`).
  - `ten_gd`: Joined from `sys_dmmagd` on `ma_gd` and `ma_ct = 'SO1'`.
  - `ten_kh`: Joined from `dmkh` on `ma_kh`.
- **No Grouping / Pivoting**: The overview grid displays flat rows without client-side grouping, pivoting, or client-side aggregations.

---

## 8. Zero, NULL, Cancelled and Unapproved Records

- **Unapproved Records**: Displayed in full (`status = 1`, label `Chờ duyệt`), showing document date and quantity. Amounts can be `0.0` or non-zero depending on whether pricing was completed.
- **Cancelled Records**: Handled via workflow cancellation endpoints (`HuyDuyet`); status reflects cancellation according to `sys_dmtt`.
- **Zero Quantities / Amounts**: Numerical fields display `0.0` when no amounts are entered.
- **NULL Values**: Null text fields (`so_po`, `dien_giai`, `ma_nvbh`) return empty strings `""` or null, rendered as empty table cells.

---

## Critical Source Assumptions Validated

1. **Transaction Type `ma_gd = 10`**:
   - **CONFIRMED**: Real ERP API and UI evidence proves `ma_gd = 10` is specifically designated for `"Giao bù hàng thiếu"` (Replacement / shortage delivery).
   - Standard orders use `ma_gd = 1` (`"Đơn hàng -> Lệnh giao hàng"`).
2. **Historical Sales Amount**:
   - Must use `ph64.t_tt` / `ct64.tien2` (transaction amount at the time of order), NOT current item price multiplied by quantity.
3. **Primary Table Identity**:
   - Table `ph64` is confirmed as the header table via grid metadata (`tablename: ph64`) and field list.
