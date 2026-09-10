#!/usr/bin/env python3
"""Fail-closed preflight for pilot promotion and shared-platform planning."""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command_ok(command: list[str]) -> bool:
    return subprocess.run(command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--promote", action="store_true", help="evaluate promotion; never mutate deployment")
    args = parser.parse_args()

    checks: dict[str, bool] = {
        "compose config": command_ok(["docker", "compose", "config", "--quiet"]),
        "step 0 approval evidence": "**Owner/approver:** TBD / TBD" not in (ROOT / "docs/evidence/BAS-20260909-r2/baseline.md").read_text(),
        "release status unblocked": "status: blocked" not in (ROOT / "docs/evidence/REL-20260909-r2/release-manifest.yaml").read_text(),
        "step 3 IAM E2E evidence": "Chưa thể xác nhận" not in (ROOT / "docs/evidence/IAM-20260909/step3.md").read_text(),
        "step 4 trace evidence": "chưa có trace end-to-end evidence" not in (ROOT / "docs/evidence/OBS-20260909/step4.md").read_text(),
        "step 5 DR evidence": "Trạng thái:** `blocked`" not in (ROOT / "docs/evidence/DR-20260909/step5.md").read_text(),
        "step 6 capacity evidence": "Trạng thái:** `blocked`" not in (ROOT / "docs/evidence/CAP-20260909/step6.md").read_text(),
        "pilot scope approved": "Trạng thái:** `target`, chưa phải approval." not in (ROOT / "docs/pilot-scope.md").read_text(),
    }
    if args.promote:
        checks["explicit pilot approval"] = os.environ.get("PILOT_APPROVED") == "YES"

    for name, ok in checks.items():
        print(f"{name}: {'PASS' if ok else 'BLOCKED'}")
    if not all(checks.values()):
        print("pilot/shared-platform promotion: BLOCKED")
        return 2
    print("pilot/shared-platform promotion: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
