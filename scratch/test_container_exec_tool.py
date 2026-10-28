import sqlite3
import json
import sys
sys.path.insert(0, '/app/backend')

con = sqlite3.connect('/app/backend/data/webui.db')
content = con.cursor().execute('SELECT content FROM tool WHERE id = "htmp_postgres_query"').fetchone()[0]
con.close()

# Exec the tool class
scope = {}
exec(content, scope)
Tools = scope.get('Tools')
t = Tools()
res = t.ask_erp("Mã QC7-5146-000 hiện có tồn kho thuộc những khuôn nào?")
print("Result type:", type(res))
if isinstance(res, tuple):
    html_resp, extra = res
    body = html_resp.body.decode('utf-8')
    print("Has canvas chart:", 'canvas id="chart-' in body)
    print("Has btn-xlsx:", 'btn-xlsx' in body)
    print("Has Pie chart block:", 'Cơ cấu tồn kho' in body)
    print("HTML length:", len(body))
    # Let's check chart data payload in script
    for line in body.splitlines():
        if 'const charts = ' in line:
            print("Charts line snippet:", line[:200])
else:
    print("Result not tuple:", str(res)[:300])
