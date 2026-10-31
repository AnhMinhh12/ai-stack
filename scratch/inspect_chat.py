import sqlite3, json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT id, user_id, title, chat FROM chat WHERE id = '60cef3c3-1278-4e3c-b63c-b8eabe6b188e';")
row = cur.fetchone()
if row:
    data = json.loads(row[3])
    print(f"Chat ID: {row[0]}, Title: {row[2]}")
    for m in data.get('messages', []):
        print(f"=== Role: {m.get('role')} ===")
        content = m.get('content', '')
        print('Content:', content[:400])
        embeds = m.get('embeds', [])
        print('Embeds count:', len(embeds))
        if embeds:
            print('Embed[0] length:', len(embeds[0]))
conn.close()
