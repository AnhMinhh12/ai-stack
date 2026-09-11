#!/usr/bin/env python3
"""Fail-closed validation of pilot external contracts without reading secret values."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDERS = {"", "TBD", "REPLACE", "CHANGEME", "example", "false"}

def present(name: str) -> bool:
    value = os.environ.get(name, "").strip()
    return value not in PLACEHOLDERS and "REPLACE" not in value.upper()

def https_url(name: str) -> bool:
    value = os.environ.get(name, "").strip()
    parsed = urlparse(value)
    return present(name) and parsed.scheme == "https" and bool(parsed.netloc)

def secret_reference(name: str) -> bool:
    value = os.environ.get(name, "").strip()
    return present(name) and not any(token in value.lower() for token in ("password=", "secret=", "token="))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path, default=ROOT / "config/pilot-contract.env.example")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--oidc", action="store_true", help="require OIDC fields even while OIDC is disabled")
    args = parser.parse_args()
    if args.env_file.is_file():
        for line in args.env_file.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
    checks = {
        "secret manager URI": present("SECRET_MANAGER_URI"),
        "VLLM key reference": secret_reference("VLLM_API_KEY_REF"),
        "Qdrant key reference": secret_reference("QDRANT_API_KEY_REF"),
        "Redis password reference": secret_reference("REDIS_PASSWORD_REF"),
        "WebUI secret reference": secret_reference("WEBUI_SECRET_KEY_REF"),
        "off-host backup URI": present("OFFHOST_BACKUP_URI"),
        "alert webhook reference": secret_reference("ALERT_WEBHOOK_REF"),
        "on-call owner": present("ONCALL_OWNER"),
        "trace retention": present("TRACE_RETENTION_DAYS"),
    }
    if args.oidc or os.environ.get("OIDC_ENABLED", "false").lower() == "true":
        checks.update({
            "OIDC issuer HTTPS URL": https_url("OIDC_ISSUER_URL"),
            "OIDC client ID": present("OIDC_CLIENT_ID"),
            "OIDC client-secret reference": secret_reference("OIDC_CLIENT_SECRET_REF"),
            "OIDC redirect HTTPS URL": https_url("OIDC_REDIRECT_URL"),
            "OIDC group claim": present("OIDC_GROUP_CLAIM"),
            "OIDC CA-bundle reference": secret_reference("OIDC_CA_BUNDLE_REF"),
        })
    for name, ok in checks.items():
        print(f"{name}: {'PASS' if ok else 'BLOCKED'}")
    if args.strict and not all(checks.values()):
        return 2
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
