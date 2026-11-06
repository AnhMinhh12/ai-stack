#!/usr/bin/env python3
"""
Quản lý và gán OpenAI GPT API Key cho từng mã nhân viên trong Open WebUI.

Chức năng:
  - Gán API key cho mã nhân viên (tự động cập nhật .env và cấp quyền model trong DB)
  - Xóa API key của mã nhân viên
  - Liệt kê danh sách nhân viên đã được gán API key GPT
  - Tra cứu mã nhân viên theo tên hoặc mã
  - Đồng bộ quyền truy cập model trong database từ cấu hình HTMP_OPENAI_USER_KEY_MAP trong .env

Cách sử dụng:
  # 1. Tra cứu mã nhân viên theo tên hoặc mã:
  python3 scripts/manage_gpt_users.py --find "Minh"

  # 2. Gán API key cho một nhân viên (VD: HP4729):
  python3 scripts/manage_gpt_users.py --assign HP4729 sk-proj-xxxx...

  # 3. Xem danh sách nhân viên đang có quyền và API key GPT:
  python3 scripts/manage_gpt_users.py --list

  # 4. Thu hồi / Xóa API key của nhân viên:
  python3 scripts/manage_gpt_users.py --remove HP4729

  # 5. Đồng bộ lại toàn bộ quyền từ .env vào Database:
  python3 scripts/manage_gpt_users.py --sync
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ENV_FILE = Path("/home/admin/ai-stack/.env")
GPT_MODELS = ("gpt-5.6-luna",)


def run_container_sqlite(query: str, params: list | tuple = ()) -> list[tuple]:
    """Execute SQLite query inside open-webui container."""
    py_code = f"""
import sqlite3, json, sys

db_path = '/app/backend/data/webui.db'
conn = sqlite3.connect(db_path, timeout=15)
cur = conn.cursor()
query = {repr(query)}
params = {repr(list(params))}

try:
    cur.execute(query, params)
    if query.strip().upper().startswith('SELECT') or 'RETURNING' in query.upper():
        rows = cur.fetchall()
        print(json.dumps({{'status': 'ok', 'rows': rows}}))
    else:
        conn.commit()
        print(json.dumps({{'status': 'ok', 'affected': cur.rowcount}}))
except Exception as e:
    conn.rollback()
    print(json.dumps({{'status': 'error', 'error': str(e)}}))
finally:
    conn.close()
"""
    cmd = ["docker", "exec", "-i", "open-webui", "python3", "-"]
    proc = subprocess.run(cmd, input=py_code.encode("utf-8"), capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Docker exec error: {proc.stderr.decode('utf-8', errors='replace')}")

    out_text = proc.stdout.decode("utf-8", errors="replace").strip()
    try:
        # Find last JSON object if container output logs before it
        json_start = out_text.rfind('{"status":')
        if json_start != -1:
            data = json.loads(out_text[json_start:])
        else:
            data = json.loads(out_text)
    except Exception as e:
        raise RuntimeError(f"Failed to parse DB output: {out_text}\nError: {e}")

    if data.get("status") == "error":
        raise RuntimeError(f"Database error: {data.get('error')}")

    return data.get("rows", [])


def read_env_key_map() -> tuple[dict[str, str], str]:
    """Read HTMP_OPENAI_USER_KEY_MAP from .env file."""
    if not ENV_FILE.is_file():
        raise FileNotFoundError(f"Không tìm thấy file cấu hình: {ENV_FILE}")

    content = ENV_FILE.read_text(encoding="utf-8")
    match = re.search(r"HTMP_OPENAI_USER_KEY_MAP='(.*?)'", content, re.DOTALL)
    if not match:
        match = re.search(r'HTMP_OPENAI_USER_KEY_MAP="(.*?)"', content, re.DOTALL)
    if not match:
        match = re.search(r"HTMP_OPENAI_USER_KEY_MAP=({.*?})", content, re.DOTALL)

    if not match:
        return {}, content

    raw_json = match.group(1).strip()
    try:
        key_map = json.loads(raw_json)
        if not isinstance(key_map, dict):
            key_map = {}
    except json.JSONDecodeError:
        key_map = {}

    return key_map, content


def write_env_key_map(key_map: dict[str, str]) -> None:
    """Save updated HTMP_OPENAI_USER_KEY_MAP back to .env."""
    _, content = read_env_key_map()

    formatted_json = json.dumps(key_map, indent=2, ensure_ascii=False)
    new_block = f"HTMP_OPENAI_USER_KEY_MAP='{formatted_json}'"

    pattern = r"HTMP_OPENAI_USER_KEY_MAP=(?:'[^']*'|\"[^\"]*\"|{[^}]*})"
    if re.search(pattern, content):
        new_content = re.sub(pattern, new_block, content, count=1)
    else:
        new_content = content.rstrip() + f"\n\n{new_block}\n"

    ENV_FILE.write_text(new_content, encoding="utf-8")


def find_user_by_identifier(identifier: str) -> dict | None:
    """Look up user in Open WebUI DB by employee code (username/email) or user ID."""
    clean_id = identifier.strip()
    query = """
    SELECT id, username, email, name, role, bio
    FROM user
    WHERE LOWER(username) = LOWER(?)
       OR LOWER(email) = LOWER(?)
       OR id = ?
    LIMIT 1;
    """
    rows = run_container_sqlite(query, (clean_id, clean_id, clean_id))
    if rows:
        row = rows[0]
        return {
            "id": row[0],
            "username": row[1] or "",
            "email": row[2] or "",
            "name": row[3] or "",
            "role": row[4] or "",
            "bio": row[5] or "",
        }
    return None


def search_users(keyword: str, limit: int = 20) -> list[dict]:
    """Search users by name, username or email."""
    pattern = f"%{keyword.strip()}%"
    query = """
    SELECT id, username, email, name, role, bio
    FROM user
    WHERE username LIKE ?
       OR email LIKE ?
       OR name LIKE ?
    LIMIT ?;
    """
    rows = run_container_sqlite(query, (pattern, pattern, pattern, limit))
    return [
        {
            "id": r[0],
            "username": r[1] or "",
            "email": r[2] or "",
            "name": r[3] or "",
            "role": r[4] or "",
            "bio": r[5] or "",
        }
        for r in rows
    ]


def grant_db_gpt_access(user_id: str) -> int:
    """Ensure user has read grant for GPT models in access_grant table."""
    py_code = f"""
