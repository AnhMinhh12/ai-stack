import sys, sqlite3

sys.path.insert(0, '/app/backend')
con = sqlite3.connect('/app/backend/data/webui.db')
content = con.cursor().execute("SELECT content FROM tool WHERE id = 'htmp_postgres_query'").fetchone()[0]
scope = {}
exec(content, scope)
t = scope['Tools']()

questions = [
    "khuôn 4509 có bao nhiêu cavity",
    "số cavity của mã khuôn K_101 40481 01 là bao nhiêu",
    "khuôn có cavity là bao nhiêu",
    "khuôn K_QC5-2919-000-V1 có bao nhiêu cavity",
    "Các khuôn 4509 này được sử dụng cho sản phẩm nào?"
]

for q in questions:
    print("\n" + "=" * 60)
    print("USER QUESTION:", q)
    res = t.ask_erp(q)
    if isinstance(res, tuple):
        print("-> Returned TUPLE (Table rendered):")
        print("   Summary:", res[1].get('summary'))
    elif isinstance(res, str):
        print("-> Returned DIRECT TEXT (No table):")
        print("  ", res)
    else:
        print("-> Returned OTHER:", type(res))
