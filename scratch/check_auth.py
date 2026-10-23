import sqlite3

conn = sqlite3.connect('/home/admin/ai-stack/local_webui.db')
c = conn.cursor()
c.execute('SELECT id, email, password, active FROM auth')
for row in c.fetchall():
    print(row[0], row[1], row[2][:30] if row[2] else None, row[3])
