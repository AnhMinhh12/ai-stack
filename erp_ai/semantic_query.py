"""Compile governed aggregate plans against explicitly approved scoped views.

Contracts must be supplied by trusted server configuration, never by the model.
An approved view must enforce all row-level ERP permissions itself using the
server-injected scope column. No production views are implicitly approved.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

IDENT = re.compile(r'^[a-z_][a-z0-9_]*$')


class PlanError(ValueError):
    pass


def identifier(value):
    if not isinstance(value, str) or not IDENT.fullmatch(value):
        raise PlanError('invalid_identifier')
    return '"' + value + '"'


@dataclass(frozen=True)
class CompiledQuery:
    sql: str
    parameters: tuple
    contract_id: str
    contract_version: str


def compile_query(plan, contracts, allowed_contracts, erp_user_id, max_rows=100):
    if type(erp_user_id) is not int or erp_user_id <= 0:
        raise PlanError('invalid_identity')
    if not isinstance(plan, dict) or set(plan) - {'dataset', 'dimensions', 'metrics', 'filters', 'order_by', 'limit'}:
        raise PlanError('invalid_plan')
    dataset = plan.get('dataset')
    if not isinstance(dataset, str) or dataset not in allowed_contracts or dataset not in contracts:
        raise PlanError('dataset_forbidden')
    contract = contracts[dataset]
    if not isinstance(contract, dict) or contract.get('status') != 'approved' or contract.get('scope') not in ('erp_user_view', 'sales_orders_scoped_v1'):
        raise PlanError('contract_not_approved')
    version = contract.get('version')
    if not isinstance(version, str) or not version:
        raise PlanError('invalid_contract')
    view = contract.get('view', {})
    if not isinstance(view, dict):
        raise PlanError('invalid_contract')
    scoped_source = contract.get('scope') == 'sales_orders_scoped_v1'
    if scoped_source:
        # Fixed, reviewed code: SQL and identity cannot come from the model.
        table = "(SELECT h.ma_kh AS customer, h.ma_nt AS currency, h.ngay_ct AS day, h.stt_rec AS order_id, d.tien_nt2 AS amount FROM public.ph64 h JOIN public.ct64 d ON d.stt_rec=h.stt_rec JOIN public.userinfo u ON u.user_id=%s WHERE h.status::text NOT IN ('14','15') AND (coalesce(u.is_super,0)=1 OR (h.ma_dvcs=ANY(string_to_array(coalesce(u.ds_branchs,''),',')) AND d.ma_kho=ANY(string_to_array(coalesce(u.ds_stocks,''),','))))) AS scoped_orders"
        scope = None
    else:
        table = identifier(view.get('schema')) + '.' + identifier(view.get('name'))
        scope = identifier(view.get('user_column'))
    dimensions, metrics, filters = plan.get('dimensions', []), plan.get('metrics', []), plan.get('filters', [])
    if not isinstance(dimensions, list) or not isinstance(metrics, list) or not isinstance(filters, list):
        raise PlanError('invalid_plan')
    if not 1 <= len(metrics) <= 10 or len(dimensions) > 10 or len(filters) > 20:
        raise PlanError('invalid_plan')
    if any(not isinstance(x, str) for x in dimensions + metrics) or len(set(dimensions + metrics)) != len(dimensions + metrics):
        raise PlanError('invalid_fields')
    dim_defs, metric_defs, filter_defs = contract.get('dimensions', {}), contract.get('metrics', {}), contract.get('filters', {})
    if not all(isinstance(x, dict) for x in (dim_defs, metric_defs, filter_defs)):
        raise PlanError('invalid_contract')
    selected_dims = []
    for name in dimensions:
        if name not in dim_defs:
            raise PlanError('dimension_forbidden')
        selected_dims.append((identifier(dim_defs[name]), identifier(name)))
    select = [f'{column} AS {alias}' for column, alias in selected_dims]
    for name in metrics:
        metric = metric_defs.get(name)
        if not isinstance(metric, dict) or metric.get('aggregate') not in ('sum', 'count', 'count_distinct'):
            raise PlanError('metric_forbidden')
        # A metric with variable units must be grouped by its unit dimension.
        unit_dimension = metric.get('unit_dimension')
        if unit_dimension and unit_dimension not in dimensions and not any(isinstance(f, dict) and f.get('field') == unit_dimension and f.get('op') == 'eq' for f in filters):
            raise PlanError('unit_dimension_required')
        aggregate = metric['aggregate']
        expression = (f"COUNT(DISTINCT {identifier(metric.get('column'))})" if aggregate == 'count_distinct'
                      else f"{aggregate.upper()}({identifier(metric.get('column'))})")
        select.append(f"{expression} AS {identifier(name)}")
    where, params = ([] if scoped_source else [f'{scope} = %s']), [erp_user_id]
    operators = {'eq': '=', 'gte': '>=', 'lte': '<='}
    for item in filters:
        if not isinstance(item, dict) or set(item) != {'field', 'op', 'value'}:
            raise PlanError('invalid_filter')
        field, op, value = item['field'], item['op'], item['value']
        if not isinstance(field, str) or field not in filter_defs or not isinstance(op, str) or op not in operators:
            raise PlanError('filter_forbidden')
        definition = filter_defs[field]
        if not isinstance(definition, dict) or op not in definition.get('ops', []):
            raise PlanError('filter_forbidden')
        kind = definition.get('type')
        if kind == 'text':
            if not isinstance(value, str) or not value or len(value) > 128:
                raise PlanError('invalid_filter_value')
        elif kind == 'date':
            try:
                if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                    raise ValueError()
            except ValueError:
                raise PlanError('invalid_filter_value') from None
        else:
            raise PlanError('invalid_filter_type')
        where.append(f"{identifier(definition.get('column'))} {operators[op]} %s")
        params.append(value)
    if scoped_source:
        starts = [x['value'] for x in filters if x['field'] == 'day' and x['op'] == 'gte']
        ends = [x['value'] for x in filters if x['field'] == 'day' and x['op'] == 'lte']
        if len(starts) != 1 or len(ends) != 1 or not 0 <= (date.fromisoformat(ends[0]) - date.fromisoformat(starts[0])).days <= 366:
            raise PlanError('bounded_date_range_required')
    ordering = plan.get('order_by', [])
    if not isinstance(ordering, list) or len(ordering) > len(dimensions) + len(metrics):
        raise PlanError('invalid_order')
    order_parts, seen_order = [], set()
    for item in ordering:
        if not isinstance(item, dict) or set(item) != {'field', 'direction'}:
            raise PlanError('invalid_order')
        field, direction = item['field'], item['direction']
        if not isinstance(field, str) or field not in dimensions + metrics or field in seen_order or direction not in ('asc', 'desc'):
            raise PlanError('invalid_order')
        seen_order.add(field)
        order_parts.append(f'{identifier(field)} {direction.upper()} NULLS LAST')
    for item in ordering:
        metric = metric_defs.get(item['field'])
        if isinstance(metric, dict) and metric.get('unit_dimension'):
            unit = metric['unit_dimension']
            if not any(f['field'] == unit and f['op'] == 'eq' for f in filters):
                raise PlanError('ranking_requires_single_unit')
    if dimensions and not order_parts:
        raise PlanError('order_required')
    # Tie-break on all group dimensions to make limited rankings stable.
    if order_parts:
        order_parts.extend(f'{identifier(name)} ASC NULLS LAST' for name in dimensions if name not in seen_order)
    limit = plan.get('limit', 50)
    if type(max_rows) is not int or not 1 <= max_rows <= 200 or type(limit) is not int or not 1 <= limit <= max_rows:
        raise PlanError('invalid_limit')
    query = f"SELECT {', '.join(select)} FROM {table}"
    if where:
        query += ' WHERE ' + ' AND '.join(where)
    if selected_dims:
        query += ' GROUP BY ' + ', '.join(column for column, _ in selected_dims)
    if order_parts:
        query += ' ORDER BY ' + ', '.join(order_parts)
    query += ' LIMIT %s'
    params.append(limit + 1)  # Fetch one extra group to detect truncation.
    return CompiledQuery(query, tuple(params), dataset, version)
