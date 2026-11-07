import urllib.request
import json
import time
from erp_ai.native_tools import ERPNativeTools

BASE_URL = "http://127.0.0.1:80"
API_KEY = "sk-1ce52487dd424dc4b2e8c54fe7041f8c"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def execute_tool_directly(fn_name, args):
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
    print(f"[{idx}] [{domain}] USER: {question}")
    
    # TURN 1
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
        return False, str(e)
    t1 = time.time()
    
    msg1 = res1["choices"][0]["message"]
    tool_calls = msg1.get("tool_calls", [])
    if not tool_calls:
        ans = msg1.get("content", "")
        print(f"[Direct Answer in {t1-t0:.2f}s]:\n{ans[:250]}...")
        return True, ans
        
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
        return False, str(e)
    t3 = time.time()
    
    msg2 = res2["choices"][0]["message"]
    final_content = msg2.get("content", "")
    print(f" -> Turn 2 Final Answer ({t3-t2:.2f}s | Total: {t3-t0:.2f}s):")
    print(final_content[:450] + ("..." if len(final_content) > 450 else ""))
    return True, final_content

TESTS = [
    (3, "Tiến độ giao", "Đơn hàng và tiến độ giao của mã QC7-5146-000 thế nào?"),
    (7, "Thẻ kho", "Cho tôi thẻ kho của vật tư QC7-5146-000 tại KHOTP00 từ 01/10 đến 07/10/2026"),
    (8, "Dừng máy MES", "Tổng hợp thời gian dừng máy theo nguyên nhân trong tháng 10/2026"),
    (9, "Sản xuất MES", "Thống kê thời gian dừng máy sự cố của máy DUC-0201 trong tháng 10/2026"),
    (12, "Chất lượng IQC", "Báo cáo đánh giá chất lượng hàng mua theo nhà cung cấp trong tháng 10/2026")
]

if __name__ == "__main__":
    for idx, domain, q in TESTS:
        run_test(idx, domain, q)

