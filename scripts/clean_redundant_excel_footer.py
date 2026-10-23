#!/usr/bin/env python3
"""Remove one redundant Excel instruction from the specified Open WebUI chat."""

from __future__ import annotations

import argparse
import json
import sqlite3
import time


CHAT_ID = "264ce3e9-2341-4643-b479-58e80c9b1942"
FOOTER = (
    "Bạn có thể lưu nội dung bảng này thành file Excel với các cột:\n\n"
    "```text\nSTT | Câu hỏi | Phân hệ/đường dẫn dự kiến | Ghi chú\n```"
)
MODEL_IDS = ("gpt-5.6-luna", "gpt-5.6-sol")
EXPORT_GUIDANCE = (
    "Khi người dùng yêu cầu tạo Excel, Word hoặc PDF từ nội dung dạng bảng, "
    "hãy đưa ra bảng Markdown đầy đủ để giao diện cung cấp nút tải. "
    "Sau bảng, chỉ giữ thông tin cần thiết cho tính chính xác của dữ liệu. "
    "Không thêm hướng dẫn sao chép/lưu thủ công và không lặp lại tên cột "
    "trong một khối mã. Không tuyên bố đã tạo file nếu chưa có nút hoặc liên kết tải."
)


def clean(content: str) -> str:
    wrapped = "\n\n" + FOOTER + "\n\n"
    if content.count(wrapped) != 1:
        raise ValueError("Expected one exact redundant footer")
    return content.replace(wrapped, "\n\n", 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="/app/backend/data/webui.db")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    with sqlite3.connect(args.db, timeout=15) as db:
        db.execute("BEGIN IMMEDIATE" if args.apply else "BEGIN")
        row = db.execute("SELECT chat FROM chat WHERE id=?", (CHAT_ID,)).fetchone()
        if not row:
            raise SystemExit("Target chat is missing")
        chat = json.loads(row[0])
        if chat.get("models") != ["gpt-5.6-luna"]:
            raise SystemExit("Target chat model changed; no changes made")
        messages = chat.get("history", {}).get("messages", {})
        targets = [(id_, message) for id_, message in messages.items()
                   if message.get("role") == "assistant" and FOOTER in (message.get("content") or "")]
        if len(targets) > 1:
            raise SystemExit("Multiple matching assistant messages; no changes made")
        chat_message = None
        if targets:
            message_id, message = targets[0]
            chat_message = db.execute(
                "SELECT id,content FROM chat_message WHERE chat_id=? AND id LIKE ? AND role='assistant'",
                (CHAT_ID, "%" + message_id),
            ).fetchone()
            if not chat_message or json.loads(chat_message[1]) != message["content"]:
                raise SystemExit("Stored chat copies differ; no changes made")
            message["content"] = clean(message["content"])

        model_rows = db.execute("SELECT id,params FROM model WHERE id IN (?,?)", MODEL_IDS).fetchall()
        if {item[0] for item in model_rows} != set(MODEL_IDS):
            raise SystemExit("GPT model configuration is missing")
        model_updates = []
        for model_id, raw_params in model_rows:
            params = json.loads(raw_params or "{}")
            system = params.get("system") or ""
            if EXPORT_GUIDANCE not in system:
                params["system"] = (system + "\n\n" + EXPORT_GUIDANCE).strip()
                model_updates.append((model_id, params))
        print("Chat footer to remove:", bool(targets))
        print("GPT prompts to update:", len(model_updates))
        if not args.apply:
            db.rollback()
            return

        now = int(time.time())
        if targets:
            db.execute("UPDATE chat SET chat=?,updated_at=? WHERE id=?",
                       (json.dumps(chat, ensure_ascii=False), now, CHAT_ID))
            db.execute("UPDATE chat_message SET content=?,updated_at=? WHERE id=?",
                       (json.dumps(targets[0][1]["content"], ensure_ascii=False), now, chat_message[0]))
        for model_id, params in model_updates:
            db.execute("UPDATE model SET params=?,updated_at=? WHERE id=?",
                       (json.dumps(params, ensure_ascii=False), now, model_id))
        db.commit()
        print("Redundant Excel footer cleanup complete")


if __name__ == "__main__":
    main()
