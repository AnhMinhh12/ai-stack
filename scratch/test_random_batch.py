import sys
import time
import json
import sqlite3

sys.path.insert(0, '/app/backend')

con = sqlite3.connect('/app/backend/data/webui.db')
content = con.cursor().execute('SELECT content FROM tool WHERE id = "htmp_postgres_query"').fetchone()[0]
con.close()

scope = {}
exec(content, scope)
Tools = scope.get('Tools')
tools = Tools()

test_questions = [
    # 1. Tồn kho theo khuôn cho mã khác: QC7-9498-001
    ("Mã QC7-9498-001 hiện có tồn kho thuộc những khuôn nào, số lượng từng khuôn?", "QC7-9498-001 / Khuôn Die"),
    
    # 2. Tồn kho theo khuôn cho mã khác: QL3-4766-000
    ("Mã QL3-4766-000 hiện có tồn kho thuộc những khuôn nào?", "QL3-4766-000 / Khuôn Die"),

    # 3. Tồn kho theo từng kho của mã QC7-5146-000
    ("Tồn kho hiện tại của mã QC7-5146-000 là bao nhiêu ở từng kho?", "QC7-5146-000 / Phân bổ kho"),

    # 4. Nhập kho từ 01/10 đến 20/10 của mã QC7-5146-000
    ("Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 được nhập kho vào những ngày nào, từ kho nào sang kho nào, số lượng bao nhiêu?", "QC7-5146-000 / Nhập theo ngày"),

    # 5. So sánh DO và FCST
    ("So sánh DO và FCST hiện tại với bản trước của mã QC7-5146-000: số lượng tăng hay giảm bao nhiêu?", "QC7-5146-000 / So sánh DO vs FCST"),

    # 6. Kiểm tra trạng thái QC
    ("Mã QC7-5146-000 hiện có lot thành phẩm nào ở trạng thái QC cần chú ý? Cho biết trạng thái QC đúng như dữ liệu ERP.", "QC7-5146-000 / Trạng thái QC"),

    # 7. BOM cấu trúc mã QC7-5146-000 (Chỉ ra bảng/text, không biểu đồ)
    ("Mã hàng QC7-5146-000 dùng loại nhựa gì? Cấu trúc sản phẩm của mã hàng này gồm những gì?", "QC7-5146-000 / Cấu trúc BOM"),

    # 8. Báo giá & MOQ mã QC7-5146-000
    ("MOQ báo giá hiện tại của mã QC7-5146-000 là bao nhiêu? Giá áp dụng hiện tại theo từng mức MOQ là bao nhiêu?", "QC7-5146-000 / Giá MOQ")
]

results = []
print("=================== BẮT ĐẦU KIỂM THỬ BỘ CÂU HỎI NGẪU NHIÊN ===================")
for idx, (q, label) in enumerate(test_questions, 1):
    t0 = time.time()
    try:
        # We call ask_erp
        res = tools.ask_erp(q)
        duration = round(time.time() - t0, 3)
        
        has_chart = False
        chart_kind = None
        has_table = False
        row_count = 0
        allowed_charts = []
        is_html_tuple = isinstance(res, tuple)

        if is_html_tuple:
            html_resp, extra = res
            body = html_resp.body.decode('utf-8')
            has_table = '<table' in body
            has_chart = '<canvas id="chart-' in body
            row_count = extra.get('row_count') or len(extra.get('rows') or [])
            if 'const charts = ' in body:
                try:
                    line = [l for l in body.splitlines() if 'const charts = ' in l][0]
                    c_json = line.replace('const charts = ', '').rstrip(';')
                    parsed = json.loads(c_json)
                    if parsed:
                        chart_kind = parsed[0].get('kind')
                        allowed_charts = parsed[0].get('allowed')
                except Exception:
                    pass
            msg = extra.get('message') or extra.get('display_message') or 'OK'
        else:
            msg = str(res)[:150]

        results.append({
            "idx": idx,
            "label": label,
            "question": q,
            "duration": duration,
            "is_html": is_html_tuple,
            "has_table": has_table,
            "has_chart": has_chart,
            "chart_kind": chart_kind,
            "allowed_charts": allowed_charts,
            "row_count": row_count,
            "snippet": msg[:180]
        })
        print(f"[{idx}] {label} ({duration}s) | Table: {has_table} (rows: {row_count}) | Chart: {has_chart} ({chart_kind}, allowed: {allowed_charts})")
    except Exception as e:
        duration = round(time.time() - t0, 3)
        print(f"[{idx}] {label} ERROR ({duration}s): {e}")

print("\n=================== TỔNG KẾT KẾT QUẢ ===================")
with open('/tmp/random_test_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("Saved details to /tmp/random_test_results.json")
