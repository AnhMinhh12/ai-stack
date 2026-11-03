import sqlite3
import json
import time

script = """
import sqlite3
import json
import time

CHATS = ['34901e7f-b4ab-42b4-924d-c7ce91efe226']
SHARED = ['a60dbf3b-e258-44d3-b8e4-aebb5353e607']

conn = sqlite3.connect('/app/backend/data/webui.db')
c = conn.cursor()

def update_dict(d):
    hist = d.get('history', {}).get('messages', {})
    
    # 1. Update message 4 (Top 10 vật tư tồn kho lớn nhất)
    m4 = hist.get('1b3ccbaf-3ec0-448b-a0de-327c1ade1671')
    if m4:
        content = m4.get('content', '')
        if '```mermaid' not in content:
            chart = (
                "\\n\\n```mermaid\\n"
                "pie title Tỷ trọng Top 10 vật tư tồn kho lớn nhất (PCS)\\n"
                '    "606267 (Terminal Lug)" : 731595\\n'
                '    "606270 (Terminal Lug)" : 450757\\n'
                '    "XB4-7300-805 (SCREW)" : 296582\\n'
                '    "117300004 (RETAINER)" : 176818\\n'
                '    "QC4-8071-000 (LF INNER GUIDE)" : 163689\\n'
                '    "108700004 (GASKET)" : 156445\\n'
                '    "120800002 (SCREW LOCK)" : 138640\\n'
                '    "K1Z-23K21-4100 (BOBBIN)" : 133462\\n'
                '    "25160-B1901000 (SCREW BH)" : 131604\\n'
                '    "432-00114 (Linh kiện BTP)" : 125332\\n'
                "```\\n"
            )
            m4['content'] = content + chart
            m4['originalContent'] = m4['content']
            if 'output' in m4 and isinstance(m4['output'], list):
                for item in m4['output']:
                    if item.get('type') == 'message' and item.get('content'):
                        for cp in item['content']:
                            if cp.get('type') == 'output_text':
                                cp['text'] = m4['content']
            print('Updated message 4 with mermaid chart')

    # 2. Update message 1 (Dừng máy stop line)
    m1 = hist.get('cd6ea733-6fa2-47a7-b7e3-8cfb37e68f59')
    if m1:
        content = m1.get('content', '')
        if '```mermaid' not in content:
            chart = (
                "\\n\\n```mermaid\\n"
                "pie title Cơ cấu thời gian dừng chuyền theo nguyên nhân (Phút)\\n"
                '    "Máy sấy nhựa lỗi hút" : 34\\n'
                '    "Chờ kết thúc lệnh SX" : 25\\n'
                '    "Vệ sinh khuôn định kỳ" : 19\\n'
                '    "Cắt gate tự động" : 18\\n'
                '    "Thử khuôn" : 10\\n'
                '    "Dừng theo kế hoạch" : 9\\n'
                '    "Lỗi monitor" : 6\\n'
                '    "Robot không lấy Runner" : 5\\n'
                "```\\n"
            )
            m1['content'] = content + chart
            m1['originalContent'] = m1['content']
            if 'output' in m1 and isinstance(m1['output'], list):
                for item in m1['output']:
                    if item.get('type') == 'message' and item.get('content'):
                        for cp in item['content']:
                            if cp.get('type') == 'output_text':
                                cp['text'] = m1['content']
            print('Updated message 1 with mermaid chart')

    # Also update messages array if present
    if 'messages' in d and isinstance(d['messages'], list):
        for msg in d['messages']:
            mid = msg.get('id')
            if mid in hist:
                msg['content'] = hist[mid]['content']

    return d

for cid in CHATS:
    c.execute("SELECT chat FROM chat WHERE id = ?", (cid,))
    r = c.fetchone()
    if r:
        d = json.loads(r[0])
        d = update_dict(d)
        c.execute("UPDATE chat SET chat = ? WHERE id = ?", (json.dumps(d, ensure_ascii=False), cid))
        print(f"Saved updated chat {cid}")

for sid in SHARED:
    c.execute("SELECT chat FROM shared_chat WHERE id = ?", (sid,))
    r = c.fetchone()
    if r:
        d = json.loads(r[0])
        d = update_dict(d)
        c.execute("UPDATE shared_chat SET chat = ? WHERE id = ?", (json.dumps(d, ensure_ascii=False), sid))
        print(f"Saved updated shared_chat {sid}")

conn.commit()
print("ALL CHAT UPDATES COMMITTED SUCCESSFULLY")
"""

import subprocess
res = subprocess.run(['docker', 'exec', '-i', 'open-webui', 'python3'], input=script, text=True, capture_output=True)
print(res.stdout)
print(res.stderr)
