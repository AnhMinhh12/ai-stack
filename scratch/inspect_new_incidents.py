import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
c = conn.cursor()

chat_ids = [
    '5e43f73b-ced6-4555-8940-bf7f6312fc7e',
    'bc95ab06-bd72-48ac-b883-fa4a8ba9e144',
    '025ccc32-c329-4c1c-901d-556b509eb584'
]

for cid in chat_ids:
    print("=" * 80)
    print("CHAT ID:", cid)
    row = c.execute("SELECT id, title, chat FROM chat WHERE id = ?", (cid,)).fetchone()
    if not row:
        print("Chat not found in webui.db")
        # try like query
        rows = c.execute("SELECT id, title, chat FROM chat WHERE id LIKE ?", (f"%{cid[:8]}%",)).fetchall()
        for r in rows:
            print("Found partial:", r[0], r[1])
            row = r
            break
    if row:
        chat_data = json.loads(row[2])
        messages = chat_data.get('messages', [])
        for m in messages:
            print(f"[{m.get('role')}]: {m.get('content')}")
            if m.get('tool_calls'):
                print(f"  TOOL CALLS: {json.dumps(m.get('tool_calls'), ensure_ascii=False)}")
