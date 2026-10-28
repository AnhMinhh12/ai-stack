# ERP live mapping - handoff and continuation guide

## Purpose

This directory was created during a **read-only** investigation of the ERP at
`http://10.0.6.2:1004/Solution/ERP/`.

The goal is to build an evidence-based map that lets an ERP assistant answer
business questions correctly. The desired chain for every field is:

```text
ERP screen and visible column
  -> data API field and request parameters
  -> database table/view/function and expression
  -> joins, filters, document status, time basis, unit, and formula
```

The files here are a useful first-stage inventory. They do **not** yet prove
the complete chain above and must not be treated as a verified ERP data model.

## Safety and access rules

- Use a dedicated ERP account with read-only permission whenever possible.
- Do not click Save, Approve, Delete, Post, Import, Export-to-write, or any
  action whose effect is unknown.
- Do not call a function, stored procedure, or API until it has been checked
  that it is read-only. A report function can create temp/work tables or make
  other changes.
- Do not store passwords, authentication tokens, or cookies in this directory.
  `session_info.json` is a transient session artifact from the original run;
  do not commit, copy, or reuse it after the session is expired/revoked.
- Do not place this directory in Git while it contains session data or raw
  responses containing ERP business data. Redact and retain only the evidence
  needed for review.

## What was verified live

The original investigation was run from a machine that could reach the ERP.
It logged in, fetched the ERP menu tree, and called the authenticated
`InitGridMenu` configuration endpoint for accessible screen states.

| Item | Evidence | Result |
|---|---|---:|
| ERP menu records | `menu_tree_raw.json` | 337 |
| Executable leaf screens | `menu_tree_raw.json` | 171 |
| Screen states with returned column configuration | `extracted_columns_live.csv` | 136 |
| Extracted column records | `extracted_columns_live.csv` | 1,703 |
| Distinct declared source objects | `extracted_columns_live.csv` | 83 |

For every row in `extracted_columns_live.csv`, `VERIFIED_LIVE` means only:

> The authenticated ERP configuration API returned this field's grid metadata.

It does **not** mean the source object, field, join, formula, or displayed
business result has been verified against the database or browser UI.

## Current gaps

The following counts come from `extracted_columns_live.csv` and are the reason
this directory is not a completed DB mapping:

| Gap | Count | Meaning |
|---|---:|---|
| Leaf screens without extracted column configuration | at least 35 | A screen may have failed, use another UI mechanism, or be a special page/dashboard. Record the actual reason per screen. |
| Columns whose source object is `UNVERIFIED` | 363 | The configuration response did not identify a source table/view. |
| Columns without a captured join/key | 1,590 | A missing join is not evidence that no join exists. |
| Columns without a captured unit/formula | 1,086 | Display style alone is not a business formula. |
| DB catalog and object definitions | no artifact | Tables, views, functions, procedures, columns, keys, and definitions have not been collected. |
| Live data response per screen | no retained coverage artifact | The configuration endpoint is not the same as the data endpoint. |
| UI/API/DB sample reconciliation | no artifact | Grouping, totals, pagination, filters, and business rules remain unproven. |

## Audit of the artifacts added on 27 October 2026

The following files were added after the initial live extraction:

- `coverage/screens.csv` — 171 rows, one for each leaf menu screen.
- `mapping/field-map.csv` — 1,712 normalized mapping rows.
- `evidence/api/SO1Overview/request_schema.json` and `ui_spec.json` — a
  proposed SO1 data-request/UI specification.
- `tools/erp_readonly_tools.ps1` — a reusable discovery helper.
- `.gitignore` — excludes local session and scratch artifacts.

They are useful organization and continuation artifacts. Their evidence must be
interpreted carefully:

