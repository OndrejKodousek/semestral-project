"""
@file lstm_daemon.py
@brief Daemon for continuous LSTM model training and prediction.

This script manages periodic training and prediction for top stock tickers,
with scheduling logic to avoid running during market closure hours.
"""

import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, date, time as dt_time

VENV_PYTHON_PATH = "/mnt/samsung/semestral-project/venv/bin/python"
DB_PATH = "data/news.db"
TOP_N_TICKERS = 10


def get_project_root() -> Path:
    """
    @brief Locates the project root directory.

    @return Path object pointing to project root directory
    """
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    print(
        "Warning: '.git' marker not found. Assuming script parent's parent is project root."
    )
    return Path(__file__).resolve().parent.parent


def get_top_tickers_by_frequency(db_file: Path) -> list[str]:
    """
    @brief Gets top tickers by analysis frequency.

    @param db_file Path to database file
    @return List of ticker strings ordered by frequency
    """
    tickers = []
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ticker
            FROM analysis
            GROUP BY ticker
            ORDER BY COUNT(*) DESC
            """
        )
        results = cursor.fetchall()
        tickers = [row[0] for row in results]
    except sqlite3.Error as e:
        print(f"Database error while fetching all tickers by frequency: {e}")
    finally:
        if conn:
            conn.close()
    return tickers


def check_if_processed_today(db_file: Path, ticker: str) -> bool:
    """
    @brief Checks if ticker was already processed today.

    @param db_file Path to database file
    @param ticker Stock ticker symbol
    @return True if already processed today, False otherwise
    """
    processed_today = False
    conn = None
    try:
        today_str = date.today().strftime("%Y-%m-%d")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM lstm_predictions
            WHERE ticker = ?
            AND prediction_made_date = ?
            LIMIT 1
            """,
            (ticker, today_str),
        )
        result = cursor.fetchone()
        if result:
            processed_today = True
    except sqlite3.Error as e:
        print(f"Database error checking if processed today for {ticker}: {e}")
    finally:
        if conn:
            conn.close()
    return processed_today


def run_script(script_path: Path, ticker: str, python_executable: str) -> bool:
    """
    @brief Executes a Python script for a given ticker.

    @param script_path Path to script to run
    @param ticker Stock ticker symbol to process
    @param python_executable Path to Python interpreter
    @return True if successful, False otherwise
    """
    try:
        python_executable_path = Path(python_executable)
        if not python_executable_path.is_file():
            print(
                f"ERROR: Configured Python executable not found at {python_executable_path}"
            )
            return False

        if not script_path.is_file():
            print(f"ERROR: Script not found at {script_path}")
            return False

        process = subprocess.run(
            [
                str(python_executable_path),
                str(script_path),
                ticker,
            ],
            capture_output=False,
            text=True,
            check=False,
            cwd=get_project_root(),
        )

        if process.returncode != 0:
            print(f"ERROR: Script {script_path.name} failed for ticker {ticker}")
            return False
        return True

    except Exception as e:
        print(f"ERROR: Script {script_path.name} processing {ticker}: {e}")
        return False


if __name__ == "__main__":
    project_root = get_project_root()
    db_file = project_root / DB_PATH
    train_script = project_root / "lstm" / "train.py"
    predict_script = project_root / "lstm" / "predict.py"

    PAUSE_START_HOUR = 23  # 11 PM
    PAUSE_END_HOUR = 0  # 12 AM
    PAUSE_END_MINUTE = 5  # 12:05 AM
    SLEEP_DURATION_SECONDS = 1800  # 30 minutes
    SHORT_SLEEP_SECONDS = 60  # 1 minute

    print("Starting continuous processing script...")

    while True:
        now = datetime.now()
        current_time = now.time()
        current_hour = current_time.hour
        current_minute = current_time.minute

        # Check if within pause window
        is_pause_time = (current_hour >= PAUSE_START_HOUR) or (
            current_hour == PAUSE_END_HOUR and current_minute <= PAUSE_END_MINUTE
        )

        if is_pause_time:
            print(f"Break time. Pausing for {SLEEP_DURATION_SECONDS // 60} minutes...")
            time.sleep(SLEEP_DURATION_SECONDS)
            continue

        print(f"Starting processing cycle at {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Get candidate tickers and filter unprocessed ones
        candidate_tickers = get_top_tickers_by_frequency(db_file)
        if not candidate_tickers:
            print(
                f"No tickers found. Waiting {SLEEP_DURATION_SECONDS // 60} minutes..."
            )
            time.sleep(SLEEP_DURATION_SECONDS)
            continue

        tickers_to_process = []
        current_processing_date = date.today().strftime("%Y-%m-%d")
        for ticker in candidate_tickers:
            if not check_if_processed_today(db_file, ticker):
                tickers_to_process.append(ticker)
                if len(tickers_to_process) == TOP_N_TICKERS:
                    break

        if not tickers_to_process:
            print(
                f"No tickers require processing. Waiting {SHORT_SLEEP_SECONDS} seconds..."
            )
            time.sleep(SHORT_SLEEP_SECONDS)
            continue

        print(f"Selected {len(tickers_to_process)} tickers to process")
        for i, ticker in enumerate(tickers_to_process):
            print(f"\nProcessing ticker {i+1}/{len(tickers_to_process)}: {ticker}")

            # Train and predict
            print(f"Running Training for {ticker}...")
            train_success = run_script(train_script, ticker, VENV_PYTHON_PATH)
            if train_success:
                print(f"Running Prediction for {ticker}...")
                predict_success = run_script(predict_script, ticker, VENV_PYTHON_PATH)
                if not predict_success:
                    print(f"Prediction failed for {ticker}.")
            else:
                print(f"Training failed for {ticker}. Skipping prediction.")
                continue

        print(
            f"\nProcessing cycle finished at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}."
        )
        print(f"Waiting {SHORT_SLEEP_SECONDS} seconds before next cycle")
        time.sleep(SHORT_SLEEP_SECONDS)
