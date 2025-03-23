import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import joblib
from tensorflow.keras.models import load_model
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime


def get_project_root():
    marker = ".git"
    current_path = os.path.abspath(__file__)
    while True:
        if os.path.exists(os.path.join(current_path, marker)):
            return current_path
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path:
            print("ERROR: Failed to find root folder of project")
            exit(1)
        current_path = parent_path


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


def load_model_and_scaler(ticker):
    filepath = os.path.join(get_project_root(), "data", "lstm_models")

    filepath_model = os.path.join(filepath, f"{ticker}_model.keras")
    filepath_scaler = os.path.join(filepath, f"{ticker}_scaler.pkl")

    if not os.path.exists(filepath_model) or not os.path.exists(filepath_scaler):
        print(f"ERROR: Model or scaler for {ticker} not found.")
        exit(1)

    model = load_model(filepath_model)
    scaler = joblib.load(filepath_scaler)

    return model, scaler


def evaluate_model(model, scaler, X_test, y_test):
    """Evaluate the model on the test data."""
    predictions = model.predict(X_test)

    predictions = scaler.inverse_transform(predictions.reshape(-1, 1))
    y_test = scaler.inverse_transform(y_test.reshape(-1, 1))

    # Calculate absolute error metrics
    mse = mean_squared_error(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mse)

    # Calculate relative error metrics
    mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100  # MAPE
    smape = (
        np.mean(
            2 * np.abs(y_test - predictions) / (np.abs(y_test) + np.abs(predictions))
        )
        * 100
    )  # sMAPE

    print(f"Mean Squared Error (MSE): {mse}")
    print(f"Mean Absolute Error (MAE): {mae}")
    print(f"Root Mean Squared Error (RMSE): {rmse}")
    print(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%")
    print(f"Symmetric Mean Absolute Percentage Error (sMAPE): {smape:.2f}%")

    # Plot the results
    plt.figure(figsize=(14, 7))
    plt.plot(y_test, color="blue", label="Actual Stock Price")
    plt.plot(predictions, color="red", label="Predicted Stock Price")
    plt.title(f"Stock Price Prediction for {ticker}")
    plt.xlabel("Time")
    plt.ylabel("Stock Price")
    plt.legend()
    filepath = os.path.join(get_project_root(), "data", "lstm_evaluate.png")
    plt.savefig(filepath)


def main(ticker):
    print(f"Loading model and scaler for {ticker}...")
    model, scaler = load_model_and_scaler(ticker)

    # Fetch new data for evaluation (you can modify the dates as needed)
    print(f"Fetching historical data for {ticker}...")
    data = fetch_stock_data(ticker, start_date="2010-01-01", end_date="2023-12-31")

    # Preprocess the data
    sequence_length = 60
    X, y, _ = preprocess_data(data, sequence_length)

    # Split into training and testing sets (same as during training)
    split = int(0.8 * len(X))
    X_test = X[split:]
    y_test = y[split:]

    # Evaluate the model
    print("Evaluating model...")
    evaluate_model(model, scaler, X_test, y_test)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python evaluate_model.py <ticker>")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    main(ticker)