| Claim in the added artifact | What is currently proved | What still must be proved |
|---|---|---|
| `CONFIG_FOUND` for 121 screens | Each state has at least one column record in `extracted_columns_live.csv`. | Capture the request, HTTP response/status, and browser behavior for the actual screen. |
| `NO_GRID_CONFIG` for 11 screens | No extracted column row exists for the state. | Do not assume HTTP 200 or an empty grid response: the original extractor catches errors and does not retain error/status logs. Re-run and retain the result. |
| `SPECIAL_PAGE` for 24 screens | The menu URL is empty or `#`. | Open the route/menu item and establish whether it is a parent, redirect, modal, report or another data source. |
| 1,325 `UI_CONFIG_LIVE` fields | Authenticated grid metadata supplied a non-empty `tablename` value. | A `tablename` value is not a confirmed physical object or complete query. Verify object type, definition, fields and joins in DB. |
| 10 `UI_RENDERED_LIVE` SO1 fields | A JSON UI specification records the intended visible fields. | Retain browser screenshots/HAR and a sanitized actual API response. The current JSON alone does not independently prove the displayed values, 579,110 total, or source mappings. |
| `db_object`, `db_expression`, `join_key` in `field-map.csv` | Values are copied from configuration metadata or manually entered for SO1. | Validate them with DB catalog/object definitions and reference queries. |

The current normalized mapping has 1,325 `UI_CONFIG_LIVE` rows, 362
`UNVERIFIED` rows, 15 `MENU_LIVE` dashboard rows, and 10 claimed SO1 UI rows.
Among the `UI_CONFIG_LIVE` rows, 1,227 have an empty `join_key`; this is a
missing proof, not a statement that the field needs no join. There is currently
no `DB_VERIFIED` or `RECONCILED` row.

`tools/erp_readonly_tools.ps1` uses GET for the grid discovery call and POST
only for authentication. It is a helper, not proof that every future endpoint
is read-only. Inspect and allowlist every endpoint before using it. The
`.gitignore` excludes `session_info.json` and scratch files, but it does not
remove the existing sensitive file; revoke/expire the session and remove it
from any shared copy before handoff.

## Directory contents

| File or group | Description | Evidence level |
|---|---|---|
| `menu_tree_raw.json` | Raw authenticated ERP menu response. | Live menu inventory |
| `extracted_columns_live.csv` | Normalized grid metadata: UI label, API field, declared source object, declared lookup/join text, style and visibility. | Live configuration metadata |
| `lookup_init_grid.json` | Raw configuration response for a sample grid. | Live configuration metadata |
| `bundle_*.js`, `appjs.js`, `angularApp.js` | ERP JavaScript bundles downloaded for endpoint/controller discovery. | Implementation clues; not DB proof |
| `SO1Overview.html`, `scratch_index.html`, `scratch_login.html` | Downloaded HTML shells. | UI implementation clues |
| `scratch_*.ps1` | One-off PowerShell discovery scripts. Read and sanitize before reuse. | Reproducibility aids; not an audited toolset |
| `session_info.json` | Transient authenticated session data. | Sensitive; do not commit or reuse |
| `docs/evidence/ERP-MAPPING-20261027/` | Earlier repository-derived mapping template copied into this work area. | Historical/template only |

## Important fields in the column inventory

`extracted_columns_live.csv` has one row per configured grid field:

| Column | Meaning | Do not assume |
|---|---|---|
| `screen_state`, `screen_url` | ERP route/state supplied by the menu/configuration. | The state always has a one-to-one screen or data query. |
| `ui_label` | Field caption from the grid configuration. | It is the actual visible browser label in every language/layout. |
| `api_field` | Name returned by the grid configuration. | It is a physical DB column. |
| `api_endpoint` | Configuration endpoint used to discover this grid. | It returns business data. |
| `source_object` | `tablename` supplied by configuration, when present. | It is a table rather than a view/alias, or that it is the complete source. |
| `source_expression` | `field_root` or the configured field name. | It is SQL or a complete computation. |
| `join_or_key` | `leftjoin` metadata, when present. | A blank value means no join is used. |
| `filter_or_status` | Visibility/search metadata. | It lists document-status, company, date, or permission filters. |
| `unit_or_formula` | Grid aggregator/style. | It is a business definition or validated unit. |

## Repeatable continuation workflow

### 1. Preserve an access baseline

On the machine that can reach ERP, record without exposing credentials:

```powershell
Test-NetConnection 10.0.6.2 -Port 1004
```

Record the account role, company/unit, language, and time of the survey. These
affect menu visibility and data returned by APIs.

### 2. Turn the menu inventory into a coverage register

Create `coverage/screens.csv` with one row for every leaf screen. Include:

```text
menu_id,module,screen_state,screen_url,screen_name,screen_type,
config_status,config_http_status,data_endpoint,data_status,
ui_capture_status,db_mapping_status,notes
```

Do not silently skip failed screens. Classify each as one of:

