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
            self.assertEqual(params, (7, 3))
            return [{'customer': 'A', 'orders': 4}, {'customer': 'B', 'orders': 3}, {'customer': 'C', 'orders': 1}]
        result = await execute_plan(plan, contracts=CONTRACTS, allowed_contracts={'sales'}, erp_user_id=7, db=db, limits=Limits())
        self.assertEqual((result['status'], result['has_more'], result['returned_rows']), ('partial', True, 2))
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
        self.contracts = json.loads((Path(__file__).resolve().parents[1] / 'config/erp-semantic-pilot.json').read_text())
        self.contracts['sales_order_lines']['status'] = 'approved'
        self.plan = {'dataset': 'sales_order_lines', 'dimensions': ['customer', 'currency'],
                     'metrics': ['order_amount'], 'filters': [
                         {'field': 'day', 'op': 'gte', 'value': '2026-09-29'},
                         {'field': 'day', 'op': 'lte', 'value': '2026-10-29'},
                         {'field': 'currency', 'op': 'eq', 'value': 'VND'}],
                     'order_by': [{'field': 'order_amount', 'direction': 'desc'}], 'limit': 5}

    def test_scoped_source_uses_injected_identity_and_bound_dates(self):
        compiled = compile_query(self.plan, self.contracts, {'sales_order_lines'}, 123)
        self.assertIn('u.user_id=%s', compiled.sql)
        self.assertEqual(compiled.parameters, (123, '2026-09-29', '2026-10-29', 'VND', 6))

    def test_reject_unbounded_dates_or_mixed_currency_ranking(self):
        plan = copy.deepcopy(self.plan)
        plan['filters'] = plan['filters'][1:]
        with self.assertRaisesRegex(PlanError, 'bounded_date_range_required'):
            compile_query(plan, self.contracts, {'sales_order_lines'}, 123)
        plan = copy.deepcopy(self.plan)
        plan['filters'] = plan['filters'][:2]
        with self.assertRaisesRegex(PlanError, 'ranking_requires_single_unit'):
            compile_query(plan, self.contracts, {'sales_order_lines'}, 123)
