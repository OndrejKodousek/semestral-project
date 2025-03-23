import os
import sys
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib


from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from datetime import datetime
from pathlib import Path


def get_project_root():
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    print("ERROR: Failed to find root folder of project")
    exit(1)


def fetch_stock_data(ticker, start_date="2010-01-01", end_date="0000-00-00"):
    if end_date == "0000-00-00":
        end_date = datetime.today().strftime("%Y-%m-%d")
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data["Close"].values.reshape(-1, 1)


def preprocess_data(data, sequence_length=60):
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)

    X, y = [], []
    for i in range(sequence_length, len(scaled_data)):
        X.append(scaled_data[i - sequence_length : i, 0])
        y.append(scaled_data[i, 0])

    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    return X, y, scaler


def build_lstm_model(input_shape):
    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=input_shape))
    model.add(LSTM(50, return_sequences=False))
    model.add(Dense(25))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


def save_model_and_scaler(model, scaler, ticker):
    filepath = os.path.join(get_project_root(), "data", "lstm_models")

    filepath_model = os.path.join(filepath, f"{ticker}_model.keras")
    filepath_scaler = os.path.join(filepath, f"{ticker}_scaler.pkl")

    model.save(f"{ticker}_model.keras")
    joblib.dump(scaler, f"{ticker}_scaler.pkl")


def main(ticker):
    print(f"Fetching historical data for {ticker}...")
    data = fetch_stock_data(ticker)

    sequence_length = 60
    X, y, scaler = preprocess_data(data, sequence_length)

    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    print("Building and training LSTM model...")
    model = build_lstm_model((X_train.shape[1], 1))
    model.fit(X_train, y_train, batch_size=32, epochs=100, verbose=1)

    print("Saving model and scaler...")
    save_model_and_scaler(model, scaler, ticker)

    print(f"Model and scaler saved for {ticker}.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python train_model.py <ticker>")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    main(ticker)
