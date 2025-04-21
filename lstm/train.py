import os
import sys
import yfinance as yf
import numpy as np
import pandas as pd
import joblib
import sqlite3
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.callbacks import EarlyStopping
from datetime import datetime
from pathlib import Path

DB_PATH = "data/news.db"


def get_project_root():
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    return Path(__file__).resolve().parent.parent


def fetch_stock_data(ticker, start_date="2010-01-01"):
    try:
        # Fetch data up to today, yfinance handles finding the last available day
        stock_data_df = yf.download(ticker, start=start_date, progress=False)
        if stock_data_df.empty:
            print(f"Warning: No data fetched for {ticker}.")
            return None, None
        # Return only Close prices and the actual data fetched
        return stock_data_df["Close"].values.reshape(-1, 1), stock_data_df
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None


def build_lstm_model(input_shape):
    model = Sequential()
    # Consider making units configurable
    model.add(LSTM(50, return_sequences=True, input_shape=input_shape))
    model.add(LSTM(50, return_sequences=False))
    model.add(Dense(25))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


def save_model_and_scaler(model, scaler, ticker, base_path):
    """Saves the model and scaler to the specified base path."""
    filepath_model = base_path / f"{ticker}_model.keras"
    filepath_scaler = base_path / f"{ticker}_scaler.pkl"

    try:
        os.makedirs(base_path, exist_ok=True)
        model.save(filepath_model)
        joblib.dump(scaler, filepath_scaler)
        print(f"Model saved to {filepath_model}")
        print(f"Scaler saved to {filepath_scaler}")
    except Exception as e:
        print(f"Error saving model or scaler for {ticker}: {e}")


def main(ticker):
    project_root = get_project_root()
    models_path = project_root / "data" / "lstm_models"
    db_file = project_root / DB_PATH

    print(f"Fetching historical data for {ticker}...")

    data_values, _ = fetch_stock_data(ticker)

    if data_values is None or len(data_values) < 61:
        print(f"Insufficient data for {ticker} to train. Skipping.")
        return

    sequence_length = 60

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data_values)

    X, y = [], []
    for i in range(sequence_length, len(scaled_data)):
        X.append(scaled_data[i - sequence_length : i, 0])
        y.append(scaled_data[i, 0])

    if not X:
        print(f"Could not create sequences for {ticker}. Skipping.")
        return

    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    print(f"Building and training LSTM model for {ticker} using {len(X)} sequences")
    model = build_lstm_model((X.shape[1], 1))

    early_stopping = EarlyStopping(
        monitor="loss", patience=10, restore_best_weights=True
    )

    model.fit(X, y, batch_size=32, epochs=25, verbose=1, callbacks=[early_stopping])

    print(f"Saving model and scaler for {ticker}...")
    save_model_and_scaler(model, scaler, ticker, models_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python train_model.py <ticker>")
        sys.exit(1)

    ticker_symbol = sys.argv[1].upper()
    main(ticker_symbol)
