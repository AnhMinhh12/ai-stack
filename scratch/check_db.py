import sqlite3
conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT id, name, updated_at, length(content) FROM function WHERE id = 'htmp_postgres_query';")
row = cur.fetchone()
print('Function in DB:', row)
