import copy
import unittest
from erp_ai.semantic_query import compile_query, PlanError

CONTRACTS = {'sales': {'status': 'approved', 'scope': 'erp_user_view', 'version': '1',
    'view': {'schema': 'erp_safe', 'name': 'sales', 'user_column': 'erp_user_id'},
    'dimensions': {'customer': 'customer_code', 'unit': 'unit_code'},
    'metrics': {'quantity': {'aggregate': 'sum', 'column': 'quantity', 'unit_dimension': 'unit'},
                'orders': {'aggregate': 'count', 'column': 'order_id'}},
    'filters': {'customer': {'column': 'customer_code', 'type': 'text', 'ops': ['eq']},
                'day': {'column': 'day', 'type': 'date', 'ops': ['gte', 'lte']}}}}


class SemanticQueryTests(unittest.TestCase):
    def test_compiles_bound_scoped_aggregate_and_fetches_extra_row(self):
        plan = {'dataset': 'sales', 'dimensions': ['customer', 'unit'], 'metrics': ['quantity'],
                'filters': [{'field': 'customer', 'op': 'eq', 'value': "x' OR 1=1 --"}], 'order_by': [{'field': 'customer', 'direction': 'asc'}], 'limit': 4}
        result = compile_query(plan, CONTRACTS, {'sales'}, 7)
        self.assertNotIn('OR 1=1', result.sql)
        self.assertIn('"erp_user_id" = %s', result.sql)
        self.assertIn('GROUP BY "customer_code", "unit_code"', result.sql)
        self.assertEqual(result.parameters, (7, "x' OR 1=1 --", 5))

    def test_denies_unapproved_scope_and_unsupported_fields(self):
        plan = {'dataset': 'sales', 'metrics': ['orders']}
        for contracts, allowed, user in [({}, {'sales'}, 1), (CONTRACTS, set(), 1), (CONTRACTS, {'sales'}, 0)]:
            with self.assertRaises(PlanError): compile_query(plan, contracts, allowed, user)
        bad = copy.deepcopy(CONTRACTS)
        bad['sales']['status'] = 'pending'
        with self.assertRaises(PlanError): compile_query(plan, bad, {'sales'}, 1)
        with self.assertRaises(PlanError): compile_query(dict(plan, dimensions=['password']), CONTRACTS, {'sales'}, 1)
        with self.assertRaises(PlanError): compile_query(dict(plan, sql='DROP TABLE x'), CONTRACTS, {'sales'}, 1)

    def test_quantity_requires_unit_group(self):
        with self.assertRaisesRegex(PlanError, 'unit_dimension_required'):
            compile_query({'dataset': 'sales', 'metrics': ['quantity']}, CONTRACTS, {'sales'}, 1)

    def test_invalid_values_and_identifiers_are_rejected(self):
        base = {'dataset': 'sales', 'metrics': ['orders']}
        for item in [{'field': 'day', 'op': 'gte', 'value': '2026-02-30'},
                     {'field': 'day', 'op': [], 'value': '2026-01-01'}]:
            with self.assertRaises(PlanError): compile_query(dict(base, filters=[item]), CONTRACTS, {'sales'}, 1)
        bad = copy.deepcopy(CONTRACTS)
        bad['sales']['view']['name'] = 'sales; DROP TABLE sales'
        with self.assertRaises(PlanError): compile_query(base, bad, {'sales'}, 1)


if __name__ == '__main__': unittest.main()

