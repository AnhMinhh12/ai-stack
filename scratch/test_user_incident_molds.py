#!/usr/bin/env python3
import json
import os
import sys

os.environ["HTMP_DB_HOST"] = "10.0.6.2"
os.environ["HTMP_DB_PORT"] = "5410"
os.environ["HTMP_DB_NAME"] = "3SERP_HTMP_DATA"
os.environ["HTMP_DB_USER"] = "read_htmp"
os.environ["HTMP_DB_PASSWORD"] = "P@ss@Htmp@W0rd!2025"
os.environ["HTMP_ERP_REPORTS_DIR"] = "/home/admin/ai-stack/config/erp-reports"
os.environ["HTMP_ERP_BUSINESS_INTENTS_PATH"] = "/home/admin/ai-stack/config/erp-business-intents.json"

sys.path.insert(0, "/home/admin/ai-stack")

from functions.htmp_postgres_query import Tools

tool = Tools()

print("="*60)
print("TEST 1: số lượng khuôn NG của nhà máy")
print("="*60)
raw1 = tool._ask_erp_data("số lượng khuôn NG của nhà máy")
data1 = json.loads(raw1)
print(f"Status: {data1.get('status')}")
print(f"Source: {data1.get('source')}")
print(f"Message: {data1.get('message')}")
print(f"Row count: {data1.get('row_count')}")
print(f"Summary: {json.dumps(data1.get('summary', {}), ensure_ascii=False)}")
print("Sample NG rows:")
for r in data1.get("rows", [])[:5]:
    print(f"  {r.get('ma_khuon')}: {r.get('ten_khuon')} | Tình trạng: {r.get('tinh_trang_khuon')}")

print("\n" + "="*60)
print("TEST 2: tổng số lượng khuôn của nhà máy là bao nhiêu")
print("="*60)
raw2 = tool._ask_erp_data("tổng số lượng khuôn của nhà máy là bao nhiêu")
data2 = json.loads(raw2)
print(f"Status: {data2.get('status')}")
print(f"Source: {data2.get('source')}")
print(f"Message: {data2.get('message')}")
print(f"Row count: {data2.get('row_count')}")
print(f"Summary: {json.dumps(data2.get('summary', {}), ensure_ascii=False)}")
print("Sample rows:")
for r in data2.get("rows", [])[:5]:
    print(f"  {r.get('ma_khuon')}: {r.get('ten_khuon')} | Tình trạng: {r.get('tinh_trang_khuon')}")
