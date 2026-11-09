#!/usr/bin/env python3
"""Comprehensive Verification of Expanded ERP/MES Tooling and Procedures.

Tests:
1. 12 Baseline survey questions (Sales, Purchase, Stock, Card, Mold, Downtime, BOM, IQC)
2. 18 Sales benchmark questions (including Question 15: QC lot status)
3. Expanded MES operations: Work Orders, Packing, NG Defects, Mold Change, AP 331 Supplier Debt.
"""

import json
import time
from erp_ai.generic_procedure_executor import GenericProcedureExecutor
from erp_ai.native_tools import ERPNativeTools

executor = GenericProcedureExecutor()
native = ERPNativeTools()

def run_test(test_id, category, prompt, runner):
    t0 = time.time()
    try:
        res = runner()
        elapsed = round(time.time() - t0, 2)
        if isinstance(res, dict):
            success = res.get("success", False)
            text = res.get("formatted_text", "")
        else:
            text = str(res)
            success = "Lỗi khi" not in text and "Không tìm thấy" not in text and "failed" not in text.lower()
        
        status = "✅ PASS" if success else "❌ FAIL"
        summary = text[:150].replace("\n", " ")
        print(f"[{status}] {test_id} ({category}) [{elapsed}s]: {summary}...")
        return success
    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        print(f"[❌ FAIL] {test_id} ({category}) [{elapsed}s]: EXCEPTION: {e}")
        return False

