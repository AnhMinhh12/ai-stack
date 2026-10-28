import sys
import json
sys.path.insert(0, '/home/admin/ai-stack')
from scratch.test_handler_implementation import carton_packing_register

print("Test with specific material code:")
res = carton_packing_register("Bảng kê đóng thùng mã QC7-5524-000")
parsed = json.loads(res)
print(f"Row count: {parsed['row_count']}")
for r in parsed['rows'][:3]:
    print(r)
