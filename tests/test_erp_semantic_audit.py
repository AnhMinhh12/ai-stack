import json
import tempfile
import unittest
from pathlib import Path
from scripts.erp_semantic_audit import build_audit


class SemanticAuditTests(unittest.TestCase):
    def test_direct_references_are_checked_without_guessing_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reports = root / 'config/erp-reports'
            reports.mkdir(parents=True)
            manifest = {'id': 'r', 'sources': ['ph64', 'missing'], 'validation': {'status': 'pending'},
                        'ui_column_mapping': {'a': 'ph64.ngay_ct', 'b': 'ph64.missing_col', 'c': 'p.ma_kh'}}
            (reports / 'r.json').write_text(json.dumps(manifest), encoding='utf-8')
            schema = {'tables': [{'table_schema': 'public', 'table_name': 'ph64'}],
                      'columns': [{'table_schema': 'public', 'table_name': 'ph64', 'column_name': 'ngay_ct'}]}
            report = build_audit(root, schema)['reports'][0]
            self.assertEqual(report['sources'], [{'name': 'ph64', 'visible': True}, {'name': 'missing', 'visible': False}])
            refs = {x['field']: x['references'][0]['exists'] for x in report['checked_mappings']}
            self.assertEqual(refs, {'a': True, 'b': False})
            self.assertEqual(report['validation']['status'], 'pending')


if __name__ == '__main__':
    unittest.main()
