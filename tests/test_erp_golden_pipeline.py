import asyncio
import copy
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from erp_ai.agent import Limits, run_agent
from erp_ai.agent_backend import ReportBackend
from erp_ai.context_hints import extract_context_hints
from erp_ai.semantic_normalizer import normalize_semantic_plan, parse_plan_arguments
from erp_ai.semantic_query import compile_query

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/erp-agent.json").read_text())


class SemanticNormalizerTests(unittest.TestCase):
    def test_parses_structured_arguments_and_plan_json(self):
        structured = parse_plan_arguments({
            "dataset": "purchase_requests",
            "dimensions": ["pr_no", "unit"],
            "metrics": ["quantity"],
            "filters": [{"field": "day", "op": "eq", "value": "2026-08-13"}],
        })
        self.assertEqual(structured["dataset"], "purchase_requests")
        self.assertEqual(structured["metrics"], ["quantity"])

        legacy = parse_plan_arguments({
            "plan_json": json.dumps({"dataset": "purchase_requests", "metrics": ["pr_count"]})
        })
        self.assertEqual(legacy["metrics"], ["pr_count"])

    def test_normalizes_dict_filters_missing_unit_order_by_and_metric_in_dims(self):
        contracts = CONFIG["semantic_contracts"]
        raw_plan = {
            "dataset": "mold_cavity_specs",
            "dimensions": ["mold", "cavity", "cycle_sec"],
            "metrics": ["total_shots"],
            "filters": {"mold": "K_QC5-2919-000-V1"},
            "limit": "250",
        }
        norm = normalize_semantic_plan(raw_plan, contracts, max_rows=50)
        self.assertEqual(norm["dimensions"], ["mold"])
        self.assertEqual(norm["metrics"], ["total_shots", "cavity", "cycle_sec"])
        self.assertEqual(norm["filters"], [{"field": "mold", "op": "eq", "value": "K_QC5-2919-000-V1"}])
        self.assertEqual(norm["order_by"], [{"field": "total_shots", "direction": "desc"}])
        self.assertEqual(norm["limit"], 50)
        compiled = compile_query(norm, contracts, {"mold_cavity_specs"}, 11)
        self.assertEqual(compiled.contract_id, "mold_cavity_specs")

    def test_auto_injects_unit_dimension_and_dict_date_range(self):
        contracts = CONFIG["semantic_contracts"]
        raw_plan = {
            "dataset": "purchase_requests",
            "dimensions": ["pr_no", "requester_name"],
            "metrics": ["quantity", "pr_count"],
            "filters": {
                "day": {"from": "2026-08-01", "to": "2026-08-31"},
                "requester_name": "Bá Thành",
            },
        }
        norm = normalize_semantic_plan(raw_plan, contracts, max_rows=50)
        self.assertIn("unit", norm["dimensions"])
        self.assertEqual(norm["order_by"], [{"field": "quantity", "direction": "desc"}])
        self.assertEqual(
            norm["filters"],
            [
                {"field": "day", "op": "gte", "value": "2026-08-01"},
                {"field": "day", "op": "lte", "value": "2026-08-31"},
                {"field": "requester_name", "op": "contains", "value": "Bá Thành"},
            ],
        )
        compiled = compile_query(norm, contracts, {"purchase_requests"}, 11)
        self.assertEqual(compiled.contract_id, "purchase_requests")

    def test_strips_spurious_top_n_code_filter(self):
        contracts = CONFIG["semantic_contracts"]
        raw_plan = {
            "dataset": "mes_ng_defects",
            "dimensions": ["material", "material_name"],
            "metrics": ["ng_qty"],
            "filters": [
                {"field": "day", "op": "gte", "value": "2026-10-01"},
                {"field": "day", "op": "lte", "value": "2026-10-31"},
                {"field": "defect_code", "op": "eq", "value": "5"},
            ],
            "order_by": [{"field": "ng_qty", "direction": "desc"}],
            "limit": 5,
        }
        norm = normalize_semantic_plan(
            raw_plan,
            contracts,
            max_rows=50,
            question="Top 5 mã hàng bị lỗi NG nhiều nhất tháng 10/2026",
        )
        self.assertEqual([f["field"] for f in norm["filters"]], ["day", "day"])

    def test_normalizes_wide_dimensions_and_recovers_dimension_in_metrics(self):
        contracts = CONFIG["semantic_contracts"]
        raw_plan = {
            "dataset": "purchase_requests",
            "dimensions": [
                "creator_name", "creator_user", "day", "department",
                "material", "material_name", "pr_no", "requester",
                "requester_name", "required_date", "status", "unit", "warehouse",
            ],
            "metrics": ["quantity", "material_name"],
            "filters": [{"field": "day", "op": "gte", "value": "2026-08-01"}, {"field": "day", "op": "lte", "value": "2026-08-31"}, {"field": "requester", "op": "eq", "value": "HP2843"}],
        }
        norm = normalize_semantic_plan(raw_plan, contracts, max_rows=50)
        self.assertLessEqual(len(norm["dimensions"]), 10)
        self.assertIn("unit", norm["dimensions"])
        self.assertIn("requester", norm["dimensions"])
        self.assertEqual(norm["metrics"], ["quantity"])
        compiled = compile_query(norm, contracts, {"purchase_requests"}, 11)
        self.assertEqual(compiled.contract_id, "purchase_requests")

    def test_extract_entities_separates_mold_prefix_and_material_code(self):
        from erp_ai.entities import extract_entities
        ent = extract_entities("Khuôn K_425-00107-V2 còn chạy được khoảng bao nhiêu tháng nữa dựa theo FCST của mã 425-00107-2?")
        self.assertEqual(ent["ma_khuon"], "K_425-00107-V2")
        self.assertEqual(ent["ma_vt"], "425-00107-2")


class ContextHintsAndToolPruningTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        async def db(sql, params, limits):
            return []
        self.backend = ReportBackend(
            ROOT,
            copy.deepcopy(CONFIG),
            {"u": {"erp_user_id": 11, "reports": [r["id"] for r in CONFIG["reports"]], "semantic_datasets": list(CONFIG["semantic_contracts"])}},
            db,
        )

    def test_context_hints_inherit_dates_across_multiturn_followups(self):
        history = [
            {"role": "user", "content": "13/8/2026 , Bá Thành đã đặt mua những gì"},
            {"role": "assistant", "content": "Không có dữ liệu."},
            {"role": "user", "content": "viết phiếu mua hàng ấy"},
        ]
        hints = extract_context_hints(
            "nhân viên công ty mà, không phải khách",
            history=history,
            datasets=self.backend.semantic_datasets_for({"id": "u"}),
        )
        self.assertEqual(hints["detected_dates_iso"], ["2026-08-13"])
        self.assertTrue(hints["dates_inherited_from_history"])
        self.assertTrue(hints["employee_lookup_suggested"])
        ds_ids = [d["id"] for d in hints["recommended_datasets"]]
        self.assertIn("purchase_requests", ds_ids)
        self.assertIn("purchase_order_lines", ds_ids)

    def test_model_specs_prunes_23_tools_to_focused_subset(self):
        specs = self.backend.model_specs(
            "Top 5 máy có OEE trung bình cao nhất tháng 10/2026",
            user={"id": "u"},
        )
        names = [s["function"]["name"] for s in specs]
        self.assertEqual(len(names), 5)
        self.assertIn("query_semantic_plan", names)
        self.assertNotIn("query_mold_profile", names)
        self.assertNotIn("query_qc_status", names)
        semantic_spec = next(s for s in specs if s["function"]["name"] == "query_semantic_plan")
        self.assertIn("dataset", semantic_spec["function"]["parameters"]["properties"])

    async def test_structured_semantic_plan_runs_through_agent_and_presentation(self):
        async def db(sql, params, limits):
            return [
                {"pr_no": "PR-1", "requester_name": "Nguyễn Bá Thành", "unit": "PCS", "quantity": 5, "pr_count": 1}
            ]
        self.backend.db = db
        seen_specs = []

        async def model(messages, specs):
            seen_specs.append(specs)
            if messages[-1]["role"] != "tool":
                return {
                    "tool_calls": [{
                        "id": "c1",
                        "type": "function",
                        "function": {
                            "name": "query_semantic_plan",
                            "arguments": json.dumps({
                                "dataset": "purchase_requests",
                                "dimensions": ["pr_no", "requester_name"],
                                "metrics": ["quantity", "pr_count"],
                                "filters": {"day": "2026-08-13"},
                            }),
                        },
                    }]
                }
            res = json.loads(messages[-1]["content"])
            return {"content": json.dumps({"answer": "Có 1 phiếu PR-1.", "source_ids": [res["sources"][0]["id"]]})}

        result = await run_agent(
            "Phiếu đề nghị mua hàng ngày 13/8/2026",
            user={"id": "u"},
            model=model,
            backend=self.backend,
            limits=Limits(),
        )
        self.assertEqual(result["status"], "answered")
        self.assertEqual(result["blocks"][1]["type"], "table")
        self.assertEqual(result["blocks"][1]["rows"][0]["pr_no"], "PR-1")
        self.assertLessEqual(len(seen_specs[0]), 6)

    async def test_empty_semantic_result_preserves_contract_notes(self):
        async def db(sql, params, limits):
            return []
        self.backend.db = db
        async def model(messages, specs):
            return {
                "tool_calls": [{
                    "id": "c1",
                    "type": "function",
                    "function": {
                        "name": "query_semantic_plan",
                        "arguments": json.dumps({
                            "dataset": "gl_account_movements",
                            "dimensions": ["account", "partner"],
                            "metrics": ["debit_vnd", "credit_vnd"],
                            "filters": [
                                {"field": "day", "op": "gte", "value": "2026-10-01"},
                                {"field": "day", "op": "lte", "value": "2026-10-31"},
                                {"field": "account", "op": "eq", "value": "131"},
                                {"field": "partner", "op": "eq", "value": "KH0034"},
                            ],
                        }),
                    },
                }]
            }
        result = await run_agent(
            "Tổng công nợ phải thu tài khoản 131 của khách KH0034 cuối tháng 10/2026 là bao nhiêu?",
            user={"id": "u"},
            model=model,
            backend=self.backend,
            limits=Limits(),
        )
        self.assertEqual(result["status"], "empty")
        self.assertIn("2024-09-06", result["display_markdown"])
        self.assertNotIn("các dòng trên là kết quả đã xác minh", result["display_markdown"])

    async def test_contract_metadata_aliases_default_dims_and_prefix_hint(self):
        contracts = CONFIG["semantic_contracts"]
        norm = normalize_semantic_plan(
            {
                "dataset": "mold_cavity_specs",
                "metrics": ["cavity"],
                "filters": [
                    {"field": "mold", "op": "eq", "value": "K_425-00107-V2"},
                    {"field": "primary_flag", "op": "eq", "value": "true"},
                ],
            },
            contracts,
            max_rows=50,
        )
        self.assertEqual(norm["dimensions"], ["mold", "material"])
        self.assertEqual(norm["filters"][1]["value"], "1")

        async def empty_db(sql, params, limits):
            return []
        self.backend.db = empty_db
        res = await self.backend.execute(
            "query_semantic_plan",
            {
                "dataset": "production_forecast_demand",
                "dimensions": ["material", "unit"],
                "metrics": ["quantity"],
                "filters": [
                    {"field": "material", "op": "eq", "value": "425-00107-2"},
                    {"field": "day", "op": "gte", "value": "2026-11-25"},
                    {"field": "day", "op": "lte", "value": "2027-06-30"},
                ],
            },
            {"id": "u"},
            Limits(),
        )
        self.assertIn("425-00107", res.get("hint", ""))

    async def test_purchase_requests_accepts_required_date_and_alternate_hint(self):
        contracts = CONFIG["semantic_contracts"]
        compiled = compile_query(
            {
                "dataset": "purchase_requests",
                "dimensions": ["pr_no", "day", "required_date", "material", "unit"],
                "metrics": ["quantity", "pr_count"],
                "filters": [
                    {"field": "required_date", "op": "eq", "value": "2026-08-13"},
                    {"field": "requester", "op": "eq", "value": "HP2843"},
                ],
                "order_by": [{"field": "pr_no", "direction": "asc"}],
                "limit": 20,
            },
            contracts,
            {"purchase_requests"},
            11,
        )
        self.assertEqual(compiled.contract_id, "purchase_requests")

        async def empty_db(sql, params, limits):
            return []
        self.backend.db = empty_db
        res = await self.backend.execute(
            "query_semantic_plan",
            {
                "dataset": "purchase_requests",
                "dimensions": ["pr_no", "unit"],
                "metrics": ["quantity"],
                "filters": [
                    {"field": "day", "op": "eq", "value": "2026-08-13"},
                    {"field": "requester", "op": "eq", "value": "HP2843"},
                ],
            },
            {"id": "u"},
            Limits(),
        )
        self.assertIn("required_date", res.get("hint", ""))

    def test_normalizes_null_limit_and_empty_metrics(self):
        contracts = CONFIG["semantic_contracts"]
        norm = normalize_semantic_plan(
            {
                "dataset": "purchase_requests",
                "dimensions": ["pr_no", "day", "required_date", "material"],
                "metrics": [],
                "filters": [
                    {"field": "required_date", "op": "eq", "value": "2026-08-13"},
                    {"field": "requester", "op": "eq", "value": "HP2843"},
                ],
                "order_by": [],
                "limit": None,
            },
            contracts,
            max_rows=50,
        )
        self.assertEqual(norm["metrics"], ["quantity", "pr_count"])
        self.assertIn("unit", norm["dimensions"])
        self.assertEqual(norm["limit"], 50)
        compiled = compile_query(norm, contracts, {"purchase_requests"}, 11)
        self.assertEqual(compiled.contract_id, "purchase_requests")


