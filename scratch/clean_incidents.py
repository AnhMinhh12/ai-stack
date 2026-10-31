import sqlite3

conn = sqlite3.connect('/app/backend/data/erp-incidents.db')
c = conn.cursor()

# Check what we have
c.execute("SELECT id, datetime(created_at, 'unixepoch', 'localtime'), user_id, chat_id, stage, code FROM incidents ORDER BY id DESC")
rows = c.fetchall()
print("BEFORE:")
for r in rows:
    print(r)

# Remove the test records generated during CLI test
c.execute("DELETE FROM incidents WHERE id IN (1, 5, 6, 7) OR user_id = ''")
print(f"Deleted {c.rowcount} test rows.")
conn.commit()

c.execute("SELECT id, datetime(created_at, 'unixepoch', 'localtime'), user_id, chat_id, stage, code FROM incidents ORDER BY id DESC")
print("AFTER:")
for r in c.fetchall():
    print(r)

conn.close()
