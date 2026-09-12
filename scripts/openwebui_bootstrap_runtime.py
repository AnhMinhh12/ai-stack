#!/usr/bin/env python3
"""Runtime half of the idempotent HTMP Open WebUI RAG bootstrap."""
from __future__ import annotations
import argparse, json, os, sqlite3, sys, time
from pathlib import Path

def fail(message: str) -> None:
    raise SystemExit(f"FAIL CLOSED: {message}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--owner-email", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    db_path = Path("/app/backend/data/webui.db")
    if not db_path.is_file():
        fail("Open WebUI database is unavailable")
    cfg = json.loads(Path(args.config).read_text())
    conn = sqlite3.connect(db_path)
    user = conn.execute("select id from user where email=?", (args.owner_email,)).fetchone()
    if not user:
        fail("bootstrap owner does not exist")
    owner_id = user[0]
    knowledge = []
    for name in cfg["knowledge_base_names"]:
        row = conn.execute("select id,name,description from knowledge where name=?", (name,)).fetchone()
        if not row:
            fail(f"required Knowledge Base missing: {name}")
        knowledge.append({"id": row[0], "name": row[1], "type": "collection", "description": row[2]})
    expected_functions = {item["id"] for item in cfg["functions"]}
    expected_models = {item["id"] for item in cfg["models"]}
    if args.check:
        found_functions = {row[0] for row in conn.execute("select id from function where is_active=1")}
        found_models = {row[0] for row in conn.execute("select id from model where is_active=1")}
        missing = sorted((expected_functions - found_functions) | (expected_models - found_models))
        if missing:
            fail("bootstrap objects missing: " + ", ".join(missing))
        print("bootstrap check: PASS")
        return 0
    now = str(int(time.time()))
    for item in cfg["functions"]:
        content = (Path(args.source_dir) / item["source"]).read_text()
        conn.execute(
            "insert into function (id,user_id,name,type,content,meta,valves,is_active,is_global,updated_at,created_at) values (?,?,?,?,?,?,?,?,?,?,?) "
            "on conflict(id) do update set user_id=excluded.user_id,name=excluded.name,type=excluded.type,content=excluded.content,meta=excluded.meta,is_active=1,is_global=excluded.is_global,updated_at=excluded.updated_at",
            (item["id"], owner_id, item["name"], item.get("type", "filter"), content, json.dumps({"description": item["description"]}), None, 1, int(item.get("is_global", False)), now, now),
        )
    capabilities = {"file_context": True, "file_upload": True, "citations": True, "status_updates": True, "builtin_tools": True, "web_search": False, "memory": False}
    for item in cfg["models"]:
        if not conn.execute("select 1 from model where id=?", (item["base_model_id"],)).fetchone():
            fail(f"base model missing: {item['base_model_id']}")
        row = conn.execute("select meta from model where id=?", (item["id"],)).fetchone()
        meta = json.loads(row[0]) if row else {}
        meta.update({"description": "HTMP internal RAG profile", "capabilities": capabilities, "knowledge": knowledge, "filterIds": item["filter_ids"], "toolIds": ["htmp_postgres_query"]})
        conn.execute(
            "insert into model (id,user_id,base_model_id,name,params,meta,updated_at,created_at,is_active) values (?,?,?,?,?,?,?,?,?) "
            "on conflict(id) do update set user_id=excluded.user_id,base_model_id=excluded.base_model_id,name=excluded.name,params=excluded.params,meta=excluded.meta,updated_at=excluded.updated_at,is_active=1",
            (item["id"], owner_id, item["base_model_id"], item["name"], json.dumps(item["params"]), json.dumps(meta), now, now, 1),
        )
    conn.commit()
    print("bootstrap apply: PASS")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
