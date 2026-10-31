import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:80"
API_KEY = "sk-1ce52487dd424dc4b2e8c54fe7041f8c"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def ask_chat(q):
    t0 = time.time()
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
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        duration = round(time.time() - t0, 2)
        choice = data["choices"][0]["message"]
        return choice, duration

print(">>> Calling End-to-End API: số lượng khuôn NG của nhà máy")
res1, dur1 = ask_chat("số lượng khuôn NG của nhà máy")
print(f"Time: {dur1}s")
print("Role:", res1.get("role"))
print("Content:", res1.get("content"))

print("\n>>> Calling End-to-End API: tổng số lượng khuôn của nhà máy là bao nhiêu")
res2, dur2 = ask_chat("tổng số lượng khuôn của nhà máy là bao nhiêu")
print(f"Time: {dur2}s")
print("Role:", res2.get("role"))
print("Content:", res2.get("content"))
