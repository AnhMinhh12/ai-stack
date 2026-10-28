import sqlite3
import json

con = sqlite3.connect('local_webui.db')
cur = con.cursor()
for row in cur.execute('SELECT id, name, meta, params FROM model'):
    print('Model ID:', row[0], '| Name:', row[1])
    try:
        meta = json.loads(row[2]) if row[2] else {}
        print('  meta.toolIds:', meta.get('toolIds'))
        print('  meta.tools:', meta.get('tools'))
    except Exception as e:
        print('  error:', e)
con.close()
