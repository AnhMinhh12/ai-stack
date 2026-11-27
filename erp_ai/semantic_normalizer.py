"""Deterministic parser and structural normalizer for semantic query plans."""
from __future__ import annotations

import copy
import json
import re
from typing import Any

from .semantic_query import PlanError
from .semantic_retriever import normalize_text

PLAN_FIELDS = ("dataset", "dimensions", "metrics", "filters", "order_by", "limit")
_TOP_N = re.compile(r"\btop\s+(\d{1,3})\b", re.I)

# Universal "unfiltered / all" sentinel literals that models sometimes hallucinate into text filters.
_WILDCARD_FILTER_VALUES = frozenset({
    "*", "all", "any", "tat ca", "toan bo", "moi", "bat ky", "khong loc", "none", "null", "n/a",
})


def _is_wildcard_filter(value: Any, field_def: Any = None) -> bool:
    if isinstance(field_def, dict) and field_def.get("type") == "date":
        return False
    if value is None:
        return True
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if not stripped:
        return True
    return normalize_text(stripped) in _WILDCARD_FILTER_VALUES


def _decode_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    try:
        parsed = json.loads(text)
    except ValueError:
        start = text.find("{")
        if start == -1:
            raise PlanError("invalid_json") from None
        try:
            parsed, _ = json.JSONDecoder().raw_decode(text[start:])
        except ValueError:
            raise PlanError("invalid_json") from None
    if not isinstance(parsed, dict):
        raise PlanError("invalid_plan")
    return parsed


