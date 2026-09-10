#!/usr/bin/env python3
"""Fail-closed gate for opening a rollout wave; never changes traffic."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOCKED_MARKERS = ("status: blocked", "`blocked`", "TBD", "pending")
REQUIRED_FILES = (
    ROOT / "docs/evidence/REL-20260909-r2/release-manifest.yaml",
    ROOT / "docs/evidence/IAM-20260909/step3.md",
    ROOT / "docs/evidence/OBS-20260909/step4.md",
    ROOT / "docs/evidence/DR-20260909/step5.md",
    ROOT / "docs/evidence/CAP-20260909/step6.md",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave-id", required=True)
    parser.add_argument("--open-traffic", action="store_true")
    args = parser.parse_args()
    wave = ROOT / "docs/rollout-waves" / f"{args.wave_id}.yaml"
    checks: dict[str, bool] = {"wave file exists": wave.is_file()}
    wave_text = wave.read_text() if wave.is_file() else ""
    checks["wave status approved"] = "status: approved" in wave_text
    checks["wave has no TBD/pending"] = not any(marker in wave_text for marker in ("TBD", "pending"))
    checks["all required evidence files exist"] = all(path.is_file() for path in REQUIRED_FILES)
    checks["release evidence unblocked"] = "status: blocked" not in (ROOT / "docs/evidence/REL-20260909-r2/release-manifest.yaml").read_text()
    checks["IAM evidence unblocked"] = "Trạng thái:** `blocked`" not in (ROOT / "docs/evidence/IAM-20260909/step3.md").read_text()
    checks["observability evidence unblocked"] = "Trạng thái:** `blocked`" not in (ROOT / "docs/evidence/OBS-20260909/step4.md").read_text()
    checks["DR evidence unblocked"] = "Trạng thái:** `blocked`" not in (ROOT / "docs/evidence/DR-20260909/step5.md").read_text()
    checks["capacity evidence unblocked"] = "Trạng thái:** `blocked`" not in (ROOT / "docs/evidence/CAP-20260909/step6.md").read_text()
    if args.open_traffic:
        checks["explicit wave approval"] = os.environ.get("WAVE_APPROVED") == "YES"

    for name, ok in checks.items():
        print(f"{name}: {'PASS' if ok else 'BLOCKED'}")
    if not all(checks.values()):
        print(f"{args.wave_id}: traffic opening BLOCKED")
        return 2
    print(f"{args.wave_id}: gate PASS; traffic change remains an external operator action")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
