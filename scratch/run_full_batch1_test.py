#!/usr/bin/env python3
import json
import time
import os
import sys

# Ensure environment is set
os.environ["HTMP_DB_HOST"] = "10.0.6.2"
os.environ["HTMP_DB_PORT"] = "5410"
os.environ["HTMP_DB_NAME"] = "3SERP_HTMP_DATA"
os.environ["HTMP_DB_USER"] = "read_htmp"
os.environ["HTMP_DB_PASSWORD"] = "P@ss@Htmp@W0rd!2025"
os.environ["HTMP_ERP_REPORTS_DIR"] = "/home/admin/ai-stack/config/erp-reports"
os.environ["HTMP_ERP_BUSINESS_INTENTS_PATH"] = "/home/admin/ai-stack/config/erp-business-intents.json"

sys.path.insert(0, "/home/admin/ai-stack")

from functions.htmp_postgres_query import Tools

TEST_SUITE = [
    # Nhóm 1: Bảng kê đóng gói, đóng thùng (mes_oi_dong_thung)
    {"id": "MES-01", "group": "Đóng gói, đóng thùng", "question": "Bảng kê đóng gói đóng thùng mã QC7-5524-000"},
    {"id": "MES-02", "group": "Đóng gói, đóng thùng", "question": "Cho tôi xem bảng kê đóng thùng gần đây nhất"},
    {"id": "MES-03", "group": "Đóng gói, đóng thùng", "question": "Bảng kê đóng gói theo WO 001-2610-2510-DUC-0011.1T"},
    {"id": "MES-04", "group": "Đóng gói, đóng thùng", "question": "Bảng kê đóng thùng mã RC6-4007-000"},
    
    # Nhóm 2: Bảng kê gộp, tách thùng (intem_carton_log + intem_log)
    {"id": "MES-05", "group": "Gộp tách thùng", "question": "Bảng kê gộp tách thùng"},
    {"id": "MES-06", "group": "Gộp tách thùng", "question": "Cho tôi xem bảng kê gộp tách thùng hôm nay"},
    {"id": "MES-07", "group": "Gộp tách thùng", "question": "Lịch sử gộp tách thùng mã VGL1A375"},
    {"id": "MES-08", "group": "Gộp tách thùng", "question": "Bảng kê gộp tách thùng mã BGTD0103"},
    
    # Nhóm 3: Bảng kê bổ sung shot khuôn (mes_oi_bo_shot)
    {"id": "MES-09", "group": "Bổ sung shot khuôn", "question": "Bảng kê bổ sung shot khuôn"},
    {"id": "MES-10", "group": "Bổ sung shot khuôn", "question": "Bảng kê bổ sung shot khuôn gần đây"},
    {"id": "MES-11", "group": "Bổ sung shot khuôn", "question": "Bảng kê bổ sung shot máy DUC-0032"},
    {"id": "MES-12", "group": "Bổ sung shot khuôn", "question": "Bảng kê bổ sung shot mã RC6-3909-000"},

    # Nhóm 4: Các nghiệp vụ đối chiếu khác
    {"id": "ERP-13", "group": "Quy cách đóng gói & Tồn kho", "question": "Quy cách đóng gói và tồn kho mã QC7-5524-000"},
    {"id": "ERP-14", "group": "Trạng thái QC thành phẩm", "question": "Trạng thái QC mã QC7-5524-000"},
    {"id": "ERP-15", "group": "Bảng kê nhập kho", "question": "Bảng kê phiếu nhập kho mã QC7-5524-000"},
    {"id": "ERP-16", "group": "Lần giao gần nhất", "question": "Đợt giao hàng gần nhất của mã QC7-5524-000"},
]

def main():
    tools = Tools()
    results = []
    print("=" * 90)
    print("BẮT ĐẦU CHẠY TOÀN BỘ BỘ TEST CÂU HỎI TRỰC TIẾP TRÊN HỆ THỐNG")
    print("=" * 90)

    for item in TEST_SUITE:
        qid = item["id"]
        group = item["group"]
        q = item["question"]
        t0 = time.time()
        
        try:
            # Test direct ask_erp which Open WebUI calls
            res = tools.ask_erp(q)
            duration = time.time() - t0
            
            # Unpack response
            has_html = False
            rows_count = 0
            sample_data = None
            source_info = ""
            downloads = []
            
            if isinstance(res, tuple):
                html_resp, ctx = res
                has_html = bool(html_resp and getattr(html_resp, "body", None))
                rows = ctx.get("rows", [])
                rows_count = len(rows) if isinstance(rows, list) else 0
                sample_data = rows[0] if rows_count > 0 else None
                source_info = ctx.get("source", ctx.get("report", {}).get("title", "Unknown"))
                downloads = ctx.get("download_formats", [])
            elif isinstance(res, str):
                try:
                    parsed = json.loads(res)
                    rows = parsed.get("rows", [])
                    rows_count = len(rows) if isinstance(rows, list) else 0
                    sample_data = rows[0] if rows_count > 0 else None
                    source_info = parsed.get("source", parsed.get("report", {}).get("title", ""))
                except Exception:
                    source_info = res[:100]

            status = "PASSED" if rows_count > 0 else "WARNING (0 rows)"
            results.append({
                "id": qid,
                "group": group,
                "question": q,
                "status": status,
                "duration_sec": round(duration, 3),
                "rows_count": rows_count,
                "source": source_info,
                "sample": sample_data,
                "downloads": downloads
            })
            
            print(f"[{qid}] {status} ({duration:.3f}s) | {group}: '{q}'")
            print(f"       -> Nguồn: {source_info} | Số dòng: {rows_count}")
            if sample_data:
                sample_str = json.dumps(sample_data, ensure_ascii=False, default=str)
                if len(sample_str) > 120:
                    sample_str = sample_str[:117] + "..."
                print(f"       -> Mẫu 1: {sample_str}")
        except Exception as e:
            duration = time.time() - t0
            results.append({
                "id": qid,
                "group": group,
                "question": q,
                "status": f"FAILED: {str(e)}",
                "duration_sec": round(duration, 3),
                "rows_count": 0,
                "source": "",
                "sample": None,
                "downloads": []
            })
            print(f"[{qid}] FAILED ({duration:.3f}s) | '{q}': {e}")
        print("-" * 90)

    print("\n" + "=" * 90)
    print("TỔNG HỢP KẾT QUẢ BỘ TEST:")
    total = len(results)
    passed = sum(1 for r in results if "PASSED" in r["status"])
    print(f"Tổng số test: {total} | Đạt: {passed}/{total} ({passed/total*100:.1f}%)")
    print("=" * 90)
    
    # Save test report to JSON
    out_file = "/tmp/batch1_test_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    print(f"Đã lưu kết quả chi tiết ra {out_file}")

if __name__ == "__main__":
    main()
