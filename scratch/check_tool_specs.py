import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT id, name, meta, specs FROM tool WHERE id = 'htmp_postgres_query'")
row = cur.fetchone()
print("ID:", row[0])
print("Name:", row[1])
print("Specs:", json.dumps(json.loads(row[3]), indent=2))
