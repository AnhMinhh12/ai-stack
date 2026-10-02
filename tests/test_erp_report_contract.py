import importlib.util
import os
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
os.environ["HTMP_ERP_REPORTS_DIR"] = str(ROOT / "config" / "erp-reports")
SPEC = importlib.util.spec_from_file_location(
    "htmp_postgres_query", ROOT / "functions" / "htmp_postgres_query.py"
)
ERP = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ERP)


class InventoryMovementJournalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = ERP.load_report_config("nhat-ky-nhap-xuat-ton")

    def test_creator_and_requested_columns(self):
        parsed = ERP.parse_report_request(
            "3/9/2026, người tạo KH05 đã sửa mã vật tư nào, "
            "tài khoản doanh thu là bao nhiêu",
            self.report,
        )
        self.assertTrue(parsed["matches_report"])
        self.assertEqual(parsed["filters"], {"nguoi_tao": "KH05"})
        self.assertEqual(
            set(parsed["requested_fields"]), {"user_name", "ma_vt", "tk_dt"}
        )

    def test_date_and_material_title_routes_to_report(self):
        parsed = ERP.parse_report_request(
            "ngày 3/9/2026 có những mã vật tư nào", self.report
        )
        self.assertTrue(parsed["matches_report"])
        self.assertEqual(parsed["requested_fields"], ["ma_vt"])

    def test_material_code_with_digits_in_the_middle_is_a_filter(self):
        parsed = ERP.parse_report_request(
            "01/09/2026 có bao nhiêu đơn có mã vật tư VGU1A423", self.report
        )
        self.assertEqual(parsed["filters"], {"ma_vt": "VGU1A423"})
        self.assertEqual(set(parsed["requested_fields"]), {"ma_vt", "so_ct"})

    def test_material_code_with_hyphen_suffix_is_a_filter(self):
        parsed = ERP.parse_report_request(
            "01/09/2026 có mã vật tư VGW1A610-1 không", self.report
        )
        self.assertEqual(parsed["filters"], {"ma_vt": "VGW1A610-1"})

    def test_material_code_with_slash_revision_is_not_truncated(self):
        entities = ERP.extract_erp_entities(
            "Mã vật tư PNKV1260WA1K115/V1 đã được đặt bao nhiêu lần?"
        )
        self.assertEqual(entities["ma_vt"], "PNKV1260WA1K115/V1")
        from erp_ai import build_request
        self.assertEqual(
            build_request("PNKV1260WA1K115/V1 đã đặt bao nhiêu lần", entities).filters["ma_vt"],
            "PNKV1260WA1K115/V1",
        )

    def test_material_code_starting_with_digits_is_recognized(self):
        self.assertEqual(ERP.extract_erp_entities("35K-H2110-0001 đã mua chưa")["ma_vt"], "35K-H2110-0001")

    def test_confirmed_code_is_not_replaced_by_abbreviated_model_context(self):
        store = ERP.ConversationStateStore()
        store.remember("chat", {"ma_vt": "35K-H2110-0001"})
        self.assertEqual(store.resolve("chat", "tổng số lần mua", "ma_vt: H2110")["ma_vt"], "35K-H2110-0001")

    def test_purchase_count_question_does_not_request_detail_rows(self):
        self.assertNotIn("nhung lan nao", ERP.normalize_text("ABS-260 đã mua bao nhiêu lần rồi"))

    def test_count_and_price_question_requests_purchase_detail(self):
        normalized = ERP.normalize_text("ABS1303 mua bao nhiêu lần và với giá bao nhiêu")
        self.assertIn("bao nhieu lan", normalized)
        self.assertIn("gia", normalized)

    def test_purchase_order_history_intent_is_detected(self):
        from erp_ai import build_request
        request = build_request(
            "Mã hàng PNKV1260WA1K115/V1 đã đặt bao giờ chưa, và bao nhiêu lần rồi?",
            {"ma_vt": "PNKV1260WA1K115/V1"},
        )
        self.assertEqual(request.intent, "purchase_order_history")

    def test_random_purchase_request_does_not_match_a_specific_material_code(self):
        self.assertEqual(ERP.extract_erp_entities("đưa một mã hàng công ty đã mua bất kỳ")["ma_vt"], "")

    def test_business_intent_file_matches_purchase_requests(self):
        with patch.object(ERP, "ERP_BUSINESS_INTENTS_PATH", ROOT / "config" / "erp-business-intents.json"):
            self.assertTrue(ERP.business_intent_matches("purchased_material_any", "đưa một mã công ty đã mua bất kỳ"))
            self.assertTrue(ERP.business_intent_matches("purchase_order_history", "mã này đã mua bao nhiêu lần", has_material_code=True))
            self.assertTrue(ERP.business_intent_matches("purchase_order_history", "mã này đã mua bao giờ chưa", has_material_code=True))
            for question in (
                "sản phẩm này mua những lần nào",
                "giá của mã này là bao nhiêu",
                "giá mua gần nhất",
                "giá mua thấp nhất và cao nhất",
                "mua của nhà cung cấp nào",
            ):
                with self.subTest(question=question):
                    self.assertTrue(ERP.business_intent_matches("purchase_order_history", question, has_material_code=True))
            self.assertTrue(ERP.business_intent_matches("supplier_price_approval", "mã này đã duyệt giá chưa", has_material_code=True))
            self.assertTrue(ERP.business_intent_matches("supplier_price_approval", "giá mã này trước VAT", has_material_code=True))

    def test_production_material_types_are_versioned_business_rules(self):
        with patch.object(ERP, "ERP_BUSINESS_INTENTS_PATH", ROOT / "config" / "erp-business-intents.json"):
            self.assertEqual(ERP.production_material_type_codes(), ("41", "51"))

    def test_price_definitions_keep_purchase_history_distinct_from_catalog_price(self):
        source = (ROOT / "functions" / "htmp_postgres_query.py").read_text()
        self.assertIn("gia_don_mua_gan_nhat", source)
        self.assertIn("gia_danh_muc_ncc_hien_hanh", source)
        self.assertIn("DISTINCT ON (p.ma_kh)", source)
        self.assertIn("nha_cung_cap_da_mua", source)

    def test_unrelated_dated_question_does_not_route(self):
        parsed = ERP.parse_report_request(
            "công nợ khách hàng ngày 3/9/2026", self.report
        )
        self.assertFalse(parsed["matches_report"])

    def test_followup_selects_new_column_and_inherits_filters(self):
        parsed = ERP.parse_report_request(
            "tài khoản doanh thu đâu\n"
            "Điều kiện kế thừa từ câu hỏi trước: ngày 3/9/2026, "
            "người tạo KHO5 đã sửa mã vật tư nào",
            self.report,
        )
        self.assertTrue(parsed["matches_report"])
        self.assertEqual(parsed["filters"], {"nguoi_tao": "KHO5"})
        self.assertEqual(parsed["requested_fields"], ["tk_dt"])

    def test_fixed_sql_parameter_contract(self):
        sql = (ROOT / "sql" / "erp-reports" / self.report["query_file"]).read_text()
        self.assertEqual(sql.count("%s"), 8)
        self.assertNotIn("ma_nvgh", sql)

    def test_quantity_out_is_a_manifest_metric_for_a_material_code(self):
        parsed = ERP.parse_report_request(
            "mã vật tư VGU1A532Z có số lượng xuất là bao nhiêu", self.report
        )
        self.assertEqual(parsed["filters"], {"ma_vt": "VGU1A532Z"})
        self.assertEqual(set(parsed["requested_fields"]), {"ma_vt", "sl_xuat"})
        self.assertIn("sl_xuat", self.report["output"]["metrics"])

    def test_unit_of_measure_selects_dvt_column(self):
        parsed = ERP.parse_report_request(
            "đơn vị tính của mã vật tư VGU1A532Z là gì", self.report
        )
        self.assertEqual(parsed["filters"], {"ma_vt": "VGU1A532Z"})
        self.assertEqual(set(parsed["requested_fields"]), {"ma_vt", "dvt"})

    def test_every_business_abbreviation_has_a_field_alias(self):
        expected = {
            "ngày ct": "ngay_ct", "đvt": "dvt", "mã nt": "ma_nt",
            "giá nt": "gia_nt", "mã cp": "ma_cp", "mã vv": "ma_vv",
            "mã loại nx": "ma_loainx", "mã bp": "ma_bp", "tk vt": "tk_vt",
            "mã nx": "ma_nx", "tk gv": "tk_gv", "tk dt": "tk_dt",
        }
        for phrase, field in expected.items():
            with self.subTest(phrase=phrase):
                parsed = ERP.parse_report_request(phrase, self.report)
                self.assertIn(field, parsed["requested_fields"])

    def test_two_requested_inventory_metrics_are_retained(self):
        parsed = ERP.parse_report_request(
            "mã vật tư QC8-2074-000, số chứng từ 001-2609-000276 tại kho KHO-IN "
            "vào ngày 3/9/2026 có số lượng nhập với xuất bao nhiêu",
            self.report,
        )
        self.assertEqual(
            [field for field in parsed["requested_fields"] if field in {"sl_nhap", "sl_xuat"}],
            ["sl_nhap", "sl_xuat"],
        )
        self.assertEqual(parsed["filters"]["ma_kho"], "KHO-IN")

    def test_metric_selection_ignores_fields_used_as_filters(self):
        parsed = ERP.parse_report_request(
            "VGU1A532Z, số chứng từ 001-2609-001226 ngày 3/9/2026 có số lượng xuất bao nhiêu",
            self.report,
        )
        filter_fields = {"ma_vt", "so_ct", "ngay_ct", "ma_kho"}
        fields = [field for field in parsed["requested_fields"] if field not in filter_fields]
        self.assertEqual(fields, ["sl_xuat"])

    def test_report_sql_loads_from_repository_layout(self):
        sql = ERP.load_report_sql(self.report)
        self.assertIn("FROM public.ct70", sql)

    def test_journal_is_fail_closed_without_a_trusted_erp_session_identity(self):
        result = ERP.Tools().ask_erp("nhật ký nhập xuất tồn ngày 03/09/2026")
        self.assertIn("bị chặn an toàn", result)

    def test_trusted_erp_user_mapping_accepts_only_injected_identity_keys(self):
        with patch.dict(os.environ, {"HTMP_ERP_USER_ID_MAP": '{"chat-uuid":42}'}, clear=False):
            self.assertEqual(ERP.trusted_erp_user_id({"id": "chat-uuid"}), 42)
            self.assertIsNone(ERP.trusted_erp_user_id({"id": "other", "erp_user_id": 42}))

    def test_shared_erp_identity_is_used_only_when_no_per_user_mapping_matches(self):
        with patch.dict(os.environ, {"HTMP_ERP_USER_ID_MAP": '{}', "HTMP_ERP_SHARED_USER_ID": "11"}, clear=False):
            self.assertEqual(ERP.trusted_erp_user_id({"id": "any-chat-user"}), 11)

    def test_revenue_account_uses_material_master_lookup(self):
        column = next(item for item in self.report["columns"] if item["field"] == "tk_dt")
        self.assertEqual(column["lookup"], "dmvt")


    def test_entity_extractor_recognizes_material_and_document(self):
        entities = ERP.extract_erp_entities(
            "VGW1A610-1 số chứng từ 001-2609-006507 ngày 05/09/2026"
        )
        self.assertEqual(entities["ma_vt"], "VGW1A610-1")
        self.assertEqual(entities["so_ct"], "001-2609-006507")
        self.assertEqual(entities["ngay_ct"], "05/09/2026")

    def test_transaction_code_is_extracted_and_routes_to_transaction_detail(self):
        from erp_ai import build_request

        entities = ERP.extract_erp_entities(
            "mã giao dịch 1014082003 ngày 3/9/2026"
        )
        self.assertEqual(entities["ma_gd"], "1014082003")
        request = build_request("mã giao dịch 1014082003", entities)
        self.assertEqual(request.intent, "transaction_detail")
        self.assertEqual(request.filters["ma_gd"], "1014082003")

    def test_numeric_material_code_is_recognized_when_labelled_as_material(self):
        entities = ERP.extract_erp_entities(
            "1014082003 mã vật tư này có số chứng từ 001-2609-000892"
        )
        self.assertEqual(entities["ma_vt"], "1014082003")
        self.assertEqual(entities["so_ct"], "001-2609-000892")

    def test_exchange_rate_is_a_computed_screen_column(self):
        self.assertIn("ty_gia", self.report["output"]["computed"])

    def test_exchange_rate_field_is_recognized_for_the_exact_transaction(self):
        parsed = ERP.parse_report_request(
            "mã vật tư 1014082003, số chứng từ 001-2609-000892 có tỉ giá bao nhiêu",
            self.report,
        )
        self.assertIn("ty_gia", parsed["requested_fields"])

    def test_explicit_warehouse_is_not_overwritten_by_blank_conversation_state(self):
        merged = ERP.merge_report_filters(
            {"ma_kho": "KHO-LAP-RAP"},
            {"ma_vt": "1014082003", "ma_kho": "", "so_ct": "001-2609-000894"},
        )
        self.assertEqual(merged["ma_kho"], "KHO-LAP-RAP")
        self.assertEqual(merged["ma_vt"], "1014082003")

    def test_hyphenated_alphabetic_warehouse_code_is_a_filter(self):
        parsed = ERP.parse_report_request(
            "mã vật tư 1014082003 tại kho KHO-LAP-RAP có số lượng nhập bao nhiêu",
            self.report,
        )
        self.assertEqual(parsed["filters"], {"ma_vt": "1014082003", "ma_kho": "KHO-LAP-RAP"})

    def test_numeric_report_values_use_erp_screen_precision(self):
        self.assertEqual(ERP.format_report_field_value("sl_nhap", Decimal("0E-20")), "0.0000")
        self.assertEqual(ERP.format_report_field_value("ty_gia", Decimal("1")), "1.00000")

    def test_context_resolver_inherits_missing_identifiers(self):
        merged = ERP.merge_erp_context(
            "đưa ra chi tiết từng đơn",
            "mã VGW1A610-1 có số chứng từ 001-2609-000025 ngày 01/09/2026",
        )
        self.assertIn("VGW1A610-1", merged)
        self.assertIn("001-2609-000025", merged)
        self.assertIn("01/09/2026", merged)


    def test_conversation_state_routes_followup_to_document_detail(self):
        from erp_ai import ConversationStateStore, build_request

        state = ConversationStateStore()
        state.resolve(
            "chat-1",
            "mã VGW1A610-1 có số chứng từ 001-2609-000025 ngày 01/09/2026",
        )
        filters = state.resolve("chat-1", "đưa ra chi tiết từng đơn")
        request = build_request("đưa ra chi tiết từng đơn", filters)
        self.assertEqual(request.intent, "material_document_detail")
        self.assertEqual(request.filters["ma_vt"], "VGW1A610-1")
        self.assertEqual(request.filters["so_ct"], "001-2609-000025")


if __name__ == "__main__":
    unittest.main()
