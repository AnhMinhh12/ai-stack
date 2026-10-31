import sqlite3, json, sys
sys.path.insert(0, '/app/backend')

from erp_ai.rich_ui import render_erp_embed

sample = {"blocks": [{"type": "table", "columns": [{"key": "a", "label": "A"}], "rows": []}]}
sample_html = render_erp_embed(sample, [])
h_start = sample_html.find('<head>') + len('<head>')
h_end = sample_html.find('</head>')
new_head_inner = sample_html[h_start:h_end]

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()

cur.execute("SELECT id, share_id, title, chat FROM chat;")
rows = cur.fetchall()

listener_code = """
window.addEventListener('message', event => {
  if (event.data && (event.data.type === 'erp:theme' || event.data.theme)) {
    const theme = event.data.theme || (event.data.isDark ? 'dark' : 'light');
    applyTheme(theme);
    if (window.Chart && activeCharts.size > 0) {
      charts.forEach((item, index) => {
        const btn = document.querySelector('[data-chart-index="' + index + '"][aria-pressed="true"]');
        const kind = btn ? btn.dataset.chartKind : item.kind;
        showChart(index, kind);
      });
    }
  }
});
"""

count = 0
for cid, share_id, title, chat_content in rows:
    try:
        data = json.loads(chat_content)
        modified = [False]

        def update_html(val):
            if isinstance(val, str) and '<!doctype html>' in val and '<div id="erp-root">' in val:
                s_idx = val.find('<head>')
                e_idx = val.find('</head>')
                if s_idx != -1 and e_idx != -1:
                    modified[0] = True
                    val = val[:s_idx + len('<head>')] + new_head_inner + val[e_idx:]
                    if "type === 'erp:theme'" not in val:
                        ls_idx = val.find('</script></body>')
                        if ls_idx != -1:
                            val = val[:ls_idx] + listener_code + val[ls_idx:]
                    return val
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
                        walk(obj[i])
                    elif isinstance(v, str):
                        obj[i] = update_html(v)

        walk(data)
        if modified[0]:
            new_json = json.dumps(data, ensure_ascii=False)
            cur.execute("UPDATE chat SET chat = ? WHERE id = ?;", (new_json, cid))
            count += 1
            print(f"Updated chat: {cid} | share_id: {share_id} | title: {title}")
    except Exception as e:
        print(f"Error in {cid}: {e}")

conn.commit()
print(f"Total updated: {count}")
conn.close()