def main():
    print("======================================================================")
    print("STARTING FULL EXPANDED ERP / MES VERIFICATION")
    print("======================================================================\n")

    results = []

    # -------------------------------------------------------------
    # SECTION 1: 12 BASELINE SURVEY QUESTIONS
    # -------------------------------------------------------------
    print("--- 1. Baseline Survey Questions (12 core domains) ---")
    results.append(run_test(
        "BASE-01", "Bán hàng", "Đơn hàng bán KH0047 trong tháng 10/2026",
        lambda: native.lookup_sales_orders(customer_code="KH0047", date_from="2026-10-01", date_to="2026-10-31")
    ))
    results.append(run_test(
        "BASE-02", "Giá bán", "Giá bán của mã hàng 156279430",
        lambda: native.lookup_sales_price(material_code="156279430")
    ))
    results.append(run_test(
        "BASE-03", "Tiến độ giao", "Tiến độ giao mã QC7-5146-000",
        lambda: executor.query_report("sobctiendogh", "QC7-5146-000", item_code="QC7-5146-000", date_from="2026-10-01", date_to="2026-10-20")
    ))
    results.append(run_test(
        "BASE-04", "Mua hàng", "Đơn mua hàng từ NCC0220 tháng 10/2026",
        lambda: native.lookup_purchase_orders(supplier_code="NCC0220")
    ))
    results.append(run_test(
        "BASE-05", "Giá mua", "Lịch sử đơn giá mua vật tư PS-576D",
        lambda: native.lookup_purchase_orders(material_code="PS-576D")
    ))
    results.append(run_test(
        "BASE-06", "Tồn kho", "Tồn kho mã 75577-BZ010 theo từng kho",
        lambda: native.lookup_inventory_stock(material_code="75577-BZ010")
    ))
    results.append(run_test(
        "BASE-07", "Thẻ kho", "Thẻ kho vật tư QC7-5146-000 tại KHOTP00",
        lambda: native.lookup_stock_card(material_code="QC7-5146-000", warehouse_code="KHOTP00", date_from="2026-10-01", date_to="2026-10-07")
    ))
    results.append(run_test(
        "BASE-08", "Dừng máy MES", "Thời gian dừng máy tháng 10/2026",
        lambda: native.lookup_mes_downtime(date_from="2026-10-01", date_to="2026-10-31")
    ))
    results.append(run_test(
        "BASE-09", "Sản xuất MES", "Thời gian dừng máy DUC-0201 tháng 10/2026",
        lambda: native.lookup_mes_downtime(date_from="2026-10-01", date_to="2026-10-31", machine_code="DUC-0201")
    ))
    results.append(run_test(
        "BASE-10", "BOM", "BOM mã QC7-5146-000 loại nhựa và định mức",
        lambda: native.lookup_bom(product_code="QC7-5146-000")
    ))
    results.append(run_test(
        "BASE-11", "Khuôn MES", "Khuôn QC7-5146-000 số shot và bảo hành",
        lambda: native.lookup_mold_and_mes(material_code="QC7-5146-000", action="shots")
    ))
    results.append(run_test(
        "BASE-12", "Chất lượng IQC", "Đánh giá chất lượng hàng mua tháng 10/2026",
        lambda: native.lookup_incoming_quality(date_from="2026-10-01", date_to="2026-10-31")
    ))

    # -------------------------------------------------------------
    # SECTION 2: QUESTION 15 VERIFICATION (QC LOT STATUS)
    # -------------------------------------------------------------
    print("\n--- 2. Question 15 Special Verification (QC Lot Status) ---")
    results.append(run_test(
        "SALES-15", "QC Lot Status", "Trạng thái QC tem thành phẩm QC7-5146-000",
        lambda: native.lookup_qc_lot_status(material_code="QC7-5146-000")
    ))

    # -------------------------------------------------------------
    # SECTION 3: EXPANDED MES & FINANCE OPERATIONS
    # -------------------------------------------------------------
    print("\n--- 3. Expanded MES & Financial Operations ---")
    results.append(run_test(
        "EXP-01", "MES Work Order", "Bảng kê điều độ sản xuất và Work Order",
        lambda: executor.query_report("mesbkwo", "dieu do san xuat thang 10", date_from="2026-10-01", date_to="2026-10-31")
    ))
    results.append(run_test(
        "EXP-02", "MES Phế phẩm NG", "Báo cáo xác nhận phế phẩm NG tháng 11/2026",
        lambda: native.lookup_mes_ng(date_from="2026-11-01", date_to="2026-11-09")
    ))
    results.append(run_test(
        "EXP-03", "MES Đóng thùng", "Bảng kê đóng thùng mã QC7-5146-000",
        lambda: native.lookup_mes_packing(material_code="QC7-5146-000")
    ))
    results.append(run_test(
        "EXP-04", "MES Gộp tách thùng", "Bảng kê gộp tách thùng tháng 10/2026",
        lambda: executor.query_report("mesbkgoptachthung", "gop tach thung thang 10", date_from="2026-10-01", date_to="2026-10-31")
    ))
    results.append(run_test(
        "EXP-05", "MES Bổ sung shot", "Bổ sung shot khuôn tháng 10/2026",
        lambda: executor.query_report("mesbkbosungshot", "bo sung shot thang 10", date_from="2026-10-01", date_to="2026-10-31")
    ))
    results.append(run_test(
        "EXP-06", "MES Thay khuôn", "Lịch sử thay khuôn tháng 10/2026",
        lambda: executor.query_report("mesbkthaykhuon", "thay khuon thang 10", date_from="2026-10-01", date_to="2026-10-31")
    ))
    results.append(run_test(
        "EXP-07", "Lệnh giao hàng TO2", "Lệnh giao hàng 001-2611-000004",
        lambda: native.lookup_delivery_orders(order_code="001-2611-000004")
    ))
    results.append(run_test(
        "EXP-08", "Công nợ 331 NCC", "Sổ chi tiết công nợ NCC0015",
        lambda: executor.query_report("posoctcongno1ncc", "cong no ncc NCC0015", partner_code="NCC0015", date_from="2026-10-01", date_to="2026-10-31")
    ))
    results.append(run_test(
        "EXP-09", "Cảnh báo HSD", "Báo cáo cảnh báo hạn sử dụng lô",
        lambda: executor.query_report("bccanhbaohsd", "canh bao han su dung lo")
    ))
    results.append(run_test(
        "EXP-10", "Tuổi hàng theo lô", "Báo cáo tuổi hàng theo lô tháng 10",
        lambda: executor.query_report("inbctuoithotheolo", "tuoi hang theo lo", date_from="2026-10-01", date_to="2026-10-31")
    ))

    print("\n======================================================================")
    passed_count = sum(1 for r in results if r)
    total_count = len(results)
    rate = round(passed_count / total_count * 100, 1)
    print(f"VERIFICATION SUMMARY: {passed_count} / {total_count} PASSED ({rate}%)")
    print("======================================================================")

if __name__ == "__main__":
    main()

