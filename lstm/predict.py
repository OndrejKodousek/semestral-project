import os
import sys
import yfinance as yf
import numpy as np
import pandas as pd
import joblib
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import disable_interactive_logging

disable_interactive_logging()

DB_PATH = "data/news.db"
DEFAULT_PREDICTION_DAYS = 12
SEQUENCE_LENGTH = 60


def get_project_root():
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    return Path(__file__).resolve().parent.parent


def fetch_recent_stock_data(ticker):
    try:
        start_date = (datetime.today() - timedelta(days=SEQUENCE_LENGTH + 30)).strftime(
            "%Y-%m-%d"
        )
        stock_data_df = yf.download(ticker, start=start_date, progress=False)
        if stock_data_df.empty or len(stock_data_df) < SEQUENCE_LENGTH:
            return None, None
        return stock_data_df["Close"].values.astype(float).reshape(-1, 1), stock_data_df
    except Exception as e:
        print(f"Error fetching recent data for {ticker}: {e}")
        return None, None


def load_model_and_scaler(ticker, base_path):
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


def predict_future_prices(model, scaler, recent_data_values):
    predictions = []
    last_sequence = recent_data_values[-SEQUENCE_LENGTH:]
    current_batch = scaler.transform(last_sequence).reshape((1, SEQUENCE_LENGTH, 1))
    for _ in range(DEFAULT_PREDICTION_DAYS):
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
    conn = None
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    prediction_made_date_str = date.today().strftime("%Y-%m-%d")
    rows_to_insert = []

    # Add the reference value row
    rows_to_insert.append(
        (
            ticker,
            prediction_made_date_str,
            last_actual_date_obj.strftime("%Y-%m-%d"),
            float(last_actual_value),
            1,
        )
    )

    # Add the prediction rows
    start_target_date = last_actual_date_obj + timedelta(days=1)
    for i, pred_value in enumerate(prediction_list):
        target_date = start_target_date + timedelta(days=i)
        rows_to_insert.append(
            (
                ticker,
                prediction_made_date_str,
                target_date.strftime("%Y-%m-%d"),
                float(pred_value),
                0,
            )
        )

    cursor.execute(
        """
        DELETE FROM lstm_predictions
        WHERE ticker = ?
        """,
        (ticker,),
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
    conn.close()


def main(ticker, days_to_predict):
    project_root = get_project_root()
    models_path = project_root / "data" / "lstm_models"
    db_file = project_root / DB_PATH

    model, scaler = load_model_and_scaler(ticker, models_path)
    if model is None or scaler is None:
        print(f"Failed to load model/scaler for {ticker}. Cannot proceed.")
        sys.exit(1)

    recent_data_values, recent_data_df = fetch_recent_stock_data(ticker)
    if recent_data_values is None or recent_data_df is None:
        print(f"Failed to fetch recent data for {ticker}. Cannot proceed.")
        sys.exit(1)

    last_actual_value = recent_data_values[-1][0]

    last_actual_date_obj = recent_data_df.index[-1].date()

    predictions = predict_future_prices(model, scaler, recent_data_values)

    save_reference_and_predictions(
        db_file,
        ticker,
        last_actual_value,
        last_actual_date_obj,
        predictions,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python predict_model.py <ticker> [days_to_predict]")
        print(f"Default prediction days: {DEFAULT_PREDICTION_DAYS}")
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
