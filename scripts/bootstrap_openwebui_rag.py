#!/usr/bin/env python3
"""Copy versioned HTMP RAG configuration into an Open WebUI runtime and upsert it."""
from __future__ import annotations
import argparse, shutil, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def run(command: list[str]) -> None:
    subprocess.run(command, check=True)
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--container", default="open-webui")
    parser.add_argument("--owner-email", required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    required = [ROOT / "config/htmp-rag-models.json", ROOT / "functions/htmp_fast_rag.py", ROOT / "functions/htmp_technical_rag.py", ROOT / "functions/htmp_postgres_query.py", ROOT / "scripts/openwebui_bootstrap_runtime.py"]
    report_dirs = [ROOT / "config/erp-reports", ROOT / "sql/erp-reports"]
    package_dirs = [ROOT / "erp_ai"]
    if missing := [str(path) for path in required if not path.is_file()]:
        raise SystemExit("FAIL CLOSED: missing bootstrap source: " + ", ".join(missing))
    if missing := [str(path) for path in report_dirs if not path.is_dir()]:
        raise SystemExit("FAIL CLOSED: missing ERP report source: " + ", ".join(missing))
    if missing := [str(path) for path in package_dirs if not path.is_dir()]:
        raise SystemExit("FAIL CLOSED: missing ERP semantic package: " + ", ".join(missing))
    remote = "/tmp/htmp-release-bootstrap"
    run(["docker", "exec", args.container, "sh", "-c", f"rm -rf {remote} && mkdir -p {remote}"])
    for path in required:
        run(["docker", "cp", str(path), f"{args.container}:{remote}/{path.name}"])
    for package in package_dirs:
        run(["docker", "exec", args.container, "rm", "-rf", f"/app/backend/{package.name}"])
        run(["docker", "cp", str(package), f"{args.container}:/app/backend/"])
    run(["docker", "exec", args.container, "sh", "-c", "rm -rf /app/backend/data/erp-reports /app/backend/data/erp-sql && mkdir -p /app/backend/data/erp-reports /app/backend/data/erp-sql"])
    run(["docker", "cp", f"{ROOT/'config/erp-reports'}/.", f"{args.container}:/app/backend/data/erp-reports/"])
    run(["docker", "cp", f"{ROOT/'sql/erp-reports'}/.", f"{args.container}:/app/backend/data/erp-sql/"])
    command = ["docker", "exec", args.container, "python", f"{remote}/openwebui_bootstrap_runtime.py", "--config", f"{remote}/htmp-rag-models.json", "--source-dir", remote, "--owner-email", args.owner_email]
    if args.check:
        command.append("--check")
    run(command)
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
