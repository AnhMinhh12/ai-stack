import sqlite3
import json
from pathlib import Path

def sync():
    db_path = Path("/app/backend/data/webui.db")
    tool_py_path = Path("/tmp/htmp_postgres_query.py")
    filter_py_path = Path("/tmp/htmp_fast_rag.py")

    print(f"Using DB: {db_path}")
    print(f"Tool code: {tool_py_path}")
    print(f"Filter code: {filter_py_path}")

    with open(tool_py_path, "r", encoding="utf-8") as f:
        tool_code = f.read()

    with open(filter_py_path, "r", encoding="utf-8") as f:
        filter_code = f.read()

    specs = [
        {
            "name": "lookup_sales_price",
            "description": "Tra cứu giá bán của mã hàng, sản phẩm hoặc linh kiện từ Bảng giá bán ERP hoặc lịch sử xuất bán gần nhất.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {
                        "type": "string",
                        "description": "Mã vật tư hoặc mã sản phẩm (ví dụ: '156279430', 'T1015910DA', 'QC7-5146-000')."
                    },
                    "customer_code": {
                        "type": "string",
                        "description": "Mã khách hàng tùy chọn để lọc theo khách hàng cụ thể (ví dụ: 'KH0056', 'KH0087'). Để trống nếu tra cứu chung."
                    }
                },
                "required": ["material_code"]
            }
        },
        {
            "name": "lookup_inventory_stock",
            "description": "Tra cứu số lượng hàng tồn kho theo mã vật tư, theo kho cụ thể hoặc tổng tồn toàn kho nhà máy tính đến ngày chỉ định.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {
                        "type": "string",
                        "description": "Mã vật tư hoặc sản phẩm cần tra cứu tồn (ví dụ: '1014084300', '156279430'). Để trống nếu muốn tra cứu tổng tồn của một kho."
                    },
                    "warehouse_code": {
                        "type": "string",
                        "description": "Mã kho cụ thể (ví dụ: 'KHOTP00', 'KHO-CXL', 'KHO-IN', 'KHONVL'). Để trống nếu muốn tra cứu tồn ở mọi kho."
                    },
                    "date_as_of": {
                        "type": "string",
                        "description": "Ngày chốt tồn định dạng YYYY-MM-DD. Mặc định là ngày hôm nay."
                    }
                }
            }
        },
        {
            "name": "lookup_sales_orders",
            "description": "Tra cứu đơn đặt hàng bán (SO), tiến độ giao hàng hoặc lịch sử xuất hàng bán (HDA).",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {
                        "type": "string",
                        "description": "Mã vật tư hoặc sản phẩm bán."
                    },
                    "customer_code": {
                        "type": "string",
                        "description": "Mã khách hàng."
                    },
                    "order_code": {
                        "type": "string",
                        "description": "Số đơn hàng bán hoặc số chứng từ SO/HDA."
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Ngày bắt đầu khoảng thời gian dạng YYYY-MM-DD."
                    },
                    "date_to": {
                        "type": "string",
                        "description": "Ngày kết thúc khoảng thời gian dạng YYYY-MM-DD."
                    }
                }
            }
        },
        {
            "name": "lookup_purchase_orders",
            "description": "Tra cứu đơn đặt mua hàng từ nhà cung cấp (PO), giá mua vật tư và lịch sử mua hàng.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {
                        "type": "string",
                        "description": "Mã vật tư cần tra cứu lịch sử mua (ví dụ: 'NHUA001', '156279430')."
                    },
                    "supplier_code": {
                        "type": "string",
                        "description": "Mã nhà cung cấp NCC nếu cần lọc."
                    },
                    "po_code": {
                        "type": "string",
                        "description": "Số đơn đặt mua hàng PO."
                    }
                },
                "required": ["material_code"]
            }
        },
        {
            "name": "lookup_mold_and_mes",
            "description": "Tra cứu hồ sơ khuôn mẫu, tổng số shot dập, định mức bảo hành khuôn và trạng thái sản xuất MES.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mold_code": {
                        "type": "string",
                        "description": "Mã khuôn hoặc tên khuôn (ví dụ: '14HI202', 'K_QC5-2919-000-V1')."
                    },
                    "material_code": {
                        "type": "string",
                        "description": "Mã sản phẩm / chi tiết đúc bởi khuôn (ví dụ: 'QC7-5146-000')."
                    },
                    "action": {
                        "type": "string",
                        "description": "Hành động tra cứu: 'shots' (số shot dập/bảo hành), 'status' (trạng thái bảo trì), 'machines' (danh sách máy ép)."
                    }
                }
            }
        },
        {
            "name": "lookup_general_catalog",
            "description": "Tra cứu danh mục thông tin chung của nhà máy: mã tài khoản nhân viên (như 4509 là anh Nguyễn Văn Trường), tên khách hàng, quy cách đóng gói (thùng/khay trong dmvt).",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Loại danh mục: 'employee' (mã nhân viên/tài khoản), 'customer' (khách hàng), 'packaging' (quy cách đóng gói)."
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Mã định danh hoặc từ khóa cần tra cứu (ví dụ: '4509', tên khách hàng, mã vật tư)."
                    }
                },
                "required": ["keyword"]
            }
        },
        {
            "name": "ask_erp",
            "description": "Công cụ tổng hợp tra cứu ERP cho các câu hỏi phức tạp hoặc tổng hợp nhiều chỉ tiêu không thuộc các công cụ trên.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Câu hỏi ERP bằng tiếng Việt."
                    },
                    "context": {
                        "type": "string",
                        "description": "Bối cảnh hội thoại từ lượt trước."
                    }
                },
                "required": ["question"]
            }
        }
    ]

    specs_json = json.dumps(specs, ensure_ascii=False)

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # 1. Update tool table
    cur.execute(
        "UPDATE tool SET content = ?, specs = ? WHERE id = 'htmp_postgres_query'",
        (tool_code, specs_json)
    )
    print(f"Updated tool 'htmp_postgres_query': {cur.rowcount} row(s)")

    # 2. Update function table for htmp_postgres_query (if exists)
    cur.execute(
        "UPDATE function SET content = ? WHERE id = 'htmp_postgres_query'",
        (tool_code,)
    )
    print(f"Updated function 'htmp_postgres_query': {cur.rowcount} row(s)")

    # 3. Update function table for htmp_fast_rag
    cur.execute(
        "UPDATE function SET content = ? WHERE id = 'htmp_fast_rag'",
        (filter_code,)
    )
    print(f"Updated function 'htmp_fast_rag': {cur.rowcount} row(s)")

    conn.commit()
    conn.close()
    print("Database sync completed successfully!")

if __name__ == "__main__":
    sync()
