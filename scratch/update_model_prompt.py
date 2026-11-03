import sqlite3, json, time, subprocess

script = """
import sqlite3, json, time
conn = sqlite3.connect('/app/backend/data/webui.db')
c = conn.cursor()
c.execute("SELECT params FROM model WHERE id = 'htmp-nhanh'")
r = c.fetchone()
params = json.loads(r[0])
base_prompt = params['system'].split(' QUY TẮC BIỂU ĐỒ:')[0].strip()
chart_rule = ' QUY TẮC BIỂU ĐỒ: Khi kết quả tra cứu từ ask_erp có chứa biểu đồ trực quan (khối code ' + chr(96)*3 + 'mermaid), BẮT BUỘC giữ nguyên toàn bộ khối code ' + chr(96)*3 + 'mermaid đó đặt ngay phía dưới bảng số liệu để hiển thị biểu đồ phân tích trực quan cho người dùng.'
params['system'] = base_prompt + chart_rule
c.execute("UPDATE model SET params = ?, updated_at = ? WHERE id = 'htmp-nhanh'", (json.dumps(params, ensure_ascii=False), int(time.time())))
conn.commit()
print("PROMPT UPDATED SUCCESSFULLY")
"""
res = subprocess.run(['docker', 'exec', '-i', 'open-webui', 'python3'], input=script, text=True, capture_output=True)
print(res.stdout)
print(res.stderr)
