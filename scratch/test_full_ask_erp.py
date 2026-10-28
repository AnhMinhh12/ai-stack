import os
import sys
import json
sys.path.insert(0, '/home/admin/ai-stack')

os.environ["HTMP_DB_HOST"] = "10.0.6.2"
os.environ["HTMP_DB_PORT"] = "5410"
os.environ["HTMP_DB_NAME"] = "3SERP_HTMP_DATA"
os.environ["HTMP_DB_USER"] = "read_htmp"
os.environ["HTMP_DB_PASSWORD"] = "P@ss@Htmp@W0rd!2025"
os.environ["HTMP_ERP_SHARED_USER_ID"] = "11"
os.environ["HTMP_ERP_REPORTS_DIR"] = "/home/admin/ai-stack/config/erp-reports"
os.environ["HTMP_ERP_BUSINESS_INTENTS_PATH"] = "/home/admin/ai-stack/config/erp-business-intents.json"

from functions.htmp_postgres_query import Tools

t = Tools()

print("=================================================================")
print("TEST 1: Bảng kê đóng gói, đóng thùng")
print("=================================================================")
res1 = t._ask_erp_data("Bảng kê đóng gói đóng thùng mã QC7-5524-000")
try:
    p1 = json.loads(res1)
    print(f"Source: {p1.get('source')}")
    print(f"Row count: {p1.get('row_count')}")
    if p1.get('rows'):
        print("Sample row 1:", p1['rows'][0])
except Exception as e:
    print("Error:", e, res1[:200])

print("\n=================================================================")
print("TEST 2: Bảng kê gộp, tách thùng")
print("=================================================================")
res2 = t._ask_erp_data("Bảng kê gộp tách thùng")
try:
    p2 = json.loads(res2)
    print(f"Source: {p2.get('source')}")
    print(f"Row count: {p2.get('row_count')}")
    if p2.get('rows'):
        print("Sample row 1:", p2['rows'][0])
except Exception as e:
    print("Error:", e, res2[:200])

print("\n=================================================================")
print("TEST 3: Bảng kê bổ sung shot")
print("=================================================================")
res3 = t._ask_erp_data("Bảng kê bổ sung shot khuôn")
try:
    p3 = json.loads(res3)
    print(f"Source: {p3.get('source')}")
    print(f"Row count: {p3.get('row_count')}")
    if p3.get('rows'):
        print("Sample row 1:", p3['rows'][0])
except Exception as e:
    print("Error:", e, res3[:200])
