import sqlite3, json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()

cur.execute("SELECT chat FROM chat WHERE share_id = 'd33d10a6-d086-431b-97a7-25e30d5c8ee5';")
row = cur.fetchone()
chat = json.loads(row[0])
history = chat.get('history', {})
messages = history.get('messages', {})

msg = messages.get('72bfe90d-6199-46ae-b4c4-1f4223049787', {})
output = msg.get('output', {})
print("Output type:", type(output))
if isinstance(output, dict):
    print("Output keys:", list(output.keys()))
    print("Output content snippet:", json.dumps(output, ensure_ascii=False)[:600])
else:
    print("Output raw:", str(output)[:600])
