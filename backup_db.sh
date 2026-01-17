#!/bin/bash
# Backup Database Script
# Saves a snapshot of the current database state to the ./backups directory.

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"

# Ensure backup directory exists
mkdir -p $BACKUP_DIR

echo "📦 Creating database backup..."
echo "Target: $BACKUP_DIR/wfm_db_$DATE.sql"

# Execute pg_dump inside the 'db' container
# Using PGPASSWORD env variable to avoid password prompt
# Usage: ./backup_db.sh
sudo docker-compose exec -T -e PGPASSWORD=1q2w3e4r db pg_dump -U postgres wfm_db > $BACKUP_DIR/wfm_db_$DATE.sql

if [ $? -eq 0 ]; then
  echo "✅ Backup Successful!"
  echo "File: $BACKUP_DIR/wfm_db_$DATE.sql"
else
  echo "❌ Backup Failed!"
fi
