import sqlite3, json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT chat FROM chat WHERE share_id = 'd33d10a6-d086-431b-97a7-25e30d5c8ee5';")
raw = cur.fetchone()[0]
data = json.loads(raw)
embeds = data['history']['messages']['72bfe90d-6199-46ae-b4c4-1f4223049787']['output'][1]['embeds']
print("Embeds count:", len(embeds))
print("First 300 chars of embeds[0]:\n", embeds[0][:300])
