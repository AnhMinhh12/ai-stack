import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()

print("--- MODELS ---")
cur.execute("SELECT id, name, base_model_id, params, meta FROM model")
for r in cur.fetchall():
    print(f"ID: {r[0]}, Name: {r[1]}, Base: {r[2]}")
    meta = json.loads(r[4]) if r[4] else {}
    print(f"  Capabilities: {meta.get('capabilities', {})}")
    print(f"  Tools: {meta.get('toolIds', [])}")
    print(f"  Profile/System: {repr(meta.get('profile', ''))[:100]}")

print("\n--- TOOLS ---")
cur.execute("SELECT id, name, user_id FROM tool")
for r in cur.fetchall():
    print(f"Tool ID: {r[0]}, Name: {r[1]}")

print("\n--- FUNCTIONS ---")
cur.execute("SELECT id, name, type FROM function")
for r in cur.fetchall():
    print(f"Function ID: {r[0]}, Name: {r[1]}, Type: {r[2]}")
