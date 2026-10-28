# Source baseline for the ERP Web machine

## Why this file exists

Machine B can open ERP Web but cannot access the AI-Stack source or DB. This
file tells Machine B what source-side report candidates already exist and what
Machine B must verify on ERP Web. Every item below is a **candidate only**:
all reports are `pending_ui_validation`, so do not treat table names, joins or
formulas as confirmed ERP facts.

Machine B should use this file to locate the corresponding ERP screen, capture
the actual API request/response and UI behavior, then send the evidence package
defined in `HANDOFF.md` to Machine A.

## Source runtime context

There are two separate paths on Machine A:

```text
htmp-nhanh -> functions/htmp_postgres_query.py -> legacy ask_erp
htmp-erp-agent-staging -> erp_ai fixed-report runtime
```

Do not assume a change or test in one path changes the other. Machine B does
not need to modify either path; it supplies ERP Web evidence only.

## Report candidate catalog

| Report ID | Intended business question | Candidate DB objects/join in source | Parameters to validate on UI |
|---|---|---|---|
| `sales_lines` | Sales warehouse issue lines | `ph81` + `ct81` by `stt_rec`, line key `stt_rec + ln` | item, date range, unit, warehouse, lot, quantity, amount |
| `price_list` | Price list and MOQ | `dmbanggia` + `dmbanggiact` by `ma_bang_gia`; `dmvt`, `dmkh` lookups | item, customer, effective date, MOQ, currency, status |
| `product_structure` | Product BOM and material norm | `mfbom` + `mfbom_material` by `bom_code`; `dmvt` | parent item, BOM version, validity date, component, norm |
| `customer_master` | Customer master | `dmkh` | code/name search, status, phone/address visibility |
| `material_customer` | Customer assigned on material | `dmvt.ma_kh = dmkh.ma_kh` | item, assigned customer, permission/unit behavior |
| `inventory_balance` | Book inventory at date | `cdvt` union `ct70`, `dmvt` | item, as-of date, unit, quantity, zero/no-row |
| `inventory_by_warehouse` | Book inventory by warehouse | `cdvt` union `ct70`, `dmkho`, `dmvt`; grouped by warehouse | item, as-of date, warehouse, warehouse total |
| `receipt_lines` | Warehouse receipt lines | `ct70` left join `userinfo` on user ID | item, date range, receipt number, warehouse, receiver |
| `forecast_po` | PO plan and forecast | `mfkhsx_po_fc` | item, delivery/calculation date, source/type, customer, model |
| `packaging_spec` | Packaging specification | `dmvt` | item, unit, box/tray/pallet quantities |
| `mold_profile` | Mold profile and shot life | `dmhosokhuon` + `dmhosokhuonsp` by mold | mold, item, total shots, warranty shots |
| `mold_label_stock` | Mold/die label inventory | `intem_log`, JSON label data | item, mold, die number, QC status, quantity |
| `sales_orders` | Sales orders and standard-price check | `ph64` + `ct64` by `stt_rec` | customer, date range, order/status, item, quantity, price, standard price |
| `sales_order_price_gaps` | Orders with missing standard price | `ph64` + `ct64`, `userinfo` | customer, date range, null/zero standard-price condition |
| `delivery_order` | Delivery order status | `ph96` + `sys_dmtt` for `TO2` status | delivery number, status label, creation date/time |
| `qc_label_status` | Inventory by QC label status | `intem_log` + `sys_listoptions` | item, QC status label, label count, quantity |
| `replacement_orders` | NG replacement delivery order | `ph96` + `ct96` by `stt_rec` | item, date range, transaction code, quantity, status |

## What Machine B must send for each candidate

For the matching ERP screen, create `handoff/<report_id>/` containing:

```text
scope.json             role, unit, language, data period and capture time
ui.png                 UI after applying filters
ui-cases.md            three cases: normal, edge, multi-line/grouped case
request.json           actual network request without credentials
response.json          actual response without credentials
metric-definition.md   UI labels, displayed total, status and time meaning
```

Record the exact screen state/URL in every package. If a candidate has no
matching screen or the UI behavior differs, say so explicitly; do not adapt the
source assumption on Machine B.

## Questions that Machine B must answer

For every candidate report, answer these from ERP Web/API evidence:

1. Which screen state and URL actually shows this metric?
2. Which request loads the data, and what fields/filters does it send?
3. Which date field does the UI use: document, posting, production, receipt,
   effective or as-of date?
4. Which statuses are included/excluded? Does the user role change scope?
5. Is a row a header, detail line, warehouse balance, lot balance or total?
6. Does the total include all pages, only the loaded page, or a server total?
7. Does the UI group, pivot, merge, format or calculate any value after API
   response?
8. Which cases show zero, NULL, no data, cancelled and unapproved records?

## Important source-side assumptions to validate first

These assumptions are especially likely to produce wrong answers if not checked:

- Historical sales value must use transaction amount, not current price times
  quantity.
- Inventory as-of date must not sum balance across dates.
- Header/detail joins must not multiply amounts or quantities.
- `ma_gd = 10` for replacement delivery must be confirmed against ERP UI.
- `tablename` and `leftjoin` from grid metadata may be aliases or incomplete.
- A label status, document status and approval status may be separate fields.
- Warehouse, lot, unit/company and user permission filters may be applied
  outside the visible grid configuration.

## What Machine B does not need

Machine B does not need the full AI-Stack source, SQL files, DB credentials,
model configuration or Open WebUI configuration. It only needs this catalog,
`HANDOFF.md`, access to ERP Web and the ability to transfer evidence back to
Machine A.
