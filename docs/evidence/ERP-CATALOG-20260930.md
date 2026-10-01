# ERP catalog audit — 2026-09-30

## Scope and method

This audit connected to `3SERP_HTMP_DATA` as the configured `read_htmp`
account.  The transaction was explicitly read-only and queried only
PostgreSQL catalog metadata (`pg_proc`, `pg_namespace`, and function source
text).  It did not execute an ERP function, query business rows, or alter any
database object.

The function inventory was compared with the source tables declared in the 70
`pending_ui_validation` report manifests.  A textual source-table overlap is a
**candidate mapping only**: it is useful for reviewing business logic, but it
does not prove that a particular ERP UI route calls that function.

## Findings

| Check | Result |
| --- | ---: |
| Non-system functions scanned | 1,301 |
| `public` functions scanned for safety flags | 1,255 |
| Functions referring to at least one tracked report-source marker | 587 |
| Functions containing dynamic-SQL markers (`EXECUTE` or `format(`) | 580 |
| Functions containing temporary-table markers | 866 |
| Functions containing DML markers | 945 |

The catalog confirms the restriction used by the fixed-SQL report layer: ERP
functions must be inspected as reference material, not executed by the AI
query path.  Many functions that overlap report sources create temporary
tables, perform DML, or construct SQL dynamically.

## Source-overlap candidates to inspect

These candidates share several distinctive sources with a report; they are
not execution dependencies and remain excluded from the AI allowlist.  They
must be confirmed through ERP screen/report metadata before their logic is
used as a reference.

| Report | Candidate function | Shared source markers |
| --- | --- | --- |
| `bang-ke-lenh-giao-hang` | `vertdata_hda_so1` | `ct96`, `ct96lo`, `ctkhgh`, `ct81`, `dmvt`, `sys_dmtt` |
| `bao-cao-tien-do-giao-hang` | `vertdata_to2_1_so1` | `ph64`, `ct64`, `ctkhgh`, `ph96`, `dmvt`, `sys_dmtt` |
| `bao-cao-ton-kho` | `db_cttonkho33` | `cdvt`, `ct70`, `dmkho` |
| `bao-cao-tinh-trang-don-hang-mua` | `vertdata_po1_pr0` | `ph94`, `ct94`, `ct77`, `dmvt` |
| `phieu-iqc` | `vertdata_iqc` | `phiqc`, `dmvt` |
| `thoi-gian-dung-chuyen-theo-phien` | `db_thldc` | `mes_oi_stop_line`, `mes_oi_confirm` |
| `thong-ke-dang-ky-ng-sx` | `db_mesbcoee` | `mes_oi_confirm`, `mes_oi_ng_confirm` |

The first detailed check rejected one textual candidate:
`vertdata_hda_so1`, despite its overlap with `bang-ke-lenh-giao-hang`, is the
generic "retrieve previous document" flow from an HDA document to SO1.  It is
not evidence that the delivery-order listing screen calls that function.  The
next audit pass therefore resolves screen-to-function mappings from ERP
metadata rather than source-table overlap alone.

## Consequence for validation

The database layer can now be used to review the original business logic and
resolve a discrepancy found during UI QA.  It cannot by itself prove the UI
endpoint, its default filters, formatting, pagination, or frontend-specific
permission rules. Reports remain `pending_ui_validation` until their three UI
comparison cases are recorded and accepted; the validated mold-product report
is recorded separately below.

## First logic comparison: `bao-cao-ton-kho`

`inbctonkho(params)` is the catalog function whose declared filters, balances,
and output grain most closely match `bao-cao-ton-kho`.  Its source confirms
the static query's core calculation: opening `cdvt.ton00`/`du00` plus
year-to-date `ct70.(sl_nhap - sl_xuat)` and
`ct70.(tien_nhap - tien_xuat)`, then exclusion of zero quantity.

The comparison found and corrected one static-query defect: the `ma_vt`
filter had been applied to the `ct70` movement branch but not the `cdvt`
opening-balance branch.  The fixed SQL now applies the same parameterized
material filter to both branches.

The original function delegates authorization to `sys_getrolerecord` for both
branch and warehouse scope.  The static report uses the approved
`userinfo.ds_branchs` model and `dmkho`; the equivalence of these two scope
models remains a UI/authorization validation item and is not claimed here.

## Screen metadata comparison: `bang-ke-lenh-giao-hang`

