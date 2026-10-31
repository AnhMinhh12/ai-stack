import sys, sqlite3

sys.path.insert(0, '/app/backend')
con = sqlite3.connect('/app/backend/data/webui.db')
content = con.cursor().execute("SELECT content FROM tool WHERE id = 'htmp_postgres_query'").fetchone()[0]
scope = {}
exec(content, scope)
t = scope['Tools']()

tests = [
    "Mã hàng QC7-5146-000 được khai báo thuộc khách hàng nào?",
    "Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long có mã khách hàng nào trên ERP?",
    "Lệnh giao hàng 001-2610-001811 được ghi nhận hoàn thành khi nào? Cho biết trạng thái lệnh và căn cứ thời gian được dùng.",
    "Khuôn FE8-3324-001-11A đã chạy tổng cộng bao nhiêu shot",
    "Bảng kê đơn hàng bán của khách hàng mã KH0047"
]

for q in tests:
    print("\n" + "=" * 50)
    print("Q:", q)
    res = t.ask_erp(q)
    if isinstance(res, tuple):
        html_resp, ctx = res
        print("-> Returned TUPLE (Rich UI Table rendered)")
        print("   Summary:", ctx.get('summary'))
        print("   Row count:", ctx.get('row_count'))
    elif isinstance(res, str):
        print("-> Returned DIRECT TEXT (Clean response, NO unnecessary table!):")
        print("  ", res[:250])
    else:
        print("-> Returned OTHER:", type(res))
