import urllib.request
import json
import time
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
        return fn(**args)
    return f"Tool {fn_name} not found"

def run_two_turn_test(question):
    print("=" * 70)
    print(f"USER: {question}")
    
    # TURN 1: User asks question
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
    with urllib.request.urlopen(req1, timeout=60) as resp:
        res1 = json.loads(resp.read().decode("utf-8"))
    t1 = time.time()
    
    msg1 = res1["choices"][0]["message"]
    tool_calls = msg1.get("tool_calls", [])
    if not tool_calls:
        print(f"Direct text response (in {t1-t0:.2f}s):\n{msg1.get('content')}")
        return
        
    tc = tool_calls[0]
    fn_name = tc["function"]["name"]
    fn_args = json.loads(tc["function"]["arguments"])
    print(f"[TURN 1] Model selected tool in {t1-t0:.2f}s:")
    print(f"  -> Tool: {fn_name}")
    print(f"  -> Arguments: {fn_args}")
    
    # EXECUTE TOOL DETERMINISTICALLY
    t_tool_0 = time.time()
    tool_result = execute_tool_directly(fn_name, fn_args)
    t_tool_1 = time.time()
    print(f"[TOOL EXECUTION] Tool completed in {t_tool_1-t_tool_0:.2f}s:")
    print(f"  -> Result: {tool_result[:180]}...")
    
    # TURN 2: Pass tool result back to model for synthesis
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
    with urllib.request.urlopen(req2, timeout=60) as resp:
        res2 = json.loads(resp.read().decode("utf-8"))
    t3 = time.time()
    
    msg2 = res2["choices"][0]["message"]
    final_content = msg2.get("content")
    print(f"[TURN 2] Final Synthesized Answer (in {t3-t2:.2f}s, Total: {t3-t0:.2f}s):")
    print("-" * 50)
    print(final_content)
    print("-" * 50)

if __name__ == "__main__":
    questions = [
        "check cho chị giá bán của mã hàng 156279430 15:49 6 thg 11",
        "check cho chị giá bán của mã hàng T1015910DA này đang bao nhiêu 15:47 6 thg 11",
        "cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11",
        "mã 4509 trên hệ thống là ai thế em?",
        "khuôn của mã QC7-5146-000 hiện tại đã dập được bao nhiêu shot rồi?"
    ]
    for q in questions:
        run_two_turn_test(q)
