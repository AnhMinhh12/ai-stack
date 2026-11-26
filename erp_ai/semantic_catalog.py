"""Canonical semantic catalog: contract invariants, 3SERP metadata linking, and join graph."""
from __future__ import annotations

import re
from typing import Any

from .system_dictionary import load_dictionary

# Canonical entity keys eligible for fanout-safe Aggregate-before-Join across facts.
CANONICAL_JOIN_ENTITIES: tuple[str, ...] = (
    "material",
    "product",
    "customer",
    "supplier",
    "partner",
    "warehouse",
    "target_warehouse",
    "machine",
    "line_group",
    "mold",
    "account",
    "employee_code",
    "work_order",
    "doc_no",
    "po_no",
    "pr_no",
    "so_no",
    "lot_no",
)

_PUBLIC_TABLE_RE = re.compile(r"\bpublic\.([a-z_][a-z0-9_]*)\b", re.I)
_BOILERPLATE_TABLES = frozenset({"userinfo", "sys_dmtt"})


def extract_sql_output_columns(sql: str) -> set[str]:
    """Extract top-level SELECT output column names/aliases from a curated subquery."""
    if not isinstance(sql, str):
        return set()
    match_sel = re.match(r"^\s*SELECT\s+(?:DISTINCT\s+)?", sql, re.I)
    if not match_sel:
        return set()
    idx = match_sel.end()
    depth = 0
    in_quote = False
    exprs: list[str] = []
    buf: list[str] = []
    length = len(sql)
    while idx < length:
        ch = sql[idx]
        if ch == "'":
            # Handle doubled single quotes '' inside SQL literals.
            if in_quote and idx + 1 < length and sql[idx + 1] == "'":
                buf.append("''")
                idx += 2
                continue
            in_quote = not in_quote
            buf.append(ch)
        elif not in_quote:
            if ch == "(":
                depth += 1
                buf.append(ch)
            elif ch == ")":
                depth = max(0, depth - 1)
                buf.append(ch)
            elif depth == 0 and sql[idx:idx + 4].upper() == "FROM" and (idx == 0 or sql[idx - 1].isspace()) and (idx + 4 == length or sql[idx + 4].isspace()):
                exprs.append("".join(buf).strip())
                break
            elif depth == 0 and ch == ",":
                exprs.append("".join(buf).strip())
                buf = []
            else:
                buf.append(ch)
        else:
            buf.append(ch)
        idx += 1
    out: set[str] = set()
    for expr in exprs:
        m_as = re.search(r"\bAS\s+([a-z_][a-z0-9_]*)\s*$", expr, re.I)
        if m_as:
            out.add(m_as.group(1))
        else:
            m_col = re.search(r"([a-z_][a-z0-9_]*)\s*$", expr, re.I)
            if m_col:
                out.add(m_col.group(1))
    return out


def extract_source_tables(sql: str, *, include_boilerplate: bool = False) -> list[str]:
    """Return distinct public.<table> names referenced by a contract's source_sql."""
    tables: list[str] = []
    seen: set[str] = set()
    for tbl in _PUBLIC_TABLE_RE.findall(sql or ""):
        low = tbl.lower()
        if not include_boilerplate and low in _BOILERPLATE_TABLES:
            continue
        if low not in seen:
            seen.add(low)
            tables.append(low)
    return tables


