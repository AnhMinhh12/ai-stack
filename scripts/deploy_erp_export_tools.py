#!/usr/bin/env python3
"""Update only the two registered ERP tool bodies in Open WebUI."""

from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import time


TOOLS = {
    "htmp_postgres_query": "htmp_postgres_query.py",
    "htmp_erp_agent": "htmp_erp_agent.py",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--db", default="/app/backend/data/webui.db")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    expected = {tool_id: (source_dir / filename).read_text() for tool_id, filename in TOOLS.items()}
    with sqlite3.connect(args.db, timeout=15) as db:
        db.execute("BEGIN IMMEDIATE" if args.apply else "BEGIN")
        rows = dict(db.execute("SELECT id,content FROM tool WHERE id IN (?,?)", tuple(TOOLS)))
        if set(rows) != set(TOOLS):
            raise SystemExit("ERP tools are not both registered; no changes made")
        changed = [tool_id for tool_id in TOOLS if rows[tool_id] != expected[tool_id]]
        print("Tools needing update:", ", ".join(changed) or "none")
        if not args.apply:
            db.rollback()
            return
        for tool_id in changed:
            db.execute(
                "UPDATE tool SET content=?,updated_at=? WHERE id=?",
                (expected[tool_id], int(time.time()), tool_id),
            )
        db.commit()
        print("ERP tool update complete")


if __name__ == "__main__":
    main()
