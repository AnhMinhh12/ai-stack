import sqlite3, json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT chat FROM chat WHERE share_id = 'd33d10a6-d086-431b-97a7-25e30d5c8ee5';")
chat_raw = cur.fetchone()[0]

data = json.loads(chat_raw)

def find_paths(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            find_paths(v, path + f"['{k}']")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_paths(item, path + f"[{i}]")
    elif isinstance(obj, str):
        if '--text-main' in obj:
            print("Found at path:", path)
            print("Snippet:", obj[:200])

find_paths(data)
