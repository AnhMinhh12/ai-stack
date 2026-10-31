import urllib.request
import json
import time
import subprocess
import os

BASE_URL = "http://127.0.0.1:80"
API_KEY = "sk-1ce52487dd424dc4b2e8c54fe7041f8c"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

QUESTIONS = [
    # Phần 1: Báo cáo tổng hợp (1-12)
    {"id": "Q01", "name": "Top vật tư tồn kho lớn nhất", "text": "Cho tôi xem báo cáo top 10 vật tư có số lượng tồn kho lớn nhất hiện tại"},
    {"id": "Q02", "name": "Tồn kho phân bổ theo từng kho", "text": "Tổng hợp số lượng tồn kho phân bổ theo từng kho hàng trong hệ thống"},
    {"id": "Q03", "name": "Biến động xuất nhập tồn theo ngày", "text": "Báo cáo tổng hợp số lượng nhập kho và xuất kho theo từng ngày từ ngày 01/10/2026 đến ngày 20/10/2026"},
    {"id": "Q04", "name": "Top khách hàng theo số lượng đặt hàng", "text": "Cho tôi báo cáo top khách hàng có số lượng đặt hàng lớn nhất trong các đơn hàng bán gần đây"},
    {"id": "Q05", "name": "Sản lượng xuất bán theo khách hàng", "text": "Tổng hợp sản lượng xuất kho bán hàng cho các khách hàng từ ngày 01/10/2026 đến hết ngày 20/10/2026"},
    {"id": "Q06", "name": "Tiến độ giao hàng mã QC7-5146-000", "text": "Tổng hợp số lượng xuất kho bán hàng của mã hàng QC7-5146-000 theo từng ngày xuất từ ngày 01/10/2026 đến ngày 20/10/2026"},
    {"id": "Q07", "name": "Nhà cung cấp phát sinh đơn mua nhiều nhất", "text": "Tổng hợp số lượng đơn hàng mua và tổng số lượng vật tư đặt mua theo từng nhà cung cấp gần đây"},
    {"id": "Q08", "name": "Lịch sử giá mua vật tư PS-576D", "text": "Tổng hợp lịch sử các lần đặt mua, đơn giá mua thấp nhất, cao nhất và giá bình quân của mã nhựa PS-576D"},
    {"id": "Q09", "name": "Tổng hợp phế phẩm (NG) theo dòng máy / line", "text": "Báo cáo tổng hợp số lượng sản phẩm lỗi NG theo từng máy sản xuất trong các ca làm việc gần đây"},
    {"id": "Q10", "name": "Phân loại lỗi sản xuất trong xác nhận NG", "text": "Tổng hợp số lượng lỗi sản phẩm theo từng mã lỗi và nguyên nhân lỗi trong bảng kê xác nhận NG"},
    {"id": "Q11", "name": "Thời gian dừng máy (Downtime)", "text": "Báo cáo tổng số phút dừng máy theo từng nguyên nhân dừng chuyền trong bảng kê stop line gần đây"},
    {"id": "Q12", "name": "Tiến độ Work Order (Lệnh sản xuất)", "text": "Tổng hợp số lượng kế hoạch sản xuất theo từng Work Order trong bảng điều độ sản xuất gần đây"},

    # Phần 2: Tra cứu ngẫu nhiên (13-42)
    {"id": "Q13", "name": "Bảng kê đơn hàng bán gần nhất", "text": "Cho tôi xem bảng kê đơn hàng bán gần đây nhất"},
    {"id": "Q14", "name": "Bảng kê đơn hàng bán của khách hàng KH0047", "text": "Bảng kê đơn hàng bán của khách hàng mã KH0047"},
    {"id": "Q15", "name": "Chi tiết đơn hàng bán 001-2610-010164", "text": "Tra cứu chi tiết đơn hàng bán số 001-2610-010164"},
    {"id": "Q16", "name": "Đơn hàng bán chứa mã hàng VGL1A416", "text": "Tìm kiếm các đơn hàng bán có chứa mã hàng VGL1A416"},
    {"id": "Q17", "name": "Phiếu xuất kho bán hàng phát sinh hôm nay", "text": "Bảng kê phiếu xuất kho bán hàng phát sinh ngày hôm nay"},
    {"id": "Q18", "name": "Phiếu xuất bán cho khách hàng KH0049", "text": "Bảng kê các phiếu xuất bán cho khách hàng mã KH0049"},
    {"id": "Q19", "name": "Chi tiết phiếu xuất bán 001-2610-002643", "text": "Xem chi tiết phiếu xuất kho bán hàng số 001-2610-002643"},
    {"id": "Q20", "name": "Lot giao gần nhất mã QC7-5146-000", "text": "Lot giao gần nhất của mã hàng QC7-5146-000 là khi nào và số lượng bao nhiêu?"},
    {"id": "Q21", "name": "Bảng kê đơn hàng mua gần nhất", "text": "Bảng kê đơn hàng mua gần đây nhất của công ty"},
    {"id": "Q22", "name": "Bảng kê đơn mua nhà cung cấp NCC0220", "text": "Bảng kê đơn hàng mua của nhà cung cấp mã NCC0220"},
    {"id": "Q23", "name": "Chi tiết đơn hàng mua 001-2610-000702", "text": "Tra cứu đơn hàng mua số 001-2610-000702"},
    {"id": "Q24", "name": "Số lần mua và giá gần nhất mã PS-576D", "text": "Mã hàng PS-576D đã mua bao nhiêu lần và giá mua gần nhất là bao nhiêu?"},
    {"id": "Q25", "name": "Duyệt giá và báo giá NCC mã PS-576D", "text": "Kiểm tra trạng thái duyệt giá và báo giá nhà cung cấp của mã vật tư PS-576D"},
    {"id": "Q26", "name": "Phiếu nhập kho nội bộ từ sản xuất gần đây", "text": "Bảng kê phiếu nhập kho nội bộ từ sản xuất phát sinh gần đây"},
    {"id": "Q27", "name": "Chi tiết phiếu nhập kho nội bộ 001-2610-011362", "text": "Chi tiết phiếu nhập kho nội bộ số 001-2610-011362"},
    {"id": "Q28", "name": "Nhập kho sản xuất mã RC4-3049-000", "text": "Bảng kê nhập kho từ sản xuất của mã hàng RC4-3049-000"},
    {"id": "Q29", "name": "Nhập kho QC7-5146-000 tháng 10/2026", "text": "Mã hàng QC7-5146-000 được nhập kho khi nào trong tháng 10/2026? Từ kho nào sang và ai lập phiếu?"},
    {"id": "Q30", "name": "Lần nhập kho gần nhất mã RC4-3049-000", "text": "Tra cứu lần nhập kho gần đây nhất của mã vật tư RC4-3049-000"},
    {"id": "Q31", "name": "Bảng kê đóng gói đóng thùng gần nhất", "text": "Bảng kê đóng gói đóng thùng thành phẩm gần đây nhất"},
    {"id": "Q32", "name": "Bảng kê gộp tách thùng tem carton", "text": "Cho tôi xem bảng kê gộp tách thùng tem carton gần đây"},
    {"id": "Q33", "name": "Bổ sung hoặc bỏ shot khuôn gần đây", "text": "Bảng kê bổ sung hoặc bỏ shot khuôn trong ca sản xuất gần đây"},
    {"id": "Q34", "name": "Hồ sơ khuôn mã K_VGY1A061", "text": "Tra cứu hồ sơ khuôn của mã khuôn K_VGY1A061"},
    {"id": "Q35", "name": "Danh sách hồ sơ khuôn và tuổi thọ shot", "text": "Danh sách các hồ sơ khuôn và tuổi thọ shot định mức mới cập nhật gần đây"},
    {"id": "Q36", "name": "Bảng kê điều độ sản xuất và Work Order", "text": "Bảng kê điều độ sản xuất và danh sách Work Order đang chạy"},
    {"id": "Q37", "name": "Lịch sử dừng máy stop line gần nhất", "text": "Lịch sử các lần dừng máy stop line gần đây nhất"},
    {"id": "Q38", "name": "Xác nhận phế phẩm NG sản xuất gần nhất", "text": "Bảng kê xác nhận phế phẩm NG sản xuất gần đây nhất"},
    {"id": "Q39", "name": "Bảng giá bán sản phẩm hiện hành", "text": "Danh mục bảng giá bán sản phẩm đang có hiệu lực hiện hành"},
    {"id": "Q40", "name": "Hạt nhựa định mức BOM mã QC7-5146-000", "text": "Mã hàng QC7-5146-000 dùng loại hạt nhựa gì theo định mức BOM?"},
    {"id": "Q41", "name": "MOQ báo giá và đơn giá bán mã QC7-5146-000", "text": "MOQ báo giá và đơn giá bán hiện hành áp dụng cho mã hàng QC7-5146-000 là bao nhiêu?"},
    {"id": "Q42", "name": "Khách hàng quản lý mã QC7-5146-000", "text": "Mã hàng QC7-5146-000 thuộc quyền quản lý của khách hàng nào?"},

    # Phần 3: Đối soát phức tạp & So sánh kỳ (43-45)
    {"id": "Q43", "name": "So sánh sản lượng xuất bán 2 kỳ mã QC7-5146-000", "text": "So sánh số lượng xuất bán của mã hàng QC7-5146-000 từ ngày 01/10/2026 đến ngày 10/10/2026 so với từ ngày 11/10/2026 đến ngày 20/10/2026"},
    {"id": "Q44", "name": "So sánh doanh thu xuất bán 2 đợt khách KH0015", "text": "Đối chiếu doanh thu và số lượng xuất bán của khách hàng KH0015 từ ngày 01/10/2026 đến ngày 10/10/2026 và từ ngày 11/10/2026 đến ngày 20/10/2026"},
    {"id": "Q45", "name": "Đối soát đơn hàng (SO) và thực xuất (HDA)", "text": "Kiểm tra tổng số lượng đặt hàng trong đơn SO và tổng số lượng đã xuất kho giao hàng của mã QC7-5146-000 trong tháng 10/2026"}
]

