#!/bin/bash

# === Configuration - PLEASE EDIT THESE VALUES ===
# Full path to your SQLite database file
DB_FILE="/mnt/samsung/semestral-project/data/news.db"

# Directory where backups should be stored
BACKUP_DIR="/mnt/samsung/semestral-project/data/db_backup"

# --- Deletion Logic Configuration ---
# Number of days of data to keep based on articles.published date.
# Records in articles older than this, AND their related analysis/predictions, will be deleted.
RETENTION_DAYS=14
# === End of Configuration ===

# --- Script Logic ---
# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR" || { echo "ERROR: Cannot create backup directory $BACKUP_DIR. Exiting."; exit 1; }

# Timestamp for backup filename and log file (e.g., YYYYMMDD_HHMMSS)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/news_backup_${TIMESTAMP}.db"
LOG_FILE="${BACKUP_DIR}/maintenance_log_${TIMESTAMP}.log"

# Redirect all output (stdout and stderr) to a log file AND the console/cron output
exec > >(tee -a "$LOG_FILE") 2>&1

echo "====================================================="
echo "Starting SQLite Maintenance at $(date)"
echo "Database: $DB_FILE"
echo "Backup Dir: $BACKUP_DIR"
echo "Retention Days (Articles): $RETENTION_DAYS"
echo "-----------------------------------------------------"

# Step 1: Create Online Backup
echo "Step 1: Creating online backup..."
sqlite3 "$DB_FILE" "VACUUM INTO '$BACKUP_FILE';"
BACKUP_EXIT_CODE=$?

if [ $BACKUP_EXIT_CODE -ne 0 ]; then
  echo "ERROR: Backup command failed with exit code $BACKUP_EXIT_CODE. Exiting."
  exit 1
fi

# Basic check: Ensure backup file exists and has size > 0
if [ ! -s "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file '$BACKUP_FILE' is empty or does not exist after VACUUM INTO. Exiting."
    exit 1
fi
echo "Backup successful: $BACKUP_FILE"
echo "-----------------------------------------------------"


# Step 2: Delete Old Data (Articles and related Analysis/Predictions)
echo "Step 2: Deleting data older than $RETENTION_DAYS days (based on articles.published)..."

# Define the multi-step DELETE logic respecting Foreign Keys
# Order: predictions -> analysis -> articles
# Uses subqueries to find relevant IDs based on articles.published date.
# Assumes 'articles.published' column stores dates SQLite understands (e.g., YYYY-MM-DD HH:MM:SS)
DELETE_LOGIC=$(cat <<SQL
-- Step A: Delete predictions linked to analysis linked to old articles
DELETE FROM predictions
WHERE analysis_id IN (
    SELECT id FROM analysis
    WHERE article_id IN (
        SELECT id FROM articles WHERE date(published) <= date('now', '-${RETENTION_DAYS} days')
    )
);

-- Step B: Delete analysis linked to old articles
DELETE FROM analysis
WHERE article_id IN (
    SELECT id FROM articles WHERE date(published) <= date('now', '-${RETENTION_DAYS} days')
);

-- Step C: Delete old articles themselves
DELETE FROM articles
WHERE date(published) <= date('now', '-${RETENTION_DAYS} days');
SQL
)

echo "Executing SQL:"
echo "${DELETE_LOGIC}"

# Execute all deletes within a single transaction
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
  # Decide if you want to exit on delete failure. Usually yes.
  exit 1
fi
echo "Deletion successful."
echo "-----------------------------------------------------"


echo "SQLite Maintenance completed successfully at $(date)."
echo "====================================================="
exit 0