import sqlite3

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()

cur.execute("SELECT chat FROM chat WHERE share_id = 'd33d10a6-d086-431b-97a7-25e30d5c8ee5';")
raw = cur.fetchone()[0]

start = raw.find('<style>')
end = raw.find('</style>', start) + len('</style>')
print("Old style snippet:\n", raw[start:end])
