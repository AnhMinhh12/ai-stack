import sqlite3, json, datetime

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("""
SELECT c.id, u.name, u.email, c.title, c.updated_at, c.chat
FROM chat c
JOIN user u ON c.user_id = u.id
ORDER BY c.updated_at DESC LIMIT 25;
""")
rows = cur.fetchall()
print(f"Latest 25 chats in webui.db:")
for cid, name, email, title, updated_at, chat_str in rows:
    dt = datetime.datetime.fromtimestamp(updated_at).strftime('%Y-%m-%d %H:%M:%S')
    data = json.loads(chat_str)
    msgs = data.get('messages', [])
    user_msgs = [m.get('content', '')[:80] for m in msgs if m.get('role') == 'user']
    has_embeds = any(bool(m.get('embeds')) for m in msgs)
    print(f"[{dt}] User: {name} ({email}) | Title: {title} | Msgs: {len(msgs)} | Embeds: {has_embeds}")
    if user_msgs:
        print(f"   Last Q: {user_msgs[-1]}")

conn.close()
