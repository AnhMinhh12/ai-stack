#!/usr/bin/env python3
"""Sync updated tools and specs to webui.db inside open-webui container."""

import json
import sqlite3
import subprocess
from pathlib import Path

def main():
    tool_file = Path("functions/htmp_postgres_query.py")
    if not tool_file.exists():
        print("Cannot find functions/htmp_postgres_query.py")
        return

    with open(tool_file, "r", encoding="utf-8") as f:
        tool_content = f.read()

    # Copy file to open-webui container
    subprocess.run(["docker", "cp", str(tool_file), "open-webui:/tmp/htmp_postgres_query.py"], check=True)

    specs = [
        {
            "name": "query_erp_report",
            "description": "Truy vấn báo cáo nghiệp vụ Fast ERP 3S & MES toàn diện cho cả 8 phân hệ doanh nghiệp: 1. KHO (NXT, tồn kho, vị trí kệ/máy, kiểm kê, HSD, tuổi hàng lô, sức chứa); 2. BÁN HÀNG (đơn bán, tiến độ giao hàng, bảng giá bán, lệnh giao TO2, trả lại NG, doanh số bán hàng, forecast); 3. MUA HÀNG (đơn mua, bảng giá mua NCC, tình trạng PO, hóa đơn, nhập mua, xuất trả, yêu cầu mua PR); 4. KẾ TOÁN & CÔNG NỢ (sổ cái phát sinh TK 111-642, cân đối phát sinh trial balance, sổ quỹ thu chi tiền mặt/ngân hàng, chi phí SXKD dở dang & quản lý, công nợ 131/331); 5. SẢN XUẤT MES (điều độ Lệnh SX / Work Order, hiệu suất thiết bị OEE, đóng thùng, gộp tách thùng, bổ sung shot, thay khuôn, dừng máy downtime, setup máy, NG linh kiện); 6. KẾ HOẠCH MF (Lệnh sản xuất LSX, thống kê sản xuất, tiêu hao NVL theo LSX, NXT công đoạn, định mức BOM); 7. CHẤT LƯỢNG QC (IQC/IPQC chi tiết, trạng thái tem QC, phế phẩm NG, lỗi NVL, lỗi thành phẩm); 8. KHUÔN MẪU VS (hồ sơ khuôn, cavity, số shot dập, bảo trì sửa chữa khuôn, cảnh báo bảo dưỡng định kỳ).",
            "parameters": {
                "type": "object",
                "properties": {
                    "report_type": {"type": "string", "description": "Tên báo cáo hoặc từ khóa nghiệp vụ"},
                    "query": {"type": "string", "description": "Câu hỏi tự nhiên của người dùng"},
                    "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD"},
                    "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD"},
                    "item_code": {"type": "string", "description": "Mã vật tư / sản phẩm"},
                    "partner_code": {"type": "string", "description": "Mã khách hàng hoặc nhà cung cấp"},
                    "warehouse_code": {"type": "string", "description": "Mã kho hàng"},
                    "account_code": {"type": "string", "description": "Tài khoản kế toán (111, 112, 131, 152, 154, 155, 331, 511, 621, 642)"}
                }
            }
        },
        {
            "name": "lookup_sales_price",
            "description": "Tra cứu đơn giá của mã hàng, sản phẩm hoặc nguyên vật liệu hạt nhựa từ Bảng giá bán ERP hoặc Danh mục giá mua nhà cung cấp (dmgiamuact).",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {"type": "string", "description": "Mã vật tư, mã sản phẩm hoặc mã hạt nhựa (ví dụ: 156279430, ABS-260, QC7-5146-000)."},
                    "customer_code": {"type": "string", "description": "Mã khách hàng hoặc nhà cung cấp. Để trống nếu tra cứu chung."}
                },
                "required": ["material_code"]
            }
        },
        {
            "name": "lookup_inventory_stock",
            "description": "Tra cứu số lượng tồn kho và vị trí tồn kho cụ thể (ma_vi_tri) theo mã vật tư, theo kho cụ thể hoặc toàn bộ các kho tính đến ngày chỉ định.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {"type": "string", "description": "Mã vật tư hoặc sản phẩm cần tra cứu tồn và vị trí tồn."},
                    "warehouse_code": {"type": "string", "description": "Mã kho cụ thể (ví dụ: KHOTP00, KHO_TAIMAY, KHO-IN)."},
                    "date_as_of": {"type": "string", "description": "Ngày chốt tồn định dạng YYYY-MM-DD."}
                }
            }
        },
        {
            "name": "lookup_stock_card",
            "description": "Tra cứu Thẻ kho / Sổ chi tiết biến động nhập - xuất - tồn theo chứng từ của một mã vật tư tại kho cụ thể.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {"type": "string", "description": "Mã vật tư."},
                    "warehouse_code": {"type": "string", "description": "Mã kho."},
                    "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD."}
                },
                "required": ["material_code"]
            }
        },
        {
            "name": "lookup_sales_orders",
            "description": "Tra cứu đơn đặt hàng bán (SO), tiến độ giao hàng hoặc lịch sử xuất hàng bán (HDA).",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {"type": "string", "description": "Mã vật tư hoặc sản phẩm bán."},
                    "customer_code": {"type": "string", "description": "Mã khách hàng."},
                    "order_code": {"type": "string", "description": "Số đơn hàng bán hoặc số chứng từ SO/HDA."},
                    "date_from": {"type": "string", "description": "Ngày bắt đầu YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "Ngày kết thúc YYYY-MM-DD."}
                }
            }
        },
        {
            "name": "lookup_purchase_orders",
            "description": "Tra cứu đơn đặt mua hàng từ nhà cung cấp (PO), giá mua vật tư và lịch sử mua hàng.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {"type": "string", "description": "Mã vật tư cần tra cứu lịch sử mua."},
                    "supplier_code": {"type": "string", "description": "Mã nhà cung cấp NCC."},
                    "po_code": {"type": "string", "description": "Số đơn đặt mua hàng PO."}
                },
                "required": ["material_code"]
            }
        },
        {
            "name": "lookup_delivery_orders",
            "description": "Tra cứu lệnh giao hàng TO2 (ph96/ct96), số lượng, tiến độ out kho thực tế và thời gian hoàn thành lệnh.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_code": {"type": "string", "description": "Số lệnh giao hàng (ví dụ: 001-2611-000004, 001-2610-001811)."},
                    "customer_code": {"type": "string", "description": "Mã khách hàng."},
                    "material_code": {"type": "string", "description": "Mã sản phẩm."},
                    "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD."}
                }
            }
        },
        {
            "name": "lookup_qc_lot_status",
            "description": "Kiểm tra trạng thái QC, tình trạng kiểm định chất lượng tem thành phẩm (3-OK, 5-NG, 6-Chờ xử lý, kiểm tra lot bị khóa hoặc khoanh vùng NG).",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {"type": "string", "description": "Mã vật tư hoặc mã thành phẩm (ví dụ: QC7-5146-000)."},
                    "warehouse_code": {"type": "string", "description": "Mã kho tùy chọn."}
                },
                "required": ["material_code"]
            }
        },
        {
            "name": "lookup_mes_ng",
            "description": "Báo cáo bảng kê phế phẩm, sản phẩm lỗi NG sản xuất MES theo máy, theo chuyền hoặc mã sản phẩm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_code": {"type": "string", "description": "Mã máy sản xuất (ví dụ: DUC-0048, DUC-0070)."},
                    "material_code": {"type": "string", "description": "Mã sản phẩm / chi tiết đúc."},
                    "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD."}
                }
            }
        },
        {
            "name": "lookup_mes_packing",
            "description": "Tra cứu bảng kê đóng thùng, serial thùng tem thành phẩm MES.",
            "parameters": {
                "type": "object",
                "properties": {
                    "material_code": {"type": "string", "description": "Mã sản phẩm thành phẩm."},
                    "box_serial": {"type": "string", "description": "Mã serial tem thùng carton."},
                    "production_order": {"type": "string", "description": "Số lệnh sản xuất hoặc Work Order."}
                }
            }
        },
        {
            "name": "lookup_mold_and_mes",
            "description": "Tra cứu hồ sơ khuôn mẫu, tổng số shot dập, định mức bảo hành khuôn và trạng thái sản xuất MES.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mold_code": {"type": "string", "description": "Mã khuôn hoặc tên khuôn."},
                    "material_code": {"type": "string", "description": "Mã sản phẩm / chi tiết đúc."},
                    "action": {"type": "string", "description": "Hành động: shots, status, machines."}
                }
            }
        },
        {
            "name": "lookup_bom",
            "description": "Tra cứu cấu trúc định mức sản phẩm (BOM), loại hạt nhựa sử dụng, định mức tiêu hao và hiệu lực.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_code": {"type": "string", "description": "Mã sản phẩm."},
                    "material_code": {"type": "string", "description": "Mã nguyên liệu phụ."}
                },
                "required": ["product_code"]
            }
        },
        {
            "name": "lookup_mes_downtime",
            "description": "Tra cứu tổng hợp thời gian dừng máy theo nguyên nhân (downtime / stop line) và số lần dừng.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD."},
                    "machine_code": {"type": "string", "description": "Mã máy ép."}
                }
            }
        },
        {
            "name": "lookup_incoming_quality",
            "description": "Báo cáo đánh giá chất lượng nguyên vật liệu / linh kiện mua vào IQC theo nhà cung cấp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "description": "Từ ngày YYYY-MM-DD."},
                    "date_to": {"type": "string", "description": "Đến ngày YYYY-MM-DD."},
                    "supplier_code": {"type": "string", "description": "Mã nhà cung cấp."}
                }
            }
        },
        {
            "name": "lookup_general_catalog",
            "description": "Tra cứu danh mục thông tin chung của nhà máy: mã nhân viên, tên khách hàng, quy cách đóng gói.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Loại: employee, customer, packaging."},
                    "keyword": {"type": "string", "description": "Từ khóa tra cứu."}
                },
                "required": ["keyword"]
            }
        },
        {
            "name": "ask_erp",
            "description": "Công cụ tổng hợp tra cứu ERP cho các câu hỏi phức tạp hoặc tổng hợp nhiều chỉ tiêu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Câu hỏi ERP bằng tiếng Việt."},
                    "context": {"type": "string", "description": "Bối cảnh hội thoại."}
                },
                "required": ["question"]
            }
        }
    ]

    with open("/tmp/update_specs.json", "w", encoding="utf-8") as f:
        json.dump(specs, f, ensure_ascii=False)

    subprocess.run(["docker", "cp", "/tmp/update_specs.json", "open-webui:/tmp/update_specs.json"], check=True)

    docker_py = """
import sqlite3
import json

with open('/tmp/htmp_postgres_query.py', 'r', encoding='utf-8') as f:
    tool_content = f.read()

with open('/tmp/update_specs.json', 'r', encoding='utf-8') as f:
    specs = json.load(f)

specs_json = json.dumps(specs, ensure_ascii=False)

conn = sqlite3.connect('/app/backend/data/webui.db')
cur = conn.cursor()
cur.execute("UPDATE tool SET content = ?, specs = ? WHERE id = 'htmp_postgres_query'", (tool_content, specs_json))
print(f"Tool rows updated: {cur.rowcount}")
cur.execute("UPDATE function SET content = ? WHERE id = 'htmp_postgres_query'", (tool_content,))
print(f"Function rows updated: {cur.rowcount}")
conn.commit()
conn.close()
print("Synced successfully to webui.db!")
"""
    subprocess.run(["docker", "exec", "open-webui", "python3", "-c", docker_py], check=True)

if __name__ == "__main__":
    main()

