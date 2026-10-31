import sys
sys.path.insert(0, '/tmp')
from htmp_postgres_query import Tools
import json

tools = Tools()

test_queries = [
    'thế 25hi117 đang có shot hiện tại là bao nhiêu',
    'thế 25HI117',
    'thế 25HI83 đang có shot hiện tại là bao nhiêu',
    'khuôn 25HI117 có bao nhiêu cavity',
    '4509 là ai',
    'mã khuôn có số shot hiện tại nhiều nhất',
]

for q in test_queries:
    print(f"\n==================== QUERY: {q} ====================")
    try:
        res = tools.ask_erp(q)
    except Exception as e:
        print("EXCEPTION:", e)
        continue
    try:
        data = json.loads(res)
        print("RESULT keys:", list(data.keys()))
        print("MESSAGE:", data.get("message"))
        print("ROW COUNT:", data.get("row_count"))
        if data.get("rows"):
            print("FIRST ROW:", data["rows"][0])
    except Exception as e:
        print("RAW RES:", res[:300])
