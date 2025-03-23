import os
import sys
import yfinance as yf
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from pathlib import Path
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler


def get_project_root():
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    print("ERROR: Failed to find root folder of project")
    exit(1)


def fetch_stock_data(ticker, start_date, end_date):
    stock_data = yf.download(ticker, start=start_date, end=end_date)
    return stock_data["Close"].values.reshape(-1, 1)


def load_model_and_scaler(ticker):
    filepath = os.path.join(get_project_root(), "data", "lstm_models")
    filepath_model = os.path.join(filepath, f"{ticker}_model.keras")
    filepath_scaler = os.path.join(filepath, f"{ticker}_scaler.pkl")

    model = load_model(filepath_model)
    scaler = joblib.load(filepath_scaler)

    return model, scaler


def predict_future_prices(model, scaler, data, sequence_length=60, prediction_days=30):
    predictions = []
    last_sequence = data[-sequence_length:]
    last_sequence_scaled = scaler.transform(last_sequence)

    for _ in range(prediction_days):
        last_sequence_scaled = last_sequence_scaled.reshape((1, sequence_length, 1))
        predicted_price_scaled = model.predict(last_sequence_scaled)
        predicted_price = scaler.inverse_transform(predicted_price_scaled)
        predictions.append(predicted_price[0][0])
        last_sequence_scaled = np.append(
            last_sequence_scaled[0][1:], predicted_price_scaled, axis=0
        )

    return predictions


def main(ticker, start_date, end_date):
    print(f"Fetching historical data for {ticker} up to today...")
    today = datetime.today().strftime("%Y-%m-%d")
    data = fetch_stock_data(
        ticker, start_date="2010-01-01", end_date=today
    )  # Fetch data up to today

    if len(data) < 60:
        print(
            "ERROR: Insufficient historical data to make predictions (need at least 60 days)."
        )
        sys.exit(1)

    print("Loading model and scaler...")
    model, scaler = load_model_and_scaler(ticker)

    print("Making predictions...")
    prediction_days = (
        datetime.strptime(end_date, "%Y-%m-%d")
        - datetime.strptime(start_date, "%Y-%m-%d")
    ).days
    predictions = predict_future_prices(
        model, scaler, data, prediction_days=prediction_days
    )

    # Generate dates for predictions
    prediction_dates = [
        datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=i)
        for i in range(1, prediction_days + 1)
    ]
    prediction_dates = [date.strftime("%Y-%m-%d") for date in prediction_dates]

    # Prepare the data in the desired format
    predictions_data = [
        {"date": date, "prediction": float(pred)}
        for date, pred in zip(prediction_dates, predictions)
    ]

    # Print the predictions data (can be modified to return or send via API)
    print(predictions_data)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python predict_model.py <ticker> <start_date> <end_date>")
        sys.exit(1)

    ticker = sys.argv[1].upper()
    start_date = sys.argv[2]
    end_date = sys.argv[3]

    main(ticker, start_date, end_date)
