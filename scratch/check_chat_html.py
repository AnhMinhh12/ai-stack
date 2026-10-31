import sqlite3, json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT chat FROM chat WHERE share_id = 'd33d10a6-d086-431b-97a7-25e30d5c8ee5';")
raw = cur.fetchone()[0]
if '<!doctype html>' in raw or '<style>' in raw or '<table' in raw:
    print("Found HTML embedded inside chat JSON!")
    idx = raw.find('<style>')
    print("Style snippet in chat JSON:", raw[idx:idx + 300])
else:
    print("No HTML embedded in chat JSON; tool output is plain JSON/text.")
