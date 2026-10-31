import sys, json, sqlite3

sys.path.insert(0, '/app/backend')
con = sqlite3.connect('/app/backend/data/webui.db')
content = con.cursor().execute("SELECT content FROM tool WHERE id = 'htmp_postgres_query'").fetchone()[0]
scope = {}
exec(content, scope)
t = scope['Tools']()

questions = [
    "số lượng khuôn NG của nhà máy",
    "tổng số lượng khuôn của nhà máy là bao nhiêu"
]

for q in questions:
    print("=" * 60)
    print("TEST QUESTION:", q)
    print("=" * 60)
    res = t.ask_erp(q)
    if isinstance(res, tuple):
        # res[0] is HTMLResponse, res[1] is dict
        ctx = res[1]
        print("Success: TUPLE RETURNED (Rich UI + LLM Context)")
        print("Source:", ctx.get("source"))
        print("Message:", ctx.get("message"))
        print("Row count:", ctx.get("row_count"))
        print("Summary:", ctx.get("summary"))
    else:
        print("Raw output:", str(res)[:300])
