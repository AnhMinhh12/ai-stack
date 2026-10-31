import sqlite3, json, datetime

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()

questions = [
    ("Q1", "QC7-5146-000 dùng loại nhựa gì"),
    ("Q2", "MOQ báo giá hiện tại của mã QC7-5146-000"),
    ("Q3", "lot gần nhất được xuất giao của mã QC7-5146-000"),
    ("Q4", "tổng số lượng xuất bán và doanh thu của mã QC7-5146-000"),
    ("Q5", "QC7-5146-000 được khai báo thuộc khách hàng nào"),
    ("Q6", "mã QC7-5146-000 được nhập kho vào những ngày nào"),
    ("Q7", "So sánh DO và FCST"),
    ("Q8", "Quy cách đóng gói của mã QC7-5146-000"),
    ("Q9", "Khuôn K_QC5-2919-000-V1"),
    ("Q10", "So sánh doanh thu mã QC7-5146-000 của khách KH0015"),
    ("Q11", "Mã QC7-5146-000 hiện có tồn kho thuộc những khuôn nào"),
    ("Q12", "đơn hàng bán của khách KH0015"),
    ("Q13", "Lệnh giao hàng 001-2610-001811"),
    ("Q14", "Tồn kho hiện tại của mã QC7-5146-000 là bao nhiêu ở từng kho"),
    ("Q15", "lot thành phẩm nào ở trạng thái QC cần chú ý"),
    ("Q16", "có mã hàng nào chưa có giá chuẩn được liên kết không"),
    ("Q17", "Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long"),
    ("Q18", "số lượng giao bù NG là bao nhiêu")
]

cur.execute("""
SELECT c.id, u.id, u.name, u.email, c.title, c.updated_at, c.chat
FROM chat c
JOIN user u ON c.user_id = u.id
ORDER BY c.updated_at DESC;
""")
chats = cur.fetchall()
print(f"Total chats in DB: {len(chats)}")

found_records = []
for cid, uid, uname, uemail, title, updated_at, chat_str in chats:
    try:
        d = json.loads(chat_str)
        msgs = []
        if 'history' in d and 'messages' in d['history']:
            msgs.extend(d['history']['messages'].values())
        if 'messages' in d:
            msgs.extend(d['messages'])
        
        user_texts = [m.get('content', '') for m in msgs if m.get('role') == 'user']
        all_user_str = " ".join(user_texts).lower()
        
        for q_id, q_kw in questions:
            if q_kw.lower() in all_user_str:
                dt = datetime.datetime.fromtimestamp(updated_at).strftime('%Y-%m-%d %H:%M:%S')
                found_records.append({
                    "qid": q_id,
                    "keyword": q_kw,
                    "user": f"{uname} ({uemail})",
                    "time": dt,
                    "chat_id": cid,
                    "title": title
                })
    except Exception:
        pass

print(f"Total matched questions in chat logs: {len(found_records)}")
for r in found_records:
    print(f"[{r['qid']}] {r['user']} at {r['time']} | Chat: {r['title']} ({r['chat_id']})")

conn.close()
