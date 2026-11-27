"""Declarative Entity-Fact semantic model compiler (Nấc 3 Composable Semantic Layer).

Allows defining shared ERP/MES entities (`customer`, `supplier`, `material`,
`warehouse`, `status`, `employee`, `machine_line`, `mold`, `account`, etc.)
and RLS policies once, and compiling modular Fact definitions (including
subqueries, multi-branch UNION ALL sources, and auxiliary joins) into governed
`semantic_contracts` for `semantic_query.py`.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


def _build_rls_clause(rls: dict[str, Any]) -> tuple[str, list[str]]:
    """Compile a declarative RLS rule into a parameterized userinfo join + predicates."""
    mode = (rls or {}).get("mode", "open_user")
    if mode == "open_user":
        return "CROSS JOIN public.userinfo u", ["u.user_id = %s"]
    join_sql = "JOIN public.userinfo u ON u.user_id = %s"
    branch_expr = rls.get("branch_expr", "h.ma_dvcs")
    if mode == "branch_required":
        return join_sql, [
            f"(coalesce(u.is_super, 0) = 1 OR {branch_expr} = ANY(string_to_array(coalesce(u.ds_branchs, ''), ',')))"
        ]
    if mode == "branch_optional":
        default_branch = rls.get("default_branch")
        b_cmp = f"coalesce({branch_expr}, '{default_branch}')" if default_branch else branch_expr
        return join_sql, [
            f"(coalesce(u.is_super, 0) = 1 OR coalesce(u.ds_branchs, '') = '' OR {b_cmp} = ANY(string_to_array(coalesce(u.ds_branchs, ''), ',')))"
        ]
    if mode == "stock_optional":
        stock_expr = rls.get("stock_expr", "c.ma_kho")
        return join_sql, [
            f"(coalesce(u.is_super, 0) = 1 OR coalesce(u.ds_stocks, '') = '' OR {stock_expr} = ANY(string_to_array(coalesce(u.ds_stocks, ''), ',')))"
        ]
    if mode == "stock_optional_nullable":
        stock_expr = rls.get("stock_expr", "s.ma_kho")
        return join_sql, [
            f"(coalesce(u.is_super, 0) = 1 OR coalesce(u.ds_stocks, '') = '' OR coalesce({stock_expr}, '') = '' OR {stock_expr} = ANY(string_to_array(coalesce(u.ds_stocks, ''), ',')))"
        ]
    if mode == "branch_stock":
        stock_expr = rls.get("stock_expr", "d.ma_kho")
        return join_sql, [
            f"(coalesce(u.is_super, 0) = 1 OR ({branch_expr} = ANY(string_to_array(coalesce(u.ds_branchs, ''), ',')) AND (coalesce(u.ds_stocks, '') = '' OR {stock_expr} = ANY(string_to_array(coalesce(u.ds_stocks, ''), ',')))))"
        ]
    if mode == "branch_stock_nullable":
        stock_expr = rls.get("stock_expr", "coalesce(d.ma_kho, h.ma_kho)")
        return join_sql, [
            f"(coalesce(u.is_super, 0) = 1 OR ({branch_expr} = ANY(string_to_array(coalesce(u.ds_branchs, ''), ',')) AND (coalesce(u.ds_stocks, '') = '' OR coalesce({stock_expr}, '') = '' OR {stock_expr} = ANY(string_to_array(coalesce(u.ds_stocks, ''), ',')))))"
        ]
    if mode == "custom":
        clause = str(rls.get("clause") or "").strip()
        if not clause:
            raise ValueError("Custom RLS mode requires non-empty 'clause'")
        return join_sql, [clause]
    raise ValueError(f"Unsupported RLS mode: {mode!r}")


def _compile_subquery(subq: dict[str, Any]) -> str:
    """Compile a declarative base subquery (single query or UNION ALL of structured branches)."""
    alias = str(subq.get("alias") or "").strip()
    if "sql" in subq and isinstance(subq["sql"], str):
        inner = subq["sql"].strip()
        return f"({inner}) {alias}".strip() if alias else f"({inner})"
    sources = subq.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("base_subquery requires 'sql' or non-empty 'sources'")
    leg_sqls: list[str] = []
    for branch in sources:
        sel = branch.get("select")
        if isinstance(sel, dict):
            sel_str = ", ".join(f"{expr} AS {col}" for col, expr in sel.items())
        elif isinstance(sel, list):
            sel_str = ", ".join(str(x) for x in sel)
        else:
            raise ValueError("subquery branch 'select' must be dict or list")
        sql = f"SELECT {sel_str} FROM {branch['from']}"
        for j in branch.get("joins") or ():
            sql += f" {j}"
        where = branch.get("where") or ()
        if where:
            sql += " WHERE " + " AND ".join(where)
        leg_sqls.append(sql)
    joined = " UNION ALL ".join(leg_sqls)
    return f"({joined}) {alias}".strip() if alias else f"({joined})"


def _compile_single_select(
    fact_id: str,
    leg: dict[str, Any],
    entities: dict[str, Any],
) -> tuple[str, dict[str, str], dict[str, dict[str, Any]]]:
    """Compile one SELECT leg (shared by single-FROM facts and multi-leg UNION facts)."""
    select_parts: list[str] = []
    join_parts: list[str] = []
    dims: dict[str, str] = {}
    filters: dict[str, dict[str, Any]] = {}

    for binding in leg.get("entity_bindings") or ():
        ent_name = binding["entity"]
        ent = entities.get(ent_name)
        if not isinstance(ent, dict):
            raise ValueError(f"Fact {fact_id!r} references unknown entity {ent_name!r}")
        alias = binding.get("alias") or ent["default_alias"]
        key_expr = binding["key_expr"]
        join_kind = binding.get("join_kind", "LEFT JOIN")

        if ent_name == "status":
            ma_ct = binding["ma_ct"]
            status_mode = binding.get("status_mode", "left_join")
            status_alias = binding.get("output_col", "status_name")
            ma_ct_expr = ma_ct if binding.get("ma_ct_is_expr") else f"'{ma_ct}'"
            if status_mode == "scalar_subquery":
                select_parts.append(
                    f"coalesce((SELECT {alias}.statusname FROM {ent['table']} {alias} "
                    f"WHERE {alias}.ma_ct = {ma_ct_expr} AND {alias}.status::text = {key_expr}::text LIMIT 1), {key_expr}::text, '') AS {status_alias}"
                )
            else:
                join_parts.append(
                    f"{join_kind} {ent['table']} {alias} ON {alias}.ma_ct = {ma_ct_expr} AND {alias}.status::text = {key_expr}::text"
                )
                if binding.get("include_status_col"):
                    select_parts.append(f"{key_expr}::text AS status")
                select_parts.append(f"coalesce({alias}.statusname, {key_expr}::text, '') AS {status_alias}")
            if binding.get("expose_name_dim", True):
                dims[status_alias] = status_alias
            if binding.get("expose_name_filter", True):
                filters[status_alias] = {"column": status_alias, "type": "text", "ops": ["eq", "contains"]}
            continue

        code_col = binding.get("code_col") or ent["code_output"]
        name_col = binding.get("name_col") or ent.get("name_output", "")
        if binding.get("expose_code_select", True):
            code_select_expr = f"coalesce({key_expr}, '')" if binding.get("coalesce_code") else key_expr
            select_parts.append(f"{code_select_expr} AS {code_col}")
        if binding.get("expose_code_dim", True):
            dims[code_col] = code_col
        if binding.get("expose_code_filter", True):
            code_fdef: dict[str, Any] = {
                "column": code_col,
                "type": "text",
                "ops": list(binding.get("code_ops") or ent.get("code_ops") or ["eq"]),
            }
            if binding.get("parent_prefix_fallback"):
                code_fdef["parent_prefix_fallback"] = True
            filters[code_col] = code_fdef

        join_key_expr = binding.get("join_key_expr") or key_expr
        table_join_col = ent["table_key"]
        if binding.get("join_mode") == "scalar_subquery" and name_col:
            fb = binding.get("fallback_name_expr")
            fb_part = f", {fb}, ''" if fb else ", ''"
            select_parts.append(
                f"coalesce((SELECT {alias}.{ent['table_name_col']} FROM {ent['table']} {alias} "
                f"WHERE {alias}.{table_join_col} = {join_key_expr} LIMIT 1){fb_part}) AS {name_col}"
            )
        else:
            on_sql = binding.get("on") or f"{alias}.{table_join_col} = {join_key_expr}"
            join_parts.append(f"{join_kind} {ent['table']} {alias} ON {on_sql}")
            if name_col and ent.get("table_name_col"):
                fb = binding.get("fallback_name_expr")
                if fb:
                    if binding.get("prefer_nonempty_entity_name"):
                        name_expr = f"coalesce(nullif({alias}.{ent['table_name_col']}, ''), {fb}, '')"
                    else:
                        name_expr = f"coalesce({alias}.{ent['table_name_col']}, {fb}, '')"
                else:
                    name_expr = f"coalesce({alias}.{ent['table_name_col']}, '')"
                select_parts.append(f"{name_expr} AS {name_col}")
        if name_col:
            if binding.get("expose_name_dim", True):
                dims[name_col] = name_col
            if binding.get("expose_name_filter", True):
                filters[name_col] = {"column": name_col, "type": "text", "ops": ["eq", "contains"]}
        for extra_alias, extra_sql in (binding.get("extra_select") or {}).items():
            select_parts.append(f"{extra_sql} AS {extra_alias}")
            if extra_alias not in (binding.get("non_dim_select") or ()):
                dims[extra_alias] = extra_alias
            if binding.get("extra_filters") and extra_alias in binding["extra_filters"]:
                filters[extra_alias] = copy.deepcopy(binding["extra_filters"][extra_alias])

    raw_base_select = leg.get("base_select")
    if isinstance(raw_base_select, dict):
        for col_alias, sql_expr in raw_base_select.items():
            select_parts.append(f"{sql_expr} AS {col_alias}")
    elif isinstance(raw_base_select, list):
        for expr in raw_base_select:
            select_parts.append(str(expr))

    for ej in leg.get("extra_joins") or ():
        join_parts.append(str(ej))

    if "base_subquery" in leg and isinstance(leg["base_subquery"], dict):
        from_sql = _compile_subquery(leg["base_subquery"])
    elif "base_from" in leg:
        from_sql = str(leg["base_from"])
    else:
        raise ValueError(f"Fact {fact_id!r} requires 'base_from' or 'base_subquery'")

    rls_join, rls_where = _build_rls_clause(leg.get("rls") or {"mode": "open_user"})
    join_parts.append(rls_join)
    where_parts = list(leg.get("base_where") or ()) + rls_where

    sql = f"SELECT {', '.join(select_parts)} FROM {from_sql}"
    if join_parts:
        sql += " " + " ".join(join_parts)
    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)
    return sql, dims, filters


def compile_fact_contract(
    fact_id: str,
    fact: dict[str, Any],
    entities: dict[str, Any],
) -> dict[str, Any]:
    """Compile a modular Fact + Shared Entities definition into an approved semantic contract."""
    if not isinstance(fact, dict):
        raise ValueError(f"Fact {fact_id!r} must be a dict")

    dims: dict[str, str] = {}
    filters: dict[str, dict[str, Any]] = {}

    if isinstance(fact.get("union_legs"), list) and fact["union_legs"]:
        leg_sqls: list[str] = []
        for idx, sub_leg in enumerate(fact["union_legs"]):
            leg_sql, leg_dims, leg_filters = _compile_single_select(f"{fact_id}#leg{idx}", sub_leg, entities)
            leg_sqls.append(leg_sql)
            dims.update(leg_dims)
            filters.update(leg_filters)
        source_sql = " UNION ALL ".join(leg_sqls)
        default_upc = len(leg_sqls)
    else:
        source_sql, dims, filters = _compile_single_select(fact_id, fact, entities)
        default_upc = 1

    for dim_name, col_name in (fact.get("own_dimensions") or {}).items():
        dims[dim_name] = col_name

    # Preserve canonical dimension ordering if specified by fact.
    if fact.get("dimension_order"):
        ordered_dims: dict[str, str] = {}
        for d in fact["dimension_order"]:
            if d in dims:
                ordered_dims[d] = dims[d]
        for d, v in dims.items():
            if d not in ordered_dims:
                ordered_dims[d] = v
        dims = ordered_dims

    for fname, fdef in (fact.get("own_filters") or {}).items():
        filters[fname] = copy.deepcopy(fdef)

    if fact.get("filter_order"):
        ordered_filters: dict[str, dict[str, Any]] = {}
        for f in fact["filter_order"]:
            if f in filters:
                ordered_filters[f] = filters[f]
        for f, v in filters.items():
            if f not in ordered_filters:
                ordered_filters[f] = v
        filters = ordered_filters

    contract: dict[str, Any] = {
        "status": fact.get("status", "approved"),
        "scope": "curated_scoped_subquery",
        "version": fact.get("version", "2026-11-27-v1"),
        "title": fact["title"],
    }
    for opt_key in (
        "notes", "date_field", "bounded_date_fields", "alternate_date_field",
        "alternate_date_label", "alternate_filter_fields", "default_metrics",
        "default_dimensions", "require_bounded_date", "max_date_span_days",
        "field_labels", "value_aliases", "cues", "secondary_cues",
    ):
        if opt_key in fact and fact[opt_key] is not None:
            contract[opt_key] = copy.deepcopy(fact[opt_key])
    if "date_field" not in fact and fact.get("require_bounded_date", True):
        contract["date_field"] = "day"
    contract.setdefault("require_bounded_date", True)
    contract["user_param_count"] = int(fact.get("user_param_count", default_upc))
    contract["source_sql"] = source_sql
    contract["dimensions"] = dims
    contract["metrics"] = copy.deepcopy(fact["measures"])
    contract["filters"] = filters
    return contract


def compile_semantic_model(model_cfg: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, str]]]:
    """Compile all Facts and field_catalog in a semantic model definition."""
    entities = model_cfg.get("entities") or {}
    facts = model_cfg.get("facts") or {}
    field_catalog = copy.deepcopy(model_cfg.get("field_catalog") or {})
    compiled: dict[str, dict[str, Any]] = {}
    for fact_id, fact_def in facts.items():
        compiled[fact_id] = compile_fact_contract(fact_id, fact_def, entities)
    return compiled, field_catalog


def load_erp_config(root: str | Path) -> dict[str, Any]:
    """Load config/erp-agent.json and overlay compiled facts/field_catalog from config/erp-semantic-model.json if present."""
    root_path = Path(root).resolve()
    cfg_path = root_path / "config/erp-agent.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    model_path = root_path / "config/erp-semantic-model.json"
    if model_path.is_file():
        model_cfg = json.loads(model_path.read_text(encoding="utf-8"))
        compiled_facts, field_catalog = compile_semantic_model(model_cfg)
        cfg.setdefault("semantic_contracts", {}).update(compiled_facts)
        if field_catalog:
            merged_catalog = dict(cfg.get("field_catalog") or {})
            merged_catalog.update(field_catalog)
            cfg["field_catalog"] = merged_catalog
    return cfg


def sync_model_to_agent_config(root: str | Path) -> tuple[int, int]:
    """Compile config/erp-semantic-model.json into config/erp-agent.json cleanly."""
    root_path = Path(root).resolve()
    model_path = root_path / "config/erp-semantic-model.json"
    agent_path = root_path / "config/erp-agent.json"
    model_cfg = json.loads(model_path.read_text(encoding="utf-8"))
    agent_cfg = json.loads(agent_path.read_text(encoding="utf-8"))
    compiled_facts, field_catalog = compile_semantic_model(model_cfg)
    agent_cfg.setdefault("semantic_contracts", {}).update(compiled_facts)
    if field_catalog:
        agent_cfg["field_catalog"] = field_catalog
    agent_path.write_text(json.dumps(agent_cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(compiled_facts), len(field_catalog)
