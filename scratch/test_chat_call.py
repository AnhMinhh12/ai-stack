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

def test_question(q):
    print("=" * 60)
    print(f"USER: {q}")
    payload = {
        "model": "htmp-nhanh",
        "messages": [{"role": "user", "content": q}],
        "stream": False
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=HEADERS
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = resp.read()
            res = json.loads(data.decode("utf-8"))
        print(f"Response in {time.time()-t0:.2f}s:")
        choice = res["choices"][0]
        msg = choice["message"]
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            print("Tool calls chosen by model:")
            for tc in tool_calls:
                fn = tc.get("function", {})
                print(f" -> Function: {fn.get('name')}, Args: {fn.get('arguments')}")
        content = msg.get("content")
        if content:
            print(f"Final Answer Content:\n{content}")
        return res
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "check cho chị giá bán của mã hàng 156279430 15:49 6 thg 11"
    test_question(q)
