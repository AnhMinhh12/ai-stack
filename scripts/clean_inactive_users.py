#!/usr/bin/env python3
"""
Check and purge any inactive (Đã nghỉ) employee accounts from Open WebUI database.
"""

from __future__ import annotations

from pathlib import Path
import sqlite3
import xml.etree.ElementTree as ET
import zipfile

ROOT_DIR = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path("/app/backend")
CONTAINER_DB = Path("/app/backend/data/webui.db")
HOST_LOCAL_DB = ROOT_DIR / "local_webui.db"
DB_PATH = CONTAINER_DB if CONTAINER_DB.is_file() else HOST_LOCAL_DB

XLSX_CANDIDATES = [
    ROOT_DIR / "docs_test" / "QLNS.xlsx",
    ROOT_DIR / "docs" / "QLNS.xlsx",
    Path("/app/backend/docs/QLNS.xlsx"),
    Path("/app/backend/docs_test/QLNS.xlsx")
]
XLSX_PATH = next((p for p in XLSX_CANDIDATES if p.is_file()), ROOT_DIR / "docs_test" / "QLNS.xlsx")


def main() -> None:
    print(f"=== Đang kiểm tra file Excel: {XLSX_PATH} ===")
    inactive_codes = set()
    with zipfile.ZipFile(XLSX_PATH, 'r') as z:
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
            ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
            for si in tree.findall(f'{ns}si'):
                shared_strings.append(''.join(si.itertext()))

        sheet_data = z.read('xl/worksheets/sheet1.xml')
        s_tree = ET.fromstring(sheet_data)
        ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

        for r_elem in s_tree.findall(f'.//{ns}row'):
            cells = {}
            for c_elem in r_elem.findall(f'{ns}c'):
                ref = c_elem.attrib.get('r', '')
                col = ''.join(ch for ch in ref if ch.isalpha())
                cell_type = c_elem.attrib.get('t', '')
                v_elem = c_elem.find(f'{ns}v')
                val = v_elem.text if v_elem is not None else ""
                if cell_type == 's' and val.isdigit():
                    idx = int(val)
                    val = shared_strings[idx] if idx < len(shared_strings) else val
                cells[col] = val.strip() if val else ""

            if cells.get('C') == 'Mã nhân viên' or not cells.get('C'):
                continue

            emp_code = cells.get('C', '').strip()
            status = cells.get('E', '').strip()

            if status and status != 'Bình thường':
                inactive_codes.add(emp_code.lower())

    print(f"Tổng số nhân sự 'Đã nghỉ' ghi nhận trong Excel: {len(inactive_codes)}")

    print(f"\n=== Kết nối cơ sở dữ liệu: {DB_PATH} ===")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, name, email, username FROM user")
    all_users = cur.fetchall()

    to_delete = []
    for u in all_users:
        uid, name, email, username = u
        email_l = (email or '').lower()
        uname_l = (username or '').lower()
        if email_l in inactive_codes or uname_l in inactive_codes:
            to_delete.append(u)

    print(f"Số tài khoản 'Đã nghỉ' phát hiện trong database: {len(to_delete)}")

    if to_delete:
        ids_to_del = [u[0] for u in to_delete]
        placeholders = ','.join('?' for _ in ids_to_del)
        cur.execute(f"DELETE FROM auth WHERE id IN ({placeholders})", ids_to_del)
        cur.execute(f"DELETE FROM user WHERE id IN ({placeholders})", ids_to_del)
        cur.execute(f"DELETE FROM access_grant WHERE principal_id IN ({placeholders})", ids_to_del)
        conn.commit()
        print(f"-> ĐÃ XÓA TRIỆT ĐỂ {len(to_delete)} TÀI KHOẢN ĐÃ NGHỈ KHỎI DATABASE!")
    else:
        print("-> XÁC NHẬN AN TOÀN: Không có tài khoản 'Đã nghỉ' nào tồn tại trong database.")
        print("   Tất cả tài khoản được import đều là nhân sự 'Bình thường' (đang làm việc).")

    total_users = cur.execute("SELECT count(*) FROM user").fetchone()[0]
    print(f"\nTổng số tài khoản người dùng hiện có trong hệ thống: {total_users}")
    conn.close()


if __name__ == "__main__":
    main()
