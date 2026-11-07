import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT id, name, content FROM tool WHERE id = 'htmp_erp_agent'")
row = cur.fetchone()
if row:
    print("ID:", row[0])
    print("Name:", row[1])
    print("Content preview:")
    print(row[2][:1500])
else:
    print("Not found!")
