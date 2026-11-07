"""Test script for GenericProcedureExecutor."""

import sys
from erp_ai.generic_procedure_executor import GenericProcedureExecutor

def test_executor():
    executor = GenericProcedureExecutor()
    print("=== TEST 1: Sổ chi tiết công nợ KH0015 (sosoctcongno1kh) ===")
    res1 = executor.query_report(
        report_type="sosoctcongno1kh",
        query="Sổ chi tiết công nợ khách hàng KH0015 tháng 10/2026",
        partner_code="KH0015",
        date_from="2026-10-01",
        date_to="2026-10-31"
    )
    print("Success:", res1.get("success"))
    print("Output:\n", res1.get("formatted_text")[:500], "\n...\n")

    print("=== TEST 2: Tổng hợp nhập xuất tồn (inbcthnxt) ===")
    res2 = executor.query_report(
        report_type="inbcthnxt",
        query="Tổng hợp nhập xuất tồn kho tháng 10/2026 mã 003-M69-101-2",
        item_code="003-M69-101-2",
        date_from="2026-10-01",
        date_to="2026-10-31"
    )
    print("Success:", res2.get("success"))
    print("Output:\n", res2.get("formatted_text"), "\n")

    print("=== TEST 3: Bảng kê đơn hàng mua (pobkdonhang) ===")
    res3 = executor.query_report(
        report_type="pobkdonhang",
        query="Bảng kê đơn mua hàng trong tháng 10/2026",
        date_from="2026-10-01",
        date_to="2026-10-31"
    )
    print("Success:", res3.get("success"))
    print("Output:\n", res3.get("formatted_text")[:600], "\n...\n")

    print("=== TEST 4: Tự động nhận diện từ câu tự nhiên (Công nợ) ===")
    res4 = executor.query_report(
        query="Cho tôi sổ chi tiết công nợ của khách hàng KH0015 trong tháng 10/2026"
    )
    print("Success:", res4.get("success"))
    print("Report matched:", res4.get("report_id"))
    print("Output:\n", res4.get("formatted_text")[:400], "\n...\n")

    print("=== TEST 5: Tự động nhận diện từ câu tự nhiên (Nhập xuất tồn) ===")
    res5 = executor.query_report(
        query="Báo cáo tổng hợp xuất nhập tồn của mã 003-M69-101-2 từ 01/10/2026 đến 31/10/2026"
    )
    print("Success:", res5.get("success"))
    print("Report matched:", res5.get("report_id"))
    print("Output:\n", res5.get("formatted_text"), "\n")

if __name__ == "__main__":
    test_executor()

