import sys
sys.path.insert(0, '/home/admin/ai-stack')
from functions.htmp_postgres_query import Tools, normalize_text

tools = Tools()

q2 = "check lại cho chị tồn của tất cả các kho trong hệ thống ERP e nhé 14:44 6 thg 11"
q3 = "Tồn kho của tất cả các mã vật tư tại tất cả các kho trong hệ thống ERP"
q4 = "Top 10 vật tư tồn kho nhiều nhất"

print("q2 normalized:", normalize_text(q2))
print("q2 warehouse stock distribution:", tools._warehouse_stock_distribution(q2) is not None)
print("q3 warehouse stock distribution:", tools._warehouse_stock_distribution(q3) is not None)
print("q4 top inventory stock:", tools._top_inventory_stock(q4) is not None)

# If False, why?
print("\n--- Testing _warehouse_stock_distribution on q2 ---")
import re
clean_q2 = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s+\d{1,2}\s+thg\s+\d{1,2}(?:\s+\d{4})?)?\b", "", q2, flags=re.I)
print("clean_q2:", repr(clean_q2))
norm_q2 = normalize_text(clean_q2)
print("norm_q2:", repr(norm_q2))
keywords = (
    "phan bo theo tung kho", "ton kho phan bo", "ton kho theo tung kho", 
    "ton kho cac kho", "ton kho tung kho", "theo tung kho hang",
    "tat ca cac kho", "toan bo cac kho", "ton cua tat ca cac kho", 
    "ton cac kho", "cac kho trong he thong", "ton o tat ca cac kho", 
    "ton theo tung kho", "ton kho tat ca cac kho", "tat ca kho"
)
for kw in keywords:
    if kw in norm_q2:
        print(f"Matched keyword: {kw}")

# Now let's try calling _warehouse_stock_distribution directly and catching any exception
try:
    res = tools._warehouse_stock_distribution(q2)
    print("Direct call result length:", len(res) if res else "None")
except Exception as e:
    import traceback
    traceback.print_exc()
