#!/bin/bash

DB_FILE="/mnt/samsung/semestral-project/data/news.db"

BACKUP_DIR="/mnt/samsung/semestral-project/data/db_backup"

RETENTION_DAYS=14

mkdir -p "$BACKUP_DIR" || { echo "ERROR: Cannot create backup directory $BACKUP_DIR. Exiting."; exit 1; }

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/news_backup_${TIMESTAMP}.db"
LOG_FILE="${BACKUP_DIR}/maintenance_log_${TIMESTAMP}.log"

echo "====================================================="
echo "Starting SQLite Maintenance at $(date)"
echo "Database: $DB_FILE"
echo "Backup Dir: $BACKUP_DIR"
echo "Retention Days (Articles): $RETENTION_DAYS"
echo "-----------------------------------------------------"

echo "Step 1: Creating online backup..."
sqlite3 "$DB_FILE" "VACUUM INTO '$BACKUP_FILE';"
BACKUP_EXIT_CODE=$?

if [ $BACKUP_EXIT_CODE -ne 0 ]; then
  echo "ERROR: Backup command failed with exit code $BACKUP_EXIT_CODE. Exiting."
  exit 1
fi

if [ ! -s "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file '$BACKUP_FILE' is empty or does not exist after VACUUM INTO. Exiting."
    exit 1
fi
echo "Backup successful: $BACKUP_FILE"
echo "-----------------------------------------------------"


echo "Step 2: Deleting data older than $RETENTION_DAYS days (based on articles.published)..."

DELETE_LOGIC=$(cat <<SQL
DELETE FROM predictions
WHERE analysis_id IN (
    SELECT id FROM analysis
    WHERE article_id IN (
        SELECT id FROM articles WHERE date(published) <= date('now', '-${RETENTION_DAYS} days')
    )
);

DELETE FROM analysis
WHERE article_id IN (
    SELECT id FROM articles WHERE date(published) <= date('now', '-${RETENTION_DAYS} days')
);

DELETE FROM articles
WHERE date(published) <= date('now', '-${RETENTION_DAYS} days');

DELETE FROM lstm_predictions
WHERE date(prediction_made_date) <= date('now', '-2 days');
SQL
)

echo "Executing SQL:"
echo "${DELETE_LOGIC}"

sqlite3 "$DB_FILE" <<EOF
BEGIN IMMEDIATE;
${DELETE_LOGIC}
COMMIT;
EOF
DELETE_EXIT_CODE=$?

if [ $DELETE_EXIT_CODE -ne 0 ]; then
  echo "ERROR: Delete command failed with exit code $DELETE_EXIT_CODE."
  if [ $DELETE_EXIT_CODE -eq 5 ]; then
      echo "Details: Database was locked. Python processes might have held locks for too long, or high contention."
      echo "Consider scheduling for a less busy time."
  fi
  exit 1
fi
echo "Deletion successful."
exit 0