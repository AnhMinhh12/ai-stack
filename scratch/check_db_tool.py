import sqlite3

for db_path in ['/home/admin/ai-stack/local_webui.db']:
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        rows = cur.execute('SELECT id, name, updated_at FROM tool').fetchall()
        print(f"Tools in {db_path}:", rows)
        # Check if ask_erp is in content
        for r in rows:
            tool_id = r[0]
            content = cur.execute('SELECT content FROM tool WHERE id = ?', (tool_id,)).fetchone()[0]
            print(f"Tool {tool_id} content length: {len(content)}, has ask_erp: {'def ask_erp' in content}")
    except Exception as e:
        print(f"Error {db_path}: {e}")
