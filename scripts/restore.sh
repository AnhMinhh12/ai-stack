#!/usr/bin/env bash
# ==============================================================================
# Enterprise Local AI Stack - Disaster Recovery & Restore Script
# Components: Qdrant Vector DB, PostgreSQL (Langfuse), Open WebUI Data
# ==============================================================================

set -euo pipefail

AI_STACK_DIR="/home/admin/ai-stack"
BACKUP_ROOT="${AI_STACK_DIR}/backups"
TARGET_BACKUP="${1:-}"

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

# Locate latest backup if target not provided
if [ -z "${TARGET_BACKUP}" ]; then
    TARGET_BACKUP=$(find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "backup_*" | sort -r | head -n 1 || true)
fi

if [ -z "${TARGET_BACKUP}" ] || [ ! -d "${TARGET_BACKUP}" ]; then
    echo "[ERROR] No valid backup directory found at '${TARGET_BACKUP}'" >&2
    exit 1
fi

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

# 2. Restore PostgreSQL (Langfuse) Database
echo "[2/4] Restoring Langfuse PostgreSQL Database..."
POSTGRES_USER="${POSTGRES_USER:-langfuse}"
POSTGRES_DB="${POSTGRES_DB:-langfuse}"

if [ -f "${TARGET_BACKUP}/postgres_langfuse.sql.gz" ]; then
    echo "  - Recreating PostgreSQL database schema and data..."
    docker exec -i langfuse-db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" > /dev/null
    gunzip -c "${TARGET_BACKUP}/postgres_langfuse.sql.gz" | docker exec -i langfuse-db psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" > /dev/null
    echo "  - PostgreSQL restoration completed."
else
    echo "  [WARNING] postgres_langfuse.sql.gz not found in backup."
fi

# 3. Restore Open WebUI Data Volume
echo "[3/4] Restoring Open WebUI Data Volume..."
if [ -f "${TARGET_BACKUP}/open_webui_data.tar.gz" ]; then
    echo "  - Extracting open_webui_data.tar.gz into open-webui-data docker volume..."
    docker run --rm -v open-webui-data:/data -v "${TARGET_BACKUP}:/backup" alpine tar -xzf /backup/open_webui_data.tar.gz -C /data
    echo "  - Open WebUI data volume restored."
else
    echo "  [WARNING] open_webui_data.tar.gz not found in backup."
fi

# 4. Restore Qdrant Vector DB Snapshots
echo "[4/4] Restoring Qdrant Vector DB Snapshots..."
QDRANT_API_KEY="${QDRANT_API_KEY:-}"
QDRANT_HOST="127.0.0.1:6333"

for col_snap in $(ls "${TARGET_BACKUP}"/qdrant_col_*.snapshot 2>/dev/null || true); do
    FILENAME=$(basename "${col_snap}")
    # Extract collection name: qdrant_col_{COL_NAME}_{SNAP_NAME}.snapshot
    COL_NAME=$(echo "${FILENAME}" | sed -E 's/^qdrant_col_([^_]+)_.*$/\1/')
    echo "  - Recovering Qdrant collection snapshot for '${COL_NAME}' from ${FILENAME}..."
    
    # Upload snapshot and recover
    UPLOAD_RESP=$(curl -s -f -X POST -H "api-key: ${QDRANT_API_KEY}" \
        -F "snapshot=@${col_snap}" \
        "http://${QDRANT_HOST}/collections/${COL_NAME}/snapshots/upload")
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
