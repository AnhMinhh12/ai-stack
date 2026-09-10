#!/usr/bin/env bash
# ==============================================================================
# Enterprise Local AI Stack - Disaster Recovery & Restore Script
# Components: Qdrant Vector DB, PostgreSQL (Langfuse), Open WebUI Data
# ==============================================================================

set -euo pipefail
umask 077

AI_STACK_DIR="/home/admin/ai-stack"
BACKUP_ROOT="${AI_STACK_DIR}/backups"
TARGET_BACKUP="${1:-}"
RESTORE_MODE="${RESTORE_MODE:-clean-room}"
RESTORE_CONFIRM="${RESTORE_CONFIRM:-}"
MIN_ARTIFACT_BYTES=256
if [[ "${RESTORE_MODE}" != "clean-room" && "${RESTORE_MODE}" != "production" ]]; then
    echo "[ERROR] RESTORE_MODE must be clean-room or production" >&2
    exit 1
fi
if [[ "${RESTORE_MODE}" == "production" && "${RESTORE_CONFIRM}" != "I_UNDERSTAND_PRODUCTION_RESTORE" ]]; then
    echo "[ERROR] Production restore requires RESTORE_CONFIRM=I_UNDERSTAND_PRODUCTION_RESTORE" >&2
    exit 1
fi

# Start timer for RTO measurement
START_TIME=$(date +%s)

# Load environment variables
if [ -f "${AI_STACK_DIR}/.env" ]; then
    set -a
    source "${AI_STACK_DIR}/.env"
    set +a
else
    echo "[ERROR] .env file not found at ${AI_STACK_DIR}/.env" >&2
    exit 1
fi

BACKUP_GPG_HOME="${BACKUP_GPG_HOME:-${AI_STACK_DIR}/.secrets/gpg-home}"
BACKUP_GPG_RECIPIENT="${BACKUP_GPG_RECIPIENT:-}"
if [ -z "${BACKUP_GPG_RECIPIENT}" ] || ! command -v gpg >/dev/null 2>&1; then
    echo "[ERROR] GPG recovery configuration is missing" >&2
    exit 1
fi

# Locate latest backup if target not provided
if [ -z "${TARGET_BACKUP}" ]; then
    TARGET_BACKUP=$(find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "backup_*" | sort -r | head -n 1 || true)
fi

if [ -z "${TARGET_BACKUP}" ] || [ ! -d "${TARGET_BACKUP}" ]; then
    echo "[ERROR] No valid backup directory found at '${TARGET_BACKUP}'" >&2
    exit 1
fi

if [ ! -f "${TARGET_BACKUP}/COMPLETE" ] || [ ! -f "${TARGET_BACKUP}/SHA256SUMS" ]; then
    echo "[ERROR] Backup is missing COMPLETE/SHA256SUMS; refusing restore" >&2
    exit 1
fi

RESTORE_TMP="$(mktemp -d)"
cleanup_restore_tmp() {
    find "${RESTORE_TMP}" -type f -exec shred -u {} + 2>/dev/null || true
    rmdir "${RESTORE_TMP}" 2>/dev/null || true
}
trap cleanup_restore_tmp EXIT

decrypt_artifact() {
    local name="$1"
    local source="${TARGET_BACKUP}/${name}.gpg"
    local output="${RESTORE_TMP}/${name}"
    if [ ! -f "${source}" ]; then
        echo "[ERROR] Encrypted artifact missing: ${source}" >&2
        return 1
    fi
    gpg --homedir "${BACKUP_GPG_HOME}" --batch --quiet --decrypt \
        --output "${output}" "${source}"
    printf '%s\n' "${output}"
}

assert_decrypted_size() {
    local artifact="$1"
    local size
    size="$(stat -c %s "${artifact}")"
    if [ "${size}" -lt "${MIN_ARTIFACT_BYTES}" ]; then
        echo "[ERROR] Decrypted artifact is suspiciously small (${size} bytes): ${artifact}" >&2
        return 1
    fi
}