class DirectPipeTests(unittest.IsolatedAsyncioTestCase):
    def _load_pipe_module(self):
        # Provide lightweight fastapi stub if run outside Open WebUI container.
        if "fastapi" not in sys.modules:
            fastapi_mod = types.ModuleType("fastapi")
            responses_mod = types.ModuleType("fastapi.responses")
            responses_mod.HTMLResponse = object
            fastapi_mod.responses = responses_mod
            sys.modules["fastapi"] = fastapi_mod
            sys.modules["fastapi.responses"] = responses_mod
        spec = importlib.util.spec_from_file_location("agent_pipe", ROOT / "functions/htmp_erp_agent_pipe.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    async def test_pipe_emits_rich_ui_embed_and_strips_cjk_without_outer_llm(self):
        mod = self._load_pipe_module()
        pipe = mod.Pipe()
        emitted = []

        async def emitter(event):
            emitted.append(event)

        fake_result = {
            "status": "answered",
            "answer": "Tổng hợp được 1 dòng dữ liệu. 瞬间测试",
            "display_markdown": "| Mã |\n| --- |\n| A |",
            "blocks": [
                {"type": "summary", "text": "Tổng hợp được 1 dòng.", "source_ids": ["records:1"]},
                {"type": "table", "title": "Bảng test", "columns": [{"key": "a", "label": "A", "type": "text"}], "rows": [{"a": "1"}], "source_ids": ["records:1"]},
            ],
        }
        with patch.object(mod, "answer", AsyncMock(return_value=fake_result)) as mock_answer, \
             patch.object(mod, "build_downloads", return_value=[]), \
             patch.object(mod, "render_erp_embed", return_value="<html>table</html>"):
            reply = await pipe.pipe(
                {
                    "messages": [
                        {"role": "system", "content": "ignored"},
                        {"role": "user", "content": "13/8/2026 Bá Thành đặt mua gì?"},
                        {"role": "assistant", "content": "Không có dữ liệu."},
                        {"role": "user", "content": "viết phiếu mua hàng ấy"},
                    ]
                },
                __user__={"id": "u1"},
                __event_emitter__=emitter,
            )
        mock_answer.assert_awaited_once()
        q, u, hist = mock_answer.call_args.args[:3]
        self.assertEqual(q, "viết phiếu mua hàng ấy")
        self.assertEqual(u, {"id": "u1"})
        self.assertEqual(len(hist), 2)
        self.assertNotIn("瞬间", reply)
        self.assertTrue(any(ev.get("type") == "embeds" for ev in emitted))

        # Headless API mode (__event_emitter__=None) returns display_markdown directly.
        with patch.object(mod, "answer", AsyncMock(return_value=fake_result)), \
             patch.object(mod, "build_downloads", return_value=[]), \
             patch.object(mod, "render_erp_embed", return_value="<html>table</html>"):
            headless_reply = await pipe.pipe({"messages": [{"role": "user", "content": "test"}]})
        self.assertIn("| Mã |", headless_reply)


if __name__ == "__main__":
    unittest.main()
