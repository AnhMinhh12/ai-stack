import copy
import json
import unittest
from pathlib import Path

from erp_ai.agent import Limits, run_agent
from erp_ai.agent_backend import ReportBackend
from erp_ai.context_hints import extract_context_hints
from erp_ai.presentation import receipt_blocks
from erp_ai.semantic_catalog import (
    build_3serp_table_catalog,
    build_join_graph,
    enrich_contract_from_dictionary,
    validate_semantic_contracts,
)
from erp_ai.semantic_executor import execute_joined_plan
from erp_ai.semantic_model import compile_semantic_model, load_erp_config
from erp_ai.semantic_normalizer import normalize_joined_plan, normalize_semantic_plan
from erp_ai.semantic_query import PlanError, compile_joined_query, compile_query
from erp_ai.semantic_retriever import (
    catalog_documents_for_indexing,
    document_text_for_dataset,
    fuse_rrf_scores,
    rank_datasets,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/erp-agent.json").read_text())


class CanonicalArchitectureTests(unittest.IsolatedAsyncioTestCase):
    def test_all_contracts_pass_invariant_validator_and_full_column_compile(self):
        contracts = CONFIG["semantic_contracts"]
        self.assertEqual(validate_semantic_contracts(contracts), [])
        for cid, contract in contracts.items():
            df = contract.get("date_field", "day")
            base_filters = (
                [{"field": df, "op": "gte", "value": "2026-10-01"},
                 {"field": df, "op": "lte", "value": "2026-10-10"}]
                if contract.get("require_bounded_date", True)
                else []
            )
            for m_name, m_def in contract["metrics"].items():
                dims = list(contract["dimensions"])[:8]
                unit_dim = m_def.get("unit_dimension")
                if unit_dim and unit_dim not in dims:
                    dims = [unit_dim, *dims[:7]]
                plan = normalize_semantic_plan(
                    {
                        "dataset": cid,
                        "dimensions": dims,
                        "metrics": [m_name],
                        "filters": list(base_filters),
                        "limit": 5,
                    },
                    contracts,
                    max_rows=50,
                )
                if m_def.get("unit_dimension") == "currency" and "currency" in contract["filters"]:
                    plan["filters"].append({"field": "currency", "op": "eq", "value": "VND"})
                compiled = compile_query(plan, contracts, {cid}, 11)
                self.assertEqual(compiled.contract_id, cid)

    def test_3serp_metadata_enrichment_links_ui_captions_and_reports(self):
        catalog = build_3serp_table_catalog()
        self.assertGreater(len(catalog), 100)
        enriched = enrich_contract_from_dictionary(
            CONFIG["semantic_contracts"]["sales_order_lines"],
            table_catalog=catalog,
        )
        self.assertIn("ph64", enriched["tables"])
        self.assertTrue(enriched["captions"] or enriched["report_titles"])

    def test_hybrid_bm25_retriever_ranks_paraphrases_and_multiclause_queries(self):
        contracts = CONFIG["semantic_contracts"]
        backend = ReportBackend(
            ROOT,
            copy.deepcopy(CONFIG),
            {"u": {"erp_user_id": 11, "reports": [r["id"] for r in CONFIG["reports"]], "semantic_datasets": list(contracts)}},
            lambda *_: [],
        )
        datasets = backend.semantic_datasets_for({"id": "u"}, include_cues=True)

        # Multi-clause query surfaces BOTH price list and PO history + join key.
        h_price_po = extract_context_hints(
            "Giá mua của mã nhựa ABS014B hiện tại theo bảng giá nhà cung cấp là bao nhiêu và đơn PO gần nhất mua giá nào?",
            datasets=datasets,
            contracts=contracts,
        )
        recs_price_po = [d["id"] for d in h_price_po["recommended_datasets"]]
        self.assertEqual(recs_price_po[0], "purchase_prices_current")
        self.assertIn("purchase_order_lines", recs_price_po)
        self.assertTrue(any(
            {j["left"], j["right"]} == {"purchase_prices_current", "purchase_order_lines"}
            for j in h_price_po.get("available_joins", [])
        ))

        # Downtime + reason query keeps mes_downtime_lines #1 (not diluted by 'máy'/'nguyên').
        h_down = extract_context_hints(
            "Trong tháng 10/2026 máy nào dừng nhiều nhất và nguyên nhân chính là gì?",
            datasets=datasets,
            contracts=contracts,
        )
        self.assertEqual(h_down["recommended_datasets"][0]["id"], "mes_downtime_lines")

        # Paraphrased 3SERP UI phrasing without exact cues still finds target contract.
        h_cost = extract_context_hints(
            "Chiết tính giá thành báo giá theo trọng lượng sản phẩm và runner",
            datasets=datasets,
            contracts=contracts,
        )
        self.assertEqual(h_cost["recommended_datasets"][0]["id"], "sales_quotation_costings")

    async def test_semantic_join_graph_and_fanout_safe_cte_compilation(self):
        contracts = CONFIG["semantic_contracts"]
        edges = build_join_graph(contracts)
        self.assertIn("mes_downtime_lines<->mes_oee_daily", edges)
        self.assertIn("machine", edges["mes_downtime_lines<->mes_oee_daily"])

        raw_join = {
            "left": {
                "dataset": "mes_downtime_lines",
                "dimensions": ["machine"],
                "metrics": ["stop_minutes", "stop_count"],
                "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}],
                "limit": 5,
            },
            "right": {
                "dataset": "mes_oee_daily",
                "dimensions": ["machine"],
                "metrics": ["oee_pct", "stop_minutes"],
                "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}],
            },
            "join_on": "machine",
            "join_type": "left",
        }
        norm_join = normalize_joined_plan(raw_join, contracts, max_rows=50)
        compiled = compile_joined_query(norm_join, contracts, {"mes_downtime_lines", "mes_oee_daily"}, 11)
        self.assertIn("WITH _left AS (", compiled.sql)
        self.assertIn("LEFT JOIN _right r ON l.\"machine\" = r.\"machine\"", compiled.sql)
        self.assertEqual(compiled.parameters.count(11), 2)
        self.assertIn("left_stop_minutes", compiled.output_columns)
        self.assertIn("right_stop_minutes", compiled.output_columns)
        self.assertIn("oee_pct", compiled.output_columns)

        # Ungranted right dataset must fail closed before execution.
        with self.assertRaisesRegex(PlanError, "dataset_forbidden"):
            compile_joined_query(norm_join, contracts, {"mes_downtime_lines"}, 11)

        # LEFT JOIN allows NULL right metrics without flagging 'missing'.
        async def join_db(sql, params, limits):
            return [{
                "machine": "M-01",
                "left_stop_minutes": 120.5,
                "stop_count": 4,
                "oee_pct": None,
                "right_stop_minutes": None,
                "__total_rows": 1,
            }]

        res = await execute_joined_plan(
            norm_join,
            contracts=contracts,
            allowed_contracts={"mes_downtime_lines", "mes_oee_daily"},
            erp_user_id=11,
            db=join_db,
            limits=Limits(),
        )
        self.assertEqual(res["status"], "complete")
        blocks = receipt_blocks(
            "Top 5 máy dừng lâu nhất kèm OEE",
            [{"tool": "query_semantic_join", "arguments": norm_join, "result": res}],
            "answered",
            config=CONFIG,
        )
        self.assertEqual([b["type"] for b in blocks], ["summary", "table"])
        self.assertIn("+", blocks[1]["title"])

    async def test_wildcard_filter_stripping_and_live_distinct_value_probe(self):
        contracts = CONFIG["semantic_contracts"]
        norm = normalize_semantic_plan(
            {
                "dataset": "mes_oee_daily",
                "dimensions": ["line_group"],
                "metrics": ["oee_pct"],
                "filters": [
                    {"field": "line_group", "op": "eq", "value": "ALL"},
                    {"field": "warehouse", "op": "eq", "value": "Tất cả"},
                    {"field": "day", "op": "gte", "value": "2026-10-01"},
                    {"field": "day", "op": "lte", "value": "2026-10-31"},
                ],
            },
            contracts,
            max_rows=50,
        )
        self.assertEqual([f["field"] for f in norm["filters"]], ["day", "day"])

        calls = []

        async def probe_db(sql, params, limits):
            calls.append((sql, params))
            if "AS _probe" in sql:
                return [{"val": "EP_NHUA"}, {"val": "LAP_RAP"}]
            return []

        backend = ReportBackend(
            ROOT,
            copy.deepcopy(CONFIG),
            {"u": {"erp_user_id": 11, "reports": [], "semantic_datasets": ["mes_oee_daily"]}},
            probe_db,
        )
        res = await backend.execute(
            "query_semantic_plan",
            {
                "dataset": "mes_oee_daily",
                "dimensions": ["line_group"],
                "metrics": ["oee_pct"],
                "filters": [
                    {"field": "line_group", "op": "eq", "value": "NHOM_KHONG_TON_TAI"},
                    {"field": "day", "op": "gte", "value": "2026-10-01"},
                    {"field": "day", "op": "lte", "value": "2026-10-31"},
                ],
            },
            {"id": "u"},
            Limits(),
        )
        self.assertEqual(res["status"], "empty")
        self.assertIn("EP_NHUA, LAP_RAP", res.get("hint", ""))
        self.assertEqual(len(calls), 2)

    async def test_agent_multistep_partial_continuation_and_superseded_empty_retry(self):
        contracts = CONFIG["semantic_contracts"]

        async def multi_db(sql, params, limits):
            outer_select = sql.split(" FROM ", 1)[0]
            if "AS _probe" in sql:
                return [{"val": "NHOM1"}]
            if "NHOM_SAI" in str(params):
                return []
            if "AS \"reason_name\"" in outer_select:
                return [{"reason_name": "Chờ khuôn", "stop_minutes": 420.0, "__total_rows": 1}]
            return [
                {"machine": "EP01", "stop_minutes": 500.0, "__total_rows": 8},
                {"machine": "EP02", "stop_minutes": 300.0, "__total_rows": 8},
            ]

        backend = ReportBackend(
            ROOT,
            copy.deepcopy(CONFIG),
            {"u": {"erp_user_id": 11, "reports": [], "semantic_datasets": ["mes_downtime_lines", "mes_oee_daily"]}},
            multi_db,
        )
        round_num = 0

        async def multi_model(messages, specs):
            nonlocal round_num
            round_num += 1
            if round_num == 1:
                return {
                    "tool_calls": [{
                        "id": "c1",
                        "type": "function",
                        "function": {
                            "name": "query_semantic_plan",
                            "arguments": json.dumps({
                                "dataset": "mes_downtime_lines",
                                "dimensions": ["machine"],
                                "metrics": ["stop_minutes"],
                                "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}],
                                "limit": 1,
                            }),
                        },
                    }]
                }
            if round_num == 2:
                return {
                    "tool_calls": [{
                        "id": "c2",
                        "type": "function",
                        "function": {
                            "name": "query_semantic_plan",
                            "arguments": json.dumps({
                                "dataset": "mes_downtime_lines",
                                "dimensions": ["reason_name"],
                                "metrics": ["stop_minutes"],
                                "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}],
                                "limit": 3,
                            }),
                        },
                    }]
                }
            src_ids = [s["id"] for m in messages if m["role"] == "tool" for s in json.loads(m["content"]).get("sources", [])]
            return {"content": json.dumps({"answer": "Máy EP01 dừng lâu nhất (500 phút), nguyên nhân chính là Chờ khuôn.", "source_ids": src_ids[:2]})}

        result = await run_agent(
            "Trong tháng 10/2026 máy nào dừng nhiều nhất và nguyên nhân chính là gì?",
            user={"id": "u"},
            model=multi_model,
            backend=backend,
            limits=Limits(**CONFIG["limits"]),
        )
        self.assertEqual(result["status"], "answered")
        self.assertEqual(len(result["verified_results"]), 2)
        self.assertEqual(sum(1 for b in result["blocks"] if b["type"] == "table"), 2)

        # Hinted-empty retry followed by valid result should suppress stale empty block in receipt_blocks.
        blocks = receipt_blocks(
            "OEE theo nhóm máy tháng 10/2026",
            [
                {
                    "tool": "query_semantic_plan",
                    "arguments": {"dataset": "mes_oee_daily", "dimensions": ["line_group"], "metrics": ["oee_pct"]},
                    "result": {"rows": [], "status": "empty", "hint": "Giá trị thực tế: NHOM1", "sources": [{"id": "records:e1"}]},
                },
                {
                    "tool": "query_semantic_plan",
                    "arguments": {"dataset": "mes_oee_daily", "dimensions": ["line_group"], "metrics": ["oee_pct"]},
                    "result": {"rows": [{"line_group": "NHOM1", "oee_pct": 78.4}], "status": "complete", "sources": [{"id": "records:e2"}]},
                },
            ],
            "answered",
            config=CONFIG,
        )
        self.assertEqual(sum(1 for b in blocks if b["type"] == "summary"), 1)
        self.assertNotIn("không tìm thấy dòng", blocks[0]["text"].lower())

    def test_model_specs_word_boundary_prevents_substring_false_matches(self):
        backend = ReportBackend(
            ROOT,
            copy.deepcopy(CONFIG),
            {"u": {"erp_user_id": 11, "reports": [r["id"] for r in CONFIG["reports"]], "semantic_datasets": list(CONFIG["semantic_contracts"])}},
            lambda *_: [],
        )
        # "So sánh" should not falsely trigger a report cue via substring collision.
        specs = backend.model_specs("So sánh sản lượng tháng 10/2026", user={"id": "u"})
        names = [s["function"]["name"] for s in specs]
        self.assertNotIn("query_allowed_records", names)

        # Purchase-price query must exclude sales-price lookup tools via declarative exclude_cues.
        specs_buy = backend.model_specs("Giá mua của mã ABS014B theo bảng giá nhà cung cấp", user={"id": "u"})
        names_buy = [s["function"]["name"] for s in specs_buy]
        self.assertNotIn("query_price_list", names_buy)
        self.assertNotIn("query_sales_order_price_gaps", names_buy)

    async def test_in_operator_merges_duplicate_eq_and_unknown_tool_redirect(self):
        contracts = CONFIG["semantic_contracts"]
        # Comma-separated 'in' filter compiles to = ANY(%s) with list parameter.
        norm_in = normalize_semantic_plan(
            {
                "dataset": "mes_oee_daily",
                "dimensions": ["machine"],
                "metrics": ["oee_pct"],
                "filters": [
                    {"field": "machine", "op": "in", "value": "DUC-0065, DUC-0069"},
                    {"field": "day", "op": "gte", "value": "2026-10-01"},
                    {"field": "day", "op": "lte", "value": "2026-10-31"},
                ],
            },
            contracts,
            max_rows=50,
        )
        cq = compile_query(norm_in, contracts, {"mes_oee_daily"}, 11)
        self.assertIn('"machine" = ANY(%s)', cq.sql)
        self.assertIn(["DUC-0065", "DUC-0069"], cq.parameters)

        # Repeated 'eq' filters on same text field auto-merge into 'in'.
        norm_merged = normalize_semantic_plan(
            {
                "dataset": "mes_machine_logs_and_cavity",
                "dimensions": ["event_type"],
                "metrics": ["pause_count"],
                "filters": [
                    {"field": "event_type", "op": "eq", "value": "DOI_CAVITY"},
                    {"field": "event_type", "op": "eq", "value": "TAT_DEN_THAP"},
                    {"field": "day", "op": "gte", "value": "2026-10-01"},
                    {"field": "day", "op": "lte", "value": "2026-10-31"},
                ],
            },
            contracts,
            max_rows=50,
        )
        self.assertEqual(norm_merged["filters"][0], {"field": "event_type", "op": "in", "value": ["DOI_CAVITY", "TAT_DEN_THAP"]})

        # Unknown tool named query_<dataset_id> returns actionable redirect hint.
        async def mock_db(*_):
            return [{"po_no": "PO-1", "unit": "KG", "quantity": 10}]

        backend = ReportBackend(
            ROOT,
            copy.deepcopy(CONFIG),
            {"u": {"erp_user_id": 11, "reports": [], "semantic_datasets": ["purchase_order_lines"]}},
            mock_db,
        )
        rounds = 0

        async def redirect_model(messages, specs):
            nonlocal rounds
            rounds += 1
            if rounds == 1:
                return {"tool_calls": [{"id": "c1", "type": "function", "function": {"name": "query_purchase_order_lines", "arguments": "{}"}}]}
            if rounds == 2:
                tool_msg = json.loads(messages[-1]["content"])
                self.assertIn("purchase_order_lines", tool_msg.get("hint", ""))
                return {"tool_calls": [{"id": "c2", "type": "function", "function": {"name": "query_semantic_plan", "arguments": json.dumps({"dataset": "purchase_order_lines", "dimensions": ["po_no", "unit"], "metrics": ["quantity"], "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}]})}}]}
            src_id = json.loads(messages[-1]["content"])["sources"][0]["id"]
            return {"content": json.dumps({"answer": "Có PO-1.", "source_ids": [src_id]})}

        res = await run_agent("PO gần nhất tháng 10/2026", user={"id": "u"}, model=redirect_model, backend=backend)
        self.assertEqual(res["status"], "answered")

    def test_semantic_model_sync_parity_and_field_catalog_presentation(self):
        loaded = load_erp_config(ROOT)
        model_raw = json.loads((ROOT / "config/erp-semantic-model.json").read_text())
        compiled_facts, field_catalog = compile_semantic_model(model_raw)
        self.assertGreater(len(field_catalog), 180)
        self.assertEqual(validate_semantic_contracts(compiled_facts), [])
        for fid, fc in compiled_facts.items():
            self.assertEqual(loaded["semantic_contracts"][fid]["dimensions"], fc["dimensions"])
            self.assertEqual(loaded["semantic_contracts"][fid]["metrics"], fc["metrics"])
            self.assertEqual(loaded["semantic_contracts"][fid]["filters"], fc["filters"])
            self.assertEqual(CONFIG["semantic_contracts"][fid]["source_sql"], fc["source_sql"])

        # Centralized field_catalog should resolve column labels cleanly even when key is custom.
        custom_cfg = copy.deepcopy(loaded)
        custom_cfg.setdefault("field_catalog", {})["qty_test_custom"] = {"label": "SL tùy biến catalog", "type": "number"}
        blocks = receipt_blocks(
            "Thống kê custom",
            [{
                "tool": "query_semantic_plan",
                "arguments": {"dataset": "mes_oee_daily", "dimensions": ["machine"], "metrics": ["oee_pct"]},
                "result": {
                    "rows": [{"machine": "DUC-01", "oee_pct": 88.5, "qty_test_custom": 42}],
                    "returned_rows": 1,
                    "has_more": False,
                    "status": "complete",
                    "contract_id": "mes_oee_daily",
                    "sources": [{"id": "records:cat1"}],
                },
            }],
            "answered",
            config=custom_cfg,
        )
        tbl = next(b for b in blocks if b["type"] == "table")
        labels = {c["key"]: c["label"] for c in tbl["columns"]}
        self.assertEqual(labels["qty_test_custom"], "SL tùy biến catalog")

    async def test_three_way_entity_join_compile_execute_and_present(self):
        contracts = CONFIG["semantic_contracts"]
        raw_join = {
            "left": {
                "dataset": "mes_downtime_lines",
                "dimensions": ["machine"],
                "metrics": ["stop_minutes"],
                "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}],
                "limit": 5,
            },
            "right": {
                "dataset": "mes_production_output",
                "dimensions": ["machine", "unit"],
                "metrics": ["complete_qty"],
                "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}],
            },
            "extra_legs": [{
                "dataset": "mes_oee_daily",
                "dimensions": ["machine"],
                "metrics": ["oee_pct"],
                "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}],
            }],
            "join_on": "machine",
            "join_type": "left",
        }
        norm = normalize_joined_plan(raw_join, contracts, max_rows=50)
        self.assertEqual(len(norm["extra_legs"]), 1)
        compiled = compile_joined_query(norm, contracts, {"mes_downtime_lines", "mes_production_output", "mes_oee_daily"}, 11)
        self.assertIn("WITH _leg0 AS (", compiled.sql)
        self.assertIn("LEFT JOIN _leg1 l1 ON l0.\"machine\" = l1.\"machine\"", compiled.sql)
        self.assertIn("LEFT JOIN _leg2 l2 ON l0.\"machine\" = l2.\"machine\"", compiled.sql)
        self.assertEqual(compiled.output_columns, ("machine", "unit", "stop_minutes", "complete_qty", "oee_pct"))

        async def mock_db(sql, params, limits):
            return [{"machine": "DUC-0065", "unit": "PCS", "stop_minutes": 180.0, "complete_qty": 12500, "oee_pct": 91.2, "__total_rows": 1}]

        res = await execute_joined_plan(
            norm,
            contracts=contracts,
            allowed_contracts={"mes_downtime_lines", "mes_production_output", "mes_oee_daily"},
            erp_user_id=11,
            db=mock_db,
            limits=Limits(),
        )
        self.assertEqual(res["status"], "complete")
        blocks = receipt_blocks(
            "Top 5 máy dừng kèm sản lượng và OEE",
            [{"tool": "query_semantic_join", "arguments": norm, "result": res}],
            "answered",
            config=CONFIG,
        )
        tbl = next(b for b in blocks if b["type"] == "table")
        self.assertEqual(len([c for c in tbl["columns"] if c["key"] in ("machine", "stop_minutes", "complete_qty", "oee_pct")]), 4)
        self.assertIn("dừng máy", tbl["title"].lower())
        self.assertIn("oee", tbl["title"].lower())

        # Colliding metrics across 3 legs disambiguate via leg0_/leg1_/leg2_.
        collide_join = normalize_joined_plan({
            "left": {"dataset": "sales_order_lines", "dimensions": ["material"], "metrics": ["quantity"], "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}]},
            "right": {"dataset": "sales_delivery_lines", "dimensions": ["material"], "metrics": ["quantity"], "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}]},
            "extra_legs": [{"dataset": "purchase_order_lines", "dimensions": ["material"], "metrics": ["quantity"], "filters": [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}]}],
            "join_on": "material",
        }, contracts)
        cq_col = compile_joined_query(collide_join, contracts, {"sales_order_lines", "sales_delivery_lines", "purchase_order_lines"}, 11)
        self.assertEqual(
            cq_col.output_columns,
            ("material", "unit", "leg1_unit", "leg2_unit", "leg0_quantity", "leg1_quantity", "leg2_quantity"),
        )

    async def test_dataset_forbidden_returns_suggestions_and_entity_gating(self):
        backend = ReportBackend.from_root(
            ROOT,
            {"u": {"erp_user_id": 11, "reports": [r["id"] for r in CONFIG["reports"]], "semantic_datasets": list(CONFIG["semantic_contracts"])}},
            lambda *_: [],
        )
        # No material entity -> single-material lookup tools stay gated out, preventing misrouting.
        specs_no_entity = backend.model_specs("Top 5 kho đang tồn nhiều lô hàng nhất hiện nay", user={"id": "u"})
        names_no_ent = [s["function"]["name"] for s in specs_no_entity]
        self.assertNotIn("query_inventory_by_warehouse", names_no_ent)
        self.assertNotIn("query_inventory_balance", names_no_ent)
        self.assertNotIn("query_sales_orders", names_no_ent)

        # With explicit material code QC7-5146-000 -> warehouse lookup tool appears cleanly.
        specs_with_mat = backend.model_specs("Tồn kho của mã QC7-5146-000 ở từng kho ngày 20/10/2026", user={"id": "u"})
        self.assertIn("query_inventory_by_warehouse", [s["function"]["name"] for s in specs_with_mat])

        # Hallucinating a report ID into query_semantic_plan returns disambiguation hint + valid suggested_datasets.
        err = await backend.execute(
            "query_semantic_plan",
            {"dataset": "inventory_by_warehouse", "dimensions": ["warehouse"], "metrics": ["stock_qty"]},
            {"id": "u"},
            Limits(),
        )
        self.assertEqual(err["error"], "invalid_semantic_plan")
        self.assertEqual(err["error_code"], "dataset_forbidden")
        self.assertIn("inventory_by_warehouse", err.get("hint", ""))
        sugg_ids = [d["id"] for d in err.get("suggested_datasets", [])]
        self.assertTrue(any("stock" in i or "warehouse" in i or "inventory" in i for i in sugg_ids))

    def test_hybrid_retriever_qdrant_rrf_fusion_and_catalog_docs(self):
        docs = catalog_documents_for_indexing(CONFIG)
        self.assertGreaterEqual(len(docs), 62)
        sample_doc = next(d for d in docs if d["dataset_id"] == "purchase_delivery_schedules")
        self.assertIn("ctkhnh", sample_doc["text"])
        self.assertIn("Trường dữ liệu", sample_doc["text"])

        rrf = fuse_rrf_scores(["a", "b"], ["b", "c"])
        self.assertAlmostEqual(rrf["b"], (1.0 / 62.0) + (1.0 / 61.0), places=6)
        self.assertGreater(rrf["b"], rrf["a"])

        datasets = [{"id": k, "title": v.get("title", k), "dimensions": list(v.get("dimensions", ())), "metrics": list(v.get("metrics", ())), "filters": list(v.get("filters", ()))} for k, v in CONFIG["semantic_contracts"].items() if v.get("status") == "approved"]
        paraphrase_q = "đối tác hay chậm so với hẹn ban đầu"
        baseline = rank_datasets(paraphrase_q, datasets=datasets, contracts=CONFIG["semantic_contracts"], vector_hits=[])
        boosted = rank_datasets(
            paraphrase_q,
            datasets=datasets,
            contracts=CONFIG["semantic_contracts"],
            vector_hits=["purchase_delivery_schedules"],
        )
        base_score = dict((ds["id"], sc) for sc, ds in baseline)["purchase_delivery_schedules"]
        boost_score = dict((ds["id"], sc) for sc, ds in boosted)["purchase_delivery_schedules"]
        self.assertGreater(boost_score, base_score)
        self.assertEqual(boosted[0][1]["id"], "purchase_delivery_schedules")

        ranked = rank_datasets(
            "nhà cung cấp nào hay trễ hẹn giao",
            datasets=datasets,
            contracts=CONFIG["semantic_contracts"],
            vector_hits=["purchase_delivery_schedules", "purchase_order_lines"],
        )
        top_ids = [ds["id"] for _, ds in ranked[:5]]
        self.assertIn("purchase_delivery_schedules", top_ids[:2])


if __name__ == "__main__":
    unittest.main()