import sqlite3, uuid, time, json

conn = sqlite3.connect('/app/backend/data/webui.db', timeout=15)
cur = conn.cursor()
user_id = {repr(user_id)}
models = {repr(list(GPT_MODELS))}
now = int(time.time())

added = 0
for m in models:
    cur.execute("SELECT 1 FROM access_grant WHERE resource_type='model' AND resource_id=? AND principal_id=?", (m, user_id))
    if not cur.fetchone():
        grant_id = str(uuid.uuid4()).replace("-", "")
        cur.execute(
            "INSERT INTO access_grant (id, resource_type, resource_id, principal_type, principal_id, permission, created_at) "
            "VALUES (?, 'model', ?, 'user', ?, 'read', ?)",
            (grant_id, m, user_id, now)
        )
        added += 1

conn.commit()
conn.close()
print(json.dumps({{'added': added}}))
"""
    cmd = ["docker", "exec", "-i", "open-webui", "python3", "-"]
    proc = subprocess.run(cmd, input=py_code.encode("utf-8"), capture_output=True)
    if proc.returncode != 0:
        return 0
    try:
        out = json.loads(proc.stdout.decode("utf-8").strip())
        return out.get("added", 0)
    except Exception:
        return 0


def revoke_db_gpt_access(user_id: str) -> int:
    """Revoke user access_grant for GPT models."""
    py_code = f"""
import sqlite3, json

conn = sqlite3.connect('/app/backend/data/webui.db', timeout=15)
cur = conn.cursor()
user_id = {repr(user_id)}
models = {repr(list(GPT_MODELS))}

