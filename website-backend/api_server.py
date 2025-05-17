"""
@file api_server.py
@brief Flask API server for stock analysis system.

This module provides RESTful endpoints for:
- Fetching LSTM predictions
- Retrieving summarized analyses
- Accessing historical stock data
- Getting stock lists and individual analyses
"""

import json
import os
import re
import sqlite3
import yfinance as yf
import traceback
import google.generativeai as genai
import warnings

from groq import Groq, RateLimitError, APIStatusError
from openai import OpenAI
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

from curl_cffi import requests

# Initialize Flask app and CORS
app = Flask(__name__)
CORS(app)
warnings.simplefilter(action="ignore", category=FutureWarning)


def get_project_root():
    """
    @brief Locates the project root directory.

    @return Path object pointing to project root directory
    @throws SystemExit if root directory cannot be found
    """
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    print("ERROR: Failed to find root folder of project")
    exit(1)


@app.route("/api/fetch_lstm", methods=["GET"])
def fetch_lstm():
    """
    @brief Endpoint for fetching LSTM predictions.

    @return JSON response with predictions or error message
    """
    ticker = request.args.get("ticker")
    if not ticker:
        return jsonify({"error": "Missing ticker parameter"}), 400

    db_path = os.path.join(get_project_root(), "data", "news.db")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch latest predictions
        cursor.execute(
            """
            SELECT prediction_made_date, prediction_target_date, value
            FROM lstm_predictions
            WHERE ticker = ?
            ORDER BY prediction_made_date DESC, prediction_target_date ASC;
            """,
            (ticker,),
        )
        all_predictions = cursor.fetchall()

        conn.close()

        if not all_predictions:
            return jsonify({})

        # Format response
        latest_prediction_made_date = all_predictions[0]["prediction_made_date"]
        latest_prediction_rows = [
            p
            for p in all_predictions
            if p["prediction_made_date"] == latest_prediction_made_date
        ]

        predictions_dict = {}
        for row in latest_prediction_rows:
            predictions_dict[row["prediction_target_date"]] = float(row["value"])

        return jsonify(predictions_dict)

    except sqlite3.Error as e:
        print(f"Database error in /api/fetch_lstm: {e}")
        if conn:
            conn.close()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        print(f"Unexpected error in /api/fetch_lstm: {e}")
        if conn:
            conn.close()
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/sum_analysis", methods=["GET"])
def sum_analysis():
    """
    @brief Endpoint for summarized analysis data.

    @return JSON response with analysis or error message
    """
    model = request.args.get("model")
    ticker = request.args.get("ticker")
    if not model or not ticker:
        return jsonify({"error": "Missing model or ticker parameter"}), 400

    db_path = os.path.join(get_project_root(), "data", "news.db")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Fetch summarized analysis
        cursor.execute(
            """
            SELECT id, summary_text, last_updated
            FROM summarized_analysis
            WHERE model_name = ? AND ticker = ?
            LIMIT 1
            """,
            (model, ticker),
        )
        summary_row = cursor.fetchone()

        if not summary_row:
            return jsonify({"error": "No summarized analysis found"}), 404

        # Fetch associated predictions
        cursor.execute(
            """
            SELECT date, prediction, confidence
            FROM summarized_predictions
            WHERE summarized_analysis_id = ?
            ORDER BY date ASC
            """,
            (summary_row["id"],),
        )
        prediction_rows = cursor.fetchall()

        conn.close()

        # Format response
        core_data = {
            "stock": ticker,  # Default if stock name not found
            "ticker": ticker,
            "summary": summary_row["summary_text"],
            "analysis_date": summary_row["last_updated"][:10],
        }

        if prediction_rows:
            predictions_with_dates = [
                {
                    "date_obj": date.fromisoformat(row["date"]),
                    "prediction": row["prediction"],
                    "confidence": row["confidence"],
                }
                for row in prediction_rows
            ]

            min_date = min(p["date_obj"] for p in predictions_with_dates)
            for p in predictions_with_dates:
                day_number = (p["date_obj"] - min_date).days + 1
                if 1 <= day_number <= 12:
                    core_data[f"prediction_{day_number}_day"] = p["prediction"]
                    core_data[f"confidence_{day_number}_day"] = p["confidence"]

        return jsonify({"analysis": core_data})

    except sqlite3.Error as e:
        print(f"Database error in /api/sum_analysis: {e}")
        if conn:
            conn.close()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        print(f"Unexpected error in /api/sum_analysis: {e}")
        if conn:
            conn.close()
        return jsonify({"error": "An unexpected error occurred"}), 500


@app.route("/api/historical-data", methods=["GET"])
def historical_data():
    """
    @brief Endpoint for historical stock price data.

    @return JSON response with price history or error message
    """
    ticker = request.args.get("ticker")
    start = request.args.get("start")

    try:
        start_date = datetime.strptime(start, "%Y-%m-%d")
        start_date = start_date - relativedelta(months=1)

        stock_data = yf.download(
            ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=None,
            progress=False,
        )

        if stock_data.empty:
            return jsonify([])

        # Format response
        prices = [
            {
                "date": date.strftime("%Y-%m-%d"),
                "price": float(row["Close"]),
            }
            for date, row in stock_data.iterrows()
        ]
        return jsonify(prices)

    except Exception as e:
        print(f"Error in historical-data endpoint: {e}")
        return jsonify({"error": "Failed to fetch historical data"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
