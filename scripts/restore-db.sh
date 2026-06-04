#!/bin/bash
# Database Restore Automator script for ViralOps
BACKUP_DIR="/backups/viralops"
mkdir -p "$BACKUP_DIR"

# Check if file name or date is passed
if [ -n "$1" ]; then
    FILE_NAME="$1"
else
    # Find latest backup in S3 or local backups
    echo "Finding latest database backup from S3 bucket: $AWS_STORAGE_BUCKET_NAME..."
    if [ -n "$AWS_STORAGE_BUCKET_NAME" ]; then
        # List files on S3, sort and get the latest
        LATEST_S3=$(aws s3 ls "s3://$AWS_STORAGE_BUCKET_NAME/backups/" | sort | tail -n 1 | awk '{print $4}')
        if [ -n "$LATEST_S3" ]; then
            echo "Downloading latest backup from S3: $LATEST_S3..."
            aws s3 cp "s3://$AWS_STORAGE_BUCKET_NAME/backups/$LATEST_S3" "$BACKUP_DIR/$LATEST_S3"
            FILE_NAME="$LATEST_S3"
        fi
    fi
fi

# Fallback to local if no file found yet
if [ -z "$FILE_NAME" ]; then
    LATEST_LOCAL=$(ls -t "$BACKUP_DIR"/db_*.sql 2>/dev/null | head -n 1)
    if [ -n "$LATEST_LOCAL" ]; then
        FILE_NAME=$(basename "$LATEST_LOCAL")
        echo "Found latest local backup: $FILE_NAME"
    fi
fi

if [ -z "$FILE_NAME" ]; then
    echo "Error: No backup file found locally or on S3 to restore."
    exit 1
fi

echo "Restoring database from snapshot: $FILE_NAME..."

DB_USER=${DB_USER:-root}
DB_PASSWORD=${DB_PASSWORD:-rootpassword}
DB_NAME=${DB_NAME:-viralops}

# Execute import inside container
docker exec -i viralops-db mysql \
  -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
  < "$BACKUP_DIR/$FILE_NAME"

if [ $? -eq 0 ]; then
    echo "Database restore completed successfully from $FILE_NAME."
    exit 0
else
    echo "Error: Database restore failed."
    exit 1
fi
