#!/usr/bin/env bash
# ==============================================================================
# Enterprise Local AI Stack - Automated Backup Script
# Components: Qdrant Vector DB, PostgreSQL (Langfuse), Open WebUI Data, Configs
# ==============================================================================

set -euo pipefail

# Configurations
AI_STACK_DIR="/home/admin/ai-stack"
BACKUP_ROOT="${AI_STACK_DIR}/backups"
TIMESTAMP="$(date +'%Y%m%d_%H%M%S')"
BACKUP_DIR="${BACKUP_ROOT}/backup_${TIMESTAMP}"
RETENTION_DAYS=7

# Load environment variables
if [ -f "${AI_STACK_DIR}/.env" ]; then
    set -a
    source "${AI_STACK_DIR}/.env"
    set +a
else
    echo "[ERROR] .env file not found at ${AI_STACK_DIR}/.env" >&2
    exit 1
fi

echo "======================================================================"
echo "Starting Enterprise AI Stack Backup: ${TIMESTAMP}"
echo "Backup Destination: ${BACKUP_DIR}"
echo "======================================================================"

mkdir -p "${BACKUP_DIR}"

# 1. Qdrant Vector DB Backup (Full Storage & Collection Snapshots)
echo "[1/4] Backing up Qdrant Vector DB..."
QDRANT_API_KEY="${QDRANT_API_KEY:-}"
QDRANT_HOST="127.0.0.1:6333"

# Create Storage Snapshot via Qdrant API
SNAPSHOT_RESP=$(curl -s -f -X POST -H "api-key: ${QDRANT_API_KEY}" "http://${QDRANT_HOST}/snapshots")
SNAPSHOT_NAME=$(echo "${SNAPSHOT_RESP}" | grep -oP '"name":"\K[^"]+' || true)

if [ -n "${SNAPSHOT_NAME}" ]; then
    echo "  - Storage snapshot created on server: ${SNAPSHOT_NAME}"
    curl -s -f -H "api-key: ${QDRANT_API_KEY}" \
        "http://${QDRANT_HOST}/snapshots/${SNAPSHOT_NAME}" \
        -o "${BACKUP_DIR}/qdrant_full_${SNAPSHOT_NAME}"
    echo "  - Downloaded full Qdrant snapshot: qdrant_full_${SNAPSHOT_NAME}"
else
    echo "  [WARNING] Storage snapshot endpoint returned empty, backing up collections individually..."
fi

# Backup collection snapshots
COLLECTIONS_JSON=$(curl -s -f -H "api-key: ${QDRANT_API_KEY}" "http://${QDRANT_HOST}/collections")
COLLECTIONS=$(echo "${COLLECTIONS_JSON}" | grep -oP '"name":"\K[^"]+' || true)

for col in ${COLLECTIONS}; do
    echo "  - Snapshotting Qdrant collection: ${col}"
    COL_SNAP_RESP=$(curl -s -f -X POST -H "api-key: ${QDRANT_API_KEY}" "http://${QDRANT_HOST}/collections/${col}/snapshots")
    COL_SNAP_NAME=$(echo "${COL_SNAP_RESP}" | grep -oP '"name":"\K[^"]+' || true)
    if [ -n "${COL_SNAP_NAME}" ]; then
        curl -s -f -H "api-key: ${QDRANT_API_KEY}" \
            "http://${QDRANT_HOST}/collections/${col}/snapshots/${COL_SNAP_NAME}" \
            -o "${BACKUP_DIR}/qdrant_col_${col}_${COL_SNAP_NAME}"
        echo "    Saved collection snapshot: qdrant_col_${col}_${COL_SNAP_NAME}"
    fi
done

# 2. PostgreSQL (Langfuse) Database Dump
echo "[2/4] Backing up Langfuse PostgreSQL Database..."
POSTGRES_USER="${POSTGRES_USER:-langfuse}"
POSTGRES_DB="${POSTGRES_DB:-langfuse}"

docker exec langfuse-db pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${BACKUP_DIR}/postgres_langfuse.sql.gz"
echo "  - PostgreSQL dump saved to postgres_langfuse.sql.gz ($(du -sh "${BACKUP_DIR}/postgres_langfuse.sql.gz" | cut -f1))"

# 3. Open WebUI Data Backup (Database, Uploads, User configs - excluding heavy cache)
echo "[3/4] Backing up Open WebUI Data Volume..."
docker run --rm -v open-webui-data:/data alpine tar --exclude=cache -czf - -C /data . > "${BACKUP_DIR}/open_webui_data.tar.gz"
echo "  - Open WebUI data exported to open_webui_data.tar.gz ($(du -sh "${BACKUP_DIR}/open_webui_data.tar.gz" | cut -f1))"

# 4. Configuration Metadata Backup
echo "[4/4] Archiving Infrastructure Configuration..."
cp "${AI_STACK_DIR}/docker-compose.yml" "${BACKUP_DIR}/docker-compose.yml.bak"
cp "${AI_STACK_DIR}/nginx/nginx.conf" "${BACKUP_DIR}/nginx.conf.bak"
# Copy .env with restricted permissions
cp "${AI_STACK_DIR}/.env" "${BACKUP_DIR}/env.bak"
chmod 600 "${BACKUP_DIR}/env.bak"

# Generate Checksums
echo "Generating SHA256 Checksums..."
cd "${BACKUP_DIR}"
sha256sum * > SHA256SUMS
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
