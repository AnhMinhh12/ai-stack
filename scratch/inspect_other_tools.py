import sqlite3

con = sqlite3.connect('local_webui.db')
cur = con.cursor()
for row in cur.execute('SELECT id, name, meta, substring(content, 1, 500) FROM tool WHERE id != "htmp_postgres_query"'):
    print(f"=== Tool: {row[0]} ({row[1]}) ===")
    print(row[3])
    print()
con.close()
