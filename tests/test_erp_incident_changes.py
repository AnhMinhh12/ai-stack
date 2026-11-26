import json
import os
import tempfile
import unittest
from pathlib import Path

from erp_ai.agent import Limits, run_agent
from erp_ai.agent_backend import ReportBackend
from erp_ai.context_hints import extract_context_hints
from erp_ai.incident_log import list_incidents, record
from erp_ai.presentation import receipt_blocks

ROOT = Path(__file__).resolve().parents[1]


class IncidentChangesTests(unittest.IsolatedAsyncioTestCase):
    def test_obsolete_legacy_modules_removed(self):
        obsolete = (
            ROOT / "functions/htmp_postgres_query.py",
            ROOT / "functions/htmp_fast_rag.py",
            ROOT / "functions/htmp_technical_rag.py",
            ROOT / "functions/htmp_erp_agent.py",
            ROOT / "functions/htmp_erp_agent_filter.py",
            ROOT / "erp_ai/procedure_catalog.py",
            ROOT / "erp_ai/native_tools.py",
            ROOT / "erp_ai/generic_procedure_executor.py",
            ROOT / "erp_ai/router.py",
            ROOT / "config/htmp-rag-models.json",
            ROOT / "config/erp-semantic-pilot.json",
        )
        for path in obsolete:
            self.assertFalse(path.exists(), f"obsolete path still present: {path}")
        self.assertEqual(sorted(p.name for p in (ROOT / "functions").glob("*.py")), ["htmp_erp_agent_pipe.py"])

    async def test_unmatched_adhoc_question_fails_closed_without_sql_generation(self):
        cfg = json.loads((ROOT / "config/erp-agent.json").read_text())
        called = False

        async def db(*args):
            nonlocal called
            called = True
            return []

        backend = ReportBackend(
            ROOT,
            cfg,
            {"u": {"erp_user_id": 11, "reports": [r["id"] for r in cfg["reports"]], "semantic_datasets": list(cfg["semantic_contracts"])}},
            db,
        )

        async def model(messages, specs):
            return {"content": json.dumps({"answer": "Chưa có hợp đồng cho câu hỏi này.", "source_ids": []})}

        result = await run_agent("Câu hỏi ngẫu nhiên ngoài phạm vi dữ liệu", user={"id": "u"}, model=model, backend=backend)
        self.assertFalse(called)
        self.assertEqual(result["status"], "insufficient_evidence")

    async def test_declarative_config_supports_new_contract_and_report_without_python_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sql").mkdir()
            (root / "sql/custom.sql").write_text("SELECT %s AS uid, %s AS code, %s AS row_limit", encoding="utf-8")
            (root / "manifest.json").write_text(json.dumps({"columns": [], "inputs": {"filters": []}, "output": {"metrics": []}, "match_phrases": []}), encoding="utf-8")
            cfg = {
                "reports": [{
                    "id": "custom_lookup",
                    "title": "Tra cứu mở rộng tùy biến",
                    "tables": ["public.custom_table"],
                    "join": "none",
                    "fields": ["code", "custom_metric"],
                    "validation": "curated_staging",
                    "manifest": "manifest.json",
                    "query_file": "sql/custom.sql",
                    "parameters": ["user_id", "code", "row_limit"],
                    "tool_name": "query_custom_lookup",
                    "tool_description": "Tra cứu tùy biến theo mã.",
                    "cues": ["tuy bien"],
                    "param_schema": {"code": {"type": "identifier", "required": True}},
                    "status_message": "Đang tra cứu tùy biến...",
                    "field_labels": {"code": "Mã tùy biến", "custom_metric": "Giá trị tùy biến"},
                }],
                "knowledge": [],
                "semantic_contracts": {
                    "custom_maintenance": {
                        "status": "approved",
                        "scope": "curated_scoped_subquery",
                        "version": "2026-11-25-v1",
                        "title": "Bảo trì thiết bị tùy biến",
                        "cues": ["bao tri thiet bi"],
                        "require_bounded_date": False,
                        "source_sql": "SELECT 'M01' AS machine, 2 AS fix_count FROM public.userinfo u WHERE u.user_id = %s",
                        "dimensions": {"machine": "machine"},
                        "metrics": {"fix_count": {"aggregate": "sum", "column": "fix_count"}},
                        "filters": {"machine": {"column": "machine", "type": "text", "ops": ["eq"]}},
                        "field_labels": {"machine": "Máy mở rộng", "fix_count": "Số lần bảo trì"},
                    }
                },
            }

            async def db(sql, params, limits):
                if "custom_maintenance" in sql or "FROM (" in sql:
                    return [{"machine": "M01", "fix_count": 2, "__total_rows": 1}]
                return [{"code": "ABC-1", "custom_metric": 99}]

            backend = ReportBackend(
                root,
                cfg,
                {"u": {"erp_user_id": 11, "reports": ["custom_lookup"], "semantic_datasets": ["custom_maintenance"]}},
                db,
            )
            self.assertEqual(backend.status_message("query_custom_lookup"), "Đang tra cứu tùy biến...")
            specs = backend.model_specs("Kiểm tra bảo trì thiết bị và dữ liệu tùy biến", user={"id": "u"})
            self.assertIn("query_custom_lookup", [s["function"]["name"] for s in specs])
            hints = extract_context_hints(
                "Thống kê bảo trì thiết bị",
                datasets=backend.semantic_datasets_for({"id": "u"}),
            )
            self.assertEqual([d["id"] for d in hints["recommended_datasets"]], ["custom_maintenance"])

            res_report = await backend.execute("query_custom_lookup", {"code": "ABC-1"}, {"id": "u"}, Limits())
            blocks_report = receipt_blocks(
                "Tra cứu tùy biến",
                [{"tool": "query_custom_lookup", "arguments": {"code": "ABC-1"}, "result": res_report}],
                "answered",
                config=cfg,
            )
            self.assertEqual(blocks_report[0]["title"], "Tra cứu mở rộng tùy biến")
            self.assertEqual([c["label"] for c in blocks_report[0]["columns"]], ["Mã tùy biến", "Giá trị tùy biến"])

            res_sem = await backend.execute(
                "query_semantic_plan",
                {"dataset": "custom_maintenance", "dimensions": ["machine"], "metrics": ["fix_count"]},
                {"id": "u"},
                Limits(),
            )
            blocks_sem = receipt_blocks(
                "Thống kê bảo trì thiết bị",
                [{"tool": "query_semantic_plan", "arguments": {"dataset": "custom_maintenance", "dimensions": ["machine"], "metrics": ["fix_count"]}, "result": res_sem}],
                "answered",
                config=cfg,
            )
            self.assertIn("Bảo trì thiết bị tùy biến", blocks_sem[0]["text"])
            self.assertEqual([c["label"] for c in blocks_sem[1]["columns"]], ["Máy mở rộng", "Số lần bảo trì"])

    async def test_declarative_presentation_and_alternate_filter_fields(self):
        cfg = json.loads((ROOT / "config/erp-agent.json").read_text())

        async def empty_db(*args):
            return []

        backend = ReportBackend(
            ROOT,
            cfg,
            {"u": {"erp_user_id": 11, "reports": [r["id"] for r in cfg["reports"]], "semantic_datasets": list(cfg["semantic_contracts"])}},
            empty_db,
        )
        self.assertEqual(backend.person_lookup_tool(), "query_employee_info")
        self.assertTrue(backend.is_direct_render("query_receipt_lines"))
        self.assertFalse(backend.is_direct_render("query_employee_info"))
        hints = backend.retrieve(
            "Tìm đề nghị mua hàng của nhân viên Bá Thành tháng 08/2026",
            {"id": "u"},
        )["context_hints"]
        self.assertEqual(hints.get("suggested_lookup_tool"), "query_employee_info")

        gl_hints = backend.retrieve(
            "Tổng công nợ phải thu tài khoản 131 của khách KH0034 cuối tháng 10/2026 là bao nhiêu?",
            {"id": "u"},
        )["context_hints"]
        self.assertNotIn("suggested_lookup_tool", gl_hints)
        self.assertEqual([d["id"] for d in gl_hints.get("recommended_datasets", [])][:1], ["gl_account_movements"])

        sem_empty = await backend.execute(
            "query_semantic_plan",
            {
                "dataset": "purchase_requests",
                "dimensions": ["day"],
                "metrics": ["pr_count"],
                "filters": [
                    {"field": "creator_user", "op": "eq", "value": "HP2843"},
                    {"field": "required_date", "op": "gte", "value": "2026-08-01"},
                    {"field": "required_date", "op": "lte", "value": "2026-08-31"},
                ],
                "order_by": [{"field": "pr_count", "direction": "desc"}],
            },
            {"id": "u"},
            Limits(),
        )
        self.assertIn("requester", sem_empty.get("hint", ""))

        custom_cfg = {
            "reports": [{
                "id": "custom_table_rep",
                "title": "Báo cáo tùy biến",
                "tool_name": "query_custom_table",
                "direct_render": True,
                "presentation": {
                    "mode": "table",
                    "title": "Lịch sử tùy biến",
                    "scope_template": "mã {code}",
                    "empty_text": "Không có dòng tùy biến cho {scope}.",
                    "summary_noun": "dòng tùy biến",
                    "columns": [
                        {"key": "ngay_ct", "label": "Ngày", "type": "date"},
                        {"key": "nhom", "label": "Nhóm", "type": "text"},
                        {"key": "qty", "label": "SL", "type": "number"},
                        {"key": "dvt", "label": "ĐVT", "type": "text"},
                    ],
                    "chart": {
                        "value_field": "qty",
                        "unit_field": "dvt",
                        "date_field": "ngay_ct",
                        "group_field": "nhom",
                        "date_label": "Ngày",
                        "group_label": "Nhóm",
                        "series_label": "Số lượng",
                    },
                },
            }],
            "semantic_contracts": {},
        }
        custom_backend = ReportBackend(ROOT, custom_cfg, {"u": {"erp_user_id": 11, "reports": ["custom_table_rep"]}}, empty_db)
        self.assertTrue(custom_backend.is_direct_render("query_custom_table"))
        blocks = receipt_blocks(
            "Lịch sử tùy biến",
            [{
                "tool": "query_custom_table",
                "arguments": {"code": "X-1"},
                "result": {
                    "rows": [
                        {"ngay_ct": "2026-10-01", "nhom": "A", "qty": 4, "dvt": "PCS"},
                        {"ngay_ct": "2026-10-02", "nhom": "B", "qty": 6, "dvt": "PCS"},
                    ],
                    "summary": {"total_records": 2, "total_quantity": 10},
                    "sources": [{"id": "records:custom"}],
                },
            }],
            "answered",
            config=custom_cfg,
        )
        self.assertEqual([b["type"] for b in blocks], ["summary", "table", "chart"])
        self.assertIn("mã X-1", blocks[0]["text"])
        self.assertEqual(blocks[1]["title"], "Lịch sử tùy biến")
        self.assertEqual(blocks[2]["chart_type"], "line")

    async def test_scalability_40_contracts_and_clarification_fallback(self):
        from erp_ai.semantic_query import compile_query
        from erp_ai.semantic_normalizer import normalize_semantic_plan

        cfg = json.loads((ROOT / "config/erp-agent.json").read_text())
        contracts = cfg["semantic_contracts"]
        self.assertGreaterEqual(len(contracts), 40)

        async def empty_db(*args):
            return []

        all_reports = [r["id"] for r in cfg["reports"]]
        all_datasets = list(contracts)
        backend = ReportBackend(
            ROOT,
            cfg,
            {"u": {"erp_user_id": 11, "reports": all_reports, "semantic_datasets": all_datasets}},
            empty_db,
        )
        allowed = set(all_datasets)
        for cid, c in contracts.items():
            self.assertEqual(c.get("status"), "approved", cid)
            filters = []
            if c.get("require_bounded_date", True):
                df = c.get("date_field", "day")
                filters = [{"field": df, "op": "gte", "value": "2026-10-01"}, {"field": df, "op": "lte", "value": "2026-10-31"}]
            dims = list(c.get("dimensions", {}))[:1]
            metrics = list(c.get("metrics", {}))[:1]
            plan = normalize_semantic_plan({"dataset": cid, "dimensions": dims, "metrics": metrics, "filters": filters}, contracts)
            compiled = compile_query(plan, contracts, allowed, 11)
            self.assertIn("userinfo", compiled.sql)

        seed = backend.retrieve("Thống kê tồn kho theo lô và hạn sử dụng tháng 10/2026", {"id": "u"})
        self.assertLess(len(json.dumps(seed, ensure_ascii=False)), 26000)
        self.assertIn("inventory_stock_lots", [d["id"] for d in seed["context_hints"]["recommended_datasets"]])
        self.assertIn("inventory_stock_lots", [d["id"] for d in seed["semantic_datasets"]])
        self.assertEqual(len(seed["semantic_datasets"]) + len(seed["other_datasets"]), len(contracts))

        canon_empty = await backend.execute(
            "query_semantic_plan",
            {
                "dataset": "sales_prices_current",
                "dimensions": ["material_name"],
                "metrics": ["line_count"],
                "filters": [{"field": "customer", "op": "eq", "value": "CANON"}],
            },
            {"id": "u"},
            Limits(),
        )
        self.assertIn("customer_name", canon_empty.get("hint", ""))

        pnd_empty = await backend.execute(
            "query_semantic_plan",
            {
                "dataset": "warehouse_internal_receipts",
                "dimensions": ["warehouse_name"],
                "metrics": ["in_qty"],
                "filters": [
                    {"field": "department", "op": "eq", "value": "PND"},
                    {"field": "day", "op": "gte", "value": "2026-10-01"},
                    {"field": "day", "op": "lte", "value": "2026-10-31"},
                ],
            },
            {"id": "u"},
            Limits(),
        )
        self.assertIn("BỎ bộ lọc 'department'", pnd_empty.get("hint", ""))

        bad_filter_err = await backend.execute(
            "query_semantic_plan",
            {
                "dataset": "warehouse_transfers",
                "dimensions": ["warehouse"],
                "metrics": ["transfer_qty"],
                "filters": [
                    {"field": "nonexistent_filter", "op": "eq", "value": "X"},
                    {"field": "day", "op": "gte", "value": "2026-10-01"},
                    {"field": "day", "op": "lte", "value": "2026-10-31"},
                ],
            },
            {"id": "u"},
            Limits(),
        )
        self.assertIn("nonexistent_filter", bad_filter_err.get("hint", ""))

        searched = await backend.execute("search_semantic_datasets", {"query": "điều chuyển kho PXB PNF"}, {"id": "u"}, Limits())
        self.assertIn("warehouse_transfers", [d["id"] for d in searched["datasets"]])
        self.assertIn("dimensions", searched["datasets"][0])

        async def clarify_model(messages, specs):
            return {"content": "Bạn muốn xem doanh thu xuất bán theo khách hàng trong khoảng thời gian nào?"}

        clarify_res = await run_agent("Tổng doanh thu theo khách hàng là bao nhiêu?", user={"id": "u"}, model=clarify_model, backend=backend)
        self.assertEqual(clarify_res["status"], "insufficient_evidence")

        async def broken_json_model(messages, specs):
            return {"content": "{not json"}

        broken_res = await run_agent("Tổng doanh thu theo khách hàng là bao nhiêu?", user={"id": "u"}, model=broken_json_model, backend=backend)
        self.assertEqual(broken_res["status"], "invalid_final")

    def test_incident_persisted_without_question_and_bounded_listing(self):
        with tempfile.TemporaryDirectory() as d, patch_env(d + "/i.db"):
            record("u", "c", "planner", "invalid_json")
            rows = list_incidents()
            self.assertEqual((rows[0]["user_id"], rows[0]["chat_id"], rows[0]["stage"]), ("u", "c", "planner"))
            self.assertNotIn("question", rows[0])
            self.assertEqual(os.stat(d + "/i.db").st_mode & 0o777, 0o600)


class _PatchEnv:
    def __init__(self, path):
        self.path = path
        self.prev = None

    def __enter__(self):
        self.prev = os.environ.get("HTMP_ERP_INCIDENT_DB")
        os.environ["HTMP_ERP_INCIDENT_DB"] = self.path
        return self

    def __exit__(self, *args):
        if self.prev is None:
            os.environ.pop("HTMP_ERP_INCIDENT_DB", None)
        else:
            os.environ["HTMP_ERP_INCIDENT_DB"] = self.prev


def patch_env(path):
    return _PatchEnv(path)


if __name__ == "__main__":
    unittest.main()
