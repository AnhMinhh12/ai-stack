#!/usr/bin/env python3
"""Read-only staging/runtime smoke checks for step 7."""
from __future__ import annotations

import json
import subprocess
import sys


def run(cmd: list[str]) -> tuple[bool, str]:
    result = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    return result.returncode == 0, result.stdout.strip()


def main() -> int:
    checks: list[tuple[str, bool]] = []
    ok, _ = run(["docker", "compose", "config", "--quiet"]); checks.append(("compose config", ok))
    ok, ps = run(["docker", "compose", "ps", "--format", "json"]);
    healthy = 0
    if ok:
        for line in ps.splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "healthy" in row.get("Health", "").lower() or "healthy" in row.get("Status", "").lower():
                healthy += 1
    checks.append(("8 services healthy", ok and healthy == 8))
    ok, _ = run(["docker", "exec", "nginx-gateway", "nginx", "-t"]); checks.append(("nginx syntax", ok))
    ok, _ = run(["docker", "exec", "open-webui", "curl", "-fsS", "http://127.0.0.1:8080/health"]); checks.append(("open-webui health", ok))
    ok, _ = run(["docker", "exec", "vllm-engine", "curl", "-fsS", "http://127.0.0.1:8000/health"]); checks.append(("vllm health", ok))
    ok, _ = run(["docker", "exec", "vllm-engine", "sh", "-lc", 'curl -fsS -H "Authorization: Bearer $VLLM_API_KEY" http://127.0.0.1:8000/v1/models >/dev/null']); checks.append(("vllm authenticated models", ok))
    ok, _ = run(["docker", "exec", "open-webui", "sh", "-lc", 'curl -fsS -H "api-key: $QDRANT_API_KEY" http://qdrant:6333/collections >/dev/null']); checks.append(("qdrant authenticated collections", ok))
    ok, _ = run(["docker", "exec", "open-webui", "curl", "-fsS", "http://tika:9998/version"]); checks.append(("tika health", ok))
    ok, output = run(["docker", "inspect", "--format", "{{.State.Health.Status}}", "langfuse-server"]); checks.append(("langfuse health", ok and output == "healthy"))

    for name, passed in checks:
        print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not all(passed for _, passed in checks):
        print("staging smoke: FAIL")
        return 2
    print("staging smoke: PASS (runtime only; not pilot acceptance)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
