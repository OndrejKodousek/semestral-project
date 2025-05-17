"""
@file train.py
@brief LSTM model training for stock price prediction.

This module provides functionality to:
- Fetch historical stock data
- Preprocess data for LSTM training
- Build and train LSTM models
- Save trained models and scalers
"""

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

DB_PATH = "data/news.db"  # Path to database file
SEQUENCE_LENGTH = 60  # Sequence length for LSTM input
EPOCHS = 25  # Maximum number of training epochs


def get_project_root():
    """
    @brief Locates the project root directory by searching for .git marker.

    @return Path object pointing to project root directory
    """
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    return Path(__file__).resolve().parent.parent


def fetch_stock_data(ticker, start_date="2010-01-01"):
    """
    @brief Fetches historical stock data from Yahoo Finance.

    @param ticker Stock ticker symbol
    @param start_date Start date for historical data
    @return Tuple containing (numpy array of close prices, pandas DataFrame of full data)
            or (None, None) if data cannot be fetched
    """
    try:
        stock_data_df = yf.download(ticker, start=start_date, progress=False)
        if stock_data_df.empty:
            print(f"Warning: No data fetched for {ticker}.")
            return None, None
        return stock_data_df["Close"].values.reshape(-1, 1), stock_data_df
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None, None


def build_lstm_model(input_shape):
    """
    @brief Constructs LSTM model architecture.

    @param input_shape Shape of input data (sequence_length, features)
    @return Compiled Keras Sequential model
    """
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=input_shape))
    model.add(LSTM(50, return_sequences=False))
    model.add(Dense(25))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


def save_model_and_scaler(model, scaler, ticker, base_path):
    """
    @brief Saves trained model and scaler to disk.

    @param model Trained Keras model
    @param scaler Fitted MinMaxScaler
    @param ticker Stock ticker symbol
    @param base_path Directory path to save files
    """
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
    """
    @brief Main training workflow.

    @param ticker Stock ticker symbol to train model for
    """
    project_root = get_project_root()
    models_path = project_root / "data" / "lstm_models"
    db_file = project_root / DB_PATH

    print(f"Fetching historical data for {ticker}...")

    data_values, _ = fetch_stock_data(ticker)

    if data_values is None or len(data_values) < 61:
        print(f"Insufficient data for {ticker} to train. Skipping.")
        return

    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data_values)

    X, y = [], []
    for i in range(SEQUENCE_LENGTH, len(scaled_data)):
        X.append(scaled_data[i - SEQUENCE_LENGTH : i, 0])
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

    model.fit(X, y, batch_size=64, epochs=EPOCHS, verbose=1, callbacks=[early_stopping])

    print(f"Saving model and scaler for {ticker}...")
    save_model_and_scaler(model, scaler, ticker, models_path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python train_model.py <ticker>")
        sys.exit(1)

    ticker_symbol = sys.argv[1].upper()
    main(ticker_symbol)
