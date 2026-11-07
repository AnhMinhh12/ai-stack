import os
import json
import httpx

base_url = "http://vllm:8000/v1"
api_key = os.environ.get("VLLM_API_KEY", "")

with open('/tmp/test_vllm_cases.json') as f:
    data = json.load(f)

tools = data['tools']
test_cases = data['test_cases']

client = httpx.Client(base_url=base_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=60)

for tc in test_cases:
    print("\n" + "=" * 70)
    print("TEST CASE:", tc['name'])
    print("User prompt:", tc['messages'][-1]['content'])
    payload = {
        "model": "qwen2.5-14b",
        "messages": tc['messages'],
        "tools": tools,
        "tool_choice": "auto",
        "temperature": 0
    }
    resp = client.post("chat/completions", json=payload)
    if resp.status_code != 200:
        print("ERROR:", resp.status_code, resp.text)
        continue
    msg = resp.json()["choices"][0]["message"]
    tool_calls = msg.get("tool_calls")
    if tool_calls:
        for tc_call in tool_calls:
            print(">>> FUNCTION CALLED:", tc_call["function"]["name"])
            print(">>> ARGUMENTS:", tc_call["function"]["arguments"])
    else:
        print(">>> CONTENT (No tool call):", msg.get("content"))
