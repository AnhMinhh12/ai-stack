#!/usr/bin/env python3
"""Static fail-closed checks for the step 3 IAM/data policy baseline."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
compose = (ROOT / "docker-compose.yml").read_text()
policy = (ROOT / "docs/step3-iam-data-governance.md").read_text()

checks = {
    "public signup disabled": "- ENABLE_SIGNUP=False" in compose,
    "deny-by-default policy": "Mặc định deny" in policy,
    "server-side identity": "server-side" in policy and "không nhận tin từ client" in policy,
    "required tenant metadata": all(f"`{field}`" in policy for field in (
        "tenant_id", "owner_id", "classification", "source_acl",
        "version", "retention_until", "deletion_status"
    )),
    "legal hold rule": "`legal_hold` chặn deletion tự động" in policy,
    "break-glass controls": all(word in policy for word in (
        "MFA", "approval", "expiry", "audit"
    )),
}
failed = [name for name, ok in checks.items() if not ok]
for name, ok in checks.items():
    print(f"{name}: {'PASS' if ok else 'FAIL'}")
if failed:
    raise SystemExit(f"step3 policy check failed: {', '.join(failed)}")
print("step3 policy baseline: PASS")
