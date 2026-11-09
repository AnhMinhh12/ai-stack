#!/usr/bin/env python3
"""Comprehensive Enterprise Verification Suite across all 8 Fast ERP 3S & MES functional departments:
1. KHO (IN)
2. BAN_HANG (SO)
3. MUA_HANG (PO)
4. KE_TOAN (GL & AR/AP)
5. SAN_XUAT (MES)
6. KE_HOACH (MF)
7. CHAT_LUONG (QC)
8. KHUON_THIET_BI (VS)
"""

import sys
import time
from typing import Callable, Tuple

from erp_ai.generic_procedure_executor import GenericProcedureExecutor
from erp_ai.native_tools import ERPNativeTools

executor = GenericProcedureExecutor()
native = ERPNativeTools()

tests = [
    # -------------------------------------------------------------
    # 1. KHO (IN)
    # -------------------------------------------------------------
    (
        "KHO-01", "Vị trí tồn kho tại máy & kệ (Bùi Thị Mai Incident 1)",
        lambda: native.lookup_inventory_stock(material_code="0591TMANCHORBASE-V3", date_as_of="2026-11-09"),
        lambda out: "DUC-0230" in out or "BAE1-12" in out or "2,850" in out or "2850" in out or "DUC" in out
    ),
    (
        "KHO-02", "Tồn kho theo từng kho",
        lambda: native.lookup_inventory_stock(material_code="75577-BZ010", date_as_of="2026-11-09"),
        lambda out: "KHOTP00" in out or "75577-BZ010" in out
    ),
    (
        "KHO-03", "Tổng hợp Nhập - Xuất - Tồn kho (inbcthnxt)",
        lambda: executor.query_report(report_type="inbcthnxt", item_code="QC7-5146-000", date_from="2026-10-01", date_to="2026-10-10"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "KHO-04", "Thẻ kho chi tiết biến động vật tư (inso1)",
        lambda: executor.query_report(report_type="inso1", item_code="QC7-5146-000", warehouse_code="KHOTP00", date_from="2026-10-01", date_to="2026-10-07"),
        lambda out: out.get("success") and "QC7-5146-000" in out.get("formatted_text", "")
    ),
    (
        "KHO-05", "Kiểm soát tồn kho theo lô (inbckstonkholo)",
        lambda: executor.query_report(report_type="inbckstonkholo", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success")
    ),
    (
        "KHO-06", "Trạng thái kho & sức chứa vị trí (inbctrangthaikho)",
        lambda: executor.query_report(report_type="inbctrangthaikho", warehouse_code="KHOTP00"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),

    # -------------------------------------------------------------
    # 2. BÁN HÀNG (SO)
    # -------------------------------------------------------------
    (
        "SO-01", "Bảng kê đơn hàng bán (sobkdonhang)",
        lambda: executor.query_report(report_type="sobkdonhang", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "SO-02", "Bảng giá bán sản phẩm (dmbanggiact)",
        lambda: executor.query_report(report_type="dmbanggiact", item_code="156279430"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "SO-03", "Tiến độ giao hàng bán (sobctiendogh)",
        lambda: executor.query_report(report_type="sobctiendogh", partner_code="KH0001", date_from="2026-10-01", date_to="2026-10-20"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "SO-04", "Lệnh giao hàng TO2 (sobklenhgiaohang)",
        lambda: executor.query_report(report_type="sobklenhgiaohang", query="001-2611-000004"),
        lambda out: out.get("success") and "001-2611-000004" in out.get("formatted_text", "")
    ),
    (
        "SO-05", "Dự báo tiêu thụ Forecast (sobkdubaotieuthu)",
        lambda: executor.query_report(report_type="sobkdubaotieuthu", date_from="2026-01-01", date_to="2026-12-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),

    # -------------------------------------------------------------
    # 3. MUA HÀNG (PO)
    # -------------------------------------------------------------
    (
        "PO-01", "Giá mua NCC hạt nhựa ABS-260 (Bùi Thị Mai Incident 2)",
        lambda: native.lookup_sales_price(material_code="ABS-260"),
        lambda out: "50,244" in out or "50244" in out or "TOYO INK" in out
    ),
    (
        "PO-02", "Danh mục giá mua NCC từ bảng dmgiamuact",
        lambda: executor.query_report(report_type="dmgiamuact", item_code="ABS-260"),
        lambda out: out.get("success") and ("50,244" in out.get("formatted_text", "") or "TOYO INK" in out.get("formatted_text", ""))
    ),
    (
        "PO-03", "Bảng kê đơn đặt mua hàng PO (pobkdonhang)",
        lambda: executor.query_report(report_type="pobkdonhang", partner_code="NCC0220", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "PO-04", "Lịch sử biến động giá mua NCC (pobclsgia)",
        lambda: executor.query_report(report_type="pobclsgia", item_code="PS-576D"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "PO-05", "Tổng hợp hàng nhập mua theo NCC (pothnhap)",
        lambda: executor.query_report(report_type="pothnhap", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),

    # -------------------------------------------------------------
    # 4. KẾ TOÁN (GL & AR/AP)
    # -------------------------------------------------------------
    (
        "GL-01", "Sổ cái tài khoản kế toán TK 1521 (glso1)",
        lambda: executor.query_report(report_type="glso1", account_code="1521", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "GL-02", "Bảng cân đối số phát sinh Trial Balance (glbccdsp)",
        lambda: executor.query_report(report_type="glbccdsp", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "GL-03", "Báo cáo tập hợp chi phí SXKD dở dang & quản lý (glbcchiphi)",
        lambda: executor.query_report(report_type="glbcchiphi", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "GL-04", "Sổ chi tiết công nợ phải trả NCC TK 331 (posoctcongno1ncc)",
        lambda: executor.query_report(report_type="posoctcongno1ncc", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and "331" in out.get("formatted_text", "")
    ),

    # -------------------------------------------------------------
    # 5. SẢN XUẤT (MES)
    # -------------------------------------------------------------
    (
        "MES-01", "Điều độ sản xuất & Work Order (mesbkwo)",
        lambda: executor.query_report(report_type="mesbkwo", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "MES-02", "Hiệu suất thiết bị toàn phần OEE (mesbcoee)",
        lambda: executor.query_report(report_type="mesbcoee", query="DC-01", date_from="2026-10-01", date_to="2026-10-05"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "MES-03", "Đóng thùng thành phẩm MES (mesbkdongthung)",
        lambda: executor.query_report(report_type="mesbkdongthung", item_code="QC7-5146-000"),
        lambda out: out.get("success") and "QC7-5146-000" in out.get("formatted_text", "")
    ),
    (
        "MES-04", "Bổ sung hoặc bỏ shot khuôn (mesbkbosungshot)",
        lambda: executor.query_report(report_type="mesbkbosungshot", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success")
    ),
    (
        "MES-05", "Lịch sử các lần thay khuôn sản xuất (mesbkthaykhuon)",
        lambda: executor.query_report(report_type="mesbkthaykhuon", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "MES-06", "Báo cáo thời gian dừng máy downtime theo nguyên nhân",
        lambda: native.lookup_mes_downtime(date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: "Dừng máy" in out or "DUC" in out
    ),

    # -------------------------------------------------------------
    # 6. KẾ HOẠCH & ĐỊNH MỨC (MF)
    # -------------------------------------------------------------
    (
        "MF-01", "Cấu trúc định mức sản phẩm BOM (lookup_bom)",
        lambda: native.lookup_bom(product_code="QC7-5146-000"),
        lambda out: "QC7-5146-000" in out and "BOM" in out
    ),
    (
        "MF-02", "Bảng kê lệnh sản xuất LSX (mfbklsx)",
        lambda: executor.query_report(report_type="mfbklsx", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "MF-03", "Thống kê sản xuất theo kỳ (mfbkthongke)",
        lambda: executor.query_report(report_type="mfbkthongke", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "MF-04", "Tiêu hao NVL theo lệnh sản xuất (mfbctieuhaonvltheolsx)",
        lambda: executor.query_report(report_type="mfbctieuhaonvltheolsx", date_from="2026-10-01", date_to="2026-10-02"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "MF-05", "Tổng hợp nhập xuất tồn công đoạn sản xuất (mfbcthnxtcd)",
        lambda: executor.query_report(report_type="mfbcthnxtcd", date_from="2026-10-01", date_to="2026-10-02"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),

    # -------------------------------------------------------------
    # 7. CHẤT LƯỢNG (QC)
    # -------------------------------------------------------------
    (
        "QC-01", "Đánh giá chất lượng hàng mua đầu vào IQC",
        lambda: native.lookup_incoming_quality(date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: "IQC" in out
    ),
    (
        "QC-02", "Chi tiết các biên bản phiếu kiểm tra IQC (qcbkiqcipqc)",
        lambda: executor.query_report(report_type="qcbkiqcipqc", date_from="2026-10-01", date_to="2026-10-31"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "QC-03", "Kiểm tra trạng thái QC tem thành phẩm OK/NG/Khóa",
        lambda: native.lookup_qc_lot_status(material_code="QC7-5146-000"),
        lambda out: "QC7-5146-000" in out and "tem" in out
    ),
    (
        "QC-04", "Phế phẩm và lỗi sản xuất NG (MES)",
        lambda: native.lookup_mes_ng(date_from="2026-11-01", date_to="2026-11-09"),
        lambda out: "NG" in out or "phế phẩm" in out.lower()
    ),
    (
        "QC-05", "Tổng hợp lỗi chỉ tiêu nguyên vật liệu (qcbcthloinvl)",
        lambda: executor.query_report(report_type="qcbcthloinvl", date_from="2026-10-01", date_to="2026-10-05"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),

    # -------------------------------------------------------------
    # 8. KHUÔN MẪU & THIẾT BỊ (VS)
    # -------------------------------------------------------------
    (
        "VS-01", "Hồ sơ khuôn mẫu & số shot dập thực tế",
        lambda: native.lookup_mold_and_mes(mold_code="K_QC5-2919-000-V1"),
        lambda out: "K_QC5-2919-000-V1" in out and "shot" in out
    ),
    (
        "VS-02", "Danh mục hồ sơ kỹ thuật khuôn (dmhosokhuon)",
        lambda: executor.query_report(report_type="dmhosokhuon"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "VS-03", "Lịch sử bảo trì và sửa chữa khuôn mẫu (dmhosokhuonsc)",
        lambda: executor.query_report(report_type="dmhosokhuonsc"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
    (
        "VS-04", "Cảnh báo bảo dưỡng khuôn định kỳ (mesbcttdskhuon)",
        lambda: executor.query_report(report_type="mesbcttdskhuon"),
        lambda out: out.get("success") and out.get("row_count", 0) > 0
    ),
]


def main():
    print("=" * 75)
    print("STARTING ENTERPRISE MULTI-DEPARTMENT VERIFICATION (STAGE 3)")
    print(f"Total Test Cases: {len(tests)} across all 8 functional departments")
    print("=" * 75)

    passed = 0
    failed = 0

    for code, desc, run_fn, check_fn in tests:
        t0 = time.time()
        try:
            res = run_fn()
            dur = round(time.time() - t0, 2)
            if check_fn(res):
                print(f"[✅ PASS] {code:7} ({desc}) [{dur}s]")
                passed += 1
            else:
                print(f"[❌ FAIL] {code:7} ({desc}) [{dur}s]: Check condition not met")
                if isinstance(res, dict):
                    print("   Output summary:", {k: v for k, v in res.items() if k != "formatted_text"})
                    print("   Sample text:", str(res.get("formatted_text", ""))[:200])
                else:
                    print("   Output text:", str(res)[:200])
                failed += 1
        except Exception as e:
            dur = round(time.time() - t0, 2)
            print(f"[❌ FAIL] {code:7} ({desc}) [{dur}s]: Exception {e}")
            failed += 1

    print("=" * 75)
    pct = round((passed / len(tests)) * 100, 1)
    print(f"ENTERPRISE VERIFICATION SUMMARY: {passed} / {len(tests)} PASSED ({pct}%)")
    print("=" * 75)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
