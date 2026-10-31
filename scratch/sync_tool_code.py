import sqlite3

with open('/tmp/htmp_postgres_query.py', 'r', encoding='utf-8') as f:
    new_content = f.read()

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("UPDATE tool SET content = ? WHERE id = 'htmp_postgres_query';", (new_content,))
print(f"Updated htmp_postgres_query tool in webui.db, affected rows: {cur.rowcount}")
conn.commit()
conn.close()
