import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("SELECT content FROM tool WHERE id = 'htmp_postgres_query'")
row = cur.fetchone()
code = row[0]

local_scope = {"__file__": "/tmp/htmp_postgres_query.py"}
exec(code, local_scope)
Tools = local_scope['Tools']
t = Tools()
user = {"id": "mai.bt", "username": "mai.bt"}

print("="*60)
print("TEST 1: Incident 29")
q1 = "check cho chị giá bán của mã hàng 156279430 15:49 6 thg 11"
print(t.ask_erp(q1, conversation_id="conv_test_1", __user__=user))

print("\n" + "="*60)
print("TEST 2: Incident 28")
q2 = "check cho chị giá bán của mã hàng T1015910DA này đang bao nhiêu 15:47 6 thg 11"
print(t.ask_erp(q2, conversation_id="conv_test_2", __user__=user))

print("\n" + "="*60)
print("TEST 3: Incident 27 (Turn 1: material 1014084300, Turn 2: warehouse KHOTP00)")
q3_1 = "cho chị hỏi mã 1014084300"
t.ask_erp(q3_1, conversation_id="conv_test_3", __user__=user)
q3_2 = "cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11"
print(t.ask_erp(q3_2, conversation_id="conv_test_3", __user__=user))

print("\n" + "="*60)
print("TEST 4: Incident 27 variant (no prior material)")
print(t.ask_erp("cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11", conversation_id="conv_test_4", __user__=user))