class SemanticExecutorTests(unittest.IsolatedAsyncioTestCase):
    async def test_ranked_query_and_truncation_are_explicit(self):
        from erp_ai.semantic_executor import execute_plan
        from erp_ai.agent import Limits
        plan = {'dataset': 'sales', 'dimensions': ['customer'], 'metrics': ['orders'],
                'order_by': [{'field': 'orders', 'direction': 'desc'}], 'limit': 2}
        async def db(sql, params, limits):
            self.assertIn('ORDER BY "orders" DESC NULLS LAST, "customer" ASC NULLS LAST', sql)
            self.assertIn('COUNT(*) OVER () AS "__total_rows"', sql)
            self.assertEqual(params, (7, 3))
            return [{'customer': 'A', 'orders': 4, '__total_rows': 12},
                    {'customer': 'B', 'orders': 3, '__total_rows': 12},
                    {'customer': 'C', 'orders': 1, '__total_rows': 12}]
        result = await execute_plan(plan, contracts=CONTRACTS, allowed_contracts={'sales'}, erp_user_id=7, db=db, limits=Limits())
        self.assertEqual((result['status'], result['has_more'], result['returned_rows'], result['total_rows']), ('partial', True, 2, 12))
        self.assertNotIn('__total_rows', result['rows'][0])
        self.assertTrue(result['sources'][0]['id'].startswith('records:'))

    async def test_invalid_result_shape_and_forbidden_plan(self):
        from erp_ai.semantic_executor import execute_plan
        from erp_ai.agent import Limits
        called = False
        async def db(sql, params, limits):
            nonlocal called
            called = True
            return [{'orders': 1, 'secret': 'unexpected'}]
        plan = {'dataset': 'sales', 'metrics': ['orders']}
        with self.assertRaisesRegex(PlanError, 'invalid_result_shape'):
            await execute_plan(plan, contracts=CONTRACTS, allowed_contracts={'sales'}, erp_user_id=7, db=db, limits=Limits())
        called = False
        with self.assertRaises(PlanError):
            await execute_plan(plan, contracts=CONTRACTS, allowed_contracts=set(), erp_user_id=7, db=db, limits=Limits())
        self.assertFalse(called)

class AgentSemanticIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_granted_plan_reaches_adapter_with_server_identity(self):
        import json
        from pathlib import Path
        from erp_ai.agent import Limits, run_agent
        from erp_ai.agent_backend import ReportBackend
        calls = []
        async def db(sql, parameters, limits):
            calls.append((sql, parameters))
            return [{'orders': 3}]
        backend = ReportBackend(Path('.'), {'reports': [], 'knowledge': [], 'semantic_contracts': CONTRACTS},
                                {'u': {'erp_user_id': 7, 'semantic_datasets': ['sales']}}, db)
        datasets = await backend.execute('search_semantic_datasets', {}, {'id': 'u'}, Limits())
        self.assertEqual(datasets['datasets'][0]['id'], 'sales')
        self.assertNotIn('erp_safe', json.dumps(datasets))
        plan = {'dataset': 'sales', 'metrics': ['orders']}
        async def model(messages, specs):
            if messages[-1]['role'] != 'tool':
                return {'tool_calls': [{'id': 'c', 'type': 'function', 'function': {'name': 'query_semantic_plan',
                        'arguments': json.dumps({'plan_json': json.dumps(plan)})}}]}
            result = json.loads(messages[-1]['content'])
            return {'content': json.dumps({'answer': 'Có 3 đơn.', 'source_ids': [result['sources'][0]['id']]})}
        result = await run_agent('Có bao nhiêu đơn?', user={'id': 'u'}, model=model, backend=backend)
        self.assertEqual(result['status'], 'answered')
        self.assertEqual(calls[0][1][0], 7)
        self.assertEqual(result['metrics']['db_queries'], 1)

    async def test_ungranted_dataset_never_queries_database(self):
        import json
        from pathlib import Path
        from erp_ai.agent import Limits
        from erp_ai.agent_backend import ReportBackend
        async def db(*args): raise AssertionError('forbidden query executed')
        backend = ReportBackend(Path('.'), {'reports': [], 'knowledge': [], 'semantic_contracts': CONTRACTS},
                                {'u': {'erp_user_id': 7, 'semantic_datasets': ['other']}}, db)
        result = await backend.execute('query_semantic_plan', {'plan_json': json.dumps({'dataset': 'sales', 'metrics': ['orders']})}, {'id': 'u'}, Limits())
        self.assertEqual(result['error'], 'invalid_semantic_plan')