def validate_semantic_contracts(contracts: dict[str, Any]) -> list[str]:
    """Verify every contract's schema invariants against its source_sql and field links."""
    errors: list[str] = []
    if not isinstance(contracts, dict):
        return ["contracts_not_dict"]
    for cid, contract in contracts.items():
        if not isinstance(contract, dict):
            errors.append(f"{cid}: contract is not dict")
            continue
        if contract.get("status") != "approved":
            errors.append(f"{cid}: status is {contract.get('status')!r}, expected 'approved'")
        scope = contract.get("scope")
        if scope not in ("erp_user_view", "sales_orders_scoped_v1", "curated_scoped_subquery"):
            errors.append(f"{cid}: unsupported scope {scope!r}")
        dims = contract.get("dimensions") or {}
        metrics = contract.get("metrics") or {}
        filters = contract.get("filters") or {}
        if not dims or not metrics:
            errors.append(f"{cid}: missing dimensions or metrics")
        if scope == "curated_scoped_subquery":
            sql = contract.get("source_sql") or ""
            if "userinfo" not in sql.lower() or "%s" not in sql:
                errors.append(f"{cid}: curated_scoped_subquery missing userinfo RLS binding")
            out_cols = extract_sql_output_columns(sql)
            if not out_cols:
                errors.append(f"{cid}: failed to parse SELECT columns from source_sql")
            else:
                for d, col in dims.items():
                    if col not in out_cols:
                        errors.append(f"{cid}: dimension {d!r} -> column {col!r} missing from source_sql")
                for m, md in metrics.items():
                    col = (md or {}).get("column")
                    if not col or col not in out_cols:
                        errors.append(f"{cid}: metric {m!r} -> column {col!r} missing from source_sql")
                for f, fd in filters.items():
                    col = (fd or {}).get("column")
                    if not col or col not in out_cols:
                        errors.append(f"{cid}: filter {f!r} -> column {col!r} missing from source_sql")
        if contract.get("require_bounded_date", True):
            df = contract.get("date_field", "day")
            if df not in filters:
                errors.append(f"{cid}: date_field {df!r} missing from filters")
        for bdf in contract.get("bounded_date_fields") or ():
            if bdf not in filters:
                errors.append(f"{cid}: bounded_date_field {bdf!r} missing from filters")
        adf = contract.get("alternate_date_field")
        if adf and adf not in filters:
            errors.append(f"{cid}: alternate_date_field {adf!r} missing from filters")
        for fk, fv in (contract.get("alternate_filter_fields") or {}).items():
            if fk not in filters or fv not in filters:
                errors.append(f"{cid}: invalid alternate_filter_fields {fk!r} -> {fv!r}")
        for dm in contract.get("default_metrics") or ():
            if dm not in metrics:
                errors.append(f"{cid}: default_metric {dm!r} missing from metrics")
        for dd in contract.get("default_dimensions") or ():
            if dd not in dims:
                errors.append(f"{cid}: default_dimension {dd!r} missing from dimensions")
        for m, md in metrics.items():
            ud = (md or {}).get("unit_dimension")
            if ud and ud not in dims:
                errors.append(f"{cid}: metric {m!r} unit_dimension {ud!r} missing from dimensions")
    return errors


def build_3serp_table_catalog(dictionary: dict[str, Any] | None = None) -> dict[str, dict[str, list[str]]]:
    """Map PostgreSQL table names to real 3SERP UI report titles and grid column captions."""
    dic = dictionary if isinstance(dictionary, dict) else load_dictionary()
    grids = dic.get("grids") or {}
    reports = dic.get("reports") or {}

    grid_titles: dict[str, list[str]] = {}
    for rep in reports.values():
        if not isinstance(rep, dict):
            continue
        gid = (rep.get("gridid") or "").strip()
        title = (rep.get("title") or "").strip()
        if gid and title:
            grid_titles.setdefault(gid, [])
            if title not in grid_titles[gid]:
                grid_titles[gid].append(title)

    by_table: dict[str, dict[str, list[str]]] = {}
    for gid, grid in grids.items():
        if not isinstance(grid, dict):
            continue
        tables = [str(t).strip().lower() for t in (grid.get("tables") or ()) if str(t).strip()]
        captions: list[str] = []
        for col in grid.get("columns") or ():
            if isinstance(col, dict):
                cap = str(col.get("caption") or "").strip()
                if cap and cap not in captions:
                    captions.append(cap)
        titles = grid_titles.get(gid, [])
        for tbl in tables:
            bucket = by_table.setdefault(tbl, {"report_titles": [], "captions": []})
            for t in titles:
                if t not in bucket["report_titles"]:
                    bucket["report_titles"].append(t)
            for cap in captions:
                if cap not in bucket["captions"]:
                    bucket["captions"].append(cap)
    return by_table