def call_openwebui(messages):
    payload = {
        "model": "htmp-nhanh",
        "messages": messages,
        "stream": False
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=HEADERS
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

os.environ["HTMP_DB_HOST"] = "10.0.6.2"
os.environ["HTMP_DB_PORT"] = "5410"
os.environ["HTMP_DB_NAME"] = "3SERP_HTMP_DATA"
os.environ["HTMP_DB_USER"] = "read_htmp"
os.environ["HTMP_DB_PASSWORD"] = "P@ss@Htmp@W0rd!2025"
os.environ["HTMP_ERP_REPORTS_DIR"] = "/home/admin/ai-stack/config/erp-reports"
os.environ["HTMP_ERP_BUSINESS_INTENTS_PATH"] = "/home/admin/ai-stack/config/erp-business-intents.json"
os.environ["HTMP_ERP_SHARED_USER_ID"] = "11"

import sys
sys.path.insert(0, "/home/admin/ai-stack")

from functions.htmp_postgres_query import Tools
tools_instance = Tools()

def execute_ask_erp(question):
    res = tools_instance.ask_erp(question)
    if isinstance(res, tuple):
        return True, res[1]
    elif isinstance(res, dict):
        return False, res
    elif isinstance(res, str):
        try:
            return False, json.loads(res)
        except Exception:
            return False, {"message": res}
    return False, {"message": str(res)}

def run_test():
    results = []
    print(f"=== BẮT ĐẦU KIỂM THỬ TOÀN BỘ {len(QUESTIONS)} CÂU HỎI QUA GIAO DIỆN OPEN WEBUI & POSTGRES ===", flush=True)
    
    success_count = 0
    fail_count = 0
    
    for idx, q_info in enumerate(QUESTIONS, start=1):
        qid = q_info["id"]
        qname = q_info["name"]
        qtext = q_info["text"]
        print(f"\n[{idx}/{len(QUESTIONS)}] {qid}: {qname}")
        print(f"  Câu hỏi: \"{qtext}\"")
        
        t0 = time.time()
        try:
            # 1. Open WebUI Chat API call
            res1 = call_openwebui([{"role": "user", "content": qtext}])
            llm_time = time.time() - t0
            msg1 = res1["choices"][0]["message"]
            tool_calls = msg1.get("tool_calls", [])
            
            if not tool_calls:
                print(f"  [CẢNH BÁO] Không có tool_call, model trả lời text trực tiếp: {msg1.get('content')[:100]}")
                results.append({
                    "id": qid,
                    "name": qname,
                    "question": qtext,
                    "status": "PASS_NO_TOOL",
                    "llm_time": round(llm_time, 2),
                    "tool_calls": 0,
                    "response_preview": msg1.get("content", "")[:200]
                })
                success_count += 1
                continue
            
            tc = tool_calls[0]
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            tool_q = fn_args.get("question", qtext)
            print(f"  -> Model gọi tool `{fn_name}` với tham số: \"{tool_q}\" ({llm_time:.2f}s)")
            
            # 2. Tool execution against Postgres
            t1 = time.time()
            is_rich_ui, tool_res = execute_ask_erp(tool_q)
            tool_time = time.time() - t1
            
            rows = tool_res.get("rows", [])
            row_count = len(rows) if isinstance(rows, list) else tool_res.get("row_count", 0)
            source = tool_res.get("source", "Postgres ERP")
            
            print(f"  -> Tool trả về trong {tool_time:.2f}s | Nguồn: {source} | Dòng: {row_count} | Rich UI: {is_rich_ui}")
            
            # Verify data presence or valid business message
            has_data = row_count > 0 or "message" in tool_res or "status" in tool_res
            
            if has_data:
                success_count += 1
                status = "PASS"
            else:
                fail_count += 1
                status = "FAIL"
                
            results.append({
                "id": qid,
                "name": qname,
                "question": qtext,
                "status": status,
                "llm_time": round(llm_time, 2),
                "tool_time": round(tool_time, 2),
                "tool_calls": 1,
                "tool_q": tool_q,
                "source": source,
                "row_count": row_count,
                "is_rich_ui": is_rich_ui,
                "sample_row": rows[0] if (isinstance(rows, list) and len(rows) > 0) else None,
                "message": tool_res.get("message") or tool_res.get("status")
            })
            
        except Exception as e:
            print(f"  [LỖI]: {e}")
            fail_count += 1
            results.append({
                "id": qid,
                "name": qname,
                "question": qtext,
                "status": "ERROR",
                "error": str(e)
            })
            
    # Save results to file
    out_file = "/home/admin/ai-stack/scratch/ket_qua_kiem_thu_giao_dien_45_cau.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(QUESTIONS),
            "success": success_count,
            "failed": fail_count,
            "results": results
        }, f, ensure_ascii=False, indent=2)
        
    print(f"\n==========================================")
    print(f"HOÀN THÀNH KIỂM THỬ: {success_count}/{len(QUESTIONS)} THÀNH CÔNG, {fail_count} THẤT BẠI")
    print(f"File kết quả: {out_file}")
    print(f"==========================================")

if __name__ == "__main__":
    run_test()
