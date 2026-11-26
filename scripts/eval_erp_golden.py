#!/usr/bin/env python3
"""Golden E2E evaluation for HTMP ERP Agent (synthetic dry-run or live vLLM + read-only ERP DB).

Usage:
  python3 scripts/eval_erp_golden.py --dry-run
  python3 scripts/eval_erp_golden.py --live --min-pass-rate 0.90

Never prints secrets or .env values. Live mode executes strictly READ ONLY SQL.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(os.environ.get("HTMP_AGENT_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT))

from erp_ai.agent import Limits, run_agent
from erp_ai.agent_backend import ReportBackend
from erp_ai.agent_runtime import QwenClient


@dataclass(frozen=True)
class GoldenCase:
    case_id: str
    question: str
    history: tuple[dict[str, str], ...]
    user: dict[str, Any]
    expected_statuses: tuple[str, ...]
    expected_tools: tuple[str, ...] = ()
    expected_dataset: str = ""
    must_contain_any: tuple[str, ...] = ()
    must_not_contain: tuple[str, ...] = ()
    reconcile_sql: str = ""
    reconcile_check: Callable[[dict[str, Any], list[dict[str, Any]]], tuple[bool, str]] | None = None


def _load_env_defaults() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _check_oee_top(result: dict[str, Any], db_rows: list[dict[str, Any]]) -> tuple[bool, str]:
    verified = result.get("verified_results") or []
    if not verified:
        return False, "no verified results"
    rows = verified[-1]["result"].get("rows") or []
    if not rows or not db_rows:
        return False, "empty rows"
    top_machine = str(rows[0].get("machine") or "").strip()
    expected_machine = str(db_rows[0].get("machine") or "").strip()
    return (top_machine == expected_machine, f"agent top={top_machine} vs sql top={expected_machine}")


def _check_sales_qc7(result: dict[str, Any], db_rows: list[dict[str, Any]]) -> tuple[bool, str]:
    verified = result.get("verified_results") or []
    if not verified or not db_rows:
        return False, "missing verified result or sql row"
    res = verified[-1]["result"]
    summary = res.get("summary") or {}
    expected_qty = float(db_rows[0]["sl"] or 0)
    if "total_quantity" in summary:
        got_qty = float(summary.get("total_quantity") or 0)
    else:
        rows = res.get("rows") or []
        got_qty = sum(float(r.get("quantity") or 0) for r in rows)
    ok = abs(got_qty - expected_qty) < 1e-3
    return ok, f"agent qty={got_qty} vs sql qty={expected_qty}"


def _check_ba_thanh_month(result: dict[str, Any], db_rows: list[dict[str, Any]]) -> tuple[bool, str]:
    verified = result.get("verified_results") or []
    if not verified:
        return False, "no verified results"
    rows = verified[-1]["result"].get("rows") or []
    pr_nos = {str(r.get("pr_no") or "").strip() for r in rows if r.get("pr_no")}
    expected_prs = {str(r["so_ct"]).strip() for r in db_rows}
    if not expected_prs:
        return len(pr_nos) == 0, "expected 0 PRs"
    return expected_prs.issubset(pr_nos), f"agent prs={len(pr_nos)} vs sql prs={len(expected_prs)}"


def build_golden_cases() -> list[GoldenCase]:
    user_ok = {"id": "golden-eval", "email": "eval@htmp.local"}
    return [
        GoldenCase(
            case_id="oee_top5_oct2026",
            question="Top 5 máy có OEE trung bình cao nhất tháng 10/2026",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="mes_oee_daily",
            reconcile_sql=(
                "SELECT trim(a.machine_code) AS machine "
                "FROM public.mes_oi_confirm a "
                "WHERE a.sp_chinh_yn = 1 AND a.create_date BETWEEN '2026-10-01' AND '2026-10-31' "
                "GROUP BY trim(a.machine_code) ORDER BY sum(coalesce(a.complete, 0)) DESC LIMIT 50"
            ),
            reconcile_check=lambda res, db_rows: (
                bool(res.get("verified_results"))
                and str((res["verified_results"][-1]["result"].get("rows") or [{}])[0].get("machine") or "").strip()
                in {str(r["machine"]).strip() for r in db_rows},
                "top OEE machine exists in mes_oi_confirm oct-2026",
            ),
        ),
        GoldenCase(
            case_id="sales_revenue_missing_period",
            question="Tổng doanh thu xuất bán theo khách hàng là bao nhiêu?",
            history=(),
            user=user_ok,
            expected_statuses=("insufficient_evidence", "answered", "partial"),
            must_not_contain=("2020-", "2023-"),
        ),
        GoldenCase(
            case_id="ba_thanh_2026_08_13",
            question="13/8/2026 , Bá Thành đã đặt mua những gì",
            history=(),
            user=user_ok,
            expected_statuses=("empty", "answered"),
            expected_tools=("query_employee_info", "query_semantic_plan"),
            must_not_contain=("2020-08-13", "瞬间", "KH00"),
        ),
        GoldenCase(
            case_id="ba_thanh_followup_pr",
            question="viết phiếu mua hàng ấy",
            history=(
                {"role": "user", "content": "13/8/2026 , Bá Thành đã đặt mua những gì"},
                {"role": "assistant", "content": "Ngày 2026-08-13 không phát sinh đơn mua hàng của Bá Thành."},
            ),
            user=user_ok,
            expected_statuses=("empty", "answered"),
            expected_tools=("query_employee_info", "query_semantic_plan"),
            must_not_contain=("2020-08-13", "tạo phiếu mới"),
        ),
        GoldenCase(
            case_id="ba_thanh_followup_employee",
            question="nhân viên công ty mà, không phải khách",
            history=(
                {"role": "user", "content": "13/8/2026 , Bá Thành đã đặt mua những gì"},
                {"role": "assistant", "content": "Chưa tìm thấy dữ liệu."},
                {"role": "user", "content": "viết phiếu mua hàng ấy"},
                {"role": "assistant", "content": "Chưa tìm thấy dữ liệu."},
            ),
            user=user_ok,
            expected_statuses=("empty", "answered"),
            expected_tools=("query_employee_info", "query_semantic_plan"),
            must_not_contain=("2020-08-13", "瞬间"),
        ),
        GoldenCase(
            case_id="ba_thanh_month_08_2026",
            question="Trong tháng 08/2026, nhân viên Nguyễn Bá Thành (HP2843) viết những phiếu đề nghị mua hàng nào?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="purchase_requests",
            reconcile_sql=(
                "SELECT DISTINCT trim(h.so_ct) AS so_ct "
                "FROM public.ph91 h WHERE h.ngay_ct BETWEEN '2026-08-01' AND '2026-08-31' "
                "AND trim(h.ma_nv) = 'HP2843' AND h.status::text NOT IN ('14', '15')"
            ),
            reconcile_check=_check_ba_thanh_month,
        ),
        GoldenCase(
            case_id="sales_qc7_5146_000",
            question="Cho tôi biết sản lượng và doanh thu xuất bán của mã QC7-5146-000 từ ngày 01/10/2026 đến 20/10/2026",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_allowed_records", "query_semantic_plan"),
            reconcile_sql=(
                "SELECT sum(d.so_luong) AS sl "
                "FROM public.ct81 d JOIN public.ph81 h ON h.stt_rec = d.stt_rec "
                "WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' "
                "AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20' "
                "AND h.status::text NOT IN ('14', '15') AND h.ma_gd <> 4"
            ),
            reconcile_check=_check_sales_qc7,
        ),
        GoldenCase(
            case_id="inventory_by_warehouse_qc7",
            question="Tồn kho của mã QC7-5146-000 ở từng kho tính đến ngày 20/10/2026 là bao nhiêu?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "empty"),
            expected_tools=("query_inventory_by_warehouse",),
        ),
        GoldenCase(
            case_id="mold_cavity_qc7",
            question="Khuôn của mã QC7-5146-000 có mấy cavity, chu kỳ bao nhiêu giây và tổng số shot đã chạy?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial", "missing"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="mold_cavity_specs",
        ),
        GoldenCase(
            case_id="mes_downtime_oct2026",
            question="Top 5 nguyên nhân dừng máy lâu nhất tháng 10/2026",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="mes_downtime_lines",
        ),
        GoldenCase(
            case_id="mes_ng_oct2026",
            question="Top 5 mã hàng bị lỗi NG nhiều nhất tháng 10/2026",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="mes_ng_defects",
        ),
        GoldenCase(
            case_id="iqc_oct2026",
            question="Thống kê kiểm tra IQC trong tháng 10/2026 theo kết quả QC",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="qc_iqc_lines",
        ),
        GoldenCase(
            case_id="bom_qc7",
            question="Cấu trúc BOM và loại nhựa của mã QC7-5146-000 tính đến ngày 20/10/2026",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "empty"),
            expected_tools=("query_bom_structure",),
        ),
        GoldenCase(
            case_id="price_moq_qc7",
            question="Bảng giá và MOQ của mã QC7-5146-000 tính đến ngày 20/10/2026",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "empty"),
            expected_tools=("query_price_list",),
        ),
        GoldenCase(
            case_id="forbidden_unmapped_user",
            question="Tra phiếu xuất bán QC7-5146-000 từ 2026-10-01 đến 2026-10-02",
            history=(),
            user={"id": "mallory"},
            expected_statuses=("forbidden",),
        ),
        GoldenCase(
            case_id="mold_fcst_k425",
            question="Khuôn K_425-00107-V2 còn chạy được khoảng bao nhiêu tháng nữa dựa theo FCST của mã 425-00107-2?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="mold_cavity_specs",
        ),
        GoldenCase(
            case_id="gl_131_kh0034_oct2026",
            question="Tổng công nợ phải thu tài khoản 131 của khách KH0034 cuối tháng 10/2026 là bao nhiêu?",
            history=(),
            user=user_ok,
            expected_statuses=("empty",),
            expected_tools=("query_semantic_plan",),
            expected_dataset="gl_account_movements",
            must_contain_any=("2024-09-06",),
        ),
    ]


def build_random_cases() -> list[GoldenCase]:
    """Cross-module random natural-language eval covering the 40-contract ERP/MES map."""
    user_ok = {"id": "golden-eval"}
    return [
        GoldenCase(
            case_id="rand_to2_canon_oct2026",
            question="Trong tháng 10/2026, khách hàng Canon có bao nhiêu lệnh giao hàng (TO2) và tổng số lượng giao là bao nhiêu?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="sales_delivery_orders",
        ),
        GoldenCase(
            case_id="rand_sq1_quotations_oct2026",
            question="Thống kê giấy báo giá bán (SQ1) trong tháng 10/2026 theo khách hàng và giá trị.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="sales_quotations",
        ),
        GoldenCase(
            case_id="rand_hdf_returns_2026",
            question="Trong tháng 10/2026 có bao nhiêu hàng bán bị trả lại (HDF) theo từng khách hàng?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial", "empty"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="sales_returns",
        ),
        GoldenCase(
            case_id="rand_bg0_supplier_quotes_oct2026",
            question="Tổng hợp báo giá nhà cung cấp (BG0) phát sinh trong tháng 10/2026 theo từng nhà cung cấp.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="supplier_quotations",
        ),
        GoldenCase(
            case_id="rand_purchase_price_top",
            question="Liệt kê 10 vật tư có đơn giá trong bảng giá mua nhà cung cấp hiện hành.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="purchase_prices_current",
        ),
        GoldenCase(
            case_id="rand_sales_price_canon",
            question="Tra danh mục bảng giá bán tổng hợp đang áp dụng cho khách hàng Canon.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="sales_prices_current",
        ),
        GoldenCase(
            case_id="rand_pending_po_top_suppliers",
            question="Top 5 nhà cung cấp đang có số lượng PO pending linh kiện và nhựa chờ giao nhiều nhất hiện nay là những ai?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="planning_pending_po",
        ),
        GoldenCase(
            case_id="rand_stock_lots_top_warehouses",
            question="Thống kê tồn kho hiện hành theo từng kho và đơn vị tính trong hệ thống lô/vị trí kho.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="inventory_stock_lots",
        ),
        GoldenCase(
            case_id="rand_warehouse_transfer_oct2026",
            question="Trong tháng 10/2026, tổng số lượng hàng điều chuyển kho (PXB/PNF) giữa các kho xuất và kho nhận là bao nhiêu?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="warehouse_transfers",
        ),
        GoldenCase(
            case_id="rand_pxa_internal_issue_oct2026",
            question="Tổng hợp phiếu xuất kho nội bộ (PXA) trong tháng 10/2026 theo từng kho xuất.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="warehouse_internal_issues",
        ),
        GoldenCase(
            case_id="rand_pnd_internal_receipt_oct2026",
            question="Tổng hợp phiếu nhập kho nội bộ (PND) trong tháng 10/2026 theo từng kho nhận.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="warehouse_internal_receipts",
        ),
        GoldenCase(
            case_id="rand_warehouse_requests_oct2026",
            question="Thống kê phiếu yêu cầu nhập kho và yêu cầu xuất kho (DNV/DXV) trong tháng 10/2026.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="warehouse_requests",
        ),
        GoldenCase(
            case_id="rand_planning_stock_snapshot",
            question="Ảnh chụp tồn kho KHSX hiện tại theo phân loại Nhựa, Linh kiện, Kho OK và Kho NG gồm bao nhiêu dòng và tổng số lượng?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="planning_stock_snapshot",
        ),
        GoldenCase(
            case_id="rand_pd1_production_orders_oct2026",
            question="Tổng hợp lệnh sản xuất ERP (PD1) tháng 10/2026 theo phân xưởng và tổng số lượng kế hoạch.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="production_orders",
        ),
        GoldenCase(
            case_id="rand_bom_reverse_lookup",
            question="Theo định mức cấu trúc BOM hiện hành, Top 5 nguyên vật liệu xuất hiện trong nhiều cấu trúc sản phẩm nhất là mã nào?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="bom_materials",
        ),
        GoldenCase(
            case_id="rand_ecn_bom_changes",
            question="Thống kê lịch sử cập nhật BOM và phiếu ECN kỹ thuật theo loại thay đổi.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="ecn_and_bom_changes",
        ),
        GoldenCase(
            case_id="rand_mes_setup_mold_oct2026",
            question="Trong tháng 10/2026, thống kê số lượt setup máy và vận hành lên/xuống khuôn theo từng máy ép.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="mes_setup_and_mold_ops",
        ),
        GoldenCase(
            case_id="rand_mes_operators_oct2026",
            question="Top 5 nhân sự đứng máy có sản lượng thực hiện cao nhất trong tháng 10/2026 là những ai?",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="mes_operators_output",
        ),
        GoldenCase(
            case_id="rand_mes_carton_packing_oct2026",
            question="Thống kê sản lượng đóng thùng thành phẩm MES trong tháng 10/2026 theo trạm sản xuất.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="mes_carton_packing",
        ),
        GoldenCase(
            case_id="rand_mes_scheduling_oct2026",
            question="Tổng hợp lịch điều độ sản xuất theo máy trong tháng 10/2026 với tổng số lượng kế hoạch và số lệnh WO.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="mes_scheduling_plan",
        ),
        GoldenCase(
            case_id="rand_qc_pqc_summary",
            question="Thống kê tổng số phiếu kiểm tra chất lượng công đoạn PQC theo trạng thái kết quả.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="qc_pqc_lines",
        ),
        GoldenCase(
            case_id="rand_mold_incident_summary",
            question="Tổng hợp tình trạng sự cố khuôn và bảo dưỡng khuôn hiện nay theo loại sự cố và trạng thái.",
            history=(),
            user=user_ok,
            expected_statuses=("answered", "partial"),
            expected_tools=("query_semantic_plan",),
            expected_dataset="mold_incident_status",
        ),
    ]


async def _run_dry_eval(cases: list[GoldenCase]) -> list[dict[str, Any]]:
    cfg = json.loads((ROOT / "config/erp-agent.json").read_text())
    all_reports = [r["id"] for r in cfg["reports"]]
    all_datasets = list(cfg["semantic_contracts"])
    grants = {"golden-eval": {"erp_user_id": 11, "reports": all_reports, "semantic_datasets": all_datasets}}

    async def dry_db(sql, params, limits):
        if "FROM (" in sql and "AS scoped_dataset" in sql:
            # Parse SELECT col AS "alias" list from compiled semantic query for synthetic dry-run.
            import re
            head = sql.split(" FROM ", 1)[0]
            aliases = re.findall(r'AS "([^"]+)"', head)
            if "2026-08-13" in str(params) or "public.ct00" in sql:
                return []
            row = {}
            numeric_cols = {
                m for c in cfg["semantic_contracts"].values() for m in (c.get("metrics") or {})
            } | {"quantity", "revenue_vnd", "amount_vnd", "oee_pct", "stop_minutes", "ng_qty", "lot_qty", "ok_qty", "cavity", "cycle_sec", "total_shots", "pr_count", "po_count", "stop_count", "defect_events", "inspection_count", "line_count"}
            for col in aliases:
                if col == "__total_rows":
                    row[col] = 1
                elif col in ("unit",):
                    row[col] = "PCS"
                elif col in ("currency",):
                    row[col] = "VND"
                elif col in ("day", "delivery_date", "expiry_date", "mfg_date", "valid_from", "valid_to", "last_maint_date", "required_date", "confirmed_delivery_date"):
                    row[col] = "2026-10-15"
                elif col in numeric_cols:
                    row[col] = 10
                else:
                    row[col] = f"SYNTH-{col}"
            return [row]
        if "dmkh" in sql and "userinfo" in sql:
            return [{"loai_ho_so": "Nhân viên (DMKH)", "ma_nv": "HP2843", "ten_nv": "Nguyễn Bá Thành", "ma_bp": "NHOM-IT", "chuc_vu": "", "trang_thai": "1", "total_lines": 1}]
        if "ph81" in sql or "ct81" in sql:
            return [{"stt_rec": "R1", "ln": 1, "ma_vt": "QC7-5146-000", "so_luong": 89100, "tien2": 170992972, "total_lines": 322, "total_quantity": 89100, "total_revenue": 170992972}]
        if "mfbom" in sql:
            return [{"ma_sp_me": "QC7-5146-000", "bom_code": "BOM-1", "bom_version": "1", "status": "1", "material_code": "NHUA-1", "ten_vt": "ABS", "sl_dinh_muc": 1.2, "dvt": "KG", "total_lines": 1}]
        if "dmbanggia" in sql:
            return [{"ma_kh": "KH0015", "ten_kh": "Khách test", "ma_vt": "QC7-5146-000", "ten_vt": "SP test", "sl_min": 100, "dvt": "PCS", "gia0": 1000, "gia": 1000, "ma_nt": "VND", "ngay_bd": "2026-01-01", "ngay_kt": "2026-12-31", "status": "1", "total_lines": 1}]
        return [{"ma_vt": "QC7-5146-000", "ma_kho": "KHOTP01", "so_luong_ton": 100, "total_lines": 1}]

    backend = ReportBackend(ROOT, cfg, grants, dry_db)
    results = []
    for case in cases:
        t0 = time.monotonic()

        async def mock_model(messages, specs):
            if messages[-1]["role"] == "tool":
                res = json.loads(messages[-1]["content"])
                sids = [s["id"] for s in res.get("sources", [])][:2]
                return {"content": json.dumps({"answer": "Đã tra cứu theo bộ lọc.", "source_ids": sids})}
            if case.case_id == "sales_revenue_missing_period":
                return {"content": json.dumps({"answer": "Vui lòng cho biết khoảng ngày hoặc tháng cần thống kê.", "source_ids": []})}
            if "employee" in case.case_id or "ba_thanh_2026" in case.case_id or "followup" in case.case_id:
                return {"tool_calls": [{"id": "c1", "type": "function", "function": {"name": "query_semantic_plan", "arguments": json.dumps({"dataset": "purchase_requests", "dimensions": ["pr_no", "unit"], "metrics": ["quantity"], "filters": [{"field": "day", "op": "eq", "value": "2026-08-13"}]})}}]}
            if case.expected_dataset:
                ds = case.expected_dataset
                c = cfg["semantic_contracts"][ds]
                dim = next(d for d in c["dimensions"] if d not in ("day", "unit", "currency"))
                metric = next(iter(c["metrics"]))
                filters = [{"field": "day", "op": "gte", "value": "2026-10-01"}, {"field": "day", "op": "lte", "value": "2026-10-31"}] if c.get("require_bounded_date", True) else []
                if ds == "purchase_requests":
                    filters = [{"field": "day", "op": "gte", "value": "2026-08-01"}, {"field": "day", "op": "lte", "value": "2026-08-31"}]
                    dim = "pr_no"
                return {"tool_calls": [{"id": "c1", "type": "function", "function": {"name": "query_semantic_plan", "arguments": json.dumps({"dataset": ds, "dimensions": [dim], "metrics": [metric], "filters": filters, "limit": 5})}}]}
            tool = case.expected_tools[0] if case.expected_tools else "query_inventory_by_warehouse"
            args = {"material": "QC7-5146-000", "date_as_of": "2026-10-20"}
            if tool in ("query_allowed_records",):
                args = {"report_id": "sales_lines", "material": "QC7-5146-000", "date_from": "2026-10-01", "date_to": "2026-10-20"}
            return {"tool_calls": [{"id": "c1", "type": "function", "function": {"name": tool, "arguments": json.dumps(args)}}]}

        res = await run_agent(case.question, user=case.user, model=mock_model, backend=backend, limits=Limits(**cfg["limits"]), history=list(case.history))
        passed = res["status"] in case.expected_statuses
        results.append({"case": case.case_id, "status": res["status"], "passed": passed, "latency_ms": round((time.monotonic() - t0) * 1000)})
    return results


async def _run_live_eval(cases: list[GoldenCase], model_name: str, model_url: str) -> list[dict[str, Any]]:
    import httpx
    import psycopg
    from psycopg.rows import dict_row
    from erp_ai.agent_runtime import _resolve_dsn, query as erp_query

    _load_env_defaults()
    dsn = _resolve_dsn()
    if not dsn:
        raise RuntimeError("Missing HTMP_AGENT_DB_DSN or HTMP_DB_* configuration for --live mode")
    cfg = json.loads((ROOT / "config/erp-agent.json").read_text())
    all_reports = [r["id"] for r in cfg["reports"]]
    all_datasets = [k for k, v in cfg["semantic_contracts"].items() if isinstance(v, dict) and v.get("status") == "approved"]
    grants = {"golden-eval": {"erp_user_id": 11, "reports": all_reports, "semantic_datasets": all_datasets}}
    backend = ReportBackend(ROOT, cfg, grants, erp_query)
    key = os.getenv("VLLM_API_KEY", "")
    results = []

    async with httpx.AsyncClient(base_url=model_url.rstrip("/") + "/", headers={"Authorization": "Bearer " + key}, timeout=120.0, trust_env=False) as client:
        transport = QwenClient(client, model_name)
        for case in cases:
            t0 = time.monotonic()
            res = await run_agent(
                case.question,
                user=case.user,
                model=transport,
                backend=backend,
                limits=Limits(**cfg["limits"]),
                history=list(case.history),
            )
            elapsed = round((time.monotonic() - t0) * 1000)
            reasons = []
            if res["status"] not in case.expected_statuses:
                reasons.append(f"unexpected status={res['status']} expected={case.expected_statuses}")
            used_tools = [v["tool"] for v in res.get("verified_results") or []]
            if case.expected_tools and not any(t in used_tools for t in case.expected_tools):
                reasons.append(f"expected tool in {case.expected_tools}, got {used_tools}")
            if case.expected_dataset:
                ds_used = [v["result"].get("contract_id") for v in res.get("verified_results") or [] if v["tool"] == "query_semantic_plan"]
                if case.expected_dataset not in ds_used:
                    reasons.append(f"expected dataset {case.expected_dataset}, got {ds_used}")
            ans = (res.get("display_markdown") or "") + " " + (res.get("answer") or "")
            if any("\u4e00" <= ch <= "\u9fff" for ch in ans):
                reasons.append("cjk_leaked")
            for bad in case.must_not_contain:
                if bad.lower() in ans.lower():
                    reasons.append(f"forbidden_text:{bad}")
            if case.must_contain_any and not any(good.lower() in ans.lower() for good in case.must_contain_any):
                reasons.append(f"missing_any:{case.must_contain_any}")
            if case.reconcile_sql and case.reconcile_check and not reasons:
                try:
                    async with await psycopg.AsyncConnection.connect(dsn, connect_timeout=10, row_factory=dict_row) as conn:
                        async with conn.cursor() as cur:
                            await cur.execute("SET TRANSACTION READ ONLY")
                            await cur.execute("SELECT set_config('statement_timeout', '10000', true)")
                            await cur.execute(case.reconcile_sql)
                            db_rows = await cur.fetchall()
                    ok, note = case.reconcile_check(res, db_rows)
                    if not ok:
                        reasons.append(f"reconcile_failed({note})")
                except Exception as exc:
                    reasons.append(f"reconcile_error:{exc.__class__.__name__}")
            item = {
                "case": case.case_id,
                "status": res["status"],
                "tools": used_tools,
                "tool_errors": res["metrics"]["tool_errors"],
                "passed": not reasons,
                "reasons": reasons,
                "latency_ms": elapsed,
            }
            print(json.dumps(item, ensure_ascii=False), flush=True)
            results.append(item)
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--live", action="store_true")
    parser.add_argument("--model", default=os.getenv("HTMP_AGENT_MODEL", "qwen2.5-14b"))
    parser.add_argument("--model-url", default=os.getenv("HTMP_AGENT_MODEL_URL", "http://127.0.0.1:8000/v1/"))
    parser.add_argument("--min-pass-rate", type=float, default=0.85)
    parser.add_argument("--suite", choices=("golden", "random", "all"), default="golden")
    args = parser.parse_args()

    if args.suite == "golden":
        cases = build_golden_cases()
    elif args.suite == "random":
        cases = build_random_cases()
    else:
        cases = build_golden_cases() + build_random_cases()
    results = asyncio.run(_run_dry_eval(cases) if args.dry_run else _run_live_eval(cases, args.model, args.model_url))
    latencies = sorted(r["latency_ms"] for r in results) or [0]
    passed = sum(1 for r in results if r["passed"])
    pass_rate = passed / len(results) if results else 0.0
    summary = {
        "mode": "dry-run" if args.dry_run else "live",
        "model": args.model,
        "total": len(results),
        "passed": passed,
        "pass_rate": round(pass_rate, 3),
        "p50_ms": latencies[math.ceil(len(latencies) * 0.5) - 1],
        "p95_ms": latencies[math.ceil(len(latencies) * 0.95) - 1],
    }
    print(json.dumps({"summary": summary}, ensure_ascii=False))
    return 0 if pass_rate >= args.min_pass_rate else 1


if __name__ == "__main__":
    raise SystemExit(main())
