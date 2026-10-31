import sqlite3, json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT id, share_id, title, chat FROM chat WHERE share_id = 'd33d10a6-d086-431b-97a7-25e30d5c8ee5';")
row = cur.fetchone()
if not row:
    print("Chat not found!")
else:
    cid, sid, title, chat = row
    print(f"Found chat: id={cid}, share_id={sid}, title={title}")
    print("Has --text-main: #f8fafc:", "--text-main: #f8fafc" in chat)
    print("Has --table-bg: rgba(24, 24, 27, 0.65):", "--table-bg: rgba(24, 24, 27, 0.65)" in chat)
    print("Has old black text (#0f172a as root):", ":root, [data-theme=\"dark\"]" in chat and "--text-main: #f8fafc" in chat)
conn.close()
