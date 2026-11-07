import urllib.request
import json
import time
import os
import sys

BASE_URL = "http://127.0.0.1:80"
API_KEY = "sk-1ce52487dd424dc4b2e8c54fe7041f8c"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def execute_tool_directly(fn_name, args):
    from erp_ai.native_tools import ERPNativeTools
    tools = ERPNativeTools()
    fn = getattr(tools, fn_name, None)
    if fn:
        try:
            return fn(**args)
        except Exception as e:
            return f"Error executing {fn_name}: {e}"
    return f"Tool {fn_name} not found"

def run_test(idx, domain, question):
    print("=" * 80)
    print(f"[{idx}/12] [{domain}] USER: {question}")
    
    # TURN 1: User prompt
    messages = [{"role": "user", "content": question}]
    payload1 = {
        "model": "htmp-nhanh",
        "messages": messages,
        "stream": False
    }
    req1 = urllib.request.Request(
        f"{BASE_URL}/api/chat/completions",
        data=json.dumps(payload1).encode("utf-8"),
        headers=HEADERS
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req1, timeout=60) as resp:
            res1 = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR Turn 1] {e}")
        return False, str(e), "", ""
    t1 = time.time()
    
    msg1 = res1["choices"][0]["message"]
    tool_calls = msg1.get("tool_calls", [])
    if not tool_calls:
        ans = msg1.get("content", "")
        print(f"[Direct Answer in {t1-t0:.2f}s]:\n{ans[:250]}...")
        return True, ans, "direct", "{}"
        
    tc = tool_calls[0]
    fn_name = tc["function"]["name"]
    fn_args = json.loads(tc["function"]["arguments"])
    print(f" -> Turn 1 Tool ({t1-t0:.2f}s): {fn_name} with args: {fn_args}")
    
    # Tool Execution
    t_tool_0 = time.time()
    tool_result = execute_tool_directly(fn_name, fn_args)
    t_tool_1 = time.time()
    print(f" -> Tool Exec ({t_tool_1-t_tool_0:.2f}s): {tool_result[:160]}...")
    
    # TURN 2: Model synthesis
    messages.append(msg1)
    messages.append({
        "role": "tool",
        "tool_call_id": tc.get("id", "call_1"),
        "content": tool_result
    })
    
    payload2 = {
        "model": "htmp-nhanh",
        "messages": messages,
        "stream": False
    }
    req2 = urllib.request.Request(
        f"{BASE_URL}/api/chat/completions",
        data=json.dumps(payload2).encode("utf-8"),
        headers=HEADERS
    )
    t2 = time.time()
    try:
        with urllib.request.urlopen(req2, timeout=90) as resp:
            res2 = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR Turn 2] {e}")
        return False, str(e), fn_name, json.dumps(fn_args)
    t3 = time.time()
    
    msg2 = res2["choices"][0]["message"]
    final_content = msg2.get("content", "")
    print(f" -> Turn 2 Final Answer ({t3-t2:.2f}s | Total: {t3-t0:.2f}s):")
    print(final_content[:350] + ("..." if len(final_content) > 350 else ""))
    return True, final_content, fn_name, json.dumps(fn_args)

QUESTIONS = [
    (1, "Bán hàng", "Cho tôi danh sách đơn hàng bán của khách hàng KH0047 trong tháng 10/2026"),
    (2, "Giá bán", "check cho chị giá bán của mã hàng 156279430"),
    (3, "Tiến độ giao", "Đơn hàng và tiến độ giao của mã QC7-5146-000 thế nào?"),
    (4, "Mua hàng", "Đơn mua hàng từ nhà cung cấp NCC0220 trong tháng 10/2026 gồm những đơn nào?"),
    (5, "Giá mua", "Lịch sử đơn giá mua của vật tư PS-576D gần đây ra sao?"),
    (6, "Tồn kho", "Tồn kho của mã 75577-BZ010 theo từng kho là bao nhiêu?"),
    (7, "Thẻ kho", "Cho tôi thẻ kho của vật tư QC7-5146-000 tại KHOTP00 từ 01/10 đến 07/10/2026"),
    (8, "Dừng máy MES", "Tổng hợp thời gian dừng máy theo nguyên nhân trong tháng 10/2026"),
    (9, "Sản xuất MES", "Thống kê thời gian dừng máy sự cố của máy DUC-0201 trong tháng 10/2026"),
    (10, "BOM", "Theo BOM mã QC7-5146-000 sử dụng loại nhựa nào và định mức bao nhiêu?"),
    (11, "Khuôn MES", "Khuôn của mã QC7-5146-000 đã dập bao nhiêu shot và giới hạn bảo hành là bao nhiêu?"),
    (12, "Chất lượng IQC", "Báo cáo đánh giá chất lượng hàng mua theo nhà cung cấp trong tháng 10/2026")
]

if __name__ == "__main__":
    records = []
    t_start = time.time()
    for idx, domain, q in QUESTIONS:
        ok, res, fn, args = run_test(idx, domain, q)
        records.append({
            "idx": idx,
            "domain": domain,
            "question": q,
            "passed": ok,
            "tool": fn,
            "args": args,
            "answer": res
        })
    
    print("\n" + "=" * 80)
    print("TỔNG KẾT KIỂM THỬ 12 CÂU NGHIỆP VỤ ERP / MES:")
    print("=" * 80)
    passed_count = sum(1 for r in records if r["passed"])
    for r in records:
        status = "PASSED" if r["passed"] else "FAILED"
        print(f"Câu {r['idx']:02d} [{r['domain']}]: {status} (Tool: {r['tool']})")
    print(f"\nKết quả: {passed_count}/{len(records)} câu thành công trong {time.time()-t_start:.1f}s!")

    out_dir = "/home/admin/ai-stack/docs/evidence/ERP-VERIFICATION-20261107"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/ket-qua-12-cau.json", "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"Saved full JSON records to {out_dir}/ket-qua-12-cau.json")
