import sqlite3, json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()

cur.execute("SELECT id, share_id, title, chat FROM chat WHERE chat LIKE '%--text-main:#0f172a%';")
rows = cur.fetchall()
print(f"Found {len(rows)} chats to migrate")

from erp_ai.rich_ui import render_erp_embed

sample = {"blocks": [{"type": "table", "columns": [{"key": "a", "label": "A"}], "rows": []}]}
sample_html = render_erp_embed(sample, [])
h_start = sample_html.find('<script>\n(function() {')
h_end = sample_html.find('</style>') + len('</style>')
new_style_part = sample_html[h_start:h_end]

count = 0
for cid, share_id, title, chat_content in rows:
    try:
        data = json.loads(chat_content)
        modified = [False]

        def transform(val):
            if isinstance(val, str) and '--text-main:#0f172a' in val:
                s_idx = val.find('<style>')
                e_idx = val.find('</style>') + len('</style>')
                if s_idx != -1 and e_idx != -1:
                    modified[0] = True
                    return val[:s_idx] + new_style_part + val[e_idx:]
            return val

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in list(obj.items()):
                    if isinstance(v, (dict, list)):
                        walk(v)
                    elif isinstance(v, str):
                        obj[k] = transform(v)
            elif isinstance(obj, list):
                for i in range(len(obj)):
                    if isinstance(obj[i], (dict, list)):
                        walk(obj[i])
                    elif isinstance(obj[i], str):
                        obj[i] = transform(obj[i])

        walk(data)
        if modified[0]:
            new_json = json.dumps(data, ensure_ascii=False)
            cur.execute("UPDATE chat SET chat = ? WHERE id = ?;", (new_json, cid))
            count += 1
            print(f"Migrated chat {cid} ({title})")
    except Exception as e:
        print(f"Error migrating {cid}: {e}")

conn.commit()
print(f"Successfully migrated {count} chats in webui.db!")
conn.close()