validate_backup_artifacts() {
    local encrypted base decrypted
    for encrypted in "${TARGET_BACKUP}"/*.gpg; do
        [ -f "${encrypted}" ] || continue
        base="$(basename "${encrypted}" .gpg)"
        decrypted="$(decrypt_artifact "${base}")"
        assert_decrypted_size "${decrypted}"
    done
    local pg_dump webui_archive
    pg_dump="$(decrypt_artifact postgres_langfuse.sql.gz)"
    webui_archive="$(decrypt_artifact open_webui_data.tar.gz)"
    gzip -t "${pg_dump}"
    tar -tzf "${webui_archive}" >/dev/null
    if ! compgen -G "${TARGET_BACKUP}/qdrant_col_*.gpg" >/dev/null; then
        echo "[ERROR] No encrypted per-collection Qdrant snapshot found" >&2
        return 1
    fi
}

echo "======================================================================"
echo "Starting Enterprise AI Stack Disaster Recovery (Restore)"
echo "Source Backup Directory: ${TARGET_BACKUP}"
echo "======================================================================"

# 1. Check Integrity via SHA256SUMS
echo "[1/4] Verifying backup file checksums..."
cd "${TARGET_BACKUP}"
if [ -f "SHA256SUMS" ]; then
    sha256sum -c SHA256SUMS
    echo "  - Backup checksum verification PASSED."
else
    echo "  [WARNING] SHA256SUMS file not found, skipping checksum check."
fi
cd "${AI_STACK_DIR}"
validate_backup_artifacts
echo "  - Decryption, size, gzip and tar validation PASSED."

if [[ "${RESTORE_MODE}" == "clean-room" ]]; then
    END_TIME=$(date +%s)
    RTO=$((END_TIME - START_TIME))
    echo "Clean-room preflight completed without writing any production volume."
    echo "Validation duration: ${RTO} seconds"
    exit 0
fi

resolve_volume() {
    local container="$1"
    local destination="$2"
    docker inspect -f "{{range .Mounts}}{{if eq .Destination \"${destination}\"}}{{.Name}}{{end}}{{end}}" "${container}"
}
WEBUI_VOLUME="$(resolve_volume open-webui /app/backend/data)"
if [ -z "${WEBUI_VOLUME}" ]; then
    echo "[ERROR] Could not resolve Open WebUI data volume; refusing production restore" >&2
    exit 1
fi

# 2. Restore PostgreSQL (Langfuse) Database
echo "[2/4] Restoring Langfuse PostgreSQL Database..."
POSTGRES_USER="${POSTGRES_USER:-langfuse}"
POSTGRES_DB="${POSTGRES_DB:-langfuse}"

PG_DUMP="$(decrypt_artifact postgres_langfuse.sql.gz)"
echo "  - Recreating PostgreSQL database schema and data..."
docker exec -i langfuse-db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" > /dev/null
gunzip -c "${PG_DUMP}" | docker exec -i langfuse-db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > /dev/null
echo "  - PostgreSQL restoration completed."

# 3. Restore Open WebUI Data Volume
echo "[3/4] Restoring Open WebUI Data Volume..."
WEBUI_ARCHIVE="$(decrypt_artifact open_webui_data.tar.gz)"
echo "  - Extracting encrypted Open WebUI archive into open-webui-data docker volume..."
docker run --rm -v "${WEBUI_VOLUME}:/data" -v "${RESTORE_TMP}:/backup:ro" alpine@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b tar -xzf "/backup/$(basename "${WEBUI_ARCHIVE}")" -C /data
echo "  - Open WebUI data volume restored."

# 4. Restore Qdrant Vector DB Snapshots
echo "[4/4] Restoring Qdrant Vector DB Snapshots..."
: "${QDRANT_API_KEY:?QDRANT_API_KEY must be set for production restore}"
QDRANT_HOST="http://qdrant:6333"

COLLECTION_MAP="$(decrypt_artifact qdrant_collections.map)"
for encrypted_snap in "${TARGET_BACKUP}"/qdrant_col_*.snapshot.gpg; do
    [ -f "${encrypted_snap}" ] || continue
    BASE_NAME=$(basename "${encrypted_snap}" .gpg)
    COL_SNAPSHOT="$(decrypt_artifact "${BASE_NAME}")"
    FILENAME=$(basename "${COL_SNAPSHOT}")
    COL_NAME=$(awk -F '\t' -v artifact="${FILENAME}" '$1 == artifact {print $2; exit}' "${COLLECTION_MAP}")
    if [ -z "${COL_NAME}" ]; then
        echo "[ERROR] No collection mapping for ${FILENAME}; refusing restore" >&2
        exit 1
    fi
    echo "  - Recovering Qdrant collection snapshot for '${COL_NAME}' from ${FILENAME}..."
    CONTAINER_SNAPSHOT="/tmp/${FILENAME}"
    docker cp "${COL_SNAPSHOT}" "open-webui:${CONTAINER_SNAPSHOT}"
    docker exec open-webui curl -s -f -X POST -H "api-key: ${QDRANT_API_KEY}" \
        -F "snapshot=@${CONTAINER_SNAPSHOT}" \
        "${QDRANT_HOST}/collections/${COL_NAME}/snapshots/upload" > /dev/null
    docker exec open-webui rm -f "${CONTAINER_SNAPSHOT}"
    echo "    Collection snapshot uploaded successfully."
done

# Calculate RTO (Recovery Time Objective)
END_TIME=$(date +%s)
RTO=$((END_TIME - START_TIME))

echo "======================================================================"
echo "Disaster Recovery Test Completed Successfully!"
echo "Recovery Time Objective (RTO): ${RTO} seconds"
echo "Recovery Point Objective (RPO): Determined by backup timestamp (${TARGET_BACKUP})"
echo "======================================================================"
