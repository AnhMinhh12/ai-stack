#!/usr/bin/env bash
# ==============================================================================
# Enterprise Local AI Stack - Automated Backup Script
# Components: Qdrant Vector DB, PostgreSQL (Langfuse), Open WebUI Data, Configs
# ==============================================================================

set -euo pipefail
umask 077

# Configurations
AI_STACK_DIR="/home/admin/ai-stack"
BACKUP_ROOT="${AI_STACK_DIR}/backups"
TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
BACKUP_DIR="${BACKUP_ROOT}/backup_${TIMESTAMP}"
RETENTION_DAYS=7
MIN_ARTIFACT_BYTES=256

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
    echo "[ERROR] Encrypted backup unavailable: set BACKUP_GPG_RECIPIENT and install gpg" >&2
    exit 1
fi
if ! gpg --homedir "${BACKUP_GPG_HOME}" --batch --list-keys "${BACKUP_GPG_RECIPIENT}" >/dev/null 2>&1; then
    echo "[ERROR] Configured backup recipient is not present in BACKUP_GPG_HOME" >&2
    exit 1
fi

echo "======================================================================"
echo "Starting Enterprise AI Stack Backup: ${TIMESTAMP}"
echo "Backup Destination: ${BACKUP_DIR}"
echo "======================================================================"

mkdir -p "${BACKUP_DIR}"

# Resolve Compose-managed volume names from the running containers; do not assume
# the project name or hard-code a volume that may point at another deployment.
resolve_volume() {
    local container="$1"
    local destination="$2"
    docker inspect -f "{{range .Mounts}}{{if eq .Destination \"${destination}\"}}{{.Name}}{{end}}{{end}}" "${container}"
}
WEBUI_VOLUME="$(resolve_volume open-webui /app/backend/data)"
if [ -z "${WEBUI_VOLUME}" ]; then
    echo "[ERROR] Could not resolve Open WebUI data volume from container" >&2
    exit 1
fi
: "${QDRANT_API_KEY:?QDRANT_API_KEY must be set for backup}"
QDRANT_HOST="http://qdrant:6333"
QDRANT_COLLECTION_MAP="${BACKUP_DIR}/qdrant_collections.map"
QDRANT_ARTIFACT_COUNT=0

assert_artifact_size() {
    local artifact="$1"
    local size
    size="$(stat -c %s "${artifact}")"
    if [ "${size}" -lt "${MIN_ARTIFACT_BYTES}" ]; then
        echo "[ERROR] Artifact is suspiciously small (${size} bytes): ${artifact}" >&2
        exit 1
    fi
}

# 1. Qdrant Vector DB Backup (Full Storage & Collection Snapshots)
echo "[1/4] Backing up Qdrant Vector DB..."

# Create Storage Snapshot via Qdrant API
SNAPSHOT_RESP=$(docker exec open-webui curl -s -f -X POST -H "api-key: ${QDRANT_API_KEY}" "${QDRANT_HOST}/snapshots")
SNAPSHOT_NAME=$(echo "${SNAPSHOT_RESP}" | grep -oP '"name":"\K[^"]+' || true)

if [ -n "${SNAPSHOT_NAME}" ]; then
    echo "  - Storage snapshot created on server: ${SNAPSHOT_NAME}"
    docker exec open-webui curl -s -f -H "api-key: ${QDRANT_API_KEY}" \
        "${QDRANT_HOST}/snapshots/${SNAPSHOT_NAME}" \
        > "${BACKUP_DIR}/qdrant_full_${SNAPSHOT_NAME}"
    assert_artifact_size "${BACKUP_DIR}/qdrant_full_${SNAPSHOT_NAME}"
    QDRANT_ARTIFACT_COUNT=$((QDRANT_ARTIFACT_COUNT + 1))
    echo "  - Downloaded full Qdrant snapshot: qdrant_full_${SNAPSHOT_NAME}"
else
    echo "  [WARNING] Storage snapshot endpoint returned empty, backing up collections individually..."
fi

# Backup collection snapshots
COLLECTIONS_JSON=$(docker exec open-webui curl -s -f -H "api-key: ${QDRANT_API_KEY}" "${QDRANT_HOST}/collections")
COLLECTIONS=$(echo "${COLLECTIONS_JSON}" | grep -oP '"name":"\K[^"]+' || true)

for col in ${COLLECTIONS}; do
    echo "  - Snapshotting Qdrant collection: ${col}"
    COL_SNAP_RESP=$(docker exec open-webui curl -s -f -X POST -H "api-key: ${QDRANT_API_KEY}" "${QDRANT_HOST}/collections/${col}/snapshots")
    COL_SNAP_NAME=$(echo "${COL_SNAP_RESP}" | grep -oP '"name":"\K[^"]+' || true)
    if [ -n "${COL_SNAP_NAME}" ]; then
        artifact="${BACKUP_DIR}/qdrant_col_${col}_${COL_SNAP_NAME}.snapshot"
        docker exec open-webui curl -s -f -H "api-key: ${QDRANT_API_KEY}" \
            "${QDRANT_HOST}/collections/${col}/snapshots/${COL_SNAP_NAME}" \
            > "${artifact}"
        assert_artifact_size "${artifact}"
        printf '%s\t%s\n' "$(basename "${artifact}")" "${col}" >> "${QDRANT_COLLECTION_MAP}"
        QDRANT_ARTIFACT_COUNT=$((QDRANT_ARTIFACT_COUNT + 1))
        echo "    Saved collection snapshot: $(basename "${artifact}")"
    fi