class RealSourceContractTests(unittest.TestCase):
    def setUp(self):
        import json
        from pathlib import Path
        cfg = json.loads((Path(__file__).resolve().parents[1] / 'config/erp-agent.json').read_text())
        self.contracts = copy.deepcopy(cfg['semantic_contracts'])
        self.contracts['sales_orders_scoped'] = {
            'status': 'approved',
            'scope': 'sales_orders_scoped_v1',
            'version': '2026-11-25-v1',
            'dimensions': {'customer': 'customer', 'currency': 'currency', 'day': 'day'},
            'metrics': {
                'order_amount': {'aggregate': 'sum', 'column': 'amount', 'unit_dimension': 'currency'},
                'order_count': {'aggregate': 'count_distinct', 'column': 'order_id'},
            },
            'filters': {
                'day': {'column': 'day', 'type': 'date', 'ops': ['gte', 'lte']},
                'customer': {'column': 'customer', 'type': 'text', 'ops': ['eq']},
                'currency': {'column': 'currency', 'type': 'text', 'ops': ['eq']},
            },
        }
        self.plan = {'dataset': 'sales_orders_scoped', 'dimensions': ['customer', 'currency'],
                     'metrics': ['order_amount'], 'filters': [
                         {'field': 'day', 'op': 'gte', 'value': '2026-09-29'},
                         {'field': 'day', 'op': 'lte', 'value': '2026-10-29'},
                         {'field': 'currency', 'op': 'eq', 'value': 'VND'}],
                     'order_by': [{'field': 'order_amount', 'direction': 'desc'}], 'limit': 5}

    def test_scoped_source_uses_injected_identity_and_bound_dates(self):
        compiled = compile_query(self.plan, self.contracts, {'sales_orders_scoped'}, 123)
        self.assertIn('u.user_id=%s', compiled.sql)
        self.assertEqual(compiled.parameters, (123, '2026-09-29', '2026-10-29', 'VND', 6))

    def test_reject_unbounded_dates_or_mixed_currency_ranking(self):
        plan = copy.deepcopy(self.plan)
        plan['filters'] = plan['filters'][1:]
        with self.assertRaisesRegex(PlanError, 'bounded_date_range_required'):
            compile_query(plan, self.contracts, {'sales_orders_scoped'}, 123)
        plan = copy.deepcopy(self.plan)
        plan['filters'] = plan['filters'][:2]
        with self.assertRaisesRegex(PlanError, 'ranking_requires_single_unit'):
            compile_query(plan, self.contracts, {'sales_orders_scoped'}, 123)

class SemanticRequestGuardTests(unittest.TestCase):
    def test_explicit_month_must_match_both_bounds(self):
        from erp_ai.semantic_request import require_explicit_month
        plan = {'filters': [{'field': 'day', 'op': 'gte', 'value': '2026-10-01'},
                            {'field': 'day', 'op': 'lte', 'value': '2026-10-31'}]}
        require_explicit_month('Đơn bán tháng 10/2026', plan, {'day'})
        for changed in ({'filters': []}, {'filters': plan['filters'][:1]},
                        {'filters': [plan['filters'][0], dict(plan['filters'][1], value='2026-11-01')]},
                        {'filters': [plan['filters'][0], dict(plan['filters'][1], field='delivery_date')]}):
            with self.assertRaisesRegex(PlanError, 'requested_period_not_preserved'):
                require_explicit_month('Đơn bán tháng 10/2026', changed, {'day'})

    def test_multiple_or_invalid_months_are_not_silently_guessed(self):
        from erp_ai.semantic_request import require_explicit_month
        for question in ('tháng 13/2026', 'so sánh tháng 10/2026 và tháng 11/2026'):
            with self.assertRaisesRegex(PlanError, 'unsupported_requested_period'):
                require_explicit_month(question, {}, {'day'})

    def test_duplicate_and_reversed_date_filters_are_rejected(self):
        plan = {'dataset': 'sales', 'metrics': ['orders'], 'filters': [
            {'field': 'day', 'op': 'gte', 'value': '2026-10-01'},
            {'field': 'day', 'op': 'gte', 'value': '2026-10-02'}]}
        with self.assertRaisesRegex(PlanError, 'duplicate_filter'):
            compile_query(plan, CONTRACTS, {'sales'}, 7)
        plan['filters'][1] = {'field': 'day', 'op': 'lte', 'value': '2026-09-30'}
        with self.assertRaisesRegex(PlanError, 'invalid_date_range'):
            compile_query(plan, CONTRACTS, {'sales'}, 7)

class SemanticPeriodIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_missing_month_filter_never_reaches_database(self):
        import json
        from pathlib import Path
        from erp_ai.agent import Limits, run_agent
        from erp_ai.agent_backend import ReportBackend
        calls = []
        async def db(*args):
            calls.append(args)
            return [{'orders': 1}]
        backend = ReportBackend(Path('.'), {'reports': [], 'knowledge': [], 'semantic_contracts': CONTRACTS},
                                {'u': {'erp_user_id': 7, 'semantic_datasets': ['sales']}}, db)
        async def model(messages, specs):
            if messages[-1]['role'] != 'tool':
                return {'tool_calls': [{'id': 'x', 'type': 'function', 'function': {
                    'name': 'query_semantic_plan',
                    'arguments': json.dumps({'plan_json': json.dumps({'dataset': 'sales', 'metrics': ['orders']})})}}]}
            return {'content': json.dumps({'answer': 'Không đủ dữ liệu.', 'source_ids': []})}
        result = await run_agent('Có bao nhiêu đơn trong tháng 10/2026?', user={'id': 'u'},
                                 model=model, backend=backend, limits=Limits())
        self.assertEqual(calls, [])
        self.assertNotEqual(result['status'], 'answered')
        self.assertGreater(result['metrics']['tool_errors'], 0)

class SemanticMissingResultsTests(unittest.IsolatedAsyncioTestCase):
    async def test_null_aggregate_not_reported_complete_or_zero(self):
        from erp_ai.semantic_executor import execute_plan
        from erp_ai.agent import Limits
        async def db(*args): return [{'orders': None}]
        result = await execute_plan({'dataset': 'sales', 'metrics': ['orders']},
                                    contracts=CONTRACTS, allowed_contracts={'sales'},
                                    erp_user_id=7, db=db, limits=Limits())
        self.assertEqual(result['status'], 'missing')
        self.assertIsNone(result['rows'][0]['orders'])

    async def test_partial_result_cannot_be_reworded_as_complete(self):
        import json
        from pathlib import Path
        from erp_ai.agent import run_agent
        from erp_ai.agent_backend import ReportBackend
        async def db(*args): return [{'customer': 'A', 'orders': 1}, {'customer': 'B', 'orders': 2}]
        backend = ReportBackend(Path('.'), {'reports': [], 'knowledge': [], 'semantic_contracts': CONTRACTS},
                                {'u': {'erp_user_id': 7, 'semantic_datasets': ['sales']}}, db)
        plan = {'dataset': 'sales', 'metrics': ['orders'], 'dimensions': ['customer'],
                'order_by': [{'field': 'customer', 'direction': 'asc'}], 'limit': 1}
        calls = []
        async def model(messages, specs):
            calls.append(1)
            if len(calls) > 1: raise AssertionError('partial results must not be rewritten')
            return {'tool_calls': [{'id': 'x', 'type': 'function', 'function': {'name': 'query_semantic_plan',
                    'arguments': json.dumps({'plan_json': json.dumps(plan)})}}]}
        result = await run_agent('Danh sách khách hàng', user={'id': 'u'}, model=model, backend=backend)
        self.assertEqual(result['status'], 'partial')
        self.assertIn('chưa đầy đủ', result['answer'])
        self.assertEqual(len(calls), 1)

