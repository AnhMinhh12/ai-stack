#!/usr/bin/env python3
"""Sync updated Enterprise Unified Gateway tool and specs to webui.db inside open-webui container."""

import json
import sqlite3
import subprocess
from pathlib import Path

def main():
    tool_file = Path("functions/htmp_postgres_query.py")
    if not tool_file.exists():
        print("Cannot find functions/htmp_postgres_query.py")
        return

    # Copy files to open-webui container
    subprocess.run(["docker", "cp", str(tool_file), "open-webui:/tmp/htmp_postgres_query.py"], check=True)
    rag_file = Path("functions/htmp_fast_rag.py")
    if rag_file.exists():
        subprocess.run(["docker", "cp", str(rag_file), "open-webui:/tmp/htmp_fast_rag.py"], check=True)

    # UNIFIED ENTERPRISE GATEWAY SPEC
    # Instead of exposing 16 fragmented tools that confuse the 14B model,
    # we expose 1 single unified enterprise gateway tool.
    specs = [
        {
            "name": "query_htmp_erp",
            "description": "CỔNG TRA CỨU DỮ LIỆU FAST ERP 3S & MES TOÀN DIỆN CỦA NHÀ MÁY HTMP. Luôn gọi công cụ duy nhất này cho MỌI câu hỏi tra cứu dữ liệu thực tế của doanh nghiệp, bao gồm cả 8 phân hệ: 1. KHO (NXT, tồn kho, vị trí kệ/máy, kiểm kê, HSD, tuổi hàng lô, sức chứa); 2. BÁN HÀNG (đơn bán SO, tiến độ giao hàng, lệnh giao TO2, bảng giá bán, so sánh DO & FCST); 3. MUA HÀNG (đơn mua PO, bảng giá mua NCC dmgiamuact, lịch sử giá mua, phiếu nhập mua); 4. KẾ TOÁN & CÔNG NỢ (sổ cái phát sinh TK 111-642, cân đối phát sinh, sổ quỹ, công nợ 131/331); 5. SẢN XUẤT MES (Lệnh SX/Work Order, OEE, đóng thùng, gộp/tách thùng, bổ sung/bỏ shot, thay khuôn, dừng máy downtime, setup máy, NG linh kiện); 6. KẾ HOẠCH MF (Lệnh SX, thống kê SX, tiêu hao NVL, BOM); 7. CHẤT LƯỢNG QC (IQC, OQC tem kiểm định, phế phẩm NG); 8. KHUÔN MẪU VS (hồ sơ khuôn, số shot dập, bảo trì bảo dưỡng); và tra cứu Danh mục chung (mã nhân viên 4509 là anh Nguyễn Văn Trường, thông tin khách hàng, quy cách đóng gói).",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Toàn bộ câu hỏi tự nhiên bằng tiếng Việt của người dùng về nghiệp vụ ERP/MES cần tra cứu."
                    }
                },
                "required": ["question"]
            }
        },
        {
            "name": "query_erp_report",
            "description": "Cổng tra cứu báo cáo Fast ERP 3S & MES toàn diện (tương thích).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Câu hỏi tự nhiên của người dùng"
                    }
                },
                "required": ["query"]
            }
        }
    ]

    with open("/tmp/update_specs.json", "w", encoding="utf-8") as f:
        json.dump(specs, f, ensure_ascii=False, indent=2)

    subprocess.run(["docker", "cp", "/tmp/update_specs.json", "open-webui:/tmp/update_specs.json"], check=True)

    docker_py = """
import sqlite3
import json
import os

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

if os.path.exists('/tmp/htmp_fast_rag.py'):
    with open('/tmp/htmp_fast_rag.py', 'r', encoding='utf-8') as f:
        rag_content = f.read()
    cur.execute("UPDATE function SET content = ? WHERE id = 'htmp_fast_rag'", (rag_content,))
    print(f"htmp_fast_rag function rows updated: {cur.rowcount}")

conn.commit()
conn.close()
print("Synced Enterprise Gateway successfully to webui.db!")
"""
    subprocess.run(["docker", "exec", "open-webui", "python3", "-c", docker_py], check=True)

if __name__ == "__main__":
    main()
