import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/erp-incidents.db')
c = conn.cursor()
for row in c.execute("SELECT id, created_at, user_id, chat_id, stage, code, chat_excerpt FROM incidents ORDER BY id DESC LIMIT 5"):
    print("=" * 60)
    print(f"ID: {row[0]}, Created: {row[1]}, User: {row[2]}, Stage: {row[4]}, Code: {row[5]}")
    try:
        data = json.loads(row[6])
        print("EXCERPT JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print("EXCERPT TEXT:", row[6])