def enrich_contract_from_dictionary(
    contract: dict[str, Any],
    table_catalog: dict[str, dict[str, list[str]]] | None = None,
) -> dict[str, list[str]]:
    """Collect 3SERP UI report titles and grid captions linked to a contract's tables."""
    catalog = table_catalog if table_catalog is not None else build_3serp_table_catalog()
    tables = extract_source_tables(contract.get("source_sql") or "")
    # Ignore generic shared lookup tables when collecting domain-specific UI titles/captions.
    domain_tables = [t for t in tables if t not in ("dmvt", "dmkh", "dmkho")] or tables
    report_titles: list[str] = []
    captions: list[str] = []
    for tbl in domain_tables:
        entry = catalog.get(tbl)
        if not entry:
            continue
        for title in entry.get("report_titles", ()):
            if title not in report_titles:
                report_titles.append(title)
        for cap in entry.get("captions", ()):
            if cap not in captions:
                captions.append(cap)
    return {
        "tables": tables,
        "report_titles": report_titles[:8],
        "captions": captions[:30],
    }


def build_join_graph(
    contracts: dict[str, Any],
    allowed: set[str] | None = None,
) -> dict[str, list[str]]:
    """Return mapping of approved contract pairs -> shared canonical entity join keys."""
    if not isinstance(contracts, dict):
        return {}
    ids = sorted(
        cid for cid, c in contracts.items()
        if (allowed is None or cid in allowed)
        and isinstance(c, dict)
        and c.get("status") == "approved"
    )
    edges: dict[str, list[str]] = {}
    join_set = set(CANONICAL_JOIN_ENTITIES)
    for i, left_id in enumerate(ids):
        left_dims = set((contracts[left_id].get("dimensions") or {}).keys()) & join_set
        if not left_dims:
            continue
        for right_id in ids[i + 1:]:
            right_dims = set((contracts[right_id].get("dimensions") or {}).keys()) & join_set
            shared = [k for k in CANONICAL_JOIN_ENTITIES if k in left_dims and k in right_dims]
            if shared:
                edges[f"{left_id}<->{right_id}"] = shared
    return edges


def find_shared_join_keys(
    left_contract: dict[str, Any],
    right_contract: dict[str, Any],
) -> list[str]:
    """Return canonical entity keys shared by two approved contracts."""
    if not isinstance(left_contract, dict) or not isinstance(right_contract, dict):
        return []
    left_dims = set((left_contract.get("dimensions") or {}).keys())
    right_dims = set((right_contract.get("dimensions") or {}).keys())
    return [k for k in CANONICAL_JOIN_ENTITIES if k in left_dims and k in right_dims]


def recommended_joins_for(
    dataset_ids: list[str],
    contracts: dict[str, Any],
    allowed: set[str] | None = None,
) -> list[dict[str, Any]]:
    """List approved join keys connecting pairs among candidate datasets."""
    joins: list[dict[str, Any]] = []
    clean_ids = [
        d for d in dataset_ids
        if isinstance(d, str)
        and d in contracts
        and (allowed is None or d in allowed)
        and isinstance(contracts[d], dict)
        and contracts[d].get("status") == "approved"
    ]
    for i, left_id in enumerate(clean_ids):
        for right_id in clean_ids[i + 1:]:
            keys = find_shared_join_keys(contracts[left_id], contracts[right_id])
            if keys:
                joins.append({
                    "left": left_id,
                    "right": right_id,
                    "join_keys": keys[:3],
                })
    return joins[:8]
