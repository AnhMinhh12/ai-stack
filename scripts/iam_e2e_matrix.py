#!/usr/bin/env python3
"""Fail-closed IAM E2E matrix scaffold; no IdP identities means no pass."""
from __future__ import annotations

import argparse
import os

REQUIRED = ("IAM_TEST_USER_A", "IAM_TEST_USER_B", "IAM_TEST_GROUP_A", "IAM_TEST_GROUP_B", "OIDC_TEST_BASE_URL")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="reserved for an approved real-identity test runner")
    args = parser.parse_args()
    missing = [key for key in REQUIRED if not os.environ.get(key, "").strip()]
    for key in REQUIRED:
        print(f"{key}: {'PRESENT' if key not in missing else 'BLOCKED'}")
    if args.execute:
        print("BLOCKED: real OIDC login, MFA, separate-group deny, offboarding and Security approval evidence are required.")
    return 2 if missing or args.execute else 0

if __name__ == "__main__":
    raise SystemExit(main())