def _coerce_list_field(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return parsed
            except ValueError:
                pass
        return [part.strip() for part in stripped.split(",") if part.strip()]
    return value


def parse_plan_arguments(args: dict[str, Any]) -> dict[str, Any]:
    """Accept either legacy plan_json string/dict or direct structured arguments."""
    if not isinstance(args, dict):
        raise PlanError("invalid_plan")
    if "plan_json" in args and args["plan_json"] is not None:
        raw = args["plan_json"]
        if isinstance(raw, dict):
            return copy.deepcopy(raw)
        if isinstance(raw, str):
            return _decode_json_object(raw)
        raise PlanError("invalid_json")
    if "dataset" in args:
        plan: dict[str, Any] = {}
        for key in PLAN_FIELDS:
            if key not in args or args[key] is None:
                continue
            val = args[key]
            if key in ("dimensions", "metrics", "filters", "order_by") and isinstance(val, str):
                stripped = val.strip()
                if stripped.startswith(("[", "{")):
                    try:
                        val = json.loads(stripped)
                    except ValueError:
                        pass
            plan[key] = copy.deepcopy(val)
        return plan
    raise PlanError("invalid_json")


def _resolve_value_alias(value: Any, fdef: dict[str, Any]) -> Any:
    aliases = fdef.get("value_aliases")
    if not isinstance(aliases, dict) or not isinstance(value, (str, bool)):
        return value
    val_low = str(value).strip().lower()
    if val_low in aliases:
        return aliases[val_low]
    val_norm = normalize_text(str(value))
    if val_norm in aliases:
        return aliases[val_norm]
    return value


def _coerce_filters(filters: Any, filter_defs: dict[str, Any]) -> Any:
    if filters is None:
        return []
    op_aliases = {
        "from": "gte", "start": "gte", ">=": "gte",
        "to": "lte", "end": "lte", "<=": "lte",
        "=": "eq", "==": "eq", "equals": "eq",
        "like": "contains", "ilike": "contains", "substr": "contains",
    }
    if isinstance(filters, dict):
        converted = []
        for field, val in filters.items():
            fdef = filter_defs.get(field) if isinstance(filter_defs.get(field), dict) else {}
            if isinstance(val, dict):
                for raw_op, op_val in val.items():
                    if _is_wildcard_filter(op_val, fdef):
                        continue
                    op = op_aliases.get(str(raw_op).strip().lower(), str(raw_op).strip().lower())
                    converted.append({"field": field, "op": op, "value": _resolve_value_alias(op_val, fdef)})
            else:
                if _is_wildcard_filter(val, fdef):
                    continue
                allowed_ops = fdef.get("ops", [])
                use_contains = "contains" in allowed_ops and ("eq" not in allowed_ops or str(field).endswith("_name"))
                op = "contains" if use_contains else "eq"
                converted.append({"field": field, "op": op, "value": _resolve_value_alias(val, fdef)})
        return converted
    if isinstance(filters, list):
        out = []
        for item in filters:
            if not isinstance(item, dict):
                out.append(item)
                continue
            norm = dict(item)
            if "field" not in norm and "field_name" in norm:
                norm["field"] = norm.pop("field_name")
            if "op" not in norm and "operator" in norm:
                norm["op"] = norm.pop("operator")
            field = norm.get("field")
            fdef = filter_defs.get(field) if isinstance(field, str) and isinstance(filter_defs.get(field), dict) else None
            val = norm.get("value")
            if _is_wildcard_filter(val, fdef):
                continue
            if isinstance(norm.get("op"), str):
                raw_op = norm["op"].strip().lower()
                norm["op"] = op_aliases.get(raw_op, raw_op)
            op = norm.get("op")
            if op == "in":
                raw_vals = (
                    [p.strip() for p in val.split(",")] if isinstance(val, str)
                    else (list(val) if isinstance(val, (list, tuple)) else [])
                )
                cleaned_in = []
                for elem in raw_vals:
                    if _is_wildcard_filter(elem, fdef):
                        continue
                    resolved = _resolve_value_alias(str(elem).strip(), fdef or {})
                    if isinstance(resolved, str) and resolved and resolved not in cleaned_in:
                        cleaned_in.append(resolved)
                if not cleaned_in:
                    continue
                if len(cleaned_in) == 1:
                    norm["op"] = "eq"
                    norm["value"] = cleaned_in[0]
                else:
                    norm["value"] = cleaned_in[:50]
            elif fdef is not None:
                allowed_ops = fdef.get("ops", [])
                if op == "eq" and "contains" in allowed_ops and ("eq" not in allowed_ops or str(field).endswith("_name")):
                    norm["op"] = "contains"
                norm["value"] = _resolve_value_alias(norm.get("value"), fdef)
            out.append(norm)
        # Merge multiple eq filters on the same text field into a single 'in' filter.
        merged = []
        eq_buckets: dict[str, list[int]] = {}
        for item in out:
            if isinstance(item, dict) and item.get("op") == "eq" and isinstance(item.get("field"), str):
                fld = item["field"]
                fdef = filter_defs.get(fld) if isinstance(filter_defs.get(fld), dict) else {}
                if fdef.get("type", "text") == "text" and isinstance(item.get("value"), str):
                    eq_buckets.setdefault(fld, []).append(len(merged))
            merged.append(item)
        if any(len(idxs) > 1 for idxs in eq_buckets.values()):
            drop_indices = set()
            for fld, idxs in eq_buckets.items():
                if len(idxs) <= 1:
                    continue
                vals = []
                for idx in idxs:
                    v = merged[idx].get("value")
                    if isinstance(v, str) and v not in vals:
                        vals.append(v)
                if len(vals) > 1:
                    merged[idxs[0]] = {"field": fld, "op": "in", "value": vals[:50]}
                for idx in idxs[1:]:
                    drop_indices.add(idx)
            merged = [m for i, m in enumerate(merged) if i not in drop_indices]
        return merged
    return filters


def _coerce_order_by(order_by: Any) -> Any:
    if order_by is None:
        return []
    if isinstance(order_by, dict):
        order_by = [order_by]
    if isinstance(order_by, list):
        out = []
        for item in order_by:
            if not isinstance(item, dict):
                out.append(item)
                continue
            norm = dict(item)
            if "direction" not in norm:
                for alias in ("dir", "order", "sort"):
                    if alias in norm:
                        norm["direction"] = norm.pop(alias)
                        break
            if isinstance(norm.get("direction"), str):
                norm["direction"] = norm["direction"].strip().lower()
            out.append(norm)
        return out
    return order_by


def normalize_semantic_plan(
    plan: dict[str, Any],
    contracts: dict[str, Any],
    *,
    max_rows: int = 50,
    question: str = "",
) -> dict[str, Any]:
    """Fix mechanical model formatting issues without inventing business filters."""
    if not isinstance(plan, dict):
        raise PlanError("invalid_plan")
    out = copy.deepcopy(plan)
    dataset = out.get("dataset")
    contract = contracts.get(dataset) if isinstance(dataset, str) and isinstance(contracts, dict) else None
    approved = isinstance(contract, dict) and contract.get("status") == "approved"
    dim_defs = contract.get("dimensions", {}) if approved else {}
    metric_defs = contract.get("metrics", {}) if approved else {}
    filter_defs = contract.get("filters", {}) if approved else {}

    if "dimensions" in out:
        out["dimensions"] = _coerce_list_field(out["dimensions"])
    else:
        out["dimensions"] = []
    if "metrics" in out:
        out["metrics"] = _coerce_list_field(out["metrics"])
    else:
        out["metrics"] = []

    out["filters"] = _coerce_filters(out.get("filters"), filter_defs)
    out["order_by"] = _coerce_order_by(out.get("order_by"))

    raw_limit = out.get("limit")
    if isinstance(raw_limit, str) and raw_limit.strip().isdigit():
        out["limit"] = int(raw_limit.strip())
    elif raw_limit is None:
        out.pop("limit", None)

    if question and isinstance(out["filters"], list):
        top_match = _TOP_N.search(question)
        if top_match:
            top_n = top_match.group(1)
            explicit_code = re.search(rf"(?:mã|ma|lỗi|loi|code|số|so)\s*[:#=-]?\s*{re.escape(top_n)}\b", question, re.I)
            if not explicit_code:
                out["filters"] = [
                    f for f in out["filters"]
                    if not (
                        isinstance(f, dict)
                        and f.get("op") == "eq"
                        and str(f.get("value", "")).strip() == top_n
                        and str(f.get("field", "")) != "day"
                    )
                ]
                if "limit" not in out and top_n.isdigit():
                    out["limit"] = min(max_rows, max(1, int(top_n)))

    if out.get("limit") is None:
        out["limit"] = min(50, max_rows)
    if isinstance(out.get("limit"), int) and not isinstance(out["limit"], bool) and out["limit"] > max_rows:
        out["limit"] = max_rows

    if approved and isinstance(out["dimensions"], list) and isinstance(out["metrics"], list):
        # Recover metrics placed inside dimensions and dimensions placed inside metrics.
        cleaned_dims = []
        recovered_metrics = []
        for m in out["metrics"]:
            if isinstance(m, str) and m not in metric_defs and m in dim_defs:
                if m not in cleaned_dims:
                    cleaned_dims.append(m)
            elif m not in recovered_metrics:
                recovered_metrics.append(m)
        for dim in out["dimensions"]:
            if isinstance(dim, str) and dim not in dim_defs and dim in metric_defs:
                if dim not in recovered_metrics:
                    recovered_metrics.append(dim)
            elif dim not in cleaned_dims:
                cleaned_dims.append(dim)
        out["dimensions"] = cleaned_dims
        out["metrics"] = recovered_metrics

        if not out["metrics"] and metric_defs:
            default_metrics = contract.get("default_metrics")
            if isinstance(default_metrics, list) and default_metrics:
                out["metrics"] = [m for m in default_metrics if isinstance(m, str) and m in metric_defs]
            if not out["metrics"]:
                out["metrics"] = [next(iter(metric_defs))]

        # Auto-inject required unit_dimension if omitted by the model.
        eq_filtered = {
            f.get("field")
            for f in out["filters"]
            if isinstance(f, dict) and f.get("op") == "eq" and isinstance(f.get("field"), str)
        }
        default_dims = contract.get("default_dimensions")
        if isinstance(default_dims, list) and not out["dimensions"]:
            out["dimensions"] = [d for d in default_dims if isinstance(d, str) and d in dim_defs]
        required_unit_dims = []
        for metric_name in out["metrics"]:
            metric_def = metric_defs.get(metric_name)
            if not isinstance(metric_def, dict):
                continue
            unit_dim = metric_def.get("unit_dimension")
            if (
                unit_dim
                and unit_dim in dim_defs
                and unit_dim not in out["dimensions"]
                and unit_dim not in eq_filtered
            ):
                out["dimensions"].append(unit_dim)
            if unit_dim and unit_dim in dim_defs and unit_dim not in eq_filtered and unit_dim not in required_unit_dims:
                required_unit_dims.append(unit_dim)

        # Keep at most 10 dimensions (preserving unit, default, filtered, and ordered dims).
        if len(out["dimensions"]) > 10:
            filter_dims = [
                f.get("field") for f in out["filters"]
                if isinstance(f, dict) and isinstance(f.get("field"), str) and f.get("field") in dim_defs
            ]
            order_dims = [
                o.get("field") for o in (out["order_by"] if isinstance(out["order_by"], list) else ())
                if isinstance(o, dict) and isinstance(o.get("field"), str) and o.get("field") in dim_defs
            ]
            priority = [*required_unit_dims, *(default_dims if isinstance(default_dims, list) else ()), *filter_dims, *order_dims]
            kept = []
            for d in [*priority, *out["dimensions"]]:
                if isinstance(d, str) and d in out["dimensions"] and d not in kept:
                    kept.append(d)
                if len(kept) >= 10:
                    break
            out["dimensions"] = kept

        # Auto-fill deterministic order_by when grouping is requested without ordering.
        if out["dimensions"] and isinstance(out["order_by"], list) and not out["order_by"]:
            chosen_field = None
            for metric_name in out["metrics"]:
                mdef = metric_defs.get(metric_name)
                if isinstance(mdef, dict) and mdef.get("unit_dimension") == "currency" and "currency" not in eq_filtered:
                    continue
                chosen_field = metric_name
                break
            if chosen_field:
                out["order_by"] = [{"field": chosen_field, "direction": "desc"}]
            else:
                out["order_by"] = [{"field": out["dimensions"][0], "direction": "asc"}]
        elif isinstance(out["order_by"], list) and out["order_by"]:
            valid_order_fields = set(out["dimensions"]) | set(out["metrics"])
            seen_order_fields = set()
            filtered_order = []
            for item in out["order_by"]:
                if not isinstance(item, dict):
                    filtered_order.append(item)
                    continue
                fld = item.get("field")
                if fld in valid_order_fields and fld not in seen_order_fields:
                    seen_order_fields.add(fld)
                    filtered_order.append(item)
            out["order_by"] = filtered_order

    return out


def normalize_joined_plan(
    join_plan: dict[str, Any],
    contracts: dict[str, Any],
    *,
    max_rows: int = 50,
    question: str = "",
) -> dict[str, Any]:
    """Normalize 2 or 3 legs of a semantic join plan and ensure the join key is grouped."""
    if not isinstance(join_plan, dict):
        raise PlanError("invalid_plan")
    left_raw = join_plan.get("left")
    right_raw = join_plan.get("right")
    extra_raw = join_plan.get("extra_legs")
    join_on = join_plan.get("join_on")
    if not isinstance(left_raw, dict) or not isinstance(right_raw, dict) or not isinstance(join_on, str) or not join_on:
        raise PlanError("invalid_plan")
    if extra_raw is not None:
        if not isinstance(extra_raw, list) or len(extra_raw) > 1 or any(not isinstance(x, dict) for x in extra_raw):
            raise PlanError("invalid_plan")

    left_copy = copy.deepcopy(left_raw)
    right_copy = copy.deepcopy(right_raw)
    extra_copies = [copy.deepcopy(x) for x in (extra_raw or ())]
    for leg in (left_copy, right_copy, *extra_copies):
        dims = leg.get("dimensions")
        if dims is None:
            leg["dimensions"] = [join_on]
        elif isinstance(dims, list) and join_on not in dims:
            leg["dimensions"] = [join_on, *dims]

    left_norm = normalize_semantic_plan(left_copy, contracts, max_rows=max_rows, question=question)
    right_norm = normalize_semantic_plan(right_copy, contracts, max_rows=200, question="")
    extra_norms = [normalize_semantic_plan(leg, contracts, max_rows=200, question="") for leg in extra_copies]
    out: dict[str, Any] = {
        "left": left_norm,
        "right": right_norm,
        "join_on": join_on,
        "join_type": str(join_plan.get("join_type") or "left").strip().lower(),
    }
    if extra_norms:
        out["extra_legs"] = extra_norms
    if join_plan.get("order_by") is not None:
        out["order_by"] = _coerce_order_by(join_plan["order_by"])
    raw_limit = join_plan.get("limit")
    if isinstance(raw_limit, str) and raw_limit.strip().isdigit():
        raw_limit = int(raw_limit.strip())
    if isinstance(raw_limit, int) and not isinstance(raw_limit, bool):
        out["limit"] = min(max_rows, max(1, raw_limit))
    else:
        out["limit"] = left_norm.get("limit", min(50, max_rows))
    return out
