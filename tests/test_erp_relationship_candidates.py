import json
import tempfile
import unittest
from pathlib import Path
from scripts.erp_relationship_candidates import extract


class RelationshipCandidatesTests(unittest.TestCase):
    def test_only_structurally_valid_unambiguous_references_are_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifests, sql = root / 'config/erp-reports', root / 'sql/erp-reports'
            manifests.mkdir(parents=True)
            sql.mkdir(parents=True)
            (manifests / 'r.json').write_text(json.dumps({'id': 'r', 'query_file': 'r.sql', 'validation': {'status': 'pending'}}))
            (sql / 'r.sql').write_text('SELECT * FROM public.orders o JOIN public.lines l ON o.id = l.order_id AND o.missing = l.order_id')
            schema = {'columns': [{'table_schema': 'public', 'table_name': t, 'column_name': c}
                                  for t, c in [('orders', 'id'), ('lines', 'order_id')]]}
            candidates = extract(root, schema)['candidates']
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]['status'], 'candidate_requires_review')
            self.assertEqual(candidates[0]['report_validation']['status'], 'pending')
            (sql / 'r.sql').write_text('SELECT * FROM public.orders o JOIN public.lines l ON o.id=l.order_id JOIN public.lines o ON o.order_id=l.order_id')
            self.assertEqual(extract(root, schema)['candidates'], [])


if __name__ == '__main__':
    unittest.main()
