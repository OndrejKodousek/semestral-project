import sqlite3
import time
import json

from datetime import datetime, timedelta, date
from collections import defaultdict


def get_db_connection():
    conn = sqlite3.connect("data/news.db", timeout=300)
    conn.row_factory = sqlite3.Row
    return conn


def load_processed_articles(model):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT article_id FROM analysis WHERE model_name = ?
    """,
        (model,),
    )
    processed_articles = cursor.fetchall()
    processed_article_ids = {row["article_id"] for row in processed_articles}

    conn.close()
    return processed_article_ids


# Save processed articles to the database
def save_processed_articles(article_id, model, data):
    max_retries = 5
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Extract the date part (YYYY-MM-DD) from the published field
            published_date = data["published"].split("T")[0]

            # Insert into analysis table
            cursor.execute(
                """
                INSERT INTO analysis (
                    article_id, model_name, published, ticker, stock, summary
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    article_id,
                    model,
                    published_date,  # Use the extracted date
                    data.get("ticker"),
                    data.get("stock"),
                    data.get("summary"),
                ),
            )
            analysis_id = cursor.lastrowid

            # Insert into predictions table
            for day in range(1, 13):  # Assuming predictions for 12 days
                prediction_key = f"prediction_{day}_day"
                confidence_key = f"confidence_{day}_day"
                prediction_date = (
                    datetime.strptime(published_date, "%Y-%m-%d") + timedelta(days=day)
                ).strftime("%Y-%m-%d")

                cursor.execute(
                    """
                    INSERT INTO predictions (
                        analysis_id, date, prediction, confidence
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        analysis_id,
                        prediction_date,
                        data.get(prediction_key),
                        data.get(confidence_key),
                    ),
                )

            conn.commit()
            cursor.close()
            conn.close()
            break

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print(
                    f"Database locked, retrying in {retry_delay} seconds (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise e
    else:
        raise Exception("Failed to save processed articles after multiple retries")


def save_processed_summarized_articles(data, model_name, ticker):
    """
    Saves summarized analysis and its associated predictions to the database,
    storing predictions in a separate linked table.
    """
    max_retries = 5
    retry_delay = 1
    summarized_analysis_id = None  # Initialize id variable

    # Extract summary text - prediction data is handled separately now
    summary_text = data.get("summary", "")
    # Get today's date to calculate prediction dates
    today_date = date.today()

    for attempt in range(max_retries):
        conn = None  # Ensure conn is defined for finally block
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            conn.execute("BEGIN TRANSACTION")  # Start transaction

            # --- Step 1: Insert or Replace the main summary ---
            last_updated_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                INSERT OR REPLACE INTO summarized_analysis (
                    model_name, ticker, last_updated, summary_text
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    model_name,
                    ticker,
                    last_updated_time,
                    summary_text,
                    # prediction_data_json is no longer needed here
                ),
            )

            # --- Step 2: Get the ID of the inserted/replaced row ---
            # This must be done *before* potential commit/rollback in exception handling
            cursor.execute(
                """
                 SELECT id FROM summarized_analysis
                 WHERE model_name = ? AND ticker = ?
                 """,
                (model_name, ticker),
            )
            result = cursor.fetchone()
            if result:
                summarized_analysis_id = result["id"]
            else:
                # Should not happen with INSERT OR REPLACE unless something went very wrong
                raise Exception("Failed to retrieve ID after INSERT OR REPLACE")

            # --- Step 3: Delete old predictions for this summary (if any) ---
            # Necessary because INSERT OR REPLACE on parent doesn't cascade delete children
            # And we want to insert the fresh set of predictions
            cursor.execute(
                """
                DELETE FROM summarized_predictions WHERE summarized_analysis_id = ?
                """,
                (summarized_analysis_id,),
            )

            # --- Step 4: Insert new predictions ---
            for day in range(1, 13):
                pred_key = f"prediction_{day}_day"
                conf_key = f"confidence_{day}_day"
                prediction_value = data.get(pred_key)
                confidence_value = data.get(conf_key)

                if prediction_value is not None and confidence_value is not None:
                    # Calculate the actual date for the prediction
                    prediction_date = (today_date + timedelta(days=day)).strftime(
                        "%Y-%m-%d"
                    )
                    cursor.execute(
                        """
                        INSERT INTO summarized_predictions (
                            summarized_analysis_id, date, prediction, confidence
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (
                            summarized_analysis_id,
                            prediction_date,
                            prediction_value,
                            confidence_value,
                        ),
                    )

            # --- Step 5: Commit transaction ---
            conn.commit()
            break  # Success, exit retry loop

        except sqlite3.OperationalError as e:
            if conn:
                conn.rollback()  # Rollback on error
            if "database is locked" in str(e):
                print(
                    f"Database locked (Summary Save), retrying in {retry_delay} seconds (attempt {attempt + 1}/{max_retries})"
                )
                if attempt + 1 == max_retries:  # Check if it was the last attempt
                    print(
                        f" | FAILED (Summary Save), DB locked after final attempt for {ticker} with {model_name}."
                    )
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                print(
                    f" | FAILED (Summary Save), DB Error: {e} for {ticker} with {model_name}"
                )
                break  # Stop retrying on non-lock errors
        except Exception as e:  # Catch other potential errors
            if conn:
                conn.rollback()  # Rollback on error
            print(
                f" | FAILED (Summary Save), Unexpected Error: {e} for {ticker} with {model_name}"
            )
            break  # Stop retrying

        finally:
            if conn:
                cursor.close()
                conn.close()


def increment_priority(article_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE articles SET priority = priority + 1 WHERE id = ?",
        (article_id,),
    )
    conn.commit()
    conn.close()


def fetch_sum_analysis_data(ticker, model):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            a.id,
            a.published,
            a.summary,
            p.date,
            p.prediction,
            p.confidence
        FROM
            analysis AS a
        JOIN
            predictions AS p ON a.id = p.analysis_id
        WHERE
            a.ticker = ?
            AND a.model_name = ?
        ORDER BY
            a.id, p.date
        """,
        (
            str(ticker),
            str(model),
        ),
    )

    data = cursor.fetchall()  #
    conn.close()

    result_list = []
    analysis_map = {}

    for row in data:
        try:
            analysis_id = row["id"]  #

            prediction_date_str = date.fromisoformat(row["date"]).strftime(
                "%Y-%m-%d"
            )  #
            prediction_details = {
                "date": prediction_date_str,
                "prediction": row["prediction"],
                "confidence": row["confidence"],
            }

            if analysis_id not in analysis_map:
                published_dt_str = datetime.strptime(
                    row["published"], "%Y-%m-%d"
                ).strftime(
                    "%Y-%m-%d"
                )  #
                current_analysis = {
                    "analysis_id": analysis_id,
                    "published": published_dt_str,
                    "summary": row["summary"],
                    "predictions": [],
                }
                analysis_map[analysis_id] = current_analysis
                result_list.append(current_analysis)
            else:
                current_analysis = analysis_map[analysis_id]  #

            current_analysis["predictions"].append(prediction_details)  #

        except (ValueError, TypeError, KeyError) as e:
            print(f"Warning: Skipping row due to error: {e} - Row data: {dict(row)}")  #
            continue

    today_str = date.today().strftime("%Y-%m-%d")
    article_count = len(result_list)

    metadata = f"Metadata:\n"
    metadata += f"Today's date: {today_str}\n"
    metadata += f"Articles Processed: {article_count}\n"
    metadata += f"Ticker: {ticker}\n"

    result_string = json.dumps(result_list, indent=4)

    return metadata + result_string


"""
DATABASE SCHEME:

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    priority INTEGER NOT NULL,
    link TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    published DATETIME NOT NULL,
    source TEXT NOT NULL,
    content TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    published DATETIME NOT NULL,
    ticker TEXT NOT NULL,
    stock TEXT NOT NULL,
    summary TEXT NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    date DATE NOT NULL,
    prediction FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES analysis(id)
);

CREATE TABLE IF NOT EXISTS summarized_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    ticker TEXT NOT NULL,
    last_updated DATETIME NOT NULL,
    summary_text TEXT NOT NULL,
    -- Removed prediction_data TEXT NOT NULL,
    UNIQUE(model_name, ticker)
);

CREATE TABLE IF NOT EXISTS summarized_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summarized_analysis_id INTEGER NOT NULL,
    date DATE NOT NULL,
    prediction FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    FOREIGN KEY (summarized_analysis_id) REFERENCES summarized_analysis(id) ON DELETE CASCADE -- Added ON DELETE CASCADE
);

"""
