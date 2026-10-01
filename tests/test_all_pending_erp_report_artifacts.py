import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = re.compile(r"\b(?:insert|update|delete|merge|alter|drop|create|grant|revoke|copy|call|do|vacuum|analyze|truncate|listen|notify|execute|prepare|deallocate|set|show|reset|discard|lock)\b", re.I)


class AllPendingERPReportArtifactTests(unittest.TestCase):
    def test_every_new_manifest_has_read_only_sql_and_three_ui_cases(self):
        manifests = sorted((ROOT / "config" / "erp-reports").glob("*.json"))
        pending = []
        for manifest_path in manifests:
            manifest = json.loads(manifest_path.read_text())
            if manifest.get("validation", {}).get("status") != "pending_ui_validation":
                continue
            pending.append(manifest_path.stem)
            sql = (ROOT / "sql" / "erp-reports" / manifest["query_file"]).read_text().strip()
            evidence = json.loads((ROOT / "tests" / "erp-reports" / f"{manifest_path.stem}.json").read_text())
            self.assertTrue(sql.lower().startswith(("select", "with")), manifest_path.stem)
            self.assertIsNone(FORBIDDEN.search(sql), manifest_path.stem)
            self.assertEqual(evidence["status"], "pending_ui_validation")
            self.assertEqual(evidence["required_comparisons"], 3)
            self.assertEqual(len(evidence["cases"]), 3)
        self.assertEqual(len(pending), 68)
