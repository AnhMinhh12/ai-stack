import sqlite3, json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT c.id, u.name, u.email, c.title, c.chat FROM chat c JOIN user u ON c.user_id = u.id WHERE c.id = '60cef3c3-1278-4e3c-b63c-b8eabe6b188e';")
row = cur.fetchone()
if row:
    cid, name, email, title, chat_str = row
    print(f"=== Chat: {title} by {name} ({email}) ===")
    d = json.loads(chat_str)
    hm = d.get('history', {}).get('messages', {})
    # follow the linked list or sort by timestamp
    msg_list = sorted(hm.values(), key=lambda x: x.get('timestamp', 0))
    for m in msg_list:
        role = m.get('role')
        content = m.get('content', '')
        embeds = m.get('embeds', [])
        print(f"\n--- [{role.upper()}] (embeds={len(embeds)}) ---")
        print(content)
        if embeds:
            print(">>> EMBED HTML PREVIEW (first 500 chars):")
            print(embeds[0][:500])
conn.close()
