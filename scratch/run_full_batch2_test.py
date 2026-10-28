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
    # Nhóm 1: Bảng kê Work Order / Điều độ sản xuất
    {"id": "MES2-01", "group": "Điều độ SX / Work Order", "question": "Bảng kê Work Order mã 1014082701"},
    {"id": "MES2-02", "group": "Điều độ SX / Work Order", "question": "Cho tôi xem bảng kê điều độ sản xuất gần đây nhất"},
    {"id": "MES2-03", "group": "Điều độ SX / Work Order", "question": "Tiến độ Work Order 001-2610-2710-DUC-0037.T30"},
    {"id": "MES2-04", "group": "Điều độ SX / Work Order", "question": "Kế hoạch sản xuất mã RC6-3087-000"},
    
    # Nhóm 2: Bảng kê dừng máy, dừng chuyền
    {"id": "MES2-05", "group": "Dừng máy, dừng chuyền", "question": "Bảng kê dừng máy gần đây"},
    {"id": "MES2-06", "group": "Dừng máy, dừng chuyền", "question": "Bảng kê dừng máy hôm nay"},
    {"id": "MES2-07", "group": "Dừng máy, dừng chuyền", "question": "Lịch sử dừng máy DUC-0266"},
    {"id": "MES2-08", "group": "Dừng máy, dừng chuyền", "question": "Bảng kê sự cố dừng máy DUC-0050"},
    
    # Nhóm 3: Bảng kê lỗi / phế phẩm sản xuất (NG)
    {"id": "MES2-09", "group": "Phế phẩm / Lỗi NG", "question": "Bảng kê phế phẩm sản xuất gần đây"},
    {"id": "MES2-10", "group": "Phế phẩm / Lỗi NG", "question": "Bảng kê lỗi sản xuất mã QC7-5021-000"},
    {"id": "MES2-11", "group": "Phế phẩm / Lỗi NG", "question": "Hàng NG máy DUC-0031"},
    {"id": "MES2-12", "group": "Phế phẩm / Lỗi NG", "question": "Bảng kê phế phẩm mã QC7-5403-000"},
]

def main():
    tools = Tools()
    results = []
    print("=" * 95)
    print("BẮT ĐẦU CHẠY KIỂM THỬ TỰ ĐỘNG ĐỢT 2: ĐIỀU ĐỘ SẢN XUẤT, DỪNG MÁY & PHẾ PHẨM MES")
    print("=" * 95)

    for item in TEST_SUITE:
        qid = item["id"]
        group = item["group"]
        q = item["question"]
        t0 = time.time()
        
        try:
            res = tools.ask_erp(q)
            duration = time.time() - t0
            
            rows_count = 0
            sample_data = None
            source_info = ""
            downloads = []
            
            if isinstance(res, tuple):
                html_resp, ctx = res
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
            print(f"[{status}] {qid} | {duration:.3f}s | {rows_count} rows | {source_info} | Q: {q}")
            if sample_data:
                sample_preview = {k: v for k, v in list(sample_data.items())[:5]}
                print(f"    Mẫu: {sample_preview}")
        except Exception as e:
            duration = time.time() - t0
            print(f"[FAILED] {qid} | {duration:.3f}s | Err: {e} | Q: {q}")
            results.append({
                "id": qid,
                "group": group,
                "question": q,
                "status": "FAILED",
                "duration_sec": round(duration, 3),
                "error": str(e)
            })

    print("\n" + "=" * 95)
    passed_count = sum(1 for r in results if r["status"] == "PASSED")
    total_count = len(results)
    avg_duration = sum(r["duration_sec"] for r in results) / total_count if total_count else 0
    print(f"KẾT QUẢ TỔNG HỢP: {passed_count}/{total_count} PASSED ({passed_count/total_count*100:.1f}%) | Thời gian TB: {avg_duration:.3f}s")
    print("=" * 95)

    with open("/home/admin/ai-stack/scratch/eval_batch2_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

if __name__ == "__main__":
    main()