`sys_reports` identifies the active report grid as `SOBKLenhGiaoHang` (with a
second active template `SOBKLenhGiaoHang1`).  Its `sys_reportparams` metadata
declares both document-date (`dfrom`/`dto`) and delivery-date
(`dfrom_gh`/`dto_gh`) ranges.  The static manifest and SQL previously exposed
only the document-date range.  Optional, parameterized delivery-date filters
have been added to the manifest and fixed SQL.  The UI evidence case now
requires those two date ranges to be checked independently.

## Screen metadata comparison: `thong-ke-dang-ky-ng-sx`

`sys_reports` maps this screen to `MESBKDangKyNG`. Its parameters include a
date/time range, work order, product, line, OI session, and branch. The static
query had used a non-existent `mes_oi_confirm.ngay_ct` column and could
multiply `in_process` when an OI had multiple NG rows. It now groups
production and NG facts separately before joining, filters by the actual
`create_date` column, and applies the session/branch scope through
`userinfo.ds_branchs`. Catalog review of `mesbkdangkyng` confirms that the UI
`cLineCode` filter is `mes_oi_confirm.machine_code`, which now replaces the
earlier provisional `mes_scheduling.work_center_code` mapping.

## Screen metadata comparison: `phan-bo-thoi-gian-dung-chuyen`

`MESBKPhanBoTGDung` declares required date range plus optional time, line, OI,
classification, and operation filters. The manifest previously declared none
of them, despite the SQL accepting only dates and line. It now exposes the
available date/time, line, OI, classification, and branch filters. The source
allocation table has no branch column, so its scope is checked with a
correlated `EXISTS` against `mes_oi_confirm.branch_code`; this prevents a
one-to-many scope join from changing the report grain. Catalog review of
`mesbkphanbotgdung` identifies the UI operation filter as
`mes_oi_confirm.operation_code`; the allocation table itself does not retain
that field, so this remains a correlated-source/UI QA item rather than a
guessed direct-column mapping.

## Full fixed-SQL compile sweep

An `EXPLAIN`-only sweep in an ERP read-only transaction now passes all **70/70**
pending report SQL files. The sweep exposed and corrected five latent compile
defects in purchase-order status, shelf-life extension, OQC, NG-by-session,
and lot NXT reports. Corrections used catalog-confirmed column names and did
not execute any ERP report function. This is a SQL validity check, not UI
validation; all reports remain `pending_ui_validation`.

## Confirmed API/function mappings previously pending

Catalog source confirms `inbctontheolo` calculates opening lot balance as
`cdbsp.ton00` plus `ct70bsp.(sl_nhap - sl_xuat)` from the financial-year start
through the day before the selected period. The fixed SQL now follows that
calculation rather than treating `cdbsp` as a dated movement table. `oqc_get_data`
confirms OQC material/name/lot are carried in `intem_log.data_tem`, carton is
joined by `mes_oi_dong_thung.serial_tem_thung`, pallet by
`palletct.id_carton`, and the status caption by `sys_listoptions.form_value`.

## ERP dynamic-permission equivalence audit

`sys_getrolerecord(type='R')` was read from `pg_catalog` without execution.
For reports its data predicate is exactly: deny a missing user; bypass for a
super user or when both `ds_branchs` and `ds_stocks` are empty; constrain a
source `ma_dvcs` to `userinfo.ds_branchs`; constrain a non-empty source
`ma_kho` to warehouses in `dmkho` whose `ma_dvcs` is allowed; and, for the
source table passed to the function, require non-empty `ds_ma_dvcs` to overlap
the allowed branches (except `dmkho`). `sys_role*` and `sys_roledt` are not
part of this row-level predicate; they govern UI/action access separately.

The fixed SQL reports already use the first four rules where the report source
has branch/warehouse data. Do not add a blanket `ds_ma_dvcs` predicate to all
joined dimensions: the ERP function evaluates the table passed as its primary
source, and filtering lookup dimensions would change UI output.

The six reports previously missing an authenticated session user now require
`authenticated_user_id` from the execution context.  Five have a
catalog-confirmed primary-source scope: `bao-cao-tinh-trang-don-hang-mua`
uses `ph94.ma_dvcs` and `ct94.ma_kho`; `gia-han-han-su-dung` uses
`cdvt13.ma_kho`; `oqc-xac-nhan-chat-luong` uses `intem_log.ma_kho`;
`tong-hop-hang-ng-theo-phien` uses `mes_oi_confirm.branch_code`; and
`tong-hop-nxt-theo-lo` applies the warehouse scope to both `cdbsp` and
`ct70bsp` before aggregation.  Each warehouse scope uses `dmkho` and no
predicate was added to a lookup dimension.

