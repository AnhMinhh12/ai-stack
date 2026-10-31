import sqlite3, json, datetime

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("""
SELECT c.id, u.name, u.email, c.title, c.updated_at, c.chat
FROM chat c
JOIN user u ON c.user_id = u.id
WHERE u.name LIKE '%Trường%' OR u.email LIKE '%4509%'
ORDER BY c.updated_at DESC LIMIT 3;
""")
rows = cur.fetchall()
for cid, name, email, title, updated_at, chat_str in rows:
    dt = datetime.datetime.fromtimestamp(updated_at).strftime('%Y-%m-%d %H:%M:%S')
    print(f"=== [{dt}] User: {name} ({email}) | Chat ID: {cid} | Title: {title} ===")
    d = json.loads(chat_str)
    msgs = []
    if 'history' in d and 'messages' in d['history']:
        msgs = list(d['history']['messages'].values())
    elif 'messages' in d:
        msgs = d['messages']
    msgs.sort(key=lambda x: x.get('timestamp', 0))
    for m in msgs:
        role = m.get('role')
        content = m.get('content', '')
        embeds = m.get('embeds', [])
        print(f"\n--- [{role.upper()}] (embeds={len(embeds)}) ---")
        print(content)
        if embeds:
            print(">>> EMBED PREVIEW:", embeds[0][:400])

conn.close()
