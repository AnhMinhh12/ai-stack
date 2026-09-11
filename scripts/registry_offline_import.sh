#!/usr/bin/env bash
# Import the approved OCI Registry image without contacting an external registry.
set -euo pipefail

EXPECTED="registry@sha256:a3d8aaa63ed8681a604f1dea0aa03f100d5895b6a58ace528858a7b332415373"
ARCHIVE="${1:-}"
if [[ -z "${ARCHIVE}" || ! -f "${ARCHIVE}" ]]; then
  echo "Usage: $0 /absolute/path/to/registry-image.tar" >&2
  exit 2
fi
docker load --input "${ARCHIVE}"
if ! docker image inspect "${EXPECTED}" >/dev/null 2>&1; then
  echo "[ERROR] Imported image does not match approved digest: ${EXPECTED}" >&2
  exit 2
fi
echo "Registry image import: PASS (${EXPECTED})"
echo "Next: create TLS/auth/data directories outside Git, trust the CA for registry.htmp.internal:5443, then run docker compose -f docker-compose.registry.yml up -d"

