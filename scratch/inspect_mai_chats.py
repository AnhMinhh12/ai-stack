import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
c = conn.cursor()

rows = c.execute("SELECT id, title, updated_at, chat FROM chat WHERE user_id = 'efc95a40-b12a-4a67-a4bf-400bdd36160e' ORDER BY updated_at DESC LIMIT 6").fetchall()
for r in rows:
    print("=" * 80)
    print("CHAT ID:", r[0], "Title:", r[1], "Updated:", r[2])
    chat_data = json.loads(r[3])
    messages = chat_data.get('messages', [])
    for m in messages:
        role = m.get('role')
        content = m.get('content')
        print(f"[{role}]: {content}")
        if m.get('tool_calls'):
            print(f"  TOOL CALLS: {json.dumps(m.get('tool_calls'), ensure_ascii=False)}")
