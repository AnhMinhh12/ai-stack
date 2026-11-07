import os
import json
import httpx

VLLM_API_KEY = os.getenv("VLLM_API_KEY", "")
BASE_URL = "http://localhost:8000/v1"

tools = [
    {
        "type": "function",
        "function": {
            "name": "lookup_sales_price",
            "description": "Tra cứu giá bán của sản phẩm hoặc vật tư cho khách hàng trong hệ thống Fast ERP (bảng giá dmbanggiact và lịch sử xuất bán ct81).",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {
                        "type": "string",
                        "description": "Mã vật tư hoặc mã sản phẩm cần tra cứu giá bán (ví dụ: '156279430', 'T1015910DA', 'QC7-5146-000')."
                    },
                    "customer_code": {
                        "type": "string",
                        "description": "Mã khách hàng cần lọc (ví dụ: 'KH0056', 'KH0087') nếu có."
                    }
                },
                "required": ["material_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_inventory_stock",
            "description": "Tra cứu số lượng tồn kho sổ sách kế toán của vật tư/sản phẩm (theo bảng cdvt và ct70), hoặc phân bổ tồn kho theo từng kho hoặc tổng tồn kho của một kho cụ thể.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {
                        "type": "string",
                        "description": "Mã vật tư hoặc mã sản phẩm (ví dụ: '1014084300', 'QC7-5146-000'). Để trống nếu muốn xem tổng tồn kho của một kho cụ thể."
                    },
                    "warehouse_code": {
                        "type": "string",
                        "description": "Mã kho cần lọc (ví dụ: 'KHOTP00', 'KHO-IN', 'KHO-CXL'). Để trống nếu muốn xem phân bổ trên tất cả các kho."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_sales_orders",
            "description": "Tra cứu đơn đặt hàng của khách hàng (SO), tiến độ giao hàng, phiếu xuất kho bán hàng (HDA) hoặc so sánh doanh thu xuất bán.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {"type": "string", "description": "Mã hàng cần tra cứu."},
                    "customer_code": {"type": "string", "description": "Mã khách hàng."},
                    "order_code": {"type": "string", "description": "Số đơn hàng SO hoặc số phiếu xuất HDA."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_purchase_orders",
            "description": "Tra cứu lịch sử đơn đặt mua hàng từ nhà cung cấp (PO), giá mua vật tư và báo giá nhà cung cấp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {"type": "string", "description": "Mã vật tư cần tra cứu lịch sử mua hàng."},
                    "supplier_code": {"type": "string", "description": "Mã nhà cung cấp nếu có."}
                },
                "required": ["material_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_mold_and_mes",
            "description": "Tra cứu hồ sơ khuôn mẫu (dmhosokhuon), số shot ép thực tế và định mức bảo hành shot (mes_oi_bo_shot), hoặc trạng thái tem kiểm định OQC.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mold_code": {"type": "string", "description": "Mã khuôn (ví dụ: 'MOLD01', '01K-2A00C')."},
                    "material_code": {"type": "string", "description": "Mã sản phẩm dập/ép bằng khuôn."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_general_catalog",
            "description": "Tra cứu danh mục thông tin chung của nhà máy: tên khách hàng, mã tài khoản nhân viên (như 4509 là anh Nguyễn Văn Trường), quy cách đóng gói (thùng/khay trong dmvt).",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Loại danh mục: 'material', 'packaging', 'customer', 'employee'."},
                    "keyword": {"type": "string", "description": "Từ khóa hoặc mã định danh cần tìm."}
                },
                "required": ["keyword"]
            }
        }
    }
]

system_prompt = (
    "Bạn là trợ lý ERP thông minh của nhà máy HTMP. "
    "Khi người dùng đặt câu hỏi, hãy chọn công cụ phù hợp nhất trong danh sách công cụ được cung cấp để tra cứu dữ liệu. "
    "Tự động trích xuất các tham số chính xác từ câu hỏi của người dùng và bỏ qua các mốc thời gian thừa do giao diện dán kèm."
)

test_cases = [
    {
        "name": "Incident 29 (Giá bán mã 156279430)",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "check cho chị giá bán của mã hàng 156279430 15:49 6 thg 11"}
        ]
    },
    {
        "name": "Incident 28 (Giá bán mã T1015910DA)",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "check cho chị giá bán của mã hàng T1015910DA này đang bao nhiêu 15:47 6 thg 11"}
        ]
    },
    {
        "name": "Incident 27 (Kế thừa đa lượt hỏi tồn kho KHOTP00)",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "cho chị hỏi mã 1014084300"},
            {"role": "assistant", "content": "Mã 1014084300 là sản phẩm FRONTAL COVER TRANSPARENT FOR TFT."},
            {"role": "user", "content": "cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11"}
        ]
    },
    {
        "name": "Hỏi nhân viên 4509",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "mã 4509 trên hệ thống là ai thế em?"}
        ]
    },
    {
        "name": "Hỏi khuôn đã chạy bao nhiêu shot",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "khuôn của mã QC7-5146-000 hiện tại đã dập được bao nhiêu shot rồi?"}
        ]
    }
]

print("Connecting to vLLM directly...")
# vLLM is reachable at http://vllm:8000/v1 inside docker network, or via container
with open('/tmp/test_vllm_cases.json', 'w') as f:
    json.dump({'tools': tools, 'test_cases': test_cases}, f, ensure_ascii=False)
print("Saved test cases to /tmp/test_vllm_cases.json")
