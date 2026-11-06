import sqlite3
import sys

with open('/tmp/htmp_postgres_query.py', 'r', encoding='utf-8') as f:
    code = f.read()

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()

# Update tool table
cur.execute("UPDATE tool SET content = ? WHERE id = 'htmp_postgres_query';", (code,))
print(f"Updated tool table, affected rows: {cur.rowcount}")

# Update function table
cur.execute("UPDATE function SET content = ? WHERE id = 'htmp_postgres_query';", (code,))
print(f"Updated function table, affected rows: {cur.rowcount}")

conn.commit()
conn.close()
print("Sync complete successfully!")
