import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT id, name, specs, content FROM tool WHERE id = 'htmp_office_editor'")
row = cur.fetchone()
if row:
    print("ID:", row[0])
    print("Specs:", json.dumps(json.loads(row[2]), indent=2))
    print("Content preview (first 40 lines):")
    print("\n".join(row[3].splitlines()[:40]))
