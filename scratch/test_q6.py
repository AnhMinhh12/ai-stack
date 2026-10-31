import sys, json, sqlite3

sys.path.insert(0, '/app/backend')
con = sqlite3.connect('/app/backend/data/webui.db')
content = con.cursor().execute("SELECT content FROM tool WHERE id = 'htmp_postgres_query'").fetchone()[0]
scope = {}
exec(content, scope)
t = scope['Tools']()

res = t._ask_erp_data("Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 được nhập kho vào những ngày nào, từ kho nào sang kho nào, số lượng bao nhiêu và tài khoản nào tạo phiếu?")
print("Type of res:", type(res))
if isinstance(res, str):
    try:
        d = json.loads(res)
        print("Keys:", list(d.keys()))
        print("Row count:", d.get("row_count"))
        print("Message:", d.get("message"))
        rows = d.get("rows", [])
        print(f"Total rows: {len(rows)}")
        for r in rows[:5]:
            print(r)
    except Exception:
        print("Raw text:", res[:500])
else:
    print("Res:", res)
