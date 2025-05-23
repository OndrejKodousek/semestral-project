"""
@file evaluate.py
@brief Evaluates LSTM model performance by comparing predictions with actual values.
Enhanced to calculate day-by-day MAPE analysis across all tickers.
"""

import os
import sys
import yfinance as yf
import numpy as np
import pandas as pd
import joblib
import sqlite3
import random
from datetime import datetime, date, timedelta
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Input
from tensorflow.keras.callbacks import EarlyStopping

DB_PATH = "data/news.db"
DEFAULT_PREDICTION_DAYS = 12
SEQUENCE_LENGTH = 60
EPOCHS = 25
EVAL_LOG_FILE = "lstm_evaluation.log"
SUMMARY_RESULTS_FILE = "mape_summary_by_day.csv"
TRAIN_DAYS = 365 * 2
TEST_DAYS_AFTER_TRAIN = 1
MAX_TIME_OFFSET_DAYS = 7  # Random offset to avoid weekend clustering

TOP_N_TICKERS = 100

daily_mape_results = []


def get_top_tickers_by_frequency(db_file, limit=TOP_N_TICKERS):
    """Gets top tickers by analysis frequency from database."""
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
            LIMIT ?
            """,
            (limit,),
        )
        results = cursor.fetchall()
        tickers = [row[0] for row in results]
        print(f"Loaded {len(tickers)} tickers from database")
    except sqlite3.Error as e:
        print(f"Database error while fetching top tickers by frequency: {e}")
        print("Falling back to empty list")
    finally:
        if conn:
            conn.close()
    return tickers


def is_weekend(date_obj):
    """Check if a date falls on weekend (Saturday=5, Sunday=6)."""
    return date_obj.weekday() >= 5


def get_trading_days_from_data(ticker, start_date, end_date):
    """Get actual trading days for a ticker by fetching the data."""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return []
        return [date.date() for date in data.index]
    except Exception as e:
        print(f"Error getting trading days for {ticker}: {str(e)}")
        return []
    """Locates the project root directory."""
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    return Path(__file__).resolve().parent.parent


def fetch_historical_data(ticker, start_date, end_date):
    """Fetches historical stock data for given date range."""
    try:
        print(f"Fetching data for {ticker} from {start_date} to {end_date}")
        stock_data_df = yf.download(
            ticker, start=start_date, end=end_date, progress=False
        )

        if stock_data_df.empty:
            print(
                f"Warning: No data fetched for {ticker} from {start_date} to {end_date}."
            )
            return None, None

        return stock_data_df["Close"].values.reshape(-1, 1), stock_data_df

    except Exception as e:
        print(f"Error fetching data for {ticker}: {str(e)}")
        return None, None


def build_lstm_model(input_shape):
    """Constructs LSTM model architecture."""
    model = Sequential(
        [
            Input(shape=input_shape),
            LSTM(50, return_sequences=True),
            LSTM(50, return_sequences=False),
            Dense(25),
            Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


def train_model(ticker, train_data):
    """Trains an LSTM model on the given data."""
    try:
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(train_data)

        X, y = [], []
        for i in range(SEQUENCE_LENGTH, len(scaled_data)):
            X.append(scaled_data[i - SEQUENCE_LENGTH : i, 0])
            y.append(scaled_data[i, 0])

        if not X:
            print(
                f"Could not create sequences for {ticker}. Need at least {SEQUENCE_LENGTH + 1} data points."
            )
            return None, None

        X, y = np.array(X), np.array(y)
        X = X.reshape((X.shape[0], X.shape[1], 1))

        model = build_lstm_model((X.shape[1], 1))
        early_stopping = EarlyStopping(
            monitor="loss", patience=10, restore_best_weights=True
        )
        model.fit(
            X, y, batch_size=64, epochs=EPOCHS, verbose=0, callbacks=[early_stopping]
        )

        return model, scaler

    except Exception as e:
        print(f"Error training model for {ticker}: {str(e)}")
        return None, None


def make_predictions(model, scaler, recent_data_values):
    """Generates future price predictions using LSTM model."""
    try:
        predictions = []
        last_sequence = recent_data_values[-SEQUENCE_LENGTH:]
        current_batch = scaler.transform(last_sequence).reshape((1, SEQUENCE_LENGTH, 1))

        for _ in range(DEFAULT_PREDICTION_DAYS):
            predicted_price_scaled = model.predict(current_batch, verbose=0)
            predicted_price = scaler.inverse_transform(predicted_price_scaled)
            predictions.append(
                float(predicted_price[0][0])
            )  # Convert to native Python float
            current_batch = np.append(
                current_batch[:, 1:, :], predicted_price_scaled.reshape(1, 1, 1), axis=1
            )
        return predictions

    except Exception as e:
        print(f"Error making predictions: {str(e)}")
        return None


def calculate_mape(actual_values, predicted_values):
    """Calculates Mean Absolute Percentage Error (absolute values)."""
    try:
        actual = np.array(actual_values, dtype=float)
        predicted = np.array(predicted_values, dtype=float)
        # Ensure MAPE is absolute value
        return float(np.mean(np.abs((actual - predicted) / actual)) * 100)
    except Exception as e:
        print(f"Error calculating MAPE: {str(e)}")
        return None


def calculate_daily_mape(actual_values, predicted_values):
    """Calculates MAPE for each prediction day separately."""
    try:
        actual = np.array(actual_values, dtype=float)
        predicted = np.array(predicted_values, dtype=float)

        daily_mapes = []
        for i in range(len(actual)):
            if actual[i] != 0:
                daily_mape = abs((actual[i] - predicted[i]) / actual[i]) * 100
                daily_mapes.append(daily_mape)
            else:
                daily_mapes.append(None)  # Mark as invalid

        return daily_mapes
    except Exception as e:
        print(f"Error calculating daily MAPE: {str(e)}")
        return None


def get_project_root():
    """Locates the project root directory."""
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    return Path(__file__).resolve().parent.parent


def save_daily_mape_results(
    ticker,
    train_end_date,
    test_start_date,
    daily_mapes,
    actual_values,
    predicted_values,
    trading_days,
):
    """Saves daily MAPE results for later aggregation, only for valid trading days."""
    global daily_mape_results

    for day_idx, mape_val in enumerate(daily_mapes):
        if mape_val is not None and day_idx < len(
            trading_days
        ):  # Only save valid MAPE values and existing trading days
            daily_mape_results.append(
                {
                    "ticker": ticker,
                    "train_end_date": train_end_date.strftime("%Y-%m-%d"),
                    "prediction_day": day_idx + 1,  # Day 1, 2, ..., 12
                    "test_date": trading_days[day_idx].strftime("%Y-%m-%d"),
                    "actual_price": float(actual_values[day_idx]),
                    "predicted_price": float(predicted_values[day_idx]),
                    "daily_mape": float(mape_val),
                    "evaluation_date": date.today().strftime("%Y-%m-%d"),
                }
            )


def log_evaluation_results(
    ticker, mape, train_end_date, test_start_date, test_end_date, success
):
    """Logs evaluation results to file."""
    status = "SUCCESS" if success else "FAILURE"
    log_entry = (
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {status} - "
        f"Ticker: {ticker}, "
        f"Train End: {train_end_date.strftime('%Y-%m-%d')}, "
        f"Test Period: {test_start_date.strftime('%Y-%m-%d')} to {test_end_date.strftime('%Y-%m-%d')}, "
        f"MAPE: {mape:.2f}%"
        if mape is not None
        else "MAPE: N/A"
    )

    project_root = get_project_root()
    log_file = project_root / EVAL_LOG_FILE

    try:
        os.makedirs(log_file.parent, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"Error writing to log file: {str(e)}")


def evaluate_ticker(ticker):
    """Evaluates a single ticker."""
    project_root = get_project_root()
    db_file = project_root / DB_PATH

    # Add random offset to avoid weekend clustering
    random_offset = random.randint(0, MAX_TIME_OFFSET_DAYS)

    # Set up date ranges with random offset
    base_end_date = date.today() - timedelta(
        days=TEST_DAYS_AFTER_TRAIN + DEFAULT_PREDICTION_DAYS
    )
    end_date = base_end_date - timedelta(days=random_offset)
    train_end_date = end_date - timedelta(days=DEFAULT_PREDICTION_DAYS)
    train_start_date = train_end_date - timedelta(days=TRAIN_DAYS)
    test_start_date = train_end_date + timedelta(days=TEST_DAYS_AFTER_TRAIN)
    test_end_date = test_start_date + timedelta(days=DEFAULT_PREDICTION_DAYS + 10)

    print(f"\n{'='*50}")
    print(f"Evaluating model for {ticker} (offset: {random_offset} days)")
    print(f"Training period: {train_start_date} to {train_end_date}")
    print(f"Testing period: {test_start_date} to {test_end_date}")
    print(f"{'='*50}\n")

    # Fetch training data
    train_data, train_df = fetch_historical_data(
        ticker, train_start_date, train_end_date
    )
    if train_data is None or train_df is None:
        print("Failed to fetch training data.")
        log_evaluation_results(
            ticker, None, train_end_date, test_start_date, test_end_date, False
        )
        return False

    if len(train_data) < SEQUENCE_LENGTH + 1:
        print(
            f"Insufficient training data. Need at least {SEQUENCE_LENGTH + 1} days, got {len(train_data)}."
        )
        log_evaluation_results(
            ticker, None, train_end_date, test_start_date, test_end_date, False
        )
        return False

    # Train model
    model, scaler = train_model(ticker, train_data)
    if model is None or scaler is None:
        print("Failed to train model.")
        log_evaluation_results(
            ticker, None, train_end_date, test_start_date, test_end_date, False
        )
        return False

    prediction_input = train_data[-SEQUENCE_LENGTH:]

    # Make predictions
    predictions = make_predictions(model, scaler, prediction_input)
    if predictions is None or len(predictions) != DEFAULT_PREDICTION_DAYS:
        print(
            f"Prediction failed. Expected {DEFAULT_PREDICTION_DAYS} predictions, got {len(predictions) if predictions else 0}."
        )
        log_evaluation_results(
            ticker, None, train_end_date, test_start_date, test_end_date, False
        )
        return False

    # Get actual trading days for this period
    trading_days = get_trading_days_from_data(ticker, test_start_date, test_end_date)
    if len(trading_days) == 0:
        print(
            f"No trading data found for test period {test_start_date} to {test_end_date}."
        )
        log_evaluation_results(
            ticker, None, train_end_date, test_start_date, test_end_date, False
        )
        return False

    # Fetch actual values for comparison - only for available trading days
    actual_data_df = yf.download(
        ticker, start=test_start_date, end=test_end_date, progress=False
    )
    if actual_data_df.empty:
        print(
            f"No actual data found for test period {test_start_date} to {test_end_date}."
        )
        log_evaluation_results(
            ticker, None, train_end_date, test_start_date, test_end_date, False
        )
        return False

    # Get up to DEFAULT_PREDICTION_DAYS of actual values
    available_trading_days = min(len(trading_days), DEFAULT_PREDICTION_DAYS)
    actual_values = actual_data_df["Close"].values[:available_trading_days]
    predictions_to_use = predictions[:available_trading_days]
    trading_days_to_use = trading_days[:available_trading_days]

    if len(actual_values) == 0:
        print("No actual values available for comparison.")
        log_evaluation_results(
            ticker, None, train_end_date, test_start_date, test_end_date, False
        )
        return False

    print(
        f"Using {len(actual_values)} trading days out of {DEFAULT_PREDICTION_DAYS} prediction days"
    )

    # Calculate overall MAPE
    mape = calculate_mape(actual_values, predictions_to_use)
    if mape is None:
        print("Failed to calculate MAPE.")
        log_evaluation_results(
            ticker, None, train_end_date, test_start_date, test_end_date, False
        )
        return False

    # Calculate daily MAPE for each available prediction day
    daily_mapes = calculate_daily_mape(actual_values, predictions_to_use)
    if daily_mapes is None:
        print("Failed to calculate daily MAPE.")
        log_evaluation_results(
            ticker, None, train_end_date, test_start_date, test_end_date, False
        )
        return False

    # Save daily MAPE results
    save_daily_mape_results(
        ticker,
        train_end_date,
        test_start_date,
        daily_mapes,
        actual_values,
        predictions_to_use,
        trading_days_to_use,
    )

    print(f"\nEvaluation results for {ticker}:")
    print(f"  Overall MAPE: {mape:.2f}%")
    print("  Day\tDate\t\tPredicted\tActual\t\tDaily MAPE")
    for i in range(len(predictions_to_use)):
        actual_val = float(actual_values[i])
        predicted_val = float(predictions_to_use[i])
        daily_mape_val = daily_mapes[i] if daily_mapes[i] is not None else "N/A"
        test_date = trading_days_to_use[i].strftime("%Y-%m-%d")

        if daily_mapes[i] is not None:
            print(
                f"  {i+1}\t{test_date}\t{predicted_val:.2f}\t\t{actual_val:.2f}\t\t{daily_mape_val:.2f}%"
            )
        else:
            print(
                f"  {i+1}\t{test_date}\t{predicted_val:.2f}\t\t{actual_val:.2f}\t\t{daily_mape_val}"
            )

    log_evaluation_results(
        ticker, mape, train_end_date, test_start_date, test_end_date, True
    )

    return True


def save_results_to_files():
    """Saves summary statistics to CSV file."""
    global daily_mape_results

    if not daily_mape_results:
        print("No daily MAPE results to save.")
        return

    project_root = get_project_root()
    os.makedirs(project_root / "data", exist_ok=True)

    # Convert to DataFrame for easier processing
    daily_df = pd.DataFrame(daily_mape_results)

    # Calculate and save summary by prediction day
    summary_stats = []
    for day in range(1, DEFAULT_PREDICTION_DAYS + 1):
        day_data = daily_df[daily_df["prediction_day"] == day]["daily_mape"]
        if len(day_data) > 0:
            summary_stats.append(
                {
                    "prediction_day": day,
                    "count_tickers": len(day_data),
                    "mean_mape": day_data.mean(),
                    "median_mape": day_data.median(),
                    "std_mape": day_data.std(),
                    "min_mape": day_data.min(),
                    "max_mape": day_data.max(),
                    "q25_mape": day_data.quantile(0.25),
                    "q75_mape": day_data.quantile(0.75),
                }
            )
        else:
            # Add placeholder for days with no data
            summary_stats.append(
                {
                    "prediction_day": day,
                    "count_tickers": 0,
                    "mean_mape": np.nan,
                    "median_mape": np.nan,
                    "std_mape": np.nan,
                    "min_mape": np.nan,
                    "max_mape": np.nan,
                    "q25_mape": np.nan,
                    "q75_mape": np.nan,
                }
            )

    summary_df = pd.DataFrame(summary_stats)
    summary_file = project_root / SUMMARY_RESULTS_FILE
    summary_df.to_csv(summary_file, index=False)
    print(f"Summary MAPE by prediction day saved to: {summary_file}")

    # Print summary to console
    print(f"\n{'='*80}")
    print("MAPE SUMMARY BY PREDICTION DAY (excluding weekends)")
    print(f"{'='*80}")
    print(
        f"{'Day':<4} {'Count':<6} {'Mean MAPE':<12} {'Median MAPE':<12} {'Std MAPE':<12} {'Min MAPE':<10} {'Max MAPE':<10}"
    )
    print("-" * 80)
    for _, row in summary_df.iterrows():
        if row["count_tickers"] > 0:
            print(
                f"{int(row['prediction_day']):<4} {int(row['count_tickers']):<6} "
                f"{row['mean_mape']:<12.2f} {row['median_mape']:<12.2f} {row['std_mape']:<12.2f} "
                f"{row['min_mape']:<10.2f} {row['max_mape']:<10.2f}"
            )
        else:
            print(
                f"{int(row['prediction_day']):<4} {int(row['count_tickers']):<6} "
                f"{'No data':<12} {'No data':<12} {'No data':<12} "
                f"{'No data':<10} {'No data':<10}"
            )

    # Print the key insight - mean MAPE for each day
    print(f"\n{'='*50}")
    print("KEY RESULTS - MEAN MAPE BY PREDICTION DAY:")
    print(f"{'='*50}")
    valid_days = summary_df[summary_df["count_tickers"] > 0]
    for _, row in valid_days.iterrows():
        print(
            f"Day {int(row['prediction_day'])}: {row['mean_mape']:.2f}% (n={int(row['count_tickers'])})"
        )

    return summary_df


def main():
    """Main evaluation workflow for all tickers."""
    global daily_mape_results
    daily_mape_results = []  # Reset results

    # Set random seed for reproducible results
    random.seed(42)

    project_root = get_project_root()
    db_file = project_root / DB_PATH

    # Load tickers from database
    tickers = get_top_tickers_by_frequency(db_file)

    if not tickers:
        print(
            "ERROR: No tickers found in database. Please ensure the 'analysis' table contains data."
        )
        sys.exit(1)

    print(f"Starting evaluation for top {len(tickers)} tickers by frequency")
    print(
        f"Using random time offsets (0-{MAX_TIME_OFFSET_DAYS} days) to avoid weekend clustering"
    )
    print(
        f"Tickers to evaluate: {', '.join(tickers[:10])}{'...' if len(tickers) > 10 else ''}"
    )
    print(f"Evaluation started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    successful_evaluations = 0
    failed_evaluations = 0

    for i, ticker in enumerate(tickers, 1):
        print(f"\nProcessing ticker {i}/{len(tickers)}: {ticker}")
        try:
            success = evaluate_ticker(ticker)
            if success:
                successful_evaluations += 1
                print(f"✓ {ticker} evaluation completed successfully")
            else:
                failed_evaluations += 1
                print(f"✗ {ticker} evaluation failed")
        except Exception as e:
            failed_evaluations += 1
            print(f"✗ {ticker} evaluation failed with exception: {str(e)}")

    # Save results to files
    summary_df = save_results_to_files()

    # Summary
    print(f"\n{'='*60}")
    print(f"EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total tickers processed: {len(tickers)}")
    print(f"Successful evaluations: {successful_evaluations}")
    print(f"Failed evaluations: {failed_evaluations}")
    print(f"Success rate: {(successful_evaluations/len(tickers)*100):.1f}%")
    print(f"Total data points collected: {len(daily_mape_results)}")

    # Show weekend impact analysis
    if len(daily_mape_results) > 0:
        daily_df = pd.DataFrame(daily_mape_results)
        total_possible_days = successful_evaluations * DEFAULT_PREDICTION_DAYS
        actual_days_collected = len(daily_mape_results)
        weekend_loss_pct = (
            (total_possible_days - actual_days_collected) / total_possible_days
        ) * 100
        print(
            f"Weekend/holiday data loss: {weekend_loss_pct:.1f}% ({total_possible_days - actual_days_collected} out of {total_possible_days} possible days)"
        )

    print(f"Evaluation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

    successful_evaluations = 0
    failed_evaluations = 0

    for i, ticker in enumerate(tickers, 1):
        print(f"\nProcessing ticker {i}/{len(tickers)}: {ticker}")
        try:
            success = evaluate_ticker(ticker)
            if success:
                successful_evaluations += 1
                print(f"✓ {ticker} evaluation completed successfully")
            else:
                failed_evaluations += 1
                print(f"✗ {ticker} evaluation failed")
        except Exception as e:
            failed_evaluations += 1
            print(f"✗ {ticker} evaluation failed with exception: {str(e)}")

    # Save results to files
    save_results_to_files()

    # Summary
    print(f"\n{'='*60}")
    print(f"EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total tickers processed: {len(tickers)}")
    print(f"Successful evaluations: {successful_evaluations}")
    print(f"Failed evaluations: {failed_evaluations}")
    print(f"Success rate: {(successful_evaluations/len(tickers)*100):.1f}%")
    print(f"Total data points collected: {len(daily_mape_results)}")
    print(f"Evaluation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
