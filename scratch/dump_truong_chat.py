import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
c = conn.cursor()

c.execute("SELECT id, title, updated_at, chat FROM chat WHERE user_id = 'fdb0a582-6fa3-4a53-81b0-87427f1438fe' ORDER BY updated_at DESC")
rows = c.fetchall()

for row in rows:
    chat_id, title, updated, chat_str = row
    chat = json.loads(chat_str)
    print("=" * 80)
    print(f"CHAT: {title} ({chat_id})")
    print("=" * 80)
    
    messages = []
    if 'history' in chat and 'messages' in chat['history']:
        msgs = chat['history']['messages']
        if isinstance(msgs, dict):
            messages = list(msgs.values())
            messages.sort(key=lambda x: x.get('timestamp', 0))
    elif 'messages' in chat:
        messages = chat['messages']

    for m in messages:
        role = m.get('role', 'unknown').upper()
        content = m.get('content', '')
        print(f"[{role}]:\n{content}\n" + "-"*50)
