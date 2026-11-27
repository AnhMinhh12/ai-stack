"""Bounded execution of compiled semantic plans and joins using an injected read-only adapter."""
from __future__ import annotations

import hashlib
import json
from .semantic_query import build_join_output_layout, compile_joined_query, compile_query, PlanError


def _clean_rows(rows, expected_cols):
    if not isinstance(rows, list):
        raise PlanError('invalid_result')
    total_rows = None
    cleaned_rows = []
    for row in rows:
        if not isinstance(row, dict):
            raise PlanError('invalid_result_shape')
        clean = dict(row)
        if '__total_rows' in clean:
            total_val = clean.pop('__total_rows')
            if isinstance(total_val, int) and not isinstance(total_val, bool) and total_rows is None:
                total_rows = total_val
        if set(clean) != expected_cols:
            raise PlanError('invalid_result_shape')
        cleaned_rows.append(clean)
    return cleaned_rows, total_rows


async def execute_plan(plan, *, contracts, allowed_contracts, erp_user_id, db, limits):
    """The adapter must enforce a read-only transaction and a statement timeout.

    `contracts` and `erp_user_id` must come from server-owned configuration and
    authentication, never from a tool argument or a model response.
    """
    compiled = compile_query(plan, contracts, allowed_contracts, erp_user_id, max_rows=limits.rows)
    rows = await db(compiled.sql, compiled.parameters, limits)
    expected = set(plan.get('dimensions', [])) | set(plan['metrics'])
    rows, total_rows = _clean_rows(rows, expected)
    limit = plan.get('limit', 50)
    has_more = len(rows) > limit
    rows = rows[:limit]
    evidence = json.dumps([compiled.contract_id, compiled.contract_version, erp_user_id, plan],
                          sort_keys=True, ensure_ascii=False, default=str)
    # SQL aggregate SUM can return NULL for no inputs or all-NULL inputs. Do
    # not label that value a verified zero or a complete result.
    missing_metric = any(row.get(metric) is None for row in rows for metric in plan['metrics'])
    status = 'partial' if has_more else ('empty' if not rows else ('missing' if missing_metric else 'complete'))
    return {'rows': rows, 'returned_rows': len(rows), 'total_rows': total_rows, 'has_more': has_more,
            'status': status,
            'contract_id': compiled.contract_id, 'contract_version': compiled.contract_version,
            'applied_filters': plan.get('filters', []),
            'sources': [{'id': 'records:' + hashlib.sha256(evidence.encode()).hexdigest()[:16],
                         'contract_id': compiled.contract_id, 'version': compiled.contract_version}]}


async def execute_joined_plan(join_plan, *, contracts, allowed_contracts, erp_user_id, db, limits):
    """Execute a fanout-safe Aggregate-before-Join plan over 2 or 3 approved contracts."""
    compiled = compile_joined_query(join_plan, contracts, allowed_contracts, erp_user_id, max_rows=limits.rows)
    rows = await db(compiled.sql, compiled.parameters, limits)
    expected = set(compiled.output_columns)
    rows, total_rows = _clean_rows(rows, expected)
    limit = join_plan.get('limit', join_plan['left'].get('limit', 50))
    has_more = len(rows) > limit
    rows = rows[:limit]
    evidence = json.dumps([compiled.contract_id, compiled.contract_version, erp_user_id, join_plan],
                          sort_keys=True, ensure_ascii=False, default=str)
    # On a LEFT JOIN, right/extra legs can be NULL when no matching record exists on those sides.
    legs = [join_plan['left'], join_plan['right'], *(join_plan.get('extra_legs') or ())]
    layout = build_join_output_layout(legs, join_plan['join_on'])
    left_out_metrics = layout['leg_metric_outputs'][0]
    missing_left = any(row.get(m) is None for row in rows for m in left_out_metrics)
    status = 'partial' if has_more else ('empty' if not rows else ('missing' if missing_left else 'complete'))
    combined_filters = [f for leg in legs for f in (leg.get('filters') or ())]
    return {'rows': rows, 'returned_rows': len(rows), 'total_rows': total_rows, 'has_more': has_more,
            'status': status,
            'contract_id': compiled.contract_id, 'contract_version': compiled.contract_version,
            'join_on': join_plan.get('join_on'),
            'applied_filters': combined_filters,
            'sources': [{'id': 'records:' + hashlib.sha256(evidence.encode()).hexdigest()[:16],
                         'contract_id': compiled.contract_id, 'version': compiled.contract_version}]}
