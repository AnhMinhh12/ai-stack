import sqlite3

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()

cur.execute("SELECT id, share_id, title FROM chat WHERE chat LIKE '%--text-main:#0f172a%';")
rows = cur.fetchall()
print("Chats containing old style:", len(rows))
for r in rows:
    print(r)
