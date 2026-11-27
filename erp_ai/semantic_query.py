"""Compile governed aggregate plans and fanout-safe semantic joins against scoped views.

Contracts must be supplied by trusted server configuration, never by the model.
An approved view must enforce all row-level ERP permissions itself using the
server-injected scope column. No production views are implicitly approved.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date

from .semantic_catalog import CANONICAL_JOIN_ENTITIES

IDENT = re.compile(r'^[a-z_][a-z0-9_]*$')
_VN_SRC = 'áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ'
_VN_DST = 'aaaaaaaaaaaaaaaaaeeeeeeeeeeeiiiiiooooooooooooooooouuuuuuuuuuuyyyyydAAAAAAAAAAAAAAAAAEEEEEEEEEEEIIIIIOOOOOOOOOOOOOOOOOUUUUUUUUUUUYYYYYD'


def _norm_text(value: str) -> str:
    stripped = unicodedata.normalize('NFD', value.strip())
    stripped = ''.join(c for c in stripped if unicodedata.category(c) != 'Mn')
    return ' '.join(stripped.replace('đ', 'd').replace('Đ', 'D').lower().split())


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
    output_columns: tuple[str, ...] = ()


def _compile_subplan(
    plan,
    contracts,
    allowed_contracts,
    erp_user_id,
    max_rows=100,
    *,
    include_total_rows=True,
    enforce_limit_clause=True,
    extra_truncation_row=True,
):
    if type(erp_user_id) is not int or erp_user_id <= 0:
        raise PlanError('invalid_identity')
    if not isinstance(plan, dict) or set(plan) - {'dataset', 'dimensions', 'metrics', 'filters', 'order_by', 'limit'}:
        raise PlanError('invalid_plan')
    dataset = plan.get('dataset')
    if not isinstance(dataset, str) or dataset not in allowed_contracts or dataset not in contracts:
        raise PlanError('dataset_forbidden')
    contract = contracts[dataset]
    scope_type = contract.get('scope') if isinstance(contract, dict) else None
    if not isinstance(contract, dict) or contract.get('status') != 'approved' or scope_type not in ('erp_user_view', 'sales_orders_scoped_v1', 'curated_scoped_subquery'):
        raise PlanError('contract_not_approved')
    version = contract.get('version')
    if not isinstance(version, str) or not version:
        raise PlanError('invalid_contract')
    view = contract.get('view', {})
    if not isinstance(view, dict):
        raise PlanError('invalid_contract')
    scoped_source = scope_type == 'sales_orders_scoped_v1'
    curated_subquery = scope_type == 'curated_scoped_subquery'
    user_param_count = 1
    if scoped_source:
        # Fixed, reviewed code: SQL and identity cannot come from the model.
        table = "(SELECT h.ma_kh AS customer, h.ma_nt AS currency, h.ngay_ct AS day, h.stt_rec AS order_id, d.tien_nt2 AS amount FROM public.ph64 h JOIN public.ct64 d ON d.stt_rec=h.stt_rec JOIN public.userinfo u ON u.user_id=%s WHERE h.status::text NOT IN ('14','15') AND (coalesce(u.is_super,0)=1 OR (h.ma_dvcs=ANY(string_to_array(coalesce(u.ds_branchs,''),',')) AND d.ma_kho=ANY(string_to_array(coalesce(u.ds_stocks,''),','))))) AS scoped_orders"
        scope = None
    elif curated_subquery:
        source_sql = contract.get('source_sql')
        user_param_count = contract.get('user_param_count', 1)
        if not isinstance(source_sql, str) or not source_sql.strip() or type(user_param_count) is not int or user_param_count < 0:
            raise PlanError('invalid_contract')
        table = f"({source_sql}) AS scoped_dataset"
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
        if not isinstance(metric, dict) or metric.get('aggregate') not in ('sum', 'count', 'count_distinct', 'avg', 'min', 'max'):
            raise PlanError('metric_forbidden')
        # A metric with variable units must be grouped by its unit dimension.
        unit_dimension = metric.get('unit_dimension')
        if unit_dimension and unit_dimension not in dimensions and not any(isinstance(f, dict) and f.get('field') == unit_dimension and f.get('op') == 'eq' for f in filters):
            raise PlanError('unit_dimension_required')
        aggregate = metric['aggregate']
        expression = (f"COUNT(DISTINCT {identifier(metric.get('column'))})" if aggregate == 'count_distinct'
                      else f"{aggregate.upper()}({identifier(metric.get('column'))})")
        select.append(f"{expression} AS {identifier(name)}")
    where, params = ([] if (scoped_source or curated_subquery) else [f'{scope} = %s']), [erp_user_id] * user_param_count
    operators = {'eq': '=', 'gte': '>=', 'lte': '<=', 'contains': 'contains', 'in': 'in'}
    seen_filters = set()
    date_bounds = {}
    for item in filters:
        if not isinstance(item, dict) or set(item) != {'field', 'op', 'value'}:
            raise PlanError('invalid_filter')
        field, op, value = item['field'], item['op'], item['value']
        if not isinstance(field, str) or field not in filter_defs or not isinstance(op, str) or op not in operators:
            raise PlanError('filter_forbidden')
        definition = filter_defs[field]
        allowed_ops = definition.get('ops', []) if isinstance(definition, dict) else []
        op_allowed = op in allowed_ops or (op == 'in' and definition.get('type') == 'text' and 'eq' in allowed_ops)
        if not isinstance(definition, dict) or not op_allowed:
            raise PlanError('filter_forbidden')
        key = (field, op)
        if key in seen_filters:
            raise PlanError('duplicate_filter')
        seen_filters.add(key)
        kind = definition.get('type')
        col_ident = identifier(definition.get('column'))
        if kind == 'text':
            if op == 'in':
                if not isinstance(value, (list, tuple)) or not 1 <= len(value) <= 50:
                    raise PlanError('invalid_filter_value')
                cleaned_vals = []
                for elem in value:
                    if not isinstance(elem, str) or not elem.strip() or len(elem) > 128:
                        raise PlanError('invalid_filter_value')
                    cleaned_vals.append(elem.strip())
                where.append(f"{col_ident} = ANY(%s)")
                params.append(cleaned_vals)
            elif not isinstance(value, str) or not value.strip() or len(value) > 128:
                raise PlanError('invalid_filter_value')
            elif op == 'contains':
                norm_val = _norm_text(value)
                if not norm_val:
                    raise PlanError('invalid_filter_value')
                where.append(f"strpos(lower(translate(coalesce({col_ident}::text, ''), '{_VN_SRC}', '{_VN_DST}')), %s) > 0")
                params.append(norm_val)
            else:
                where.append(f"{col_ident} {operators[op]} %s")
                params.append(value)
        elif kind == 'date':
            try:
                if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                    raise ValueError()
            except ValueError:
                raise PlanError('invalid_filter_value') from None
            date_bounds.setdefault(field, {})[op] = value
            where.append(f"{col_ident} {operators[op]} %s")
            params.append(value)
        else:
            raise PlanError('invalid_filter_type')
    for bounds in date_bounds.values():
        if 'gte' in bounds and 'lte' in bounds and bounds['gte'] > bounds['lte']:
            raise PlanError('invalid_date_range')
        if 'eq' in bounds and ((bounds.get('gte') and bounds['eq'] < bounds['gte']) or
                               (bounds.get('lte') and bounds['eq'] > bounds['lte'])):
            raise PlanError('invalid_date_range')
    if scoped_source:
        starts = [x['value'] for x in filters if x['field'] == 'day' and x['op'] == 'gte']
        ends = [x['value'] for x in filters if x['field'] == 'day' and x['op'] == 'lte']
        if len(starts) != 1 or len(ends) != 1 or not 0 <= (date.fromisoformat(ends[0]) - date.fromisoformat(starts[0])).days <= 366:
            raise PlanError('bounded_date_range_required')
    elif curated_subquery and contract.get('require_bounded_date', True):
        date_fields = contract.get('bounded_date_fields') or [contract.get('date_field', 'day')]
        max_span = int(contract.get('max_date_span_days', 366))
        has_bounded = False
        for date_field in date_fields:
            eqs = [x['value'] for x in filters if x['field'] == date_field and x['op'] == 'eq']
            starts = [x['value'] for x in filters if x['field'] == date_field and x['op'] == 'gte']
            ends = [x['value'] for x in filters if x['field'] == date_field and x['op'] == 'lte']
            valid_range = len(starts) == 1 and len(ends) == 1 and 0 <= (date.fromisoformat(ends[0]) - date.fromisoformat(starts[0])).days <= max_span
            if len(eqs) == 1 or valid_range:
                has_bounded = True
                break
        if not has_bounded:
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
        if isinstance(metric, dict) and metric.get('unit_dimension') == 'currency':
            unit = metric['unit_dimension']
            if not any(f['field'] == unit and f['op'] == 'eq' for f in filters):
                raise PlanError('ranking_requires_single_unit')
    if dimensions and not order_parts:
        raise PlanError('order_required')
    # Tie-break on all group dimensions to make limited rankings stable.
    if order_parts:
        order_parts.extend(f'{identifier(name)} ASC NULLS LAST' for name in dimensions if name not in seen_order)
    if selected_dims and include_total_rows:
        select.append('COUNT(*) OVER () AS "__total_rows"')
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
    if enforce_limit_clause:
        query += ' LIMIT %s'
        params.append(limit + 1 if extra_truncation_row else limit)
    return CompiledQuery(query, tuple(params), dataset, version, tuple(dimensions + metrics))


def compile_query(plan, contracts, allowed_contracts, erp_user_id, max_rows=100):
    return _compile_subplan(plan, contracts, allowed_contracts, erp_user_id, max_rows=max_rows)


def build_join_output_layout(legs, join_on):
    """Compute canonical CTE names, aliases, SELECT projections, and collision-free output columns for N-way joins."""
    if not legs:
        return {
            'cte_names': [],
            'cte_aliases': [],
            'select_parts': [],
            'output_cols': [],
            'dim_sources': [],
            'metric_sources': [],
            'leg_metric_outputs': [],
        }
    is_two_way = (len(legs) == 2)
    cte_names = ['_left', '_right'] if is_two_way else [f'_leg{i}' for i in range(len(legs))]
    cte_aliases = ['l', 'r'] if is_two_way else [f'l{i}' for i in range(len(legs))]

    select_parts = [f'{cte_aliases[0]}.{identifier(join_on)} AS {identifier(join_on)}']
    output_cols = [join_on]
    seen_cols = {join_on}
    dim_sources = [(0, join_on, join_on)]

    for leg_idx, leg in enumerate(legs):
        cte_alias = cte_aliases[leg_idx]
        for d in (leg.get('dimensions') or ()):
            if d == join_on:
                continue
            if is_two_way and leg_idx == 0 and d in seen_cols:
                continue
            if d in seen_cols:
                alias = f'r_{d}' if (is_two_way and leg_idx == 1) else f'leg{leg_idx}_{d}'
            else:
                alias = d
            select_parts.append(f'{cte_alias}.{identifier(d)} AS {identifier(alias)}')
            output_cols.append(alias)
            seen_cols.add(alias)
            dim_sources.append((leg_idx, d, alias))

    metric_counts = {}
    for leg in legs:
        for m in (leg.get('metrics') or ()):
            metric_counts[m] = metric_counts.get(m, 0) + 1

    metric_sources = []
    leg_metric_outputs = []
    for leg_idx, leg in enumerate(legs):
        cte_alias = cte_aliases[leg_idx]
        cur_outputs = []
        for m in (leg.get('metrics') or ()):
            if metric_counts.get(m, 0) > 1 or m in seen_cols:
                if is_two_way:
                    alias = f'left_{m}' if leg_idx == 0 else f'right_{m}'
                else:
                    alias = f'leg{leg_idx}_{m}'
            else:
                alias = m
            select_parts.append(f'{cte_alias}.{identifier(m)} AS {identifier(alias)}')
            output_cols.append(alias)
            seen_cols.add(alias)
            metric_sources.append((leg_idx, m, alias))
            cur_outputs.append(alias)
        leg_metric_outputs.append(cur_outputs)

    return {
        'cte_names': cte_names,
        'cte_aliases': cte_aliases,
        'select_parts': select_parts,
        'output_cols': output_cols,
        'dim_sources': dim_sources,
        'metric_sources': metric_sources,
        'leg_metric_outputs': leg_metric_outputs,
    }


def compile_joined_query(join_plan, contracts, allowed_contracts, erp_user_id, max_rows=100):
    """Compile a fanout-safe Aggregate-before-Join query over 2 or 3 approved contracts on a shared join_on key."""
    allowed_keys = {'left', 'right', 'extra_legs', 'join_on', 'join_type', 'order_by', 'limit'}
    if not isinstance(join_plan, dict) or set(join_plan) - allowed_keys:
        raise PlanError('invalid_plan')
    left = join_plan.get('left')
    right = join_plan.get('right')
    extra_legs = join_plan.get('extra_legs')
    join_on = join_plan.get('join_on')
    join_type = join_plan.get('join_type', 'left')
    if not isinstance(left, dict) or not isinstance(right, dict):
        raise PlanError('invalid_plan')
    if extra_legs is not None:
        if not isinstance(extra_legs, list) or len(extra_legs) > 1 or any(not isinstance(x, dict) for x in extra_legs):
            raise PlanError('invalid_plan')
    legs = [left, right, *(extra_legs or ())]
    if not isinstance(join_on, str) or join_on not in CANONICAL_JOIN_ENTITIES:
        raise PlanError('invalid_join_key')
    if join_type not in ('left', 'inner'):
        raise PlanError('invalid_join_type')
    if any(join_on not in (leg.get('dimensions') or ()) for leg in legs):
        raise PlanError('join_key_not_in_dimensions')
    if type(max_rows) is not int or not 1 <= max_rows <= 200:
        raise PlanError('invalid_limit')

    compiled_legs = [
        _compile_subplan(
            left, contracts, allowed_contracts, erp_user_id,
            max_rows=max_rows, include_total_rows=False, enforce_limit_clause=True, extra_truncation_row=False,
        )
    ]
    # On outer legs, avoid truncating pre-aggregations unless an explicit limit is supplied on INNER JOIN.
    for leg in legs[1:]:
        compiled_legs.append(
            _compile_subplan(
                leg, contracts, allowed_contracts, erp_user_id,
                max_rows=200, include_total_rows=False,
                enforce_limit_clause=(join_type == 'inner' and 'limit' in leg),
                extra_truncation_row=False,
            )
        )

    layout = build_join_output_layout(legs, join_on)
    select_parts = [*layout['select_parts'], 'COUNT(*) OVER () AS "__total_rows"']
    output_cols = layout['output_cols']
    first_left_metric = layout['leg_metric_outputs'][0][0] if layout['leg_metric_outputs'] and layout['leg_metric_outputs'][0] else None

    ordering = join_plan.get('order_by')
    if ordering is None:
        ordering = [{'field': first_left_metric, 'direction': 'desc'}] if first_left_metric else []
    if not isinstance(ordering, list):
        raise PlanError('invalid_order')
    order_parts, seen_order = [], set()
    valid_cols = set(output_cols)
    for item in ordering:
        if not isinstance(item, dict) or set(item) != {'field', 'direction'}:
            raise PlanError('invalid_order')
        fld, direction = item['field'], item['direction']
        if not isinstance(fld, str) or fld not in valid_cols or fld in seen_order or direction not in ('asc', 'desc'):
            raise PlanError('invalid_order')
        seen_order.add(fld)
        order_parts.append(f'{identifier(fld)} {direction.upper()} NULLS LAST')
    if order_parts:
        order_parts.append(f'{identifier(join_on)} ASC NULLS LAST')

    limit = join_plan.get('limit', left.get('limit', 50))
    if type(limit) is not int or not 1 <= limit <= max_rows:
        raise PlanError('invalid_limit')

    join_kw = 'INNER JOIN' if join_type == 'inner' else 'LEFT JOIN'
    cte_defs = [f"{layout['cte_names'][idx]} AS ({comp.sql})" for idx, comp in enumerate(compiled_legs)]
    a0 = layout['cte_aliases'][0]
    from_sql = f"{layout['cte_names'][0]} {a0}"
    for idx in range(1, len(legs)):
        ai = layout['cte_aliases'][idx]
        from_sql += (
            f" {join_kw} {layout['cte_names'][idx]} {ai} "
            f"ON {a0}.{identifier(join_on)} = {ai}.{identifier(join_on)}"
        )
    sql = f"WITH {', '.join(cte_defs)} SELECT {', '.join(select_parts)} FROM {from_sql}"
    if order_parts:
        sql += ' ORDER BY ' + ', '.join(order_parts)
    sql += ' LIMIT %s'
    params = tuple(p for comp in compiled_legs for p in comp.parameters) + (limit + 1,)
    return CompiledQuery(
        sql,
        params,
        '+'.join(comp.contract_id for comp in compiled_legs),
        '|'.join(comp.contract_version for comp in compiled_legs),
        tuple(output_cols),
    )
