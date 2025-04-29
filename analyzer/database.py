import sqlite3
import time
import json
import pandas as pd
import warnings
import yfinance as yf

from datetime import datetime, timedelta, date
from collections import defaultdict

warnings.simplefilter(action="ignore", category=FutureWarning)


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


def get_last_trading_day(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")

    pd_date = pd.Timestamp(date)

    # 5=Saturday, 6=Sunday
    if pd_date.dayofweek >= 5:

        # Go back to the most recent business day
        trading_day = pd_date - pd.tseries.offsets.BDay(1)
        return trading_day.strftime("%Y-%m-%d")

    return date_str


def get_stock_price(ticker, date_str):
    max_retries = 3
    retry_delay = 2
    trading_date = get_last_trading_day(date_str)

    for attempt in range(max_retries):
        try:
            # Get data for a window around the target date
            start_date = datetime.strptime(trading_date, "%Y-%m-%d") - timedelta(days=5)
            end_date = datetime.strptime(trading_date, "%Y-%m-%d") + timedelta(days=1)

            stock_data = yf.download(
                ticker,
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                progress=False,
            )

            if not stock_data.empty:
                closest_date = None
                for date in stock_data.index:
                    date_str_format = date.strftime("%Y-%m-%d")
                    if date_str_format <= trading_date and (
                        closest_date is None or date > closest_date
                    ):
                        closest_date = date

                if closest_date is not None:
                    close_price = float(stock_data.loc[closest_date, "Close"])
                    return close_price

            print(
                f"No price data found for {ticker} on {trading_date}, attempt {attempt+1}"
            )
            time.sleep(retry_delay)
            retry_delay *= 2

        except Exception as e:
            print(f"Error fetching stock price for {ticker} on {date_str}: {e}")
            time.sleep(retry_delay)
            retry_delay *= 2

    raise Exception(
        f"Failed to fetch stock price for {ticker} after {max_retries} attempts"
    )


def save_processed_articles(article_id, model, data):
    max_retries = 5
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Extract the date part (YYYY-MM-DD) from the published field
            published_date = data["published"].split("T")[0]
            ticker = data.get("ticker")

            base_stock_price = None
            if ticker:
                try:
                    # print(f"Fetching stock price for {ticker} on {published_date}")
                    base_stock_price = get_stock_price(ticker, published_date)
                # print(
                #     f"Base price for {ticker} on {published_date}: ${base_stock_price:.2f}"
                # )
                except Exception as e:
                    print(f" | FAILED to get stock price: {e}")
                    return False  # TODO: Probably handle this somehow. Idk how tho

            if base_stock_price is None:
                print(f" | FAILED to get stock price: {e}")
                return False  # TODO: Probably handle this somehow. Idk how tho

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
                    published_date,
                    ticker,
                    data.get("stock"),
                    data.get("summary"),
                ),
            )
            analysis_id = cursor.lastrowid

            # Insert into predictions table
            for day in range(1, 13):
                prediction_key = f"prediction_{day}_day"
                confidence_key = f"confidence_{day}_day"

                prediction_date = (
                    datetime.strptime(published_date, "%Y-%m-%d") + timedelta(days=day)
                ).strftime("%Y-%m-%d")

                percentage_prediction = data.get(prediction_key)

                if percentage_prediction is not None:
                    try:
                        # Convert percentage to decimal and calculate absolute price
                        percentage_decimal = float(percentage_prediction)
                        absolute_prediction = base_stock_price * (
                            1 + percentage_decimal
                        )

                        # print(f"percentage_prediction: {percentage_prediction}")
                        # print(f"percentage_decimal: {percentage_decimal}")
                        # print(f"base_stock_price: {base_stock_price}")
                        # print(f"absolute_prediction: {absolute_prediction}")

                        cursor.execute(
                            """
                            INSERT INTO predictions (
                                analysis_id, date, prediction, confidence
                            ) VALUES (?, ?, ?, ?)
                            """,
                            (
                                analysis_id,
                                prediction_date,
                                absolute_prediction,
                                data.get(confidence_key),
                            ),
                        )
                    except (ValueError, TypeError) as e:
                        print(f"Could not calculate absolute value for day {day}: {e}")

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

    return True


def save_processed_summarized_articles(data, model_name, ticker, published_date):
    max_retries = 5
    retry_delay = 1
    summarized_analysis_id = None

    summary_text = data.get("summary", "")
    today_date = date.today()

    for attempt in range(max_retries):
        conn = None
        try:

            # Extract the date part (YYYY-MM-DD) from the published field
            ticker = data.get("ticker")

            base_stock_price = None
            if ticker:
                try:
                    # print(f"Fetching stock price for {ticker} on {published_date}")
                    base_stock_price = get_stock_price(ticker, published_date)
                # print(
                #     f"Base price for {ticker} on {published_date}: ${base_stock_price:.2f}"
                # )
                except Exception as e:
                    print(f" | FAILED to get stock price: {e}")
                    return False  # TODO: Probably handle this somehow. Idk how tho

            if base_stock_price is None:
                print(f" | FAILED to get stock price: {e}")
                return False  # TODO: Probably handle this somehow. Idk how tho

            conn = get_db_connection()
            cursor = conn.cursor()
            conn.execute("BEGIN TRANSACTION")  # NTFS-like thingy

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
                ),
            )

            # Get the ID of the inserted/replaced row
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
                # Should not happen with INSERT OR REPLACE unless something went very, very wrong
                raise Exception("Failed to retrieve ID after INSERT OR REPLACE")

            # Delete old predictions for this summary
            cursor.execute(
                """
                DELETE FROM summarized_predictions WHERE summarized_analysis_id = ?
                """,
                (summarized_analysis_id,),
            )

            # Insert new predictions
            for day in range(1, 13):
                pred_key = f"prediction_{day}_day"
                conf_key = f"confidence_{day}_day"
                prediction_value = data.get(pred_key)
                confidence_value = data.get(conf_key)

                prediction_date = (
                    datetime.strptime(published_date, "%Y-%m-%d") + timedelta(days=day)
                ).strftime("%Y-%m-%d")

                percentage_prediction = data.get(pred_key)

                if percentage_prediction is not None:
                    try:
                        # Convert percentage to decimal and calculate absolute price
                        percentage_decimal = float(percentage_prediction)
                        absolute_prediction = base_stock_price * (
                            1 + percentage_decimal
                        )

                        # print(f"percentage_prediction: {percentage_prediction}")
                        # print(f"percentage_decimal: {percentage_decimal}")
                        # print(f"base_stock_price: {base_stock_price}")
                        # print(f"absolute_prediction: {absolute_prediction}")

                        cursor.execute(
                            """
                            INSERT INTO summarized_predictions (
                            summarized_analysis_id, date, prediction, confidence
                        ) VALUES (?, ?, ?, ?)
                            """,
                            (
                                summarized_analysis_id,
                                prediction_date,
                                absolute_prediction,
                                confidence_value,
                            ),
                        )
                    except (ValueError, TypeError) as e:
                        print(f"Could not calculate absolute value for day {day}: {e}")

            conn.commit()
            break

        except sqlite3.OperationalError as e:
            if conn:
                conn.rollback()
            if "database is locked" in str(e):
                print(
                    f"Database locked (Summary Save), retrying in {retry_delay} seconds (attempt {attempt + 1}/{max_retries})"
                )
                if attempt + 1 == max_retries:
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

    return today_str, (metadata + result_string)
