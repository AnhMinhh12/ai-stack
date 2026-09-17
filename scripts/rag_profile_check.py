#!/usr/bin/env python3
"""Verify versioned HTMP RAG model profiles and citation capability in Open WebUI."""
from __future__ import annotations
import json, subprocess

def run(command: list[str]) -> tuple[bool, str]:
    r = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return r.returncode == 0, r.stdout.strip()

def main() -> int:
    code = (
        "import json,sqlite3; c=sqlite3.connect('/app/backend/data/webui.db'); "
        "rows=c.execute(\"select id,meta from model where id in ('htmp-nhanh','htmp-ky')\").fetchall(); "
        "print(json.dumps({i:json.loads(m) for i,m in rows}))"
    )
    ok, output = run(["docker","exec","open-webui","python","-c",code])
    checks: dict[str,bool] = {"Open WebUI profile query": ok}
    if ok:
        try:
            profiles = json.loads(output)
            expected = (
                ("htmp-nhanh", "htmp_fast_rag", False, ["htmp_postgres_query"]),
                ("htmp-ky", "htmp_technical_rag", True, []),
            )
            for model, filter_id, expects_knowledge, tool_ids in expected:
                meta = profiles.get(model, {})
                capabilities = meta.get("capabilities") or {}
                checks[f"{model} knowledge isolation"] = bool(meta.get("knowledge")) is expects_knowledge
                checks[f"{model} profile filter"] = filter_id in meta.get("filterIds", [])
                checks[f"{model} tool isolation"] = meta.get("toolIds", []) == tool_ids
                checks[f"{model} citations enabled"] = capabilities.get("citations") is True
        except Exception:
            checks["profile metadata valid JSON"] = False
    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    return 0 if all(checks.values()) else 2
if __name__ == "__main__":
    raise SystemExit(main())
