import json
import os
import re
import sqlite3
import yfinance as yf

from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from datetime import datetime, timedelta


app = Flask(__name__)
CORS(app)

# gunicorn --bind 0.0.0.0:5000 website-backend/api_server:app


def get_project_root():
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    print("ERROR: Failed to find root folder of project")
    exit(1)


def extract_ticker(company_string):
    match = re.match(r"^([A-Z]+)", company_string)
    return match.group(1) if match else None


@app.route("/api/historical-data", methods=["GET"])
def historical_data():
    ticker = request.args.get("ticker")
    published = request.args.get("published")

    try:
        published_date = datetime.strptime(published, "%Y-%m-%d")

        stock = yf.Ticker(ticker)
        historical_data = stock.history(
            start=published_date, end=published_date + timedelta(days=7)
        )

        published_price = historical_data.iloc[0]["Close"]

        price_changes = []
        for date, row in historical_data.iterrows():
            close_price = row["Close"]
            percentage_change = (close_price - published_price) / published_price
            price_changes.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "change": percentage_change,
                }
            )

        return jsonify(price_changes)
    except IndexError:
        # No data found
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stocks", methods=["GET"])
def get_stocks():
    try:
        model = request.args.get("model")
        min_articles = request.args.get("min_articles")
        print(min_articles)
        if not model or not min_articles:
            return (
                jsonify({"error": "Model and min_articles parameters are required"}),
                400,
            )

        db_path = os.path.join(get_project_root(), "data", "news.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT an.ticker, an.stock
            FROM analysis AS an
            WHERE an.model_name = ?
            GROUP BY an.ticker
            HAVING COUNT(an.ticker) >= ?
            """,
            (model, int(min_articles)),
        )

        rows = cursor.fetchall()
        conn.close()

        unique_tickers = set()
        stocks = []

        for row in rows:
            ticker = row["ticker"]
            if ticker not in unique_tickers:
                unique_tickers.add(ticker)
                stocks.append(f"{ticker} ({row['stock']})")

        # Sort alphabetically
        stocks.sort()

        return jsonify(stocks)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error"}), 500


@app.route("/api/analysis", methods=["GET"])
def get_results():
    try:
        ticker = request.args.get("ticker")
        model = request.args.get("model")

        if not ticker or not model:
            return jsonify({"error": "Ticker and model parameters are required"}), 400

        db_path = os.path.join(get_project_root(), "data", "news.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT 
                a.title, 
                a.source, 
                a.link,
                a.published, 
                an.summary,
                an.pred_1_day, 
                an.conf_1_day, 
                an.pred_2_day, 
                an.conf_2_day, 
                an.pred_3_day, 
                an.conf_3_day, 
                an.pred_4_day, 
                an.conf_4_day, 
                an.pred_5_day, 
                an.conf_5_day, 
                an.pred_6_day, 
                an.conf_6_day, 
                an.pred_7_day, 
                an.conf_7_day
            FROM 
                analysis AS an
            JOIN 
                articles AS a ON an.article_id = a.id
            WHERE 
                an.ticker = ? AND an.model_name = ?
        """
        cursor.execute(query, (ticker, model))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            entry = {
                "title": row["title"],
                "source": row["source"],
                "link": row["link"],
                "published": row["published"],
                "summary": row["summary"],
                "ticker": ticker,
                "predictions": {
                    "1_day": {
                        "prediction": row["pred_1_day"],
                        "confidence": row["conf_1_day"],
                    },
                    "2_day": {
                        "prediction": row["pred_2_day"],
                        "confidence": row["conf_2_day"],
                    },
                    "3_day": {
                        "prediction": row["pred_3_day"],
                        "confidence": row["conf_3_day"],
                    },
                    "4_day": {
                        "prediction": row["pred_4_day"],
                        "confidence": row["conf_4_day"],
                    },
                    "5_day": {
                        "prediction": row["pred_5_day"],
                        "confidence": row["conf_5_day"],
                    },
                    "6_day": {
                        "prediction": row["pred_6_day"],
                        "confidence": row["conf_6_day"],
                    },
                    "7_day": {
                        "prediction": row["pred_7_day"],
                        "confidence": row["conf_7_day"],
                    },
                },
            }
            results.append(entry)

        return jsonify(results)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
