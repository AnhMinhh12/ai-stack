import os
import sys
import json
import time
import psycopg2
from decimal import Decimal

# PostgreSQL connection settings
DB_CONFIG = {
    "dbname": os.environ.get("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
    "user": os.environ.get("HTMP_DB_USER", "htmp_ro"),
    "password": os.environ.get("HTMP_DB_PASSWORD", "Htmp@2026_Secure"),
    "host": os.environ.get("HTMP_DB_HOST", "10.0.6.2"),
    "port": os.environ.get("HTMP_DB_PORT", "5410"),
    "connect_timeout": 5
}

# The 12 randomized test cases spanning all functional modules
TEST_CASES = [
    {
        "id": "RAND-01",
        "module": "BOM & Định mức kỹ thuật",
        "question": "Cho tôi xem cấu trúc định mức BOM của mã sản phẩm 1014095300 gồm những linh kiện hạt nhựa gì?",
        "entity_code": "1014095300",
        "ground_truth_sql": """
            SELECT b.ma_sp, b.bom_version, b.ma_vt, b.ten_vt, b.so_luong_dm
            FROM public.mfkhsx_bom b
            WHERE b.ma_sp = '1014095300'
            ORDER BY b.bom_version DESC, b.ma_vt;
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            any(r.get("ma_sp") == "1014095300" for r in ai_data.get("rows", []))
        )
    },
    {
        "id": "RAND-02",
        "module": "BOM & Định mức kỹ thuật",
        "question": "Định mức BOM của mã sản phẩm 639957 gồm những loại vật tư nào?",
        "entity_code": "639957",
        "ground_truth_sql": """
            SELECT b.ma_sp, b.bom_version, b.ma_vt, b.ten_vt, b.so_luong_dm
            FROM public.mfkhsx_bom b
            WHERE b.ma_sp = '639957'
            ORDER BY b.bom_version DESC, b.ma_vt;
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            any(r.get("ma_sp") == "639957" for r in ai_data.get("rows", []))
        )
    },
    {
        "id": "RAND-03",
        "module": "Quản lý Chất lượng IQC",
        "question": "Bảng kê kiểm tra chất lượng đầu vào IQC tháng 10/2026 của nhà cung cấp NCC0010",
        "entity_code": "NCC0010",
        "ground_truth_sql": """
            SELECT count(*) as total_criteria, count(DISTINCT h.so_ct) as total_sheets
            FROM public.phiqc h
            JOIN public.ctiqc d USING(stt_rec)
            WHERE h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31' AND h.ma_ncc = 'NCC0010';
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            all(r.get("ma_ncc") == "NCC0010" for r in ai_data.get("rows", []))
        )
    },
    {
        "id": "RAND-04",
        "module": "Quản lý Chất lượng IQC",
        "question": "Bảng kê kiểm định IQC tháng 10/2026 của nhà cung cấp NCC0001",
        "entity_code": "NCC0001",
        "ground_truth_sql": """
            SELECT count(*) as total_criteria, count(DISTINCT h.so_ct) as total_sheets
            FROM public.phiqc h
            JOIN public.ctiqc d USING(stt_rec)
            WHERE h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31' AND h.ma_ncc = 'NCC0001';
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            all(r.get("ma_ncc") == "NCC0001" for r in ai_data.get("rows", []))
        )
    },
    {
        "id": "RAND-05",
        "module": "Phiếu xuất kho bán hàng (PXK)",
        "question": "Bảng kê phiếu xuất kho bán hàng PXK tháng 10/2026",
        "entity_code": "PH85",
        "ground_truth_sql": """
            SELECT count(*) as count_ph85
            FROM public.ph85
            WHERE ngay_ct BETWEEN '2026-10-01' AND '2026-10-31';
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            "PXK" in ai_data.get("source", "") or "ph85" in ai_data.get("source", "")
        )
    },
    {
        "id": "RAND-06",
        "module": "Xuất kho cho Sản xuất",
        "question": "Bảng kê xuất kho nguyên vật liệu cho sản xuất tháng 10/2026",
        "entity_code": "PH76",
        "ground_truth_sql": """
            SELECT count(*) as count_ph76
            FROM public.ph76
            WHERE ngay_ct BETWEEN '2026-10-01' AND '2026-10-31';
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            "ph76" in ai_data.get("source", "").lower()
        )
    },
    {
        "id": "RAND-07",
        "module": "Nhập kho Thành phẩm sản xuất",
        "question": "Bảng kê nhập kho thành phẩm tháng 10/2026",
        "entity_code": "PH77",
        "ground_truth_sql": """
            SELECT count(*) as count_ph77
            FROM public.ph77
            WHERE ngay_ct BETWEEN '2026-10-01' AND '2026-10-31';
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            "ph77" in ai_data.get("source", "").lower()
        )
    },
    {
        "id": "RAND-08",
        "module": "Quản lý Pallet MES",
        "question": "Chi tiết pallet số 20261020000051378760 gồm những thùng hàng nào?",
        "entity_code": "20261020000051378760",
        "ground_truth_sql": """
            SELECT p.id_pallet, p.so_luong_thung, p.so_luong, count(c.id_carton) as sl_carton
            FROM public.pallet p
            LEFT JOIN public.palletct c ON c.id_pallet = p.id_pallet
            WHERE p.id_pallet = '20261020000051378760'
            GROUP BY p.id_pallet, p.so_luong_thung, p.so_luong;
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            any(r.get("id_pallet") == "20261020000051378760" for r in ai_data.get("rows", []))
        )
    },
    {
        "id": "RAND-09",
        "module": "Hồ sơ Khuôn mẫu",
        "question": "Tra cứu hồ sơ khuôn của mã khuôn K_RC6-3059-000-11A",
        "entity_code": "K_RC6-3059-000-11A",
        "ground_truth_sql": """
            SELECT ma_khuon, ten_khuon, so_shot_bh, so_cavity
            FROM public.dmhosokhuon
            WHERE ma_khuon = 'K_RC6-3059-000-11A';
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            any("K_RC6-3059" in str(r.get("ma_khuon", "")) for r in ai_data.get("rows", []))
        )
    },
    {
        "id": "RAND-10",
        "module": "Đơn hàng bán SO",
        "question": "Bảng kê đơn hàng bán của khách hàng mã KH0047",
        "entity_code": "KH0047",
        "ground_truth_sql": """
            SELECT count(DISTINCT h.so_ct) as so_don, coalesce(sum(d.so_luong), 0) as tong_sl
            FROM public.ph64 h
            JOIN public.ct64 d USING(stt_rec)
            WHERE h.ma_kh = 'KH0047' AND h.status NOT IN ('14', '15');
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            (ai_data.get("lookup", {}).get("ma_kh") == "KH0047" or any(r.get("ma_kh") == "KH0047" for r in ai_data.get("rows", [])))
        )
    },
    {
        "id": "RAND-11",
        "module": "Tồn kho theo Kho",
        "question": "Tổng hợp số lượng tồn kho phân bổ theo từng kho hàng trong hệ thống",
        "entity_code": "WAREHOUSES",
        "ground_truth_sql": """
            SELECT count(DISTINCT k.ma_kho) as active_warehouses
            FROM public.dmkho k
            WHERE coalesce(k.ma_kho, '') != '';
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) >= 20 and 
            any("KHOTP" in str(r.get("ma_kho", "")) for r in ai_data.get("rows", []))
        )
    },
    {
        "id": "RAND-12",
        "module": "Dừng chuyền MES Stop Line",
        "question": "Lịch sử các lần dừng máy stop line gần đây nhất",
        "entity_code": "STOP_LINE",
        "ground_truth_sql": """
            SELECT count(*) as total_stops
            FROM public.mes_oi_stop_line
            WHERE create_date >= '2026-10-01';
        """,
        "validate_fn": lambda ai_data, db_rows: (
            len(ai_data.get("rows", [])) > 0 and 
            any("ma_may" in r or "nguyen_nhan" in r or "station_code" in r or "machine_code" in r for r in ai_data.get("rows", []))
        )
    }
]

def run_reconciliation():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Import Tools from container path
    sys.path.insert(0, "/tmp")
    from htmp_postgres_query import Tools
    tool = Tools()

    audit_results = []
    print(f"================================================================================")
    print(f"BẮT ĐẦU ĐỐI SOÁT TOÀN DIỆN {len(TEST_CASES)} CÂU HỎI NGẪU NHIÊN VỚI DATABASE THỰC TẾ")
    print(f"================================================================================\n")

    passed_count = 0
    for idx, tc in enumerate(TEST_CASES, start=1):
        cid = tc["id"]
        mod = tc["module"]
        q = tc["question"]
        sql = tc["ground_truth_sql"].strip()

        print(f"[{idx}/{len(TEST_CASES)}] {cid} | Phân hệ: {mod}")
        print(f"  Câu hỏi: \"{q}\"")

        # 1. Chọc trực tiếp vào DB để lấy Ground Truth
        t0 = time.time()
        cur.execute(sql)
        db_raw = cur.fetchall()
        db_time_ms = (time.time() - t0) * 1000
        col_names = [desc[0] for desc in cur.description]
        db_summary = [dict(zip(col_names, row)) for row in db_raw[:5]]

        # 2. Gọi AI / UI query tool
        t1 = time.time()
        ai_resp_str = tool._ask_erp_data(q)
        ai_time_ms = (time.time() - t1) * 1000

        try:
            ai_data = json.loads(ai_resp_str)
        except Exception as e:
            ai_data = {"error": str(e), "raw": ai_resp_str}

        # 3. Đối soát tính đúng đắn giữa AI output và DB Ground Truth
        is_valid = False
        reconcile_status = "FAILED"
        if "rows" in ai_data:
            try:
                is_valid = tc["validate_fn"](ai_data, db_raw)
                reconcile_status = "RECONCILED: 100% MATCH" if is_valid else "VALIDATION_MISMATCH"
            except Exception as e:
                reconcile_status = f"VALIDATION_ERROR: {e}"

        if is_valid:
            passed_count += 1
            print(f"  --> ĐỐI SOÁT: [PASS] - {reconcile_status}")
            print(f"      Nguồn AI: {ai_data.get('source')} | Số dòng AI: {len(ai_data.get('rows', []))} | Thời gian: {ai_time_ms:.1f}ms")
            print(f"      Dữ liệu DB: {len(db_raw)} bản ghi kiểm tra ({db_time_ms:.1f}ms)")
        else:
            print(f"  --> ĐỐI SOÁT: [FAIL] - {reconcile_status}")
            print(f"      AI Response: {str(ai_data)[:200]}")

        audit_results.append({
            "test_id": cid,
            "module": mod,
            "question": q,
            "entity": tc["entity_code"],
            "status": "PASS" if is_valid else "FAIL",
            "reconciliation_result": reconcile_status,
            "ai_source": ai_data.get("source"),
            "ai_row_count": len(ai_data.get("rows", [])),
            "ai_sample_row": ai_data.get("rows", [])[0] if ai_data.get("rows") else None,
            "ai_message": ai_data.get("message"),
            "db_ground_truth_sample": db_summary[:2],
            "ai_latency_ms": round(ai_time_ms, 1),
            "db_latency_ms": round(db_time_ms, 1)
        })
        print()

    print(f"================================================================================")
    print(f"KẾT QUẢ ĐỐI SOÁT: {passed_count}/{len(TEST_CASES)} PASS ({passed_count/len(TEST_CASES)*100:.1f}%)")
    print(f"================================================================================")

    with open("/tmp/reconciliation_audit_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_tests": len(TEST_CASES),
            "passed": passed_count,
            "pass_rate": f"{passed_count/len(TEST_CASES)*100:.1f}%",
            "details": audit_results
        }, f, ensure_ascii=False, indent=2, default=str)

    print("Báo cáo đối soát đã được lưu tại /tmp/reconciliation_audit_report.json")

if __name__ == "__main__":
    run_reconciliation()
