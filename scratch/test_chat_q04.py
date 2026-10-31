import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:80"
API_KEY = "sk-1ce52487dd424dc4b2e8c54fe7041f8c"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

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

def execute_ask_erp_in_container(question):
    import subprocess
    escaped_q = json.dumps(question)
    py_code = f"""
import sys, json, sqlite3
sys.path.insert(0, '/app/backend')
con = sqlite3.connect('/app/backend/data/webui.db')
content = con.cursor().execute("SELECT content FROM tool WHERE id = 'htmp_postgres_query'").fetchone()[0]
scope = {{}}
exec(content, scope)
t = scope['Tools']()
res = t.ask_erp({escaped_q})
if isinstance(res, tuple):
    # res[0] is HTMLResponse, res[1] is the result context dict for LLM
    print(json.dumps(res[1], ensure_ascii=False, default=str))
else:
    print(str(res))
"""
    cmd = ["docker", "exec", "open-webui", "python3", "-c", py_code]
    return subprocess.check_output(cmd, timeout=30).decode("utf-8").strip()

if __name__ == "__main__":
    q = "Cho tôi báo cáo top khách hàng có số lượng đặt hàng lớn nhất trong các đơn hàng bán gần đây"
    print(f"Step 1: Asking Open WebUI: {q}")
    t0 = time.time()
    res1 = call_openwebui([{"role": "user", "content": q}])
    print(f"Model response in {time.time()-t0:.2f}s")
    msg1 = res1["choices"][0]["message"]
    tool_calls = msg1.get("tool_calls", [])
    print(f"Tool calls: {len(tool_calls)}")
    if tool_calls:
        tc = tool_calls[0]
        fn_args = json.loads(tc["function"]["arguments"])
        print(f"Tool: {tc['function']['name']}, Args: {fn_args}")
        
        print("Step 2: Executing tool in container against Postgres...")
        t1 = time.time()
        tool_data_json = execute_ask_erp_in_container(fn_args.get("question", q))
        print(f"Tool finished in {time.time()-t1:.2f}s, output length: {len(tool_data_json)}")
        
        print("Step 3: Sending tool result back to Open WebUI for final user answer...")
        messages = [
            {"role": "user", "content": q},
            msg1,
            {
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": tc["function"]["name"],
                "content": tool_data_json
            }
        ]
        t2 = time.time()
        res2 = call_openwebui(messages)
        print(f"Final response in {time.time()-t2:.2f}s")
        final_text = res2["choices"][0]["message"]["content"]
        print("\n=== FINAL ANSWER FROM CHAT INTERFACE ===\n")
        print(final_text)
        print("\n=========================================\n")
