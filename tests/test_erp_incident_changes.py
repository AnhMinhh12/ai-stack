import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from functions.htmp_postgres_query import Tools, parse_planner_json, split_batched_erp_questions
from erp_ai.incident_log import record, list_incidents

class IncidentChangesTests(unittest.TestCase):
    def test_planner_requires_one_object(self):
        self.assertEqual(parse_planner_json('```json\n{"sql": null, "reason": "thiếu"}\n```')['reason'], 'thiếu')
        for value in ('{"sql":"SELECT 1"}\n{"sql":"SELECT 2"}', 'text {"sql":"SELECT 1"}', '[]'):
            with self.assertRaises(ValueError): parse_planner_json(value)

    def test_related_delivery_followup_remains_one_request(self):
        q = 'Tính đến ngày 20/10/2026, lot gần nhất được xuất giao của mã QC7-5146-000 là lot nào? Ngày xuất và số lượng bao nhiêu?'
        self.assertEqual(split_batched_erp_questions(q), [])

    def test_unverified_mold_queries_do_not_use_planner(self):
        tool = Tools()
        with patch.object(tool, '_schema_catalog', side_effect=AssertionError('must not query')):
            self.assertIn('số shot bảo hành', tool._ask_erp_data('mã khuôn đang số shot hiện tại nhiều nhất'))

    def test_journal_rejects_invented_warehouse_filter(self):
        from datetime import date
        parsed = {'matches_report': True, 'dates': [date(2026, 10, 1)],
                  'filters': {'ma_kho': 'VAO'}, 'requested_fields': [], 'requested_columns': []}
        with patch('functions.htmp_postgres_query.load_report_config', return_value={}), \
             patch('functions.htmp_postgres_query.parse_report_request', return_value=parsed), \
             patch('functions.htmp_postgres_query.extract_erp_entities', return_value={'ma_vt': 'QC7-5146-000'}):
            result = Tools()._inventory_movement_journal('Nhập kho mã QC7-5146-000 vào ngày 01/10/2026', 1)
        self.assertIn('không thể kết luận không có giao dịch', result)

    def test_incident_persisted_without_question_and_bounded_listing(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {'HTMP_ERP_INCIDENT_DB': d+'/i.db'}):
            record('u', 'c', 'planner', 'invalid_json')
            rows = list_incidents()
            self.assertEqual((rows[0]['user_id'], rows[0]['chat_id'], rows[0]['stage']), ('u','c','planner'))
            self.assertNotIn('question', rows[0])
            self.assertEqual(os.stat(d+'/i.db').st_mode & 0o777, 0o600)

if __name__ == '__main__': unittest.main()
