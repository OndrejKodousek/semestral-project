# python predict_model.py <ticker> [days_to_predict]
import os
import sys
import yfinance as yf
import numpy as np
import pandas as pd
import joblib
import sqlite3
from datetime import datetime, date, timedelta  # Added date
from pathlib import Path
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import disable_interactive_logging

disable_interactive_logging()

DB_PATH = "data/news.db"
DEFAULT_PREDICTION_DAYS = 12
SEQUENCE_LENGTH = 60


def get_project_root():
    # (Function remains the same)
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    return Path(__file__).resolve().parent.parent


def fetch_recent_stock_data(ticker, days_needed=SEQUENCE_LENGTH):
    # (Function remains the same)
    try:
        start_date = (datetime.today() - timedelta(days=days_needed + 30)).strftime(
            "%Y-%m-%d"
        )
        stock_data_df = yf.download(ticker, start=start_date, progress=False)
        if stock_data_df.empty or len(stock_data_df) < days_needed:
            print(
                f"Warning: Insufficient recent data fetched for {ticker} (< {days_needed} days)."
            )
            return None, None
        return stock_data_df["Close"].values.astype(float).reshape(-1, 1), stock_data_df
    except Exception as e:
        print(f"Error fetching recent data for {ticker}: {e}")
        return None, None


def load_model_and_scaler(ticker, base_path):
    # (Function remains the same)
    filepath_model = base_path / f"{ticker}_model.keras"
    filepath_scaler = base_path / f"{ticker}_scaler.pkl"
    if not filepath_model.exists() or not filepath_scaler.exists():
        print(f"ERROR: Model or scaler for {ticker} not found at {base_path}.")
        return None, None
    try:
        model = load_model(filepath_model)
        scaler = joblib.load(filepath_scaler)
        return model, scaler
    except Exception as e:
        print(f"Error loading model or scaler for {ticker}: {e}")
        return None, None


def predict_future_prices(
    model,
    scaler,
    recent_data_values,
    sequence_length=SEQUENCE_LENGTH,
    prediction_days=DEFAULT_PREDICTION_DAYS,
):
    # (Function remains the same)
    predictions = []
    last_sequence = recent_data_values[-sequence_length:]
    current_batch = scaler.transform(last_sequence).reshape((1, sequence_length, 1))
    for _ in range(prediction_days):
        predicted_price_scaled = model.predict(current_batch, verbose=0)
        predicted_price = scaler.inverse_transform(predicted_price_scaled)
        predictions.append(predicted_price[0][0])
        current_batch = np.append(
            current_batch[:, 1:, :], predicted_price_scaled.reshape(1, 1, 1), axis=1
        )
    return predictions


def save_reference_and_predictions(
    db_path, ticker, last_actual_value, last_actual_date_obj, prediction_list
):
    """Saves the reference value and the predictions to the database."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Use only the date part for prediction_made_date
        prediction_made_date_str = date.today().strftime("%Y-%m-%d")
        rows_to_insert = []

        # 1. Add the reference value row
        rows_to_insert.append(
            (
                ticker,
                prediction_made_date_str,
                last_actual_date_obj.strftime(
                    "%Y-%m-%d"
                ),  # Target date is the actual date
                float(last_actual_value),
                1,  # is_reference = True
            )
        )

        # 2. Add the prediction rows
        start_target_date = last_actual_date_obj + timedelta(
            days=1
        )  # Predictions start day after actual
        for i, pred_value in enumerate(prediction_list):
            target_date = start_target_date + timedelta(days=i)
            rows_to_insert.append(
                (
                    ticker,
                    prediction_made_date_str,
                    target_date.strftime("%Y-%m-%d"),  # Target date for prediction
                    float(pred_value),
                    0,  # is_reference = False
                )
            )

        cursor.executemany(
            """
             INSERT INTO lstm_predictions
             (ticker, prediction_made_date, prediction_target_date, value, is_reference)
             VALUES (?, ?, ?, ?, ?)
             """,
            rows_to_insert,
        )
        conn.commit()
        print(
            f"Successfully saved reference + {len(prediction_list)} predictions for {ticker} to DB."
        )

    except sqlite3.Error as e:
        print(f"Database error saving predictions for {ticker}: {e}")
    finally:
        if conn:
            conn.close()


def main(ticker, days_to_predict):
    project_root = get_project_root()
    models_path = project_root / "data" / "lstm_models"
    db_file = project_root / DB_PATH

    print(f"Attempting prediction for {ticker}...")

    model, scaler = load_model_and_scaler(ticker, models_path)
    if model is None or scaler is None:
        print(f"Failed to load model/scaler for {ticker}. Cannot proceed.")
        sys.exit(1)

    recent_data_values, recent_data_df = fetch_recent_stock_data(
        ticker, SEQUENCE_LENGTH
    )
    if recent_data_values is None or recent_data_df is None:
        print(f"Failed to fetch recent data for {ticker}. Cannot proceed.")
        sys.exit(1)

    last_actual_value = recent_data_values[-1][0]
    # Ensure last_actual_date is a date object
    last_actual_date_obj = None
    if isinstance(recent_data_df.index, pd.DatetimeIndex):
        last_actual_date_obj = recent_data_df.index[-1].date()
    else:
        print("Error: Could not determine last actual date from DataFrame index.")
        sys.exit(1)  # Exit if we can't get the reference date

    try:
        print(f"Making {days_to_predict}-day prediction for {ticker}...")
        predictions = predict_future_prices(
            model, scaler, recent_data_values, SEQUENCE_LENGTH, days_to_predict
        )
        print(f"Predictions generated.")
    except Exception as e:
        print(f"Error during prediction generation for {ticker}: {e}")
        sys.exit(1)

    print(f"Saving reference + predictions for {ticker} to database...")
    save_reference_and_predictions(  # Renamed function call
        db_file,
        ticker,
        last_actual_value,
        last_actual_date_obj,  # Pass date object
        predictions,
    )

    print(f"Prediction process complete for {ticker}.")


if __name__ == "__main__":
    # (Argument parsing remains the same)
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python predict_model.py <ticker> [days_to_predict]")
        print(f"  (Default prediction days: {DEFAULT_PREDICTION_DAYS})")
        sys.exit(1)
    ticker_symbol = sys.argv[1].upper()
    num_days = DEFAULT_PREDICTION_DAYS
    if len(sys.argv) == 3:
        try:
            num_days = int(sys.argv[2])
            if num_days <= 0:
                raise ValueError("Prediction days must be positive.")
        except ValueError as e:
            print(f"Error: Invalid number of prediction days. {e}")
            sys.exit(1)
    main(ticker_symbol, num_days)
