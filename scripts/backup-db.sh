#!/bin/bash
# Database Backup Automator script for ViralOps
BACKUP_DIR="/backups/viralops"
mkdir -p "$BACKUP_DIR"
DATE=$(date +%Y%m%d_%H%M%S)

# Use env defaults or fallback values
DB_USER=${DB_USER:-root}
DB_PASSWORD=${DB_PASSWORD:-rootpassword}
DB_NAME=${DB_NAME:-viralops}

echo "[$DATE] Initiating MySQL database dump..."

# MySQL dump executed inside the running container
docker exec viralops-db mysqldump \
  -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
  > "$BACKUP_DIR/db_$DATE.sql"

if [ $? -eq 0 ]; then
  echo "[$DATE] Database dump completed: db_$DATE.sql"
  
  # Upload to S3 if bucket is configured
  if [ -n "$AWS_STORAGE_BUCKET_NAME" ]; then
    echo "[$DATE] Uploading backup to S3 bucket: $AWS_STORAGE_BUCKET_NAME..."
    aws s3 cp "$BACKUP_DIR/db_$DATE.sql" \
      "s3://$AWS_STORAGE_BUCKET_NAME/backups/db_$DATE.sql"
    
    if [ $? -eq 0 ]; then
      echo "[$DATE] S3 upload successful."
    else
      echo "[$DATE] S3 upload failed."
    fi
  else
    echo "[$DATE] AWS_STORAGE_BUCKET_NAME not set. Skipping S3 upload."
  fi
else
  echo "[$DATE] Database dump execution failed."
  exit 1
fi

# Keep only last 7 days of local backups
find "$BACKUP_DIR" -name "db_*.sql" -mtime +7 -delete

# Log backup execution status
echo "[$DATE] Backup completed: db_$DATE.sql" >> /var/log/backup.log
