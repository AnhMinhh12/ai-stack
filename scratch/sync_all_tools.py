import sqlite3
import time

with open('/home/admin/ai-stack/functions/htmp_postgres_query.py', 'r', encoding='utf-8') as f:
    code = f.read()

now = int(time.time())

# 1. Host local_webui.db
con = sqlite3.connect('/home/admin/ai-stack/local_webui.db')
cur = con.cursor()
cur.execute('UPDATE tool SET content = ?, updated_at = ? WHERE id = "htmp_postgres_query"', (code, now))
con.commit()
print("Updated host local_webui.db:", cur.rowcount)
con.close()

# 2. Container /app/backend/data/webui.db
import subprocess
res = subprocess.run([
    'docker', 'exec', 'open-webui', 'python3', '-c',
    f'''import sqlite3, time
con = sqlite3.connect("/app/backend/data/webui.db")
with open("/tmp/code.py", "r", encoding="utf-8") as f:
    code = f.read()
con.cursor().execute("UPDATE tool SET content = ?, updated_at = ? WHERE id = 'htmp_postgres_query'", (code, {now}))
con.commit()
print("Updated container webui.db")
con.close()'''
], capture_output=True, text=True)

# Copy code to /tmp/code.py first
subprocess.run(['docker', 'cp', '/home/admin/ai-stack/functions/htmp_postgres_query.py', 'open-webui:/tmp/code.py'])
res = subprocess.run([
    'docker', 'exec', 'open-webui', 'python3', '-c',
    f'''import sqlite3, time
con = sqlite3.connect("/app/backend/data/webui.db")
with open("/tmp/code.py", "r", encoding="utf-8") as f:
    code = f.read()
con.cursor().execute("UPDATE tool SET content = ?, updated_at = ? WHERE id = 'htmp_postgres_query'", (code, {now}))
con.commit()
print("Updated container webui.db successfully")
con.close()'''
], capture_output=True, text=True)
print("Container update:", res.stdout, res.stderr)