placeholders = ', '.join('?' * len(models))
cur.execute(f"DELETE FROM access_grant WHERE resource_type='model' AND resource_id IN ({placeholders}) AND principal_id=?", (*models, user_id))
deleted = cur.rowcount
conn.commit()
conn.close()
print(json.dumps({{'deleted': deleted}}))
"""
    cmd = ["docker", "exec", "-i", "open-webui", "python3", "-"]
    proc = subprocess.run(cmd, input=py_code.encode("utf-8"), capture_output=True)
    if proc.returncode != 0:
        return 0
    try:
        out = json.loads(proc.stdout.decode("utf-8").strip())
        return out.get("deleted", 0)
    except Exception:
        return 0


def restart_openwebui():
    """Recreate open-webui container to reload .env configuration."""
    print("-> Đang cập nhật và nạp lại container open-webui với cấu hình mới...")
    subprocess.run(["docker", "compose", "up", "-d", "open-webui"], check=True, cwd=str(ENV_FILE.parent))
    print("-> Cập nhật container thành công!")


def cmd_find(keyword: str):
    results = search_users(keyword)
    if not results:
        print(f"Không tìm thấy nhân viên nào khớp với từ khóa '{keyword}'")
        return

    print(f"\nTìm thấy {len(results)} kết quả khớp với '{keyword}':")
    print("-" * 75)
    print(f"{'Mã NV':<10} | {'Tên nhân viên':<25} | {'Email':<20} | {'Chức vụ / Phòng ban'}")
    print("-" * 75)
    for u in results:
        code = u["username"] or u["email"]
        bio = u["bio"] or ""
        print(f"{code:<10} | {u['name']:<25} | {u['email']:<20} | {bio}")
    print("-" * 75)


def cmd_assign(identifier: str, api_key: str, auto_restart: bool = True):
    user = find_user_by_identifier(identifier)
    if not user:
        print(f"LỖI: Không tìm thấy nhân viên có mã hoặc email '{identifier}' trong hệ thống!")
        print("Gợi ý: Dùng `python3 scripts/manage_gpt_users.py --find <tên>` để tìm mã nhân viên.")
        sys.exit(1)

    code = user["username"] or user["email"]
    key_map, _ = read_env_key_map()
    key_map[code] = api_key.strip()
    write_env_key_map(key_map)

    # Cấp quyền trong DB
    added = grant_db_gpt_access(user["id"])

    print(f"\n THÀNH CÔNG: Đã gán OpenAI API Key cho nhân viên:")
    print(f" - Mã nhân viên: {code}")
    print(f" - Họ và tên:   {user['name']}")
    print(f" - Email:       {user['email']}")
    print(f" - API Key:     {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
    print(f" - Quyền model: Đã kích hoạt quyền dùng {', '.join(GPT_MODELS)} ({added} quyền mới)")

    if auto_restart:
        restart_openwebui()
    else:
        print("\n Lưu ý: Vui lòng chạy `docker restart open-webui` để áp dụng cấu hình mới.")


def cmd_remove(identifier: str, auto_restart: bool = True):
    key_map, _ = read_env_key_map()
    clean_id = identifier.strip().lower()

    # Find matching key in key_map
    matched_key = None
    for k in key_map:
        if k.strip().lower() == clean_id:
            matched_key = k
            break

    user = find_user_by_identifier(identifier)

    if not matched_key and not user:
        print(f"Không tìm thấy cấu hình hoặc nhân viên khớp với '{identifier}'")
        return

    if matched_key:
        del key_map[matched_key]
        write_env_key_map(key_map)
        print(f"Đã xóa cấu hình API key của '{matched_key}' trong .env")

    if user:
        deleted = revoke_db_gpt_access(user["id"])
        print(f"Đã thu hồi quyền truy cập model GPT trong DB cho {user['name']} ({deleted} quyền đã xóa)")

    if auto_restart:
        restart_openwebui()


def cmd_list():
    key_map, _ = read_env_key_map()
    print(f"\nDANH SÁCH NHÂN VIÊN ĐƯỢC GÁN OPENAI GPT API KEY ({len(key_map)} người):")
    print("=" * 80)
    print(f"{'Mã NV / Email':<22} | {'Họ và tên':<24} | {'API Key (Rút gọn)':<20} | {'Trạng thái DB'}")
    print("-" * 80)

    if not key_map:
        print(" (Chưa có nhân viên nào được gán API key riêng)")
    else:
        for ident, key in key_map.items():
            user = find_user_by_identifier(ident)
            name = user["name"] if user else "[Chưa có trong DB]"
            masked_key = f"{key[:8]}...{key[-4:]}" if len(key) > 12 else key[:8]

            # Check DB access
            has_db_access = "Chưa có"
            if user:
                placeholders = ', '.join('?' * len(GPT_MODELS))
                rows = run_container_sqlite(
                    f"SELECT COUNT(*) FROM access_grant WHERE resource_type='model' AND resource_id IN ({placeholders}) AND principal_id=?",
                    (*GPT_MODELS, user["id"]),
                )
                if rows and rows[0][0] >= len(GPT_MODELS):
                    has_db_access = "Đã cấp quyền"
                elif rows and rows[0][0] > 0:
                    has_db_access = f"{rows[0][0]}/{len(GPT_MODELS)} model"

            print(f"{ident:<22} | {name:<24} | {masked_key:<20} | {has_db_access}")

    print("=" * 80)


def cmd_sync(auto_restart: bool = False):
    key_map, _ = read_env_key_map()
    print(f"\nĐang đồng bộ quyền truy cập GPT cho {len(key_map)} tài khoản trong HTMP_OPENAI_USER_KEY_MAP...")

    total_synced = 0
    for ident in key_map:
        user = find_user_by_identifier(ident)
        if user:
            added = grant_db_gpt_access(user["id"])
            total_synced += 1
            print(f" - {ident} ({user['name']}): Đã đồng bộ quyền (+{added})")
        else:
            print(f" - CẢNH BÁO: Không tìm thấy nhân viên '{ident}' trong database!")

    print(f"\nHoàn tất đồng bộ {total_synced} nhân viên.")
    if auto_restart:
        restart_openwebui()


def main():
    parser = argparse.ArgumentParser(description="Quản lý gán API Key GPT theo mã nhân viên")
    parser.add_argument("--find", type=str, help="Tìm mã nhân viên theo tên hoặc mã")
    parser.add_argument("--assign", nargs=2, metavar=("MA_NV", "API_KEY"), help="Gán API Key cho mã nhân viên")
    parser.add_argument("--remove", type=str, metavar="MA_NV", help="Xóa API Key của mã nhân viên")
    parser.add_argument("--list", action="store_true", help="Xem danh sách nhân viên đã gán API Key")
    parser.add_argument("--sync", action="store_true", help="Đồng bộ quyền DB từ cấu hình .env")
    parser.add_argument("--no-restart", action="store_true", help="Không tự động restart open-webui")

    args = parser.parse_args()

    if args.find:
        cmd_find(args.find)
    elif args.assign:
        cmd_assign(args.assign[0], args.assign[1], auto_restart=not args.no_restart)
    elif args.remove:
        cmd_remove(args.remove, auto_restart=not args.no_restart)
    elif args.list:
        cmd_list()
    elif args.sync:
        cmd_sync(auto_restart=not args.no_restart)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

