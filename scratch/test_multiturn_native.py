import urllib.request
import json
import time

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

def step(messages):
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

def main():
    print("=" * 70)
    print("TESTING REAL MULTI-TURN CONVERSATION FLOW (INCIDENT 29 -> 27)")
    
    # 1. User Turn 1
    q1 = "check cho chị giá bán của mã hàng 156279430 15:49 6 thg 11"
    print(f"\n[TURN 1] User: {q1}")
    history = [{"role": "user", "content": q1}]
    
    res1 = step(history)
    msg1 = res1["choices"][0]["message"]
    tc1 = msg1.get("tool_calls")[0]
    print(f" -> Model called: {tc1['function']['name']}({tc1['function']['arguments']})")
    
    r1 = execute_tool_directly(tc1["function"]["name"], json.loads(tc1["function"]["arguments"]))
    history.append(msg1)
    history.append({"role": "tool", "tool_call_id": tc1["id"], "content": r1})
    
    res1_ans = step(history)
    ans1 = res1_ans["choices"][0]["message"]
    print(f" -> AI Answer: {ans1['content']}")
    history.append(ans1)
    
    # 2. User Turn 2 (Follow-up question inheriting material 156279430)
    q2 = "cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11"
    print(f"\n[TURN 2] User: {q2}")
    history.append({"role": "user", "content": q2})
    
    res2 = step(history)
    msg2 = res2["choices"][0]["message"]
    tc2 = msg2.get("tool_calls")
    if tc2:
        tc2 = tc2[0]
        print(f" -> Model called: {tc2['function']['name']}({tc2['function']['arguments']})")
        r2 = execute_tool_directly(tc2["function"]["name"], json.loads(tc2["function"]["arguments"]))
        history.append(msg2)
        history.append({"role": "tool", "tool_call_id": tc2["id"], "content": r2})
        res2_ans = step(history)
        ans2 = res2_ans["choices"][0]["message"]
        print(f" -> AI Answer: {ans2['content']}")
    else:
        print(f" -> Direct Answer: {msg2.get('content')}")

if __name__ == "__main__":
    main()
