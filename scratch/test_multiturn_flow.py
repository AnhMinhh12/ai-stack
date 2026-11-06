import sys
import os
import json
import importlib.util

if os.path.exists('/tmp/htmp_postgres_query.py'):
    spec = importlib.util.spec_from_file_location("htmp_postgres_query", "/tmp/htmp_postgres_query.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    Tools = mod.Tools
    ERP_CONVERSATION_STATE = mod.ERP_CONVERSATION_STATE
else:
    sys.path.insert(0, '/home/admin/ai-stack')
    from functions.htmp_postgres_query import Tools, ERP_CONVERSATION_STATE

tools = Tools()
conv_id = "test-chat-session-001"

print("=" * 80)
print("TEST 1: Turn 1 - Specific inventory question with material 01K-2A00C-0000-1")
q1 = "Check cho tôi tồn kho mã 01K-2A00C-0000-1 tại tất cả các kho có tồn 14:41 6 thg 11"
res1 = tools.ask_erp(q1, conversation_id=conv_id)
print("Result 1:")
print(res1)

stored_state = ERP_CONVERSATION_STATE._states.get(conv_id, {})
print("Conversation state after Turn 1:", stored_state)
assert stored_state.get("ma_vt") == "01K-2A00C-0000-1", f"Expected 01K-2A00C-0000-1 but got {stored_state.get('ma_vt')}"

print("\n" + "=" * 80)
print("TEST 2: Turn 2 - Follow-up: 'ở từng kho còn bao nhiêu?' without mentioning material code")
q2 = "ở từng kho còn bao nhiêu?"
res2 = tools.ask_erp(q2, conversation_id=conv_id)
print("Result 2:")
print(res2)
d2 = json.loads(res2)
assert d2.get("lookup", {}).get("ma_vt") == "01K-2A00C-0000-1", f"Lookup failed: {d2}"
print("SUCCESS: Turn 2 correctly inherited 01K-2A00C-0000-1!")

print("\n" + "=" * 80)
print("TEST 3: Turn 3 - Follow-up: 'quy cách đóng gói của nó thế nào?'")
q3 = "quy cách đóng gói của nó thế nào?"
res3 = tools.ask_erp(q3, conversation_id=conv_id)
print("Result 3:")
print(res3)
d3 = json.loads(res3)
assert d3.get("lookup", {}).get("ma_vt") == "01K-2A00C-0000-1", f"Lookup failed: {d3}"
print("SUCCESS: Turn 3 correctly inherited 01K-2A00C-0000-1 for packaging spec!")

print("\n" + "=" * 80)
print("TEST 4: Non-existent code with fuzzy suggestion")
q4 = "tồn kho mã 01K-2A00C-9999-9 ở từng kho"
res4 = tools.ask_erp(q4, conversation_id="test-chat-session-002")
print("Result 4:")
print(res4)
d4 = json.loads(res4)
assert "01K-2A00C" in d4.get("message", ""), f"Expected suggestion in message: {d4}"
print("SUCCESS: Fuzzy suggestion worked!")

print("\n" + "=" * 80)
print("TEST 5: All warehouses distribution (Incident 26)")
q5 = "check lại cho chị tồn của tất cả các kho trong hệ thống ERP e nhé 14:44 6 thg 11"
res5 = tools.ask_erp(q5, conversation_id="test-chat-session-003")
print("Result 5 (summary):")
d5 = json.loads(res5)
print("Source:", d5.get("source"))
print("Row count:", d5.get("row_count"))
print("First 3 warehouses:", d5.get("rows", [])[:3])
assert d5.get("row_count", 0) > 0, "Expected warehouses returned"

print("\n" + "=" * 80)
print("ALL MULTI-TURN & FUZZY TESTS PASSED PERFECTLY!")
