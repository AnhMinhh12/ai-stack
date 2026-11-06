import sys
sys.path.insert(0, '/home/admin/ai-stack')
from functions.htmp_postgres_query import Tools

tools = Tools()

print("=" * 80)
print("TEST 1: 156279430")
q1 = "check cho chị giá bán của mã hàng 156279430 15:49 6 thg 11"
res1 = tools.ask_erp(q1)
print("Result 1:", res1)

print("=" * 80)
print("TEST 2: T1015910DA")
q2 = "check cho chị giá bán của mã hàng T1015910DA này đang bao nhiêu 15:47 6 thg 11"
res2 = tools.ask_erp(q2)
print("Result 2:", res2)

print("=" * 80)
print("TEST 3: 1014084300 at KHOTP00")
q3 = "cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11"
# With context that 1014084300 was discussed
tools.ERP_CONVERSATION_STATE = tools.__class__
from functions.htmp_postgres_query import ERP_CONVERSATION_STATE
ERP_CONVERSATION_STATE.remember("test_chat", {"ma_vt": "1014084300"})
res3 = tools.ask_erp(q3, conversation_id="test_chat")
print("Result 3:", res3)
