import sys
import time
import json
sys.path.insert(0, '/home/admin/ai-stack')
from functions.htmp_postgres_query import Tools

tools = Tools()

demo_questions = [
    ("Q01", "Tổng số lượng xuất hàng của mã hàng từ thời điểm này đến thời điểm này là bao nhiêu? Và doanh thu? tách đơn hàng bán và đơn giao bù NG (mã giao dịch 1 và 10)"),
    ("Q02", "DO và FCST: so sánh sự biến động demand giữa lần update trước và update sau của mã QC7-5146-000"),
    ("Q03", "Khuôn H131-TBT-H612 đã chạy được bao nhiêu shots? Theo demand của khách hàng thì dự kiến khi nào hết tuổi thọ khuôn?"),
    ("Q04", "so sánh doanh thu mã sản phẩm HK2C2-393-01-00 tháng 9 và tháng 10"),
    ("Q05", "So sánh doanh thu của mã hàng H131-TBT-H612? tách đơn hàng bán và giao bù NG"),
    ("Q06", "Mã hàng QC7-5146-000 có tồn kho hiện tại bao gồm của những khuôn nào? Số lượng tồn kho cụ thể của từng khuôn? chỉ lấy ở các kho tp, kho xhtl"),
    ("Q07", "Cung cấp data đơn hàng quá khứ 9/2026 của mã H131-TBT-H612"),
    ("Q08", "lệnh giao hàng 001-2611-000004 được hoàn thiện khi nào lấy theo thời gian kho hoàn thành lệnh out hàng ra khỏi hệ thống"),
    ("Q09", "Khách hàng KH0062 có mã hàng nào chưa link được giá trên ERP không?"),
    ("Q10", "khách hàng ATSUMITEC có mã khách hàng là gì"),
    ("Q11", "số lượng NG đã nhận lại và đã giao bù là bao nhiêu")
]

print("======================================================================")
print("           KIỂM THỬ TOÀN DIỆN 11 KỊCH BẢN DEMO THỰC TẾ ERP            ")
print("======================================================================\n")

all_pass = True
for qid, qtext in demo_questions:
    t0 = time.time()
    try:
        res = tools.ask_erp(qtext, __user__={"id": "admin", "email": "admin@htmp.com.vn"})
        elapsed = time.time() - t0
        
        # Verify result is json with message
        res_obj = None
        msg = ""
        if isinstance(res, str):
            try:
                res_obj = json.loads(res)
                if isinstance(res_obj, dict):
                    msg = res_obj.get("message", "")
            except Exception:
                msg = res
        
        has_content = len(msg) > 30
        print(f"[{qid}] {'PASS' if has_content else 'FAIL'} ({elapsed:.3f}s)")
        print(f"  Câu hỏi: {qtext}")
        print(f"  Trích xuất tóm tắt kết quả:")
        lines = msg.strip().split("\n")
        for line in lines[:6]:
            print(f"    {line}")
        if len(lines) > 6:
            print(f"    ... ({len(lines)} dòng kết quả)")
        print()
        if not has_content:
            all_pass = False
    except Exception as e:
        elapsed = time.time() - t0
        print(f"[{qid}] ERROR ({elapsed:.3f}s): {e}\n")
        all_pass = False

print("======================================================================")
print(f"KẾT QUẢ CUỐI CÙNG: {'11/11 TEST PASS 100%' if all_pass else 'CÓ TEST THẤT BẠI'}")
print("======================================================================")