UI evidence now confirms `khai-bao-quy-trinh-san-xuat-sp` uses `MfBomBop` and
the primary grid source is `mfbom`: `bom_version` is Version,
`branch_list` is Mã ĐVCS, and `status` is Trạng thái. The UI loads only its
4,986 Sử dụng records; the 55 Không sử dụng records in the base table are not
loaded, so a grid search for “Không sử dụng” correctly returns zero. Fixed SQL
therefore scopes `mfbom.branch_list` for restricted identities and always
limits output to status 1, matching the UI.

`MESBKPhanBoTGDung` now has UI data evidence for the dynamic rule: the screen
found the next OI, split one interval into four rows at the 08:00 boundary,
and repeated the two allocated causes (A1 = 0.0500 and B1 = 0.2700 minutes)
on every split row. Its top allocation total was therefore 1.2800 minutes
(0.3200 × 4), while the four interval durations totalled 4,368.1500 minutes.
The fixed SQL now implements that rule from `mes_oi_confirm`, `new_oi_cbsx`,
and `mes_oi_allocation_stop_line`, rather than directly joining allocation to
a single raw interval. It remains `pending_ui_validation` only for the
separate restricted-user/branch comparison.

## Complete report-scope sweep

The full manifest set was re-scanned after the targeted remediation. All
fixed-SQL report artifacts now either bind their session user to `userinfo`
and apply a branch/warehouse predicate, or are explicitly fail-closed where
the catalog exposes no reliable branch-bearing primary source. The latter
class currently includes mold master/detail, carton split/merge, and OI
version records; it is unavailable to users with a configured scope until UI
evidence supplies the source mapping. The only former live report without a
trusted ERP session mapping, `nhat-ky-nhap-xuat-ton`, is also blocked at the
tool boundary; its old hard-coded branch default is not treated as
authorization.

An `EXPLAIN`-only read-only sweep after these changes passes all **71/71**
report SQL artifacts. This verifies SQL/catalog compatibility only; reports
still marked `pending_ui_validation` require their recorded UI cases before
allowlisting.

## State and grid metadata resolution

The remaining state mappings were resolved from `sys_command`, `sys_reports`,
`sys_gridconfig`, and the unexecuted function source:

| Artifact | Confirmed ERP state/grid | Primary data and authorization path | Result |
| --- | --- | --- | --- |
| `khai-bao-quy-trinh-san-xuat-sp` | `MfBomBop` | `mfbom` is the primary grid table; `bom_version`, `branch_list`, and `status` directly supply Version, Mã ĐVCS, and Trạng thái. | **UI validation complete:** base row, product filter, and the active-only UI default match fixed SQL. |
| `gop-tach-thung` | `MESBKGopTachThung` | `intem_carton_log` → `mes_oi_dong_thung` → `phlsx.ma_dvcs`; the function also enriches carton, material, and user data. | Scoped through `phlsx.ma_dvcs`; full display projection remains a UI comparison item. |
| `version-oi-theo-day-chuyen` | `MESBCVersionOI` / `MESBCVersionOI1` | `mflist_line_station.ip` left-joins `mes_oi_version`; line authorization is `mflist_line.branch_code`. | Scoped by the line branch. |
| `bao-cao-thong-tin-sp-theo-ho-so-khuon` | `MESBCTTSPTHSK` | UI evidence confirms the filters are Mã khuôn, Mã sản phẩm, and Trạng thái. The function reads `dmhosokhuonsp`, then enriches the mold from `dmhosokhuon` and the product from `dmvt`. | **UI validation complete:** row values, Mã sản phẩm/Tất cả, and Mã sản phẩm/Sử dụng all match the fixed SQL. |
| `phan-bo-thoi-gian-dung-chuyen` | `MESBKPhanBoTGDung` | The function builds OI intervals from `mes_oi_confirm`, finds the next OI through `new_oi_cbsx`, splits cross-day intervals at 08:00, then joins `mes_oi_allocation_stop_line`. | State/source resolved; dynamic interval/allocation output still requires UI comparison before replacement. |
| `danh-muc-khuon` | `ListDMKhuon` | `mfdmkhuon.mold_code`; no direct branch key exists in the catalog table. | Remains fail-closed for scoped users. |
