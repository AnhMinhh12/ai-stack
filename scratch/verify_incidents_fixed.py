import sys
import os
import json
import importlib.util

if os.path.exists('/tmp/htmp_postgres_query.py'):
    spec = importlib.util.spec_from_file_location("htmp_postgres_query", "/tmp/htmp_postgres_query.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    Tools = mod.Tools
else:
    sys.path.insert(0, '/home/admin/ai-stack')
    from functions.htmp_postgres_query import Tools

tools = Tools()

print("=" * 70)
print("TEST 1: Incident 25 - Inventory of 01K-2A00C-0000-1 by warehouse")
q1 = "Check cho tôi tồn kho mã 01K-2A00C-0000-1 tại tất cả các kho có tồn 14:41 6 thg 11"
res1 = tools.ask_erp(q1)
print("Result 1:")
print(res1)

print("\n" + "=" * 70)
print("TEST 2: Incident 26 - Stock of all warehouses with timestamp")
q2 = "check lại cho chị tồn của tất cả các kho trong hệ thống ERP e nhé 14:44 6 thg 11"
res2 = tools.ask_erp(q2)
print("Result 2 (summary):")
try:
    d2 = json.loads(res2)
    print("Source:", d2.get("source"))
    print("Row count:", d2.get("row_count"))
    print("First 3 rows:", d2.get("rows", [])[:3])
except Exception:
    print(res2[:500])

print("\n" + "=" * 70)
print("TEST 3: Model translated query for all warehouses")
q3 = "Tồn kho của tất cả các mã vật tư tại tất cả các kho trong hệ thống ERP"
res3 = tools.ask_erp(q3)
print("Result 3 (summary):")
try:
    d3 = json.loads(res3)
    print("Source:", d3.get("source"))
    print("Row count:", d3.get("row_count"))
    print("First 3 rows:", d3.get("rows", [])[:3])
except Exception:
    print(res3[:500])

print("\n" + "=" * 70)
print("TEST 4: Top inventory stock")
q4 = "Top 10 vật tư tồn kho nhiều nhất"
res4 = tools.ask_erp(q4)
print("Result 4 (summary):")
try:
    d4 = json.loads(res4)
    print("Source:", d4.get("source"))
    print("Row count:", d4.get("row_count"))
    print("First 3 rows:", d4.get("rows", [])[:3])
except Exception:
    print(res4[:500])

print("=" * 70)
print("ALL VERIFICATIONS FINISHED")
