import sys
import json
from functions.htmp_postgres_query import Tools

t = Tools()
user = {"id": "mai.bt", "username": "mai.bt"}

q1 = "check cho chị giá bán của mã hàng 156279430 15:49 6 thg 11"
res1 = t.ask_erp(q1, conversation_id="conv1", __user__=user)
print("Q1 (Incident 29):", q1)
print("RES1:", res1)
print("-" * 60)

q2 = "check cho chị giá bán của mã hàng T1015910DA này đang bao nhiêu 15:47 6 thg 11"
res2 = t.ask_erp(q2, conversation_id="conv2", __user__=user)
print("Q2 (Incident 28):", q2)
print("RES2:", res2)
print("-" * 60)

# Incident 27: multi-turn
# Turn 1:
q3_1 = "cho chị hỏi mã 1014084300"
res3_1 = t.ask_erp(q3_1, conversation_id="conv3", __user__=user)
print("Q3 Turn 1:", q3_1)
print("RES3_1:", res3_1)
# Turn 2:
q3_2 = "cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11"
res3_2 = t.ask_erp(q3_2, conversation_id="conv3", __user__=user)
print("Q3 Turn 2 (Incident 27):", q3_2)
print("RES3_2:", res3_2)
