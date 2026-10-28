import sys
import json

sys.path.insert(0, '/home/admin/ai-stack')
from functions.htmp_postgres_query import Tools

t = Tools()
res = t.ask_erp("Mã QC7-5146-000 hiện có tồn kho thuộc những khuôn nào?")
print("Result type:", type(res))
if isinstance(res, tuple):
    html_resp, extra = res
    print("HTML Response content length:", len(html_resp.body))
    body = html_resp.body.decode('utf-8')
    print("Has canvas chart in html:", 'canvas id="chart-' in body)
    print("Has btn-xlsx in html:", 'btn-xlsx' in body)
    print("Has Pie chart in html:", 'Cơ cấu tồn kho tem thành phẩm' in body)
    print("Extra payload keys:", list(extra.keys()))
else:
    print("Res is str/dict:", str(res)[:300])
