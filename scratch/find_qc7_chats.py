import sqlite3, json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("""
SELECT u.id, u.name, u.email, c.id, c.title, c.updated_at, c.chat
FROM chat c 
JOIN user u ON c.user_id = u.id 
WHERE c.chat LIKE '%QC7-5146-000%' 
ORDER BY c.updated_at DESC LIMIT 10;
""")
rows = cur.fetchall()
print(f"Found {len(rows)} chats:")
for uid, name, email, cid, title, updated_at, chat_str in rows:
    print(f"User: {name} ({email}) | Chat ID: {cid} | Title: {title} | Updated: {updated_at}")
    try:
        data = json.loads(chat_str)
        messages = data.get('messages', [])
        print(f"  Total messages: {len(messages)}")
        for m in messages[:4]:
            role = m.get('role')
            content = str(m.get('content', ''))[:150]
            embeds = len(m.get('embeds', [])) if m.get('embeds') else 0
            print(f"    [{role}] {content}... (embeds={embeds})")
    except Exception as e:
        print("  Error parsing chat JSON:", e)

conn.close()
