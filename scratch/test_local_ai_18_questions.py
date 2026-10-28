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
os.environ["HTMP_ERP_USER_ID_MAP"] = '{"1": 1, "admin@htmp.vn": 1}'

sys.path.insert(0, "/home/admin/ai-stack")

from functions.htmp_postgres_query import Tools

QUESTIONS = [
    {
        "id": 1,
        "question": "Mã hàng QC7-5146-000 dùng loại nhựa gì? Cấu trúc sản phẩm của mã hàng này gồm những gì?"
    },
    {
        "id": 2,
        "question": "MOQ báo giá hiện tại của mã QC7-5146-000 là bao nhiêu? Giá áp dụng hiện tại theo từng mức MOQ là bao nhiêu?"
    },
    {
        "id": 3,
        "question": "Tính đến ngày 20/10/2026, lot gần nhất được xuất giao của mã QC7-5146-000 là lot nào? Ngày xuất và số lượng bao nhiêu?"
    },
    {
        "id": 4,
        "question": "Từ ngày 01/10/2026 đến hết ngày 20/10/2026, tổng số lượng xuất bán và doanh thu của mã QC7-5146-000 là bao nhiêu?"
    },
    {
        "id": 5,
        "question": "Mã hàng QC7-5146-000 được khai báo thuộc khách hàng nào?"
    },
    {
        "id": 6,
        "question": "Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 được nhập kho vào những ngày nào, từ kho nào sang kho nào, số lượng bao nhiêu và tài khoản nào tạo phiếu?"
    },
    {
        "id": 7,
        "question": "So sánh DO và FCST hiện tại với bản trước của mã QC7-5146-000: số lượng tăng hay giảm bao nhiêu?"
    },
    {
        "id": 8,
        "question": "Quy cách đóng gói của mã QC7-5146-000 gồm những thông tin gì? Có thể quy đổi tồn kho hiện tại theo quy cách đóng gói không?"
    },
    {
        "id": 9,
        "question": "Khuôn K_QC5-2919-000-V1 đã chạy tổng cộng bao nhiêu shot cho mã QC7-5146-000? Với demand của khách KH0015, có đủ dữ liệu để dự kiến thời điểm khuôn hết tuổi thọ không?"
    },
    {
        "id": 10,
        "question": "So sánh doanh thu mã QC7-5146-000 của khách KH0015 trong hai khoảng 01/09/2026–20/09/2026 và 01/10/2026–20/10/2026. Nêu số lượng và doanh thu từng kỳ."
    },
    {
        "id": 11,
        "question": "Mã QC7-5146-000 hiện có tồn kho thuộc những khuôn nào? Số lượng theo từng khuôn là bao nhiêu?"
    },
    {
        "id": 12,
        "question": "Liệt kê dữ liệu đơn hàng bán của khách KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026, gồm số đơn, ngày đặt, mã hàng, số lượng và trạng thái."
    },
    {
        "id": 13,
        "question": "Lệnh giao hàng 001-2610-001811 được ghi nhận hoàn thành khi nào? Cho biết trạng thái lệnh và căn cứ thời gian được dùng."
    },
    {
        "id": 14,
        "question": "Tồn kho hiện tại của mã QC7-5146-000 là bao nhiêu ở từng kho?"
    },
    {
        "id": 15,
        "question": "Mã QC7-5146-000 hiện có lot thành phẩm nào ở trạng thái QC cần chú ý? Cho biết trạng thái QC đúng như dữ liệu ERP."
    },
    {
        "id": 16,
        "question": "Trong đơn hàng của khách KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026, có mã hàng nào chưa có giá chuẩn được liên kết không?"
    },
    {
        "id": 17,
        "question": "Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long có mã khách hàng nào trên ERP?"
    },
    {
        "id": 18,
        "question": "Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 có số lượng giao bù NG là bao nhiêu, số lượng hàng NG đã nhận lại là bao nhiêu, và còn bao nhiêu chưa giao bù hoặc chưa nhận về? Phân biệt rõ giao bù NG với giao bù hàng thiếu; nếu ERP không lưu đủ căn cứ để phân biệt thì nêu rõ."
    }
]

def main():
    tools = Tools()
    print("Khởi tạo Tools() thành công. Bắt đầu test 18 câu hỏi qua ask_erp...\n")
    
    results = []
    user_payload = {"id": 1, "email": "admin@htmp.vn"}
    
    for item in QUESTIONS:
        qid = item["id"]
        q_text = item["question"]
        print(f"--- [CÂU {qid}] ---")
        print(f"Hỏi: {q_text}")
        t0 = time.time()
        try:
            resp = tools.ask_erp(question=q_text, __user__=user_payload)
            elapsed = time.time() - t0
            print(f"Thời gian: {elapsed:.3f}s")
            
            # Parse or inspect response
            resp_str = str(resp)
            is_valid = bool(resp_str and "Không tìm thấy" not in resp_str and "Lỗi" not in resp_str[:50])
            status = "PASSED" if is_valid else "FAILED/EMPTY"
            print(f"Kết quả ({status}):\n{resp_str[:300]}...\n")
            
            results.append({
                "id": qid,
                "question": q_text,
                "status": status,
                "elapsed": elapsed,
                "response": resp_str
            })
        except Exception as e:
            elapsed = time.time() - t0
            print(f"LỖI EXCEPTION ({elapsed:.3f}s): {e}\n")
            results.append({
                "id": qid,
                "question": q_text,
                "status": "EXCEPTION",
                "elapsed": elapsed,
                "error": str(e)
            })

    # Summary
    print("\n" + "="*50)
    print("TỔNG KẾT KIỂM THỬ LOCAL AI (18 CÂU)")
    print("="*50)
    passed = sum(1 for r in results if r["status"] == "PASSED")
    print(f"Tổng số câu: {len(results)} | Đạt: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    for r in results:
        print(f"Câu {r['id']:02d}: [{r['status']}] ({r['elapsed']:.2f}s) - {r['question'][:60]}...")

    with open("/home/admin/ai-stack/scratch/ai_eval_18_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
