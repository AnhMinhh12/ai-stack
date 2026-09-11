#!/usr/bin/env bash
# Verify an encrypted backup in a new temporary Docker volume. Never touches production state.
set -euo pipefail
umask 077

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${1:-}"
KEEP_VOLUME="${CLEAN_ROOM_KEEP_VOLUME:-false}"
if [[ -z "${BACKUP_DIR}" || ! -d "${BACKUP_DIR}" ]]; then
  echo "[ERROR] Usage: $0 /absolute/path/to/backup_DIR" >&2
  exit 2
fi
case "${BACKUP_DIR}" in
  "${ROOT}"/backups/backup_*) ;;
  *) echo "[ERROR] Backup must be under ${ROOT}/backups/backup_*" >&2; exit 2 ;;
esac
if [[ ! -f "${BACKUP_DIR}/COMPLETE" || ! -f "${BACKUP_DIR}/SHA256SUMS" ]]; then
  echo "[ERROR] Backup is incomplete; refusing clean-room verification" >&2
  exit 2
fi
if [[ -z "${BACKUP_GPG_RECIPIENT:-}" ]]; then
  echo "[ERROR] BACKUP_GPG_RECIPIENT is required; refusing unencrypted verification" >&2
  exit 2
fi

# restore.sh performs checksum, decrypt, gzip, tar and snapshot-mapping validation,
# and exits before a write when RESTORE_MODE=clean-room.
RESTORE_MODE=clean-room BACKUP_GPG_RECIPIENT="${BACKUP_GPG_RECIPIENT}" \
  BACKUP_GPG_HOME="${BACKUP_GPG_HOME:-${ROOT}/.secrets/gpg-home}" \
  "${ROOT}/scripts/restore.sh" "${BACKUP_DIR}"

archive_tmp="$(mktemp)"
volume="htmp_cleanroom_$(date -u +%Y%m%d%H%M%S)_$RANDOM"
cleanup() {
  shred -u "${archive_tmp}" 2>/dev/null || rm -f "${archive_tmp}"
  if [[ "${KEEP_VOLUME}" != "true" ]]; then docker volume rm -f "${volume}" >/dev/null 2>&1 || true; fi
}
trap cleanup EXIT

gpg --homedir "${BACKUP_GPG_HOME:-${ROOT}/.secrets/gpg-home}" --batch --quiet --decrypt \
  --output "${archive_tmp}" "${BACKUP_DIR}/open_webui_data.tar.gz.gpg"
docker volume create "${volume}" >/dev/null
docker run --rm -v "${volume}:/data" -v "${archive_tmp}:/backup/archive.tar.gz:ro" \
  alpine@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b \
  sh -ec 'tar -xzf /backup/archive.tar.gz -C /data; test -s /data/webui.db; test -d /data/uploads'
# SQLite is checked inside an isolated copy. This only reads the temporary volume.
docker run --rm -v "${volume}:/data:ro" "${HTMP_OPEN_WEBUI_IMAGE:?HTMP_OPEN_WEBUI_IMAGE must be a registry digest}" \
  python3 -c 'import sqlite3; db=sqlite3.connect("/data/webui.db"); n=db.execute("select count(*) from sqlite_master where type=\"table\"").fetchone()[0]; print("open_webui_tables", n); assert n > 0'
echo "CLEAN_ROOM_ARCHIVE_VERIFY: PASS volume=${volume}"
echo "Qdrant snapshot and Langfuse dump were checksum/decrypt/format validated by restore.sh."
echo "Full service recovery, source-file retrieval and sample RAG require a separately provisioned clean-room Compose project."

