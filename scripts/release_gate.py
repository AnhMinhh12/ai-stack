#!/usr/bin/env python3
"""Fail-closed release gate for an immutable HTMP supply-chain candidate."""
from __future__ import annotations
import argparse, re
from pathlib import Path

REQUIRED = ("sbom.spdx.json", "sbom.cdx.json", "cve.grype.json", "licenses.json", "scan-policy.yaml", "security-approval.yaml", "rollback.yaml")
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    checks = {"manifest exists": args.manifest.is_file()}
    text = args.manifest.read_text() if args.manifest.is_file() else ""
    checks["owner assigned"] = "owner: Ho Anh Minh" in text
    checks["security approval assigned"] = "approver: Security" in text
    checks["immutable Open WebUI digest"] = bool(re.search(r"open_webui:[\s\S]*?reference: .*@sha256:[0-9a-f]{64}", text))
    checks["release status approved"] = "status: approved" in text
    for name in REQUIRED:
        checks[f"artifact {name}"] = (args.evidence_dir / name).is_file()
    for name, ok in checks.items():
        print(f"{name}: {'PASS' if ok else 'BLOCKED'}")
    if not all(checks.values()):
        print("release promotion: BLOCKED")
        return 2
    print("release promotion: PASS")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
