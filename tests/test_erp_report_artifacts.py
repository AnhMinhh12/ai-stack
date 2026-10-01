import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = (
    "bao-cao-tinh-trang-don-hang-mua",
    "tong-hop-nxt-theo-lo",
    "thong-ke-dang-ky-ng-sx",
    "tong-hop-hang-ng-theo-phien",
    "oqc-xac-nhan-chat-luong",
    "gia-han-han-su-dung",
)
FORBIDDEN = re.compile(r"\\b(?:insert|update|delete|merge|alter|drop|create|grant|revoke|copy|call|do|vacuum|analyze|truncate|listen|notify|execute|prepare|deallocate|set|show|reset|discard|lock)\\b", re.I)


class PendingERPReportArtifactTests(unittest.TestCase):
    def test_all_pending_reports_have_the_three_required_artifacts(self):
        for report_id in REPORTS:
            with self.subTest(report_id=report_id):
                config = json.loads((ROOT / "config" / "erp-reports" / f"{report_id}.json").read_text())
                evidence = json.loads((ROOT / "tests" / "erp-reports" / f"{report_id}.json").read_text())
                sql = (ROOT / "sql" / "erp-reports" / config["query_file"]).read_text().strip()
                self.assertEqual(config["id"], report_id)
                self.assertEqual(config["validation"]["status"], "pending_ui_validation")
                self.assertEqual(evidence["required_comparisons"], 3)
                self.assertEqual(len(evidence["cases"]), 3)
                self.assertTrue(sql.lower().startswith(("select", "with")))
                self.assertIsNone(FORBIDDEN.search(sql))