class PilotApprovalStatusTests(unittest.TestCase):
    def test_unreviewed_contracts_are_not_activated_by_configuration(self):
        import json
        from pathlib import Path
        cfg = json.loads((Path(__file__).resolve().parents[1] / 'config/erp-agent.json').read_text())
        self.assertTrue(all(c.get('status') == 'approved' for c in cfg['semantic_contracts'].values()))
        unapproved = {
            'draft_orders': {
                'status': 'pilot_unapproved',
                'scope': 'sales_orders_scoped_v1',
                'version': '2026-11-25-draft',
                'dimensions': {'customer': 'customer'},
                'metrics': {'order_count': {'aggregate': 'count_distinct', 'column': 'order_id'}},
                'filters': {'day': {'column': 'day', 'type': 'date', 'ops': ['gte', 'lte']}},
            }
        }
        with self.assertRaisesRegex(PlanError, 'contract_not_approved'):
            compile_query({'dataset': 'draft_orders', 'metrics': ['order_count']},
                          unapproved, {'draft_orders'}, 78)


CURATED_CONTRACTS = {
    'po_lines': {
        'status': 'approved',
        'scope': 'curated_scoped_subquery',
        'version': '2026-11-25-v1',
        'date_field': 'day',
        'require_bounded_date': True,
        'user_param_count': 1,
        'source_sql': 'SELECT ma_kh AS supplier, dvt AS unit, ngay_ct AS day, so_luong AS quantity, gia AS unit_price_vnd, tien_nt AS amount_orig FROM public.po WHERE user_id = %s',
        'dimensions': {'supplier': 'supplier', 'unit': 'unit', 'day': 'day'},
        'metrics': {
            'quantity': {'aggregate': 'sum', 'column': 'quantity', 'unit_dimension': 'unit'},
            'avg_price_vnd': {'aggregate': 'avg', 'column': 'unit_price_vnd'},
            'amount_orig': {'aggregate': 'sum', 'column': 'amount_orig', 'unit_dimension': 'currency'},
        },
        'filters': {
            'day': {'type': 'date', 'column': 'day', 'ops': ['eq', 'gte', 'lte']},
            'currency': {'type': 'text', 'column': 'currency', 'ops': ['eq']},
            'unit': {'type': 'text', 'column': 'unit', 'ops': ['eq']},
        },
    }
}


