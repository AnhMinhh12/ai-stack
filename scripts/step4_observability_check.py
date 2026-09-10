#!/usr/bin/env python3
"""Static observability and redaction checks for the step 4 baseline."""
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
nginx = (root / "nginx/nginx.conf").read_text()
policy = (root / "docs/step4-observability-policy.md").read_text()

checks = {
    "server generated request id": "$request_id" in nginx,
    "request id forwarded upstream": "proxy_set_header X-Request-ID $request_id" in nginx,
    "logs avoid query string": '"$request"' not in nginx and "$uri" in nginx,
    "logs avoid auth headers": "authorization" not in nginx.lower() and "api_key" not in nginx.lower(),
    "logs avoid body": "$request_body" not in nginx,
    "logs include timing": "$request_time" in nginx and "$upstream_response_time" in nginx,
    "logs use container streams": "/dev/stdout" in nginx and "/dev/stderr" in nginx,
    "policy redaction": all(word in policy for word in ("prompt", "Authorization", "pseudonymous")),
    "policy alert ownership": all(word in policy for word in ("owner", "severity", "runbook", "escalation")),
    "policy says health is insufficient": "Healthcheck chỉ chứng minh process sống" in policy,
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{name}: {'PASS' if ok else 'FAIL'}")
if failed:
    raise SystemExit("step4 observability check failed: " + ", ".join(failed))
print("step4 observability baseline: PASS")