- `CONFIG_FOUND`
- `NO_GRID_CONFIG`
- `AUTH_OR_PERMISSION_DENIED`
- `HTTP_ERROR`
- `TIMEOUT`
- `SPECIAL_PAGE`
- `GRAFANA_EMBED`
- `NEEDS_MANUAL_UI_REVIEW`

For the existing `coverage/screens.csv`, repeat the configuration call for all
171 screens and populate `config_http_status` from the observed response, not
from inference. Store a redacted evidence record for every non-200 response,
timeout or empty response. This resolves the current 11 `NO_GRID_CONFIG` and
confirms the 24 `SPECIAL_PAGE` classifications.

### 3. Capture each screen's real data request

Open each screen in a browser using the same account. In Network tools, capture
the read request that populates the grid/report and record:

- HTTP method and endpoint;
- request parameters/body, redacted of tokens and personal/business data;
- response schema and paging fields;
- default search/filter expression;
- company/unit, date range, document status, warehouse, and user-scope filters;
- whether totals are supplied by the server or calculated by the browser.

Save redacted request/response schemas under `evidence/api/<screen_state>/`.
Use `DATA_API_LIVE` only after this is captured.

### 4. Capture browser behavior

For every important screen, take a reproducible UI record containing:

- visible columns and their display order;
- hidden columns and user-configurable columns;
- grouped rows, subtotals, grand total, pivoting, and merged cells;
- formatter rules for dates, amounts, quantities, status labels and null/zero;
- page size and whether a total covers all records or only the current page;
- the exact filters and a timestamp.

Use `UI_RENDERED_LIVE` only when this has been checked in the browser.

### 5. Map the database using a read-only DB account

Acquire a DB connection with SELECT and metadata/definition permissions only.
Inventory tables, views, functions, procedures, columns, indexes, foreign keys
and object definitions. The exact catalog query depends on the DB engine.

For each field, prove one of:

- direct physical mapping: `schema.table.column`;
- view mapping: view definition and its upstream source;
- computed mapping: expression and all input fields;
- lookup mapping: lookup table, key and null behavior;
- API-only/derived mapping: clearly mark that it cannot yet be traced to DB.

Never infer a relation simply because two columns have the same name. Record the
actual join cardinality and key. In particular, guard against multiplying
quantities or amounts when joining header, detail, allocation, lot, warehouse,
or approval data.

Save the result in `mapping/field-map.csv` with at least:

```text
screen_state,ui_label,api_endpoint,api_field,db_object,db_expression,
join_key,join_cardinality,filters,status_rule,time_basis,unit,formula,
evidence_level,evidence_path,verified_at,verified_by,notes
```

Use `DB_VERIFIED` only when the definition or a read-only reference query
supports the mapping.

### 6. Reconcile data before publishing a metric

Choose at least three examples per screen, including a difficult case such as a
cancelled document, missing value, multiple lots/warehouses, or grouped rows.
For each example compare:

```text
same account + same company/unit + same filters + same time cutoff
browser UI == API response == independent read-only DB query
```

Record differences. A query that returns a plausible total is insufficient if
it has a different document status, time basis, permissions, pagination scope,
or aggregation level.

### 7. Treat dashboards separately

Grafana-embedded screens are not covered by ERP grid metadata. Inventory the
dashboard URL, panel IDs, variables, datasource, panel query, time range and
transformations. Verify the panel result against its datasource before treating
it as a business metric.

## Work register: required deliverables and acceptance gates

Complete the work below in order. Do not mark an item complete merely because a
script ran; attach the stated evidence.