class CuratedSubqueryAndPresentationTests(unittest.TestCase):
    def test_curated_subquery_bounds_and_quantity_ranking(self):
        with self.assertRaisesRegex(PlanError, 'bounded_date_range_required'):
            compile_query({'dataset': 'po_lines', 'metrics': ['avg_price_vnd']},
                          CURATED_CONTRACTS, {'po_lines'}, 7)
        with self.assertRaisesRegex(PlanError, 'bounded_date_range_required'):
            compile_query({'dataset': 'po_lines', 'metrics': ['avg_price_vnd'],
                           'filters': [{'field': 'day', 'op': 'gte', 'value': '2025-01-01'},
                                       {'field': 'day', 'op': 'lte', 'value': '2026-10-31'}]},
                          CURATED_CONTRACTS, {'po_lines'}, 7)
        q = compile_query({'dataset': 'po_lines', 'dimensions': ['supplier', 'unit'],
                           'metrics': ['quantity', 'avg_price_vnd'],
                           'filters': [{'field': 'day', 'op': 'gte', 'value': '2026-10-01'},
                                       {'field': 'day', 'op': 'lte', 'value': '2026-10-31'}],
                           'order_by': [{'field': 'quantity', 'direction': 'desc'}],
                           'limit': 10},
                          CURATED_CONTRACTS, {'po_lines'}, 7)
        self.assertIn('AVG("unit_price_vnd") AS "avg_price_vnd"', q.sql)
        self.assertEqual(q.parameters, (7, '2026-10-01', '2026-10-31', 11))
        with self.assertRaisesRegex(PlanError, 'ranking_requires_single_unit'):
            compile_query({'dataset': 'po_lines', 'dimensions': ['supplier', 'currency'],
                           'metrics': ['amount_orig'],
                           'filters': [{'field': 'day', 'op': 'eq', 'value': '2026-10-01'}],
                           'order_by': [{'field': 'amount_orig', 'direction': 'desc'}]},
                          {'po_lines': {**CURATED_CONTRACTS['po_lines'],
                                        'dimensions': {**CURATED_CONTRACTS['po_lines']['dimensions'], 'currency': 'currency'}}},
                          {'po_lines'}, 7)

    def test_approved_config_semantic_contracts_all_compile(self):
        import json
        from pathlib import Path
        cfg = json.loads((Path(__file__).resolve().parents[1] / 'config/erp-agent.json').read_text())
        contracts = cfg.get('semantic_contracts', {})
        self.assertEqual(len(contracts), 66)
        for name, contract in contracts.items():
            self.assertEqual(contract.get('status'), 'approved')
            first_dim = next(d for d in contract['dimensions'] if d not in ('day', 'unit', 'currency'))
            dims = [first_dim]
            if 'unit' in contract['dimensions']:
                dims.append('unit')
            first_metric = next(iter(contract['metrics']))
            if contract['metrics'][first_metric].get('unit_dimension') == 'currency' and 'currency' in contract['dimensions']:
                dims.append('currency')
            df = contract.get('date_field', 'day')
            filters = ([{'field': df, 'op': 'gte', 'value': '2026-10-01'},
                        {'field': df, 'op': 'lte', 'value': '2026-10-10'}]
                       if contract.get('require_bounded_date', True) else [])
            compiled = compile_query({
                'dataset': name,
                'dimensions': dims,
                'metrics': [first_metric],
                'filters': filters,
                'order_by': [{'field': first_dim, 'direction': 'asc'}],
                'limit': 5,
            }, contracts, {name}, 7)
            self.assertEqual(compiled.contract_id, name)

    def test_semantic_presentation_and_rich_ui_blocks(self):
        import json
        from decimal import Decimal
        from erp_ai.presentation import receipt_blocks, render_markdown
        from erp_ai.rich_ui import render_erp_embed
        plan = {
            'dataset': 'sales_delivery_lines',
            'dimensions': ['customer', 'customer_name', 'unit'],
            'metrics': ['quantity', 'revenue_vnd'],
            'filters': [{'field': 'day', 'op': 'gte', 'value': '2026-10-01'},
                        {'field': 'day', 'op': 'lte', 'value': '2026-10-31'}],
            'order_by': [{'field': 'revenue_vnd', 'direction': 'desc'}],
            'limit': 2,
        }
        verified = [{
            'tool': 'query_semantic_plan',
            'arguments': {'plan_json': json.dumps(plan)},
            'result': {
                'contract_id': 'sales_delivery_lines',
                'status': 'partial',
                'has_more': True,
                'total_rows': 25,
                'applied_filters': plan['filters'],
                'rows': [
                    {'customer': 'KH001', 'customer_name': 'Canon', 'unit': 'PCS',
                     'quantity': Decimal('1000'), 'revenue_vnd': Decimal('5000000')},
                    {'customer': 'KH002', 'customer_name': 'Brother', 'unit': 'PCS',
                     'quantity': Decimal('800'), 'revenue_vnd': Decimal('3000000')},
                ],
                'sources': [{'id': 'records:abc'}],
            },
        }]
        blocks = receipt_blocks('Top khách hàng tháng 10/2026', verified, 'partial')
        types = [b['type'] for b in blocks]
        self.assertEqual(types[:3], ['summary', 'table', 'chart'])
        self.assertIn('chưa đầy đủ', blocks[0]['text'])
        self.assertIn('2 dòng đầu trên tổng 25 dòng', blocks[0]['text'])
        html = render_erp_embed({'blocks': blocks})
        self.assertIn('Chỉ hiển thị 2 dòng trên tổng 25 dòng', html)
        self.assertIn('num-cell', html)
        self.assertIn('5,000,000', html)
        md = render_markdown(blocks)
        self.assertIn('Canon', md)

    def test_extract_inline_tool_call_fallback(self):
        from erp_ai.agent_runtime import _extract_inline_tool_calls
        tools = [{'function': {'name': 'query_semantic_plan'}}]
        msg = {'content': 'Thử lại:\n<tool_call>\n{"name": "query_semantic_plan", "arguments": {"plan_json": "{\\"dataset\\":\\"sales\\"}"}}\n</tool_call>'}
        fixed = _extract_inline_tool_calls(msg, tools)
        self.assertIsNone(fixed['content'])
        self.assertEqual(fixed['tool_calls'][0]['function']['name'], 'query_semantic_plan')
        missing_brace = {'content': '<tool_call>\n{"name": "query_semantic_plan", "arguments": {"plan_json": "{\\"dataset\\":\\"sales\\"}"}\n</tool_call>'}
        fixed2 = _extract_inline_tool_calls(missing_brace, tools)
        self.assertEqual(fixed2['tool_calls'][0]['function']['name'], 'query_semantic_plan')

    def test_catalog_contract_no_date_and_multi_semantic_tables(self):
        import json
        from pathlib import Path
        from erp_ai.presentation import receipt_blocks
        cfg = json.loads((Path(__file__).resolve().parents[1] / 'config/erp-agent.json').read_text())
        q = compile_query({
            'dataset': 'mold_cavity_specs',
            'dimensions': ['mold', 'material'],
            'metrics': ['cavity', 'cycle_sec', 'total_shots'],
            'filters': [{'field': 'mold', 'op': 'eq', 'value': 'K_QC5-2919-000-V1'}],
            'order_by': [{'field': 'material', 'direction': 'asc'}],
            'limit': 5,
        }, cfg['semantic_contracts'], {'mold_cavity_specs'}, 7)
        self.assertEqual(q.parameters, (7, 'K_QC5-2919-000-V1', 6))
        verified = [
            {'tool': 'query_semantic_plan',
             'arguments': {'plan_json': json.dumps({'dataset': 'mold_cavity_specs', 'dimensions': ['mold'], 'metrics': ['cavity', 'total_shots']})},
             'result': {'contract_id': 'mold_cavity_specs', 'status': 'complete', 'has_more': False,
                        'rows': [{'mold': 'K1', 'cavity': 2, 'total_shots': 90000}], 'sources': [{'id': 'records:1'}]}},
            {'tool': 'query_semantic_plan',
             'arguments': {'plan_json': json.dumps({'dataset': 'production_forecast_demand', 'dimensions': ['material', 'unit'], 'metrics': ['quantity']})},
             'result': {'contract_id': 'production_forecast_demand', 'status': 'complete', 'has_more': False,
                        'rows': [{'material': 'M1', 'unit': 'PCS', 'quantity': 50000}], 'sources': [{'id': 'records:2'}]}},
        ]
        blocks = receipt_blocks('Khuôn và FCST', verified, 'answered')
        self.assertEqual([b['type'] for b in blocks], ['table', 'table'])

    def test_semantic_contains_accent_insensitive_and_purchase_requests(self):
        import json
        from pathlib import Path
        from erp_ai.presentation import receipt_blocks
        cfg = json.loads((Path(__file__).resolve().parents[1] / 'config/erp-agent.json').read_text())
        q = compile_query({
            'dataset': 'purchase_requests',
            'dimensions': ['pr_no', 'requester', 'requester_name', 'material', 'unit'],
            'metrics': ['quantity', 'pr_count'],
            'filters': [
                {'field': 'day', 'op': 'eq', 'value': '2026-08-13'},
                {'field': 'requester_name', 'op': 'contains', 'value': 'Bá Thành'},
            ],
            'order_by': [{'field': 'pr_no', 'direction': 'asc'}],
            'limit': 10,
        }, cfg['semantic_contracts'], {'purchase_requests'}, 7)
        self.assertIn('strpos(lower(translate(', q.sql)
        self.assertEqual(q.parameters, (7, '2026-08-13', 'ba thanh', 11))
        with self.assertRaisesRegex(PlanError, 'invalid_filter_value'):
            compile_query({
                'dataset': 'purchase_requests',
                'dimensions': ['pr_no'],
                'metrics': ['pr_count'],
                'filters': [
                    {'field': 'day', 'op': 'eq', 'value': '2026-08-13'},
                    {'field': 'requester_name', 'op': 'contains', 'value': '   '},
                ],
                'order_by': [{'field': 'pr_no', 'direction': 'asc'}],
            }, cfg['semantic_contracts'], {'purchase_requests'}, 7)
        verified = [{
            'tool': 'query_semantic_plan',
            'arguments': {'plan_json': json.dumps({'dataset': 'purchase_requests'})},
            'result': {'contract_id': 'purchase_requests', 'status': 'complete', 'has_more': False,
                       'rows': [{'pr_no': '001-2608-000131', 'requester': 'HP2843', 'requester_name': 'Nguyễn Bá Thành', 'material': 'VPMA0386', 'unit': 'PCS', 'quantity': 3, 'pr_count': 1}],
                       'sources': [{'id': 'records:pr1'}]},
        }]
        blocks = receipt_blocks('Đề nghị mua hàng', verified, 'answered')
        self.assertEqual(blocks[0]['type'], 'summary')
        self.assertIn('Phiếu yêu cầu', blocks[0]['text'])

    def test_normalizer_top_n_limit_blank_filters_and_pipe_sanitizer(self):
        import importlib.util
        import json
        import sys
        import types
        from pathlib import Path
        from erp_ai.semantic_normalizer import normalize_semantic_plan

        cfg = json.loads((Path(__file__).resolve().parents[1] / 'config/erp-agent.json').read_text())
        norm = normalize_semantic_plan(
            {
                'dataset': 'mes_oee_daily',
                'dimensions': ['machine'],
                'metrics': ['oee_pct'],
                'filters': [
                    {'field': 'day', 'op': '>=', 'value': '2026-10-01'},
                    {'field': 'day', 'op': '<=', 'value': '2026-10-31'},
                    {'field': 'machine', 'op': '=', 'value': '   '},
                ],
                'limit': None,
            },
            cfg['semantic_contracts'],
            max_rows=50,
            question='Top 5 máy có OEE trung bình cao nhất tháng 10/2026',
        )
        self.assertEqual(norm['limit'], 5)
        self.assertEqual([(f['field'], f['op'], f['value']) for f in norm['filters']], [
            ('day', 'gte', '2026-10-01'),
            ('day', 'lte', '2026-10-31'),
        ])

        if 'fastapi' not in sys.modules:
            fastapi_mod = types.ModuleType('fastapi')
            responses_mod = types.ModuleType('fastapi.responses')
            responses_mod.HTMLResponse = object
            fastapi_mod.responses = responses_mod
            sys.modules['fastapi'] = fastapi_mod
            sys.modules['fastapi.responses'] = responses_mod
        spec = importlib.util.spec_from_file_location('agent_pipe', Path(__file__).resolve().parents[1] / 'functions/htmp_erp_agent_pipe.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        dirty = 'Dựa trên thông tin mới. Một瞬间暂停以便调整。\n\nKhông có dữ liệu ngày 13/8/2026.'
        cleaned = mod.sanitize_reply_text(dirty)
        self.assertNotIn('瞬间', cleaned)
        self.assertIn('Không có dữ liệu ngày 13/8/2026.', cleaned)
