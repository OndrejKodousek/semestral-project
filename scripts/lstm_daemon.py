import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime, date

VENV_PYTHON_PATH = "/mnt/samsung/semestral-project/venv/bin/python"

DB_PATH = "data/news.db"


def get_project_root():
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    return Path(__file__).resolve().parent.parent


def get_unique_tickers(db_file):
    tickers = set()
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ticker FROM analysis")
    results = cursor.fetchall()
    for row in results:
        tickers.add(row[0])
    conn.close()
    return list(tickers)


def check_if_processed_today(db_file, ticker):
    """Checks if a prediction record exists for the ticker today."""
    processed_today = False
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    today_str = date.today().strftime("%Y-%m-%d")
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
    conn.close()
    return processed_today


def run_script(script_path, ticker):
    try:
        python_executable = VENV_PYTHON_PATH
        project_root = get_project_root()
        python_executable_path = Path(python_executable)

        if not python_executable_path.is_file():
            print(
                f"ERROR: Configured Python executable not found or is not a file at {python_executable_path}"
            )
            print("Please check the VENV_PYTHON_PATH variable in master_workflow.py")
            return False

        result = subprocess.run(
            [
                str(python_executable_path),
                str(script_path),
                ticker,
            ],
            capture_output=False,
            text=True,
            check=True,
        )
        return True
    except:
        return False


if __name__ == "__main__":
    overall_start_time = time.perf_counter()

    project_root = get_project_root()
    db_file = project_root / DB_PATH
    train_script = project_root / "lstm" / "train.py"
    predict_script = project_root / "lstm" / "predict.py"

    tickers_to_process = get_unique_tickers(db_file)

    if not tickers_to_process:
        print("No tickers found in database. Exiting.")
        sys.exit(0)

    print(f"Found {len(tickers_to_process)} tickers to process.")

    total_tickers_processed = 0
    total_skipped = 0
    total_train_success = 0
    total_predict_success = 0

    for i, ticker in enumerate(tickers_to_process):
        print(f"\nProcessing ticker {i+1}/{len(tickers_to_process)}: {ticker}")

        if check_if_processed_today(db_file, ticker):
            print(f"  Skipping {ticker}, already processed today.")
            total_skipped += 1
            continue

        ticker_start_time = time.perf_counter()
        train_success = False
        predict_success = False

        print(f"  Running Training for {ticker}")
        train_success = run_script(train_script, ticker)
        if train_success is True:
            total_train_success += 1
        else:
            continue

        print(f"  Running Prediction for {ticker}")
        predict_success = run_script(predict_script, ticker)
        if predict_success is True:
            total_predict_success += 1
        else:
            continue
        ticker_end_time = time.perf_counter()
        ticker_duration = ticker_end_time - ticker_start_time

        try:
            with open(project_root / "data" / "time_tracking.txt", "a+") as f:
                f.write(f"{ticker_duration:.2f}" + "\n")
        except Exception as e:
            pass

        total_tickers_processed += 1

    overall_end_time = time.perf_counter()
    overall_duration = overall_end_time - overall_start_time

    print(f"\nMaster workflow finished at: {datetime.now()}")
    print(f"--- Summary ---")
    print(f"Total tickers found:   {len(tickers_to_process)}")
    print(f"Tickers skipped:     {total_skipped}")
    print(f"Tickers processed:   {total_tickers_processed}")
    print(f"Successful trains:   {total_train_success}")
    print(f"Successful predicts: {total_predict_success}")
    print(
        f"Total processing time: {overall_duration:.2f} seconds ({overall_duration/60:.2f} minutes)"
    )
    if total_tickers_processed > 0:
        avg_time = overall_duration / total_tickers_processed
        print(f"Average time per processed ticker: {avg_time:.2f} seconds")
