#!/usr/bin/env python3
"""Read-only staging/runtime smoke checks for Step 7."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def run(cmd: list[str]) -> tuple[bool, str]:
    result = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return result.returncode == 0, result.stdout.strip()

def main() -> int:
    checks: list[tuple[str, bool]] = []
    ok, _ = run(["docker", "compose", "config", "--quiet"]); checks.append(("compose config", ok))
    ok, ps = run(["docker", "compose", "ps", "--format", "json"])
    healthy = 0
    if ok:
        for line in ps.splitlines():
            try: row = json.loads(line)
            except json.JSONDecodeError: continue
            if "healthy" in row.get("Health", "").lower() or "healthy" in row.get("Status", "").lower(): healthy += 1
    checks.append(("8 services healthy", ok and healthy == 8))
    for name, command in (
        ("nginx syntax", ["docker","exec","nginx-gateway","nginx","-t"]),
        ("open-webui health", ["docker","exec","open-webui","curl","-fsS","http://127.0.0.1:8080/health"]),
        ("vllm health", ["docker","exec","vllm-engine","curl","-fsS","http://127.0.0.1:8000/health"]),
        ("vllm authenticated models", ["docker","exec","vllm-engine","sh","-lc",'curl -fsS -H "Authorization: Bearer $VLLM_API_KEY" http://127.0.0.1:8000/v1/models >/dev/null']),
        ("qdrant authenticated collections", ["docker","exec","open-webui","sh","-lc",'curl -fsS -H "api-key: $QDRANT_API_KEY" http://qdrant:6333/collections >/dev/null']),
        ("tika health", ["docker","exec","open-webui","curl","-fsS","http://tika:9998/version"]),
    ):
        ok, _ = run(command); checks.append((name, ok))
    ok, output = run(["docker","inspect","--format","{{.State.Health.Status}}","langfuse-server"]); checks.append(("langfuse health", ok and output == "healthy"))
    ok, _ = run([sys.executable, "scripts/bootstrap_openwebui_rag.py", "--owner-email", "hoanhminhz@gmail.com", "--check"]); checks.append(("versioned RAG bootstrap", ok))
    ok, _ = run([sys.executable, "scripts/rag_profile_check.py"]); checks.append(("RAG profiles and citations", ok))
    for name, passed in checks: print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not all(passed for _, passed in checks):
        print("staging smoke: FAIL"); return 2
    print("staging smoke: PASS (runtime/RAG only; external pilot gates remain blocked)")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
