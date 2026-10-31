"""Bounded execution of a compiled semantic plan using an injected read-only adapter."""
from __future__ import annotations

import hashlib
import json
from .semantic_query import compile_query, PlanError


async def execute_plan(plan, *, contracts, allowed_contracts, erp_user_id, db, limits):
    """The adapter must enforce a read-only transaction and a statement timeout.

    `contracts` and `erp_user_id` must come from server-owned configuration and
    authentication, never from a tool argument or a model response.
    """
    compiled = compile_query(plan, contracts, allowed_contracts, erp_user_id, max_rows=limits.rows)
    rows = await db(compiled.sql, compiled.parameters, limits)
    if not isinstance(rows, list):
        raise PlanError('invalid_result')
    expected = set(plan.get('dimensions', [])) | set(plan['metrics'])
    if any(not isinstance(row, dict) or set(row) != expected for row in rows):
        raise PlanError('invalid_result_shape')
    limit = plan.get('limit', 50)
    has_more = len(rows) > limit
    rows = rows[:limit]
    evidence = json.dumps([compiled.contract_id, compiled.contract_version, erp_user_id, plan],
                          sort_keys=True, ensure_ascii=False, default=str)
    return {'rows': rows, 'returned_rows': len(rows), 'has_more': has_more,
            'status': 'partial' if has_more else ('empty' if not rows else 'complete'),
            'contract_id': compiled.contract_id, 'contract_version': compiled.contract_version,
            'applied_filters': plan.get('filters', []),
            'sources': [{'id': 'records:' + hashlib.sha256(evidence.encode()).hexdigest()[:16],
                         'contract_id': compiled.contract_id, 'version': compiled.contract_version}]}
