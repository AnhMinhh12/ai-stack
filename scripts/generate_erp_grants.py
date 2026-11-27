#!/usr/bin/env python3
"""Generate and validate per-user HTMP_AGENT_GRANTS JSON from department role profiles."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from erp_ai.semantic_model import load_erp_config


def validate_grant_profiles(config: dict[str, Any], profiles: dict[str, Any]) -> list[str]:
    """Validate that every report/dataset ID referenced in role profiles exists and is approved."""
    valid_reports = {r["id"] for r in config.get("reports", []) if isinstance(r, dict) and r.get("id")}
    valid_datasets = {
        k for k, v in (config.get("semantic_contracts") or {}).items()
        if isinstance(v, dict) and v.get("status") == "approved"
    }
    errors: list[str] = []
    roles = profiles.get("roles")
    if not isinstance(roles, dict) or not roles:
        return ["missing_roles_section"]
    for role_name, role_cfg in roles.items():
        if not isinstance(role_cfg, dict):
            errors.append(f"{role_name}: invalid role object")
            continue
        for rid in role_cfg.get("reports") or ():
            if rid not in valid_reports:
                errors.append(f"{role_name}: unknown report {rid!r}")
        for dsid in role_cfg.get("semantic_datasets") or ():
            if dsid not in valid_datasets:
                errors.append(f"{role_name}: unknown or unapproved dataset {dsid!r}")
    return errors


def compile_user_grants(
    user_rows: list[dict[str, Any]],
    *,
    config: dict[str, Any],
    profiles: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Compile normalized user assignments into HTMP_AGENT_GRANTS mapping."""
    errors = validate_grant_profiles(config, profiles)
    if errors:
        raise ValueError("Invalid role profiles: " + "; ".join(errors))

    roles_map = profiles["roles"]
    all_reports = sorted(r["id"] for r in config.get("reports", []) if isinstance(r, dict) and r.get("id"))
    all_datasets = sorted(
        k for k, v in (config.get("semantic_contracts") or {}).items()
        if isinstance(v, dict) and v.get("status") == "approved"
    )
    grants: dict[str, dict[str, Any]] = {}

    for row in user_rows:
        identity = str(row.get("webui_user_id") or row.get("email") or "").strip().lower()
        if not identity:
            raise ValueError(f"Missing email or webui_user_id in row: {row!r}")
        erp_uid_raw = row.get("erp_user_id")
        try:
            erp_uid = int(erp_uid_raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid erp_user_id for {identity!r}: {erp_uid_raw!r}") from exc
        if erp_uid <= 0:
            raise ValueError(f"erp_user_id must be > 0 for {identity!r}")

        raw_roles = row.get("roles")
        if isinstance(raw_roles, str):
            role_names = [r.strip() for r in raw_roles.replace(";", ",").split(",") if r.strip()]
        elif isinstance(raw_roles, (list, tuple)):
            role_names = [str(r).strip() for r in raw_roles if str(r).strip()]
        else:
            role_names = []
        if not role_names:
            raise ValueError(f"No roles assigned for {identity!r}")

        reports_set: set[str] = set()
        datasets_set: set[str] = set()
        for role_name in role_names:
            if role_name == "admin":
                reports_set.update(all_reports)
                datasets_set.update(all_datasets)
                continue
            if role_name not in roles_map:
                raise ValueError(f"Unknown role {role_name!r} for {identity!r}")
            rcfg = roles_map[role_name]
            reports_set.update(rcfg.get("reports") or ())
            datasets_set.update(rcfg.get("semantic_datasets") or ())

        grants[identity] = {
            "erp_user_id": erp_uid,
            "reports": sorted(reports_set),
            "semantic_datasets": sorted(datasets_set),
        }
    return grants


def _read_user_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON user mapping must be a list of objects")
        return data
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--users", type=Path, help="CSV or JSON file with columns: email,erp_user_id,roles")
    parser.add_argument("--profiles", type=Path, default=ROOT / "config/erp-grant-profiles.json")
    parser.add_argument("--check", action="store_true", help="Validate role profiles against config/erp-agent.json only")
    parser.add_argument("--example", action="store_true", help="Print an anonymized example HTMP_AGENT_GRANTS payload")
    args = parser.parse_args()

    config = load_erp_config(ROOT)
    profiles = json.loads(args.profiles.read_text(encoding="utf-8"))
    errs = validate_grant_profiles(config, profiles)
    if errs:
        print("Profile errors:", json.dumps(errs, ensure_ascii=False), file=sys.stderr)
        return 1
    if args.check:
        roles = profiles.get("roles", {})
        ds_count = sum(1 for v in (config.get("semantic_contracts") or {}).values() if isinstance(v, dict) and v.get("status") == "approved")
        print(f"OK: validated {len(roles)} role profiles against {ds_count} semantic datasets and {len(config['reports'])} reports.")
        return 0
    if args.example:
        sample = compile_user_grants(
            [
                {"email": "sales.demo@example.invalid", "erp_user_id": 101, "roles": "sales"},
                {"email": "wh.plan.demo@example.invalid", "erp_user_id": 102, "roles": "warehouse,planning"},
            ],
            config=config,
            profiles=profiles,
        )
        print(json.dumps(sample, ensure_ascii=False, indent=2))
        return 0
    if not args.users:
        parser.error("Provide --check, --example, or --users <path>")
    grants = compile_user_grants(_read_user_rows(args.users), config=config, profiles=profiles)
    print(json.dumps(grants, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
