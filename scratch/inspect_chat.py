# scratch/inspect_chat.py
import sqlite3
import json

conn = sqlite3.connect('/tmp/live-webui.db')
cur = conn.cursor()
cur.execute("SELECT title, chat FROM chat WHERE id = '95c67968-935b-422a-be22-fb3061fabfba';")
row = cur.fetchone()
if row:
    print("Title:", row[0])
    chat_data = json.loads(row[1])
    messages = chat_data.get('history', {}).get('messages', {})
    for mid, m in messages.items():
        role = m.get('role')
        content = m.get('content')
        print(f"\n--- [{role}] (id: {mid}) ---")
        print(content[:300] if content else "(no content)")
        if 'tool_calls' in m:
            print("Tool calls:", m['tool_calls'])
        if role == 'tool':
            print("Tool result:", content[:200])

conn.close()