done
if [ "${QDRANT_ARTIFACT_COUNT}" -eq 0 ] || [ ! -s "${QDRANT_COLLECTION_MAP}" ]; then
    echo "[ERROR] No complete per-collection Qdrant snapshot mapping was produced" >&2
    exit 1
fi

# 2. PostgreSQL (Langfuse) Database Dump
echo "[2/4] Backing up Langfuse PostgreSQL Database..."
POSTGRES_USER="${POSTGRES_USER:-langfuse}"
POSTGRES_DB="${POSTGRES_DB:-langfuse}"

docker exec langfuse-db pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${BACKUP_DIR}/postgres_langfuse.sql.gz"
assert_artifact_size "${BACKUP_DIR}/postgres_langfuse.sql.gz"
echo "  - PostgreSQL dump saved to postgres_langfuse.sql.gz ($(du -sh "${BACKUP_DIR}/postgres_langfuse.sql.gz" | cut -f1))"

# 3. Open WebUI Data Backup (Database, Uploads, User configs - excluding heavy cache)
echo "[3/4] Backing up Open WebUI Data Volume..."
docker run --rm -v "${WEBUI_VOLUME}:/data:ro" alpine@sha256:28bd5fe8b56d1bd048e5babf5b10710ebe0bae67db86916198a6eec434943f8b tar --exclude=cache -czf - -C /data . > "${BACKUP_DIR}/open_webui_data.tar.gz"
assert_artifact_size "${BACKUP_DIR}/open_webui_data.tar.gz"
echo "  - Open WebUI data exported to open_webui_data.tar.gz ($(du -sh "${BACKUP_DIR}/open_webui_data.tar.gz" | cut -f1))"

# 4. Configuration Metadata Backup
echo "[4/4] Archiving Infrastructure Configuration..."
cp "${AI_STACK_DIR}/docker-compose.yml" "${BACKUP_DIR}/docker-compose.yml.bak"
cp "${AI_STACK_DIR}/nginx/nginx.conf" "${BACKUP_DIR}/nginx.conf.bak"
# Record only non-secret environment metadata; never copy .env values.
{
    echo "source=.env (values intentionally excluded)"
    echo "mode=$(stat -c %a "${AI_STACK_DIR}/.env")"
    echo "open_webui_volume=${WEBUI_VOLUME}"
    echo "model_revision=cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8"
    echo "embedding_revision=5617a9f61b028005a4858fdac845db406aefb181"
    sed -E 's/[[:space:]]*#.*$//; /^[[:space:]]*$/d; s/=.*$//' "${AI_STACK_DIR}/.env" | sort
} > "${BACKUP_DIR}/env.keys"
chmod 600 "${BACKUP_DIR}/env.keys"
cat > "${BACKUP_DIR}/manifest.tsv" <<EOF
backup_id\tbackup_${TIMESTAMP}
created_utc\t$(date -u +%Y-%m-%dT%H:%M:%SZ)
qdrant_artifacts\t${QDRANT_ARTIFACT_COUNT}
min_artifact_bytes\t${MIN_ARTIFACT_BYTES}
webui_volume\t${WEBUI_VOLUME}
EOF
chmod 600 "${BACKUP_DIR}/manifest.tsv"

# Encrypt all state-bearing artifacts before checksumming. The plaintext source
# is removed only after GPG has produced the encrypted artifact successfully.
encrypt_artifact() {
    local source="$1"
    local encrypted="${source}.gpg"
    gpg --homedir "${BACKUP_GPG_HOME}" --batch --yes --trust-model always \
        --recipient "${BACKUP_GPG_RECIPIENT}" --output "${encrypted}.tmp" --encrypt "${source}"
    mv "${encrypted}.tmp" "${encrypted}"
    rm -f "${source}"
}
for artifact in "${BACKUP_DIR}"/qdrant_* "${BACKUP_DIR}"/postgres_langfuse.sql.gz "${BACKUP_DIR}"/open_webui_data.tar.gz; do
    if [ -f "${artifact}" ]; then
        encrypt_artifact "${artifact}"
    fi
done


# Generate Checksums
echo "Generating SHA256 Checksums..."
cd "${BACKUP_DIR}"
sha256sum * > SHA256SUMS
printf '%s\n' "${TIMESTAMP}" > COMPLETE
cd "${AI_STACK_DIR}"

# Retention Cleanup
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "backup_*" -mtime +"${RETENTION_DAYS}" -exec rm -rf {} +

echo "======================================================================"
echo "Backup Completed Successfully!"
echo "Backup Location: ${BACKUP_DIR}"
echo "Summary of Backed up Files:"
ls -lh "${BACKUP_DIR}"
echo "======================================================================"
