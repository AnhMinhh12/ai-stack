#!/usr/bin/env python3
"""Update only the ERP tool's display instruction, with an exact-match guard."""
import sqlite3
import time

OLD = "Bảng kết quả đã hiển thị ở trên. Chỉ trả lời đúng một câu: 'Vui lòng xem bảng kết quả ở trên.' Không nhắc lại số liệu, không tạo bảng hoặc biểu đồ khác."
NEW = "Trả lời trực tiếp bằng tiếng Việt tự nhiên, trình bày rõ các số liệu và bối cảnh trong kết quả. Không lặp lại nguyên bảng hay tạo thêm bảng nếu bảng đã hiển thị; không tự suy diễn số liệu."
OLD_RENDER = '            html = render_erp_embed({"blocks": blocks}, downloads)'
NEW_RENDER = '''            comparison = bool(rows) and all(
                isinstance(row, dict) and {"chi_tieu", "hien_tai", "ban_truoc", "chenh_lech"} <= row.keys()
                for row in rows
            )
            html = render_erp_embed({"blocks": blocks}, downloads, show_table=explicit_table or not comparison)'''

with sqlite3.connect('/app/backend/data/webui.db', timeout=15) as db:
    db.execute('BEGIN IMMEDIATE')
    row = db.execute('SELECT content FROM tool WHERE id=?', ('htmp_postgres_query',)).fetchone()
    if not row or row[0].count(OLD) != 1 or row[0].count(OLD_RENDER) != 1:
        raise SystemExit('ERP instruction does not match the expected version; no changes made')
    db.execute('UPDATE tool SET content=?, updated_at=? WHERE id=?',
               (row[0].replace(OLD, NEW).replace(OLD_RENDER, NEW_RENDER), int(time.time()), 'htmp_postgres_query'))
    print('Updated ERP display instruction')
