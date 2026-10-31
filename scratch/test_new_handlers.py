import json, sys
sys.path.insert(0, '/tmp')
from htmp_postgres_query import Tools

tool = Tools()

test_questions = [
    # 1. BOM
    "Định mức BOM của mã sản phẩm 009-M66-198 gồm những linh kiện gì?",
    # 2. IQC
    "Bảng kê kiểm tra chất lượng đầu vào IQC tháng 10/2026 của nhà cung cấp NCC0619",
    # 3. PXK
    "Cho tôi xem bảng kê phiếu xuất kho bán hàng PXK tháng 10/2026",
    # 4. Xuất kho sản xuất
    "Bảng kê xuất kho nguyên vật liệu cho sản xuất tháng 10/2026",
    # 5. Nhập kho thành phẩm
    "Bảng kê nhập kho thành phẩm tháng 10/2026",
    # 6. Pallet
    "Danh sách pallet đóng thùng thành phẩm MES",
]

print("=== TESTING 6 NEW QUESTION TYPES ===")
for q in test_questions:
    print(f"\n>>> QUESTION: {q}")
    res = tool._ask_erp_data(q)
    try:
        data = json.loads(res)
        print(f"Status: OK, Source: {data.get('source')}, Rows: {data.get('row_count', len(data.get('rows', [])))}")
        print(f"Message: {data.get('message', '')[:120]}")
        sample = data.get('rows', [])[:2]
        print(f"Sample row 1: {sample[0] if sample else 'NO ROWS'}")
    except Exception as e:
        print(f"FAILED TO PARSE JSON: {res[:200]} ({e})")
