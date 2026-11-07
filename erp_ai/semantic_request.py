"""Preserve explicit user constraints in the isolated semantic pilot.

This is deliberately conservative: it does not infer business metrics or joins.
Unsupported or multiple explicit months are rejected rather than broadened.
"""
from __future__ import annotations

import calendar
import re

from .semantic_query import PlanError

_MONTH = re.compile(r'\b(?:tháng|thang)\s*(\d{1,2})\s*(?:/|[-.]|\s+(?:năm|nam)\s+|\s+)(\d{4})\b', re.I)


def require_explicit_month(question: str, plan: dict, date_fields: set[str]) -> None:
    """Fail closed when an explicit calendar month is dropped or changed."""
    months = _MONTH.findall(question or '')
    if not months:
        return
    if len(months) != 1 or not isinstance(plan, dict):
        raise PlanError('unsupported_requested_period')
    month, year = map(int, months[0])
    if not 1 <= month <= 12 or not 1 <= year <= 9999:
        raise PlanError('unsupported_requested_period')
    start = f'{year:04d}-{month:02d}-01'
    end = f'{year:04d}-{month:02d}-{calendar.monthrange(year, month)[1]:02d}'
    filters = plan.get('filters', [])
    if not isinstance(filters, list):
        raise PlanError('requested_period_not_preserved')
    dates = [(f.get('field'), f.get('op'), f.get('value')) for f in filters if isinstance(f, dict)]
    starts = [(f, v) for f, op, v in dates if op == 'gte' and v == start]
    ends = [(f, v) for f, op, v in dates if op == 'lte' and v == end]
    if len(starts) != 1 or len(ends) != 1 or starts[0][0] != ends[0][0] or starts[0][0] not in date_fields:
        raise PlanError('requested_period_not_preserved')
