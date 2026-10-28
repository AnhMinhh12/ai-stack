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
    # Nhóm 1: Bán hàng — Đơn hàng bán SO1 (ph64/ct64)
    {"id": "ERP3-01", "group": "Đơn hàng bán SO1", "question": "Cho tôi xem bảng kê đơn hàng bán gần đây nhất"},
    {"id": "ERP3-02", "group": "Đơn hàng bán SO1", "question": "Bảng kê đơn hàng bán mã KH0047"},
    {"id": "ERP3-03", "group": "Đơn hàng bán SO1", "question": "Bảng kê đơn hàng bán số 001-2610-010164"},
    {"id": "ERP3-04", "group": "Đơn hàng bán SO1", "question": "Đơn hàng bán mã VGL1A416"},
    
    # Nhóm 2: Bán hàng — Phiếu xuất kho bán hàng HDA (ph81/ct81)
    {"id": "ERP3-05", "group": "Phiếu xuất kho bán hàng", "question": "Bảng kê phiếu xuất kho bán hàng gần đây"},
    {"id": "ERP3-06", "group": "Phiếu xuất kho bán hàng", "question": "Bảng kê phiếu xuất bán mã KH0049"},
    {"id": "ERP3-07", "group": "Phiếu xuất kho bán hàng", "question": "Phiếu xuất kho bán hàng 001-2610-002643"},
    
    # Nhóm 3: Mua hàng — Đơn hàng mua PO1 (ph94/ct94)
    {"id": "ERP3-08", "group": "Đơn hàng mua PO1", "question": "Bảng kê đơn hàng mua gần đây nhất"},
    {"id": "ERP3-09", "group": "Đơn hàng mua PO1", "question": "Bảng kê đơn hàng mua mã NCC0220"},
    {"id": "ERP3-10", "group": "Đơn hàng mua PO1", "question": "Đơn hàng mua số 001-2610-000702"},
    
    # Nhóm 4: Kho vận — Nhập / xuất kho nội bộ (ph74/ct74)
    {"id": "ERP3-11", "group": "Nhập xuất kho nội bộ", "question": "Bảng kê phiếu nhập kho nội bộ gần đây"},
    {"id": "ERP3-12", "group": "Nhập xuất kho nội bộ", "question": "Phiếu nhập kho nội bộ số 001-2610-011362"},
    {"id": "ERP3-13", "group": "Nhập xuất kho nội bộ", "question": "Bảng kê nhập kho từ sản xuất mã RC4-3049-000"},
    
    # Nhóm 5: Hồ sơ khuôn — Quản lý tài sản khuôn (dmhosokhuon)
    {"id": "ERP3-14", "group": "Hồ sơ khuôn", "question": "Bảng kê hồ sơ khuôn gần đây"},
    {"id": "ERP3-15", "group": "Hồ sơ khuôn", "question": "Hồ sơ khuôn mã K_VGY1A061"},
    
    # Nhóm 6: Bảng giá bán (dmbanggia/dmbanggiact)
    {"id": "ERP3-16", "group": "Bảng giá bán", "question": "Danh mục bảng giá bán hiện hành"}
]

def main():
    tools = Tools()
    results = []
    print("=" * 95)
    print("BẮT ĐẦU CHẠY KIỂM THỬ TỰ ĐỘNG ĐỢT 3: BÁN HÀNG (SO1, HDA), MUA HÀNG (PO1), KHO VẬN & KHUÔN")
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

    with open("/home/admin/ai-stack/scratch/eval_batch3_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

if __name__ == "__main__":
    main()
