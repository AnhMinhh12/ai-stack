import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from erp_ai.agent import Limits
from erp_ai.agent_backend import ReportBackend


class SemanticRetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def test_manifest_search_respects_report_grants_and_field_allowlist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'one.json').write_text(json.dumps({'match_phrases': ['khách đặt hàng'], 'columns': [
                {'field': 'visible', 'label': 'Khách đặt hàng', 'aliases': ['người mua']},
                {'field': 'secret', 'label': 'Mật khẩu'}],
                'validation': {'status': 'pending_ui_validation'}}), encoding='utf-8')
            (root / 'two.json').write_text(json.dumps({'match_phrases': ['khách đặt hàng']}), encoding='utf-8')
            def report(ident, path):
                return {'id': ident, 'title': ident, 'tables': ['public.test'], 'join': 'none',
                        'fields': ['visible'], 'validation': 'pending', 'manifest': path}
            async def db(*args):
                raise AssertionError('search must not query database')
            backend = ReportBackend(root, {'reports': [report('one', 'one.json'), report('two', 'two.json')], 'knowledge': []},
                                    {'u': {'erp_user_id': 1, 'reports': ['one']}}, db)
            result = await backend.execute('search_schema', {'query': 'người mua'}, {'id': 'u'}, Limits())
            self.assertEqual([s['id'] for s in result['schemas']], ['one'])
            encoded = json.dumps(result, ensure_ascii=False)
            self.assertNotIn('secret', encoded)
            self.assertNotIn('two.json', encoded)
            self.assertIn('pending_ui_validation', encoded)
            self.assertEqual(backend.retrieve('người mua', {'id': 'other'})['schemas'], [])

    def test_missing_manifest_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            report = {'id': 'x', 'title': 'x', 'tables': [], 'join': '', 'fields': [],
                      'validation': 'pending', 'manifest': 'missing.json'}
            backend = ReportBackend(directory, {'reports': [report], 'knowledge': []}, {}, None)
            self.assertEqual(backend.schema(report)['semantic_metadata'], {'status': 'unavailable'})


if __name__ == '__main__':
    unittest.main()

class EvidenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_schema_is_not_operational_data(self):
        from erp_ai.agent import run_agent
        class Backend:
            specs = []
            def authorized(self, user): return True
            def retrieve(self, question, user):
                return {'sources': [{'id': 'knowledge:example', 'title': 'Definition'}]}
        async def model(messages, specs):
            return {'content': json.dumps({'answer': 'Có 999 đơn hàng', 'source_ids': ['knowledge:example']})}
        result = await run_agent('Có bao nhiêu đơn hàng?', user={'id': 'u'}, model=model, backend=Backend())
        self.assertEqual(result['status'], 'insufficient_evidence')
        self.assertNotIn('999', result['answer'])
