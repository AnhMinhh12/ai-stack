import sqlite3, json, re
from erp_ai.rich_ui import render_erp_embed

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()

sample = {"blocks": [{"type": "table", "columns": [{"key": "a", "label": "A"}], "rows": []}]}
sample_html = render_erp_embed(sample, [])
h_start = sample_html.find('<script>\n(function() {')
h_end = sample_html.find('</style>') + len('</style>')
new_style_block = sample_html[h_start:h_end]

cur.execute("SELECT id, share_id, title, chat FROM chat;")
rows = cur.fetchall()

migrated = 0
for cid, share_id, title, chat_content in rows:
    try:
        data = json.loads(chat_content)
        changed = [False]

        def update_html(val):
            if isinstance(val, str) and ('<!doctype html>' in val or '<div id="erp-root">' in val):
                # Check if it has old style or missing new script
                if 'getTheme()' not in val:
                    # Replace style or insert before </head>
                    if '<style>' in val and '</style>' in val:
                        s_idx = val.find('<style>')
                        e_idx = val.find('</style>') + len('</style>')
                        changed[0] = True
                        return val[:s_idx] + new_style_block + val[e_idx:]
                    elif '</head>' in val:
                        h_idx = val.find('</head>')
                        changed[0] = True
                        return val[:h_idx] + new_style_block + val[h_idx:]
            return val

        def walk(obj):
            if isinstance(obj, dict):
                for k in list(obj.keys()):
                    v = obj[k]
                    if isinstance(v, (dict, list)):
                        walk(v)
                    elif isinstance(v, str):
                        obj[k] = update_html(v)
            elif isinstance(obj, list):
                for i in range(len(obj)):
                    v = obj[i]
                    if isinstance(v, (dict, list)):
                        walk(v)
                    elif isinstance(v, str):
                        obj[i] = update_html(v)

        walk(data)
        if changed[0]:
            new_json = json.dumps(data, ensure_ascii=False)
            cur.execute("UPDATE chat SET chat = ? WHERE id = ?;", (new_json, cid))
            migrated += 1
            print(f"Updated chat: {cid} | share_id: {share_id} | title: {title}")
    except Exception as e:
        print(f"Error in chat {cid}: {e}")

conn.commit()
print(f"Done! Updated {migrated} chats.")
conn.close()