| ID | Work | Required deliverable | Acceptance gate |
|---|---|---|---|
| A1 | Secure the work area | Revoke/expire the old ERP session; remove `session_info.json` from any copied/shared artifact; confirm `.gitignore` is retained. | No credential, token, cookie, raw business record or password appears in files intended for sharing. |
| A2 | Reproduce menu baseline | `evidence/menu/menu-tree-redacted.json` and `coverage/screens.csv` with survey time, role, unit and language. | Exactly one coverage row for each accessible leaf menu item; menu count and leaf count reconcile to the raw menu. |
| A3 | Verify grid-config coverage | `evidence/config/<screen_state>.json` or a redacted failure record for every screen. | Every row has an observed `config_http_status`; no inferred 200 responses; empty grid, error, timeout and access denial are distinguishable. |
| A4 | Classify non-grid screens | A register for dashboards, special pages, redirects, modals and parents. | The 15 Grafana and 24 special-page rows have a real route/behavior description and next data source. |
| A5 | Capture actual data APIs | Redacted request/response schema per priority screen in `evidence/api/<screen_state>/`. | The endpoint, method, parameters, paging, total field, default filters and response fields come from a saved live capture. |
| A6 | Validate SO1 evidence | Browser screenshot/HAR, sanitized `GetData` response schema, applied filters, timestamp and page count for SO1. | All 10 visible SO1 fields and the reported total are reproducible from the saved capture; otherwise downgrade their evidence level. |
| A7 | Inspect DB catalog read-only | `evidence/db/catalog/` containing DB engine/version, tables, views, functions, procedures, columns, indexes and keys; object definitions where permitted. | A dedicated read-only account was used and every catalog query is retained/redacted. |
| A8 | Map fields to DB | Update `mapping/field-map.csv` with object type, exact expression, join key/cardinality, filters, status rule, time basis, unit and formula. | A row is `DB_VERIFIED` only when linked to catalog/definition/reference-query evidence. Keep unknowns as `UNVERIFIED`. |
| A9 | Reconcile priority business flows | `evidence/reconciliation/<screen_state>/<case>.md` for at least three cases per priority screen. | Same account, unit, filter and cutoff yield matching UI, API and independent DB result; explain every difference. |
| A10 | Validate dashboards | Panel inventory and datasource/query evidence for each dashboard. | A dashboard metric is not promoted beyond `MENU_LIVE` until panel query, variables and datasource are verified. |
| A11 | Publish supported scope | `coverage/summary.md` and a machine-readable mapping export. | Every accessible screen is classified; every business metric used by the AI is `RECONCILED`; unsupported or inaccessible scope is explicit. |

### Priority order for reconciliation

Start with flows that will drive ERP assistant answers and that are prone to
wrong aggregation:

1. Inventory by item, warehouse, lot and as-of date.
2. Sales quotation, order, delivery, invoice, return and compensation delivery.
3. Purchasing request, order, receipt, invoice and supplier price.
4. Production order, BOM, material issue/return, output, rejection and downtime.
5. Quality, lots, labels, inspection status and expiry.
6. Grafana OEE and production dashboards.

For each flow, explicitly test cancelled/unapproved documents, zero vs no row,
multiple warehouses/lots, document header-to-detail joins, current price versus
historical transaction value, paging and group/grand totals.

## Evidence levels

Use these labels consistently:

| Label | Minimum proof |
|---|---|
| `MENU_LIVE` | Menu is returned for the account. |
| `UI_CONFIG_LIVE` | Authenticated configuration endpoint returns the field metadata. |
| `DATA_API_LIVE` | Actual data endpoint/request and response schema captured. |
| `UI_RENDERED_LIVE` | Field and transformation verified in browser. |
| `DB_VERIFIED` | Read-only DB catalog/definition and reference query identify the source and logic. |
| `RECONCILED` | UI, API and DB match for documented samples. |
| `UNVERIFIED` | No sufficient evidence yet. |

Do not replace `UNVERIFIED` with `DB_VERIFIED` based on a field name, a UI
caption, or a `tablename` value alone.

## Completion criteria

The mapping is complete only when all accessible screens have a coverage row,
every supported business metric is `RECONCILED`, and every unresolved item is
explicitly recorded as out-of-scope, inaccessible, API-only, or unknown.

Before using the mapping for AI answers, test compound questions that preserve
context across sales, inventory, lots, warehouses, quality status and dates.
The answer must show its data period and material filters, and must distinguish
zero, no data, null, permission denial and query failure.

The work is **not complete** until A1 through A11 are accepted. In particular,
do not use `UI_CONFIG_LIVE` as permission to answer a financial, inventory,
production or quality question; use only metrics that have reached
`RECONCILED` for the relevant account scope and period.

## Recommended cleanup after handoff

1. Expire/revoke the original ERP session.
2. Move or securely delete `session_info.json` and any raw response containing
   a token before sharing this directory.
3. Replace the one-off `scratch_*.ps1` files with one reviewed read-only tool
   that loads credentials from a secure local mechanism and writes redacted
   artifacts.
4. Add a `.gitignore` entry for session files, raw responses and local secrets
   before putting future work under version control.
