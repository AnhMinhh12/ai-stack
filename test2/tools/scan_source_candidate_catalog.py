#!/usr/bin/env python3
"""Read-only catalog scan for all objects referenced by config/erp-agent.json.

Run on Machine A with HTMP_DB_HOST, HTMP_DB_PORT, HTMP_DB_NAME, HTMP_DB_USER
and HTMP_DB_PASSWORD already supplied by its local runtime environment. The
script never prints or writes those settings. It starts a READ ONLY transaction
and writes catalog metadata only, not ERP business rows.
"""
import json
import os
import re
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "erp-agent.json"
OUTPUT = ROOT / "test2" / "handoff" / "db-catalog-candidates.json"
NAME = re.compile(r"^(?:(?P<schema>[a-z_][a-z0-9_]*)\.)?(?P<table>[a-z_][a-z0-9_]*)$", re.I)


def connection_settings():
    required = ("HTMP_DB_HOST", "HTMP_DB_USER", "HTMP_DB_PASSWORD")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise SystemExit("Missing local DB environment settings: " + ", ".join(missing))
    return {
        "host": os.environ["HTMP_DB_HOST"],
        "port": os.getenv("HTMP_DB_PORT", "5410"),
        "dbname": os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
        "user": os.environ["HTMP_DB_USER"],
        "password": os.environ["HTMP_DB_PASSWORD"],
        "connect_timeout": 10,
        "row_factory": dict_row,
    }


def candidates(config):
    found = set()
    for report in config["reports"]:
        for value in report.get("tables", []):
            match = NAME.fullmatch(value)
            if match:
                found.add((match.group("schema") or "public", match.group("table")))
    return sorted(found)


def main():
    config = json.loads(CONFIG.read_text())
    objects = candidates(config)
    catalog = {"source_config": str(CONFIG.relative_to(ROOT)), "objects": [], "reports": {}}
    for report in config["reports"]:
        catalog["reports"][report["id"]] = {"tables": report["tables"], "join": report["join"], "fields": report["fields"], "validation": report["validation"]}
    with psycopg.connect(**connection_settings()) as conn:
        with conn.cursor() as cur:
            cur.execute("BEGIN READ ONLY")
            cur.execute("SET LOCAL statement_timeout = '15s'")
            for schema, table in objects:
                cur.execute("""
                    SELECT c.relkind, c.oid, pg_get_userbyid(c.relowner) AS owner
                    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                    WHERE n.nspname=%s AND c.relname=%s
                """, (schema, table))
                relation = cur.fetchone()
                cur.execute("""
                    SELECT column_name, data_type, udt_name, is_nullable, ordinal_position
                    FROM information_schema.columns
                    WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position
                """, (schema, table))
                columns = cur.fetchall()
                cur.execute("""
                    SELECT con.conname, con.contype, pg_get_constraintdef(con.oid, true) AS definition
                    FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid
                    JOIN pg_namespace n ON n.oid=c.relnamespace
                    WHERE n.nspname=%s AND c.relname=%s ORDER BY con.conname
                """, (schema, table))
                constraints = cur.fetchall()
                definition = None
                if relation and relation["relkind"] in ("v", "m"):
                    cur.execute("SELECT pg_get_viewdef(%s, true) AS definition", (relation["oid"],))
                    definition = cur.fetchone()["definition"]
                catalog["objects"].append({"schema": schema, "name": table, "relation": relation, "columns": columns, "constraints": constraints, "view_definition": definition})
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, indent=2, default=str) + "\n")
    print(f"Wrote {len(catalog['objects'])} catalog objects to {OUTPUT}")


if __name__ == "__main__":
    main()
