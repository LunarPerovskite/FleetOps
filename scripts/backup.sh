#!/bin/bash
# FleetOps Automated Backup Script

set -e

# Configuration
BACKUP_DIR=${BACKUP_DIR:-"/backups"}
RETENTION_DAYS=${RETENTION_DAYS:-30}
DB_HOST=${DB_HOST:-"postgres"}
DB_PORT=${DB_PORT:-"5432"}
DB_NAME=${DB_NAME:-"fleetops"}
DB_USER=${DB_USER:-"fleetops"}
DB_PASSWORD=${DB_PASSWORD:-"changeme"}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/fleetops_backup_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Database backup
echo "Starting database backup..."
PGPASSWORD="${DB_PASSWORD}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --verbose \
    --format=plain \
    | gzip > "${BACKUP_FILE}"

echo "Database backup completed: ${BACKUP_FILE}"

# Upload to S3 if configured
if [ -n "${S3_BUCKET}" ]; then
    echo "Uploading to S3..."
    aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/backups/$(basename ${BACKUP_FILE})"
    echo "Upload completed"
fi

# Upload to R2 if configured
if [ -n "${R2_BUCKET}" ] && [ -n "${R2_ENDPOINT}" ]; then
    echo "Uploading to Cloudflare R2..."
    aws s3 cp "${BACKUP_FILE}" "s3://${R2_BUCKET}/backups/$(basename ${BACKUP_FILE})" \
        --endpoint-url="${R2_ENDPOINT}"
    echo "R2 upload completed"
fi

# Cleanup old backups
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "fleetops_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

# Cleanup S3 old backups
if [ -n "${S3_BUCKET}" ]; then
    echo "Cleaning up S3 backups..."
    aws s3 ls "s3://${S3_BUCKET}/backups/" | \
        awk '$1 < "'$(date -d "-${RETENTION_DAYS} days" +%Y-%m-%d)'" {print $4}' | \
        xargs -I {} aws s3 rm "s3://${S3_BUCKET}/backups/{}"
fi

echo "Backup process completed successfully"

# Health check - verify backup file exists and has size > 0
if [ ! -s "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file is empty or does not exist!"
    exit 1
fi

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
echo "Backup size: ${BACKUP_SIZE}"

# Log backup metrics
echo "{
  \"timestamp\": \"$(date -Iseconds)\",
  \"backup_file\": \"${BACKUP_FILE}\",
  \"backup_size\": \"${BACKUP_SIZE}\",
  \"retention_days\": ${RETENTION_DAYS}
}" > "${BACKUP_DIR}/last_backup.json"
