#!/usr/bin/env python3
"""
Import users from docs_test/QLNS.xlsx into Open WebUI database and manage passwords.

Usage:
    # 1. Chạy thử (Dry-run):
    python3 scripts/import_users_from_qlns.py

    # 2. Áp dụng cập nhật/tạo mới vào container Open WebUI:
    docker exec -i open-webui python3 - --apply < scripts/import_users_from_qlns.py

    # Hoặc nếu chạy trực tiếp trên host:
    python3 scripts/import_users_from_qlns.py --db /path/to/webui.db --apply
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
import uuid
import xml.etree.ElementTree as ET
import zipfile

try:
    import bcrypt
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
except ImportError:
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        def hash_password(password: str) -> str:
            return pwd_context.hash(password)
    except ImportError:
        def hash_password(password: str) -> str:
            raise RuntimeError("Cần cài đặt thư viện 'bcrypt' hoặc 'passlib' để băm mật khẩu")


DEFAULT_PASSWORD = "Htmp1234"
DEFAULT_ROLE = "user"
APPROVED_MODELS = ("htmp-nhanh", "qwen2.5-14b", "htmp-erp-agent-staging")

ROOT_DIR = Path(__file__).resolve().parents[1] if "__file__" in globals() else Path("/app/backend")
CONTAINER_DB = Path("/app/backend/data/webui.db")
HOST_LOCAL_DB = ROOT_DIR / "local_webui.db"
DEFAULT_DB = CONTAINER_DB if CONTAINER_DB.is_file() else HOST_LOCAL_DB

XLSX_CANDIDATES = [
    ROOT_DIR / "docs_test" / "QLNS.xlsx",
    ROOT_DIR / "docs" / "QLNS.xlsx",
    Path("/app/backend/docs/QLNS.xlsx"),
    Path("/app/backend/docs_test/QLNS.xlsx")
]
DEFAULT_XLSX = next((p for p in XLSX_CANDIDATES if p.is_file()), ROOT_DIR / "docs_test" / "QLNS.xlsx")


def parse_qlns_excel(xlsx_path: Path) -> list[dict[str, str]]:
    """Parse QLNS.xlsx using standard library zipfile and XML parser."""
    if not xlsx_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file: {xlsx_path}")

    with zipfile.ZipFile(xlsx_path, 'r') as z:
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
            ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
            for si in tree.findall(f'{ns}si'):
                shared_strings.append(''.join(si.itertext()))

        sheet_data = z.read('xl/worksheets/sheet1.xml')
        s_tree = ET.fromstring(sheet_data)
        ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

        rows = []
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
            name = cells.get('F', '').strip()
            department = cells.get('D', '').strip()
            sub_dept = cells.get('A', '').strip()
            position = cells.get('B', '').strip()
            status = cells.get('E', '').strip()

            if emp_code:
                rows.append({
                    "emp_code": emp_code,
                    "name": name,
                    "department": department,
                    "sub_dept": sub_dept,
                    "position": position,
                    "status": status,
                })

        return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Tạo hoặc cập nhật mật khẩu Open WebUI từ file QLNS.xlsx")
    parser.add_argument("--xlsx", default=str(DEFAULT_XLSX), help="Đường dẫn file QLNS.xlsx")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Đường dẫn file webui.db (SQLite)")
    parser.add_argument("--apply", action="store_true", help="Thực hiện ghi vào DB (mặc định dry-run)")
    parser.add_argument("--include-inactive", action="store_true", help="Bao gồm cả nhân viên Đã nghỉ")
    parser.add_argument("--department", help="Chỉ import nhân viên thuộc phòng ban chỉ định (vd: 'IT-ERP')")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help=f"Mật khẩu mặc định (mặc định: {DEFAULT_PASSWORD})")
    args = parser.parse_args()

    xlsx_path = Path(args.xlsx)
    db_path = Path(args.db)

    print(f"=== Đọc dữ liệu nhân sự: {xlsx_path} ===")
    employees = parse_qlns_excel(xlsx_path)
    print(f"Tổng số dòng nhân sự trong file: {len(employees)}")

    if not args.include_inactive:
        employees = [e for e in employees if e["status"] == "Bình thường"]
        print(f"Số lượng nhân sự đang làm việc (Trạng thái = Bình thường): {len(employees)}")

    if args.department:
        employees = [e for e in employees if args.department.lower() in e["department"].lower()]
        print(f"Số lượng nhân sự thuộc phòng ban '{args.department}': {len(employees)}")

    if not employees:
        print("Không có nhân sự nào thỏa mãn điều kiện lọc.")
        return

    print(f"\n=== Kết nối cơ sở dữ liệu: {db_path} ===")
    if not db_path.is_file():
        print(f"LỖI: Không tìm thấy file database tại {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Lấy danh sách user hiện có
    existing_users = {}
    for uid, email, username in cur.execute("SELECT id, email, username FROM user").fetchall():
        if email:
            existing_users[email.lower()] = uid
        if username:
            existing_users[username.lower()] = uid

    to_create = []
    to_update = []

    for emp in employees:
        emp_code = emp["emp_code"]
        login_id = emp_code.lower()

        if login_id in existing_users:
            to_update.append((login_id, existing_users[login_id], emp))
        else:
            to_create.append((login_id, emp))

    print(f"Số tài khoản đã có (sẽ CẬP NHẬT mật khẩu sang '{args.password}'): {len(to_update)}")
    print(f"Số tài khoản mới (sẽ TẠO MỚI với mật khẩu '{args.password}'): {len(to_create)}")

    print("\n--- Mẫu 5 tài khoản sẽ cập nhật/tạo mới ---")
    samples = (to_update + to_create)[:5]
    for item in samples:
        emp = item[-1]
        login_id = item[0]
        status_txt = "Cập nhật" if len(item) == 3 else "Tạo mới"
        print(f" - [{status_txt}] {emp['emp_code']} ({login_id}) | {emp['name']:25} | {emp['department']:18} | {emp['position']}")

    if not args.apply:
        print("\n>>> ĐANG CHẠY Ở CHẾ ĐỘ KIỂM TRA (DRY-RUN) - CHƯA GHI VÀO DB <<<")
        print("Để thực hiện ghi vào DB, hãy chạy lại với cờ: --apply")
        conn.close()
        return

    # Thực hiện ghi DB
    print(f"\nĐang băm mật khẩu mới: '{args.password}'...")
    pwd_hash = hash_password(args.password)

    now = int(time.time())
    created_count = 0
    updated_count = 0

    print("Đang tiến hành cập nhật cơ sở dữ liệu...")
    cur.execute("BEGIN TRANSACTION")

    try:
        has_access_grant = bool(cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='access_grant'").fetchone())

        # 1. Cập nhật mật khẩu cho các tài khoản đã có
        for login_id, user_id, emp in to_update:
            cur.execute(
                "UPDATE auth SET password = ?, active = 1 WHERE lower(email) = ? OR id = ?",
                (pwd_hash, login_id, user_id)
            )
            # Đảm bảo phân quyền model
            if has_access_grant:
                for model_id in APPROVED_MODELS:
                    grant_id = str(uuid.uuid4()).replace("-", "")
                    cur.execute(
                        """
                        INSERT OR IGNORE INTO access_grant (
                            id, resource_type, resource_id,
                            principal_type, principal_id, permission,
                            created_at
                        ) VALUES (?, 'model', ?, 'user', ?, 'read', ?)
                        """,
                        (grant_id, model_id, user_id, now)
                    )
            updated_count += 1

        # 2. Tạo mới các tài khoản chưa có
        for login_id, emp in to_create:
            user_id = str(uuid.uuid4())
            name = emp["name"]
            username = emp["emp_code"]
            bio = f"{emp['department']} - {emp['sub_dept']} - {emp['position']}"

            cur.execute(
                """
                INSERT INTO user (
                    id, name, email, role, profile_image_url,
                    last_active_at, updated_at, created_at,
                    username, bio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, login_id, DEFAULT_ROLE, "/user.png", now, now, now, username, bio)
            )

            cur.execute(
                """
                INSERT INTO auth (
                    id, email, password, active
                ) VALUES (?, ?, ?, ?)
                """,
                (user_id, login_id, pwd_hash, 1)
            )

            if has_access_grant:
                for model_id in APPROVED_MODELS:
                    grant_id = str(uuid.uuid4()).replace("-", "")
                    cur.execute(
                        """
                        INSERT OR IGNORE INTO access_grant (
                            id, resource_type, resource_id,
                            principal_type, principal_id, permission,
                            created_at
                        ) VALUES (?, 'model', ?, 'user', ?, 'read', ?)
                        """,
                        (grant_id, model_id, user_id, now)
                    )
            created_count += 1

        conn.commit()
        print(f"\n THÀNH CÔNG!")
        print(f" - Đã cập nhật mật khẩu cho {updated_count} tài khoản hiện có.")
        print(f" - Đã tạo mới {created_count} tài khoản.")
        print(f" - Tổng cộng: {updated_count + created_count} tài khoản nhân sự đang hoạt động.")
        print(f" Tên đăng nhập: Mã nhân viên (ví dụ: HP0001, HP4963...)")
        print(f" Mật khẩu mới: {args.password}")
        if has_access_grant:
            print(f" Đã cấp quyền truy cập các model: {', '.join(APPROVED_MODELS)}")
    except Exception as e:
        conn.rollback()
        print(f"\n LỖI trong quá trình ghi DB: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
