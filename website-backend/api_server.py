import json
import os
import re
import sqlite3
import yfinance as yf
import traceback
import google.generativeai as genai
from groq import Groq, RateLimitError, APIStatusError
from openai import OpenAI
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

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


def fetch_analyzed_articles_and_predictions(model, ticker):
    db_path = os.path.join(get_project_root(), "data", "news.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT a.summary, p.date, p.prediction, p.confidence
        FROM analysis a
        JOIN predictions p ON a.id = p.analysis_id
        WHERE a.model_name = ? AND a.ticker = ?
        ORDER BY a.published DESC
        """,
        (model, ticker),
    )
    results = cursor.fetchall()

    conn.close()
    return results


def process_article_groq(article, model, system_instruction):
    file_path = os.path.join(get_project_root(), "data", "API_KEY_GROQ")
    with open(file_path, "r") as f:
        api_key = f.readline().strip()

    client = Groq(api_key=api_key)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": article["content"]},
                {"role": "system", "content": system_instruction},
            ],
            model=model,
        )
    except RateLimitError as e:
        error_details = traceback.format_exc()
        return f"ERROR-429", None
    except APIStatusError as e:
        error_details = traceback.format_exc()
        return f"ERROR-413", None
    except:
        return f"ERROR-00", None

    response_text = chat_completion.choices[0].message.content
    return None, response_text


def process_article_openrouter(article, model, system_instruction):
    file_path = os.path.join(get_project_root(), "data", "API_KEY_OPENROUTER")
    with open(file_path, "r") as f:
        api_key = f.readline().strip()

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": article["content"]},
                {"role": "system", "content": system_instruction},
            ],
            model=model,
        )
        if chat_completion.choices is None:
            error_code = str(chat_completion.error["code"])
            if error_code == "429":
                return f"ERROR-429", None
            elif error_code == "413":
                return f"ERROR-413", None
            raise TypeError
    except:
        return f"ERROR-00", None

    response_text = chat_completion.choices[0].message.content
    return None, response_text


def process_article_gemini(article, model, system_instruction):
    file_path = os.path.join(get_project_root(), "data", "API_KEY_GEMINI")
    with open(file_path, "r") as f:
        api_key = f.readline().strip()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model, system_instruction=system_instruction
    )

    try:
        response = model.generate_content([article["content"]])
        return None, response.text
    except Exception as e:
        return f"ERROR-00", str(e)


@app.route("/api/sum_analysis", methods=["GET"])
def sum_analysis():
    model = request.args.get("model")
    ticker = request.args.get("ticker")

    if not model or not ticker:
        return jsonify({"error": "Missing model or ticker parameter"}), 400

    data = fetch_analyzed_articles_and_predictions(model, ticker)
    if not data:
        return jsonify({"error": "No data found for the given model and ticker"}), 404

    analysis_data = [dict(row) for row in data]
    analysis_content = json.dumps(analysis_data)

    file_path = os.path.join(
        get_project_root(), "website-backend", "system_instruction_sum_analysis.txt"
    )
    with open(file_path, "r") as f:
        system_instruction = f.read().strip()

    if "groq" in model:
        error_code, result = process_article_groq(
            {"content": analysis_content}, model, system_instruction
        )
    elif "openrouter" in model:
        error_code, result = process_article_openrouter(
            {"content": analysis_content}, model, system_instruction
        )
    elif "gemini" in model:
        error_code, result = process_article_gemini(
            {"content": analysis_content}, model, system_instruction
        )
    else:
        return jsonify({"error": "Unsupported model"}), 400

    if error_code:
        return (
            jsonify({"error": f"Failed to analyze data with model: {error_code}"}),
            500,
        )

    try:
        json_match = re.search(r"```json\n(.*?)\n```", result, re.DOTALL)
        if json_match:
            json_content = json_match.group(1)
            analysis_dict = json.loads(json_content)
            return jsonify({"analysis": analysis_dict})
        else:
            return jsonify({"error": "Failed to extract JSON from the response"}), 500
    except json.JSONDecodeError as e:
        return jsonify({"error": f"Failed to parse JSON: {str(e)}"}), 500


@app.route("/api/historical-data", methods=["GET"])
def historical_data():
    ticker = request.args.get("ticker")
    start = request.args.get("start")

    try:
        start = datetime.strptime(start, "%Y-%m-%d")
        start = start - relativedelta(months=1)  # Workaround

        stock = yf.Ticker(ticker)
        historical_data = stock.history(start=start)

        prices = []
        for date, row in historical_data.iterrows():
            latest_day_price = row["Close"]
            prices.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "price": latest_day_price,
                }
            )
        # print(
        #     f"Ticker: {ticker}, Entries: {len(prices)}, Period: {prices[0]['date']} - {prices[-1]['date']}"
        # )
        return jsonify(prices)
    except IndexError:
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stocks", methods=["GET"])
def get_stocks():
    try:
        model = request.args.get("model")
        min_articles = request.args.get("min_articles")
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

        if len(rows) < 1:
            return jsonify({"message": "No stocks found with the given criteria"}), 200

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
                p.date,
                p.prediction,
                p.confidence
            FROM 
                analysis AS an
            JOIN 
                articles AS a ON an.article_id = a.id
            JOIN 
                predictions AS p ON an.id = p.analysis_id
            WHERE 
                an.ticker = ? AND an.model_name = ?
            ORDER BY 
                p.date
        """
        cursor.execute(query, (ticker, model))

        rows = cursor.fetchall()
        conn.close()

        results = {}
        for row in rows:
            article_id = row["link"]  # Use link as a unique identifier for the article
            if article_id not in results:
                results[article_id] = {
                    "title": row["title"],
                    "source": row["source"],
                    "link": row["link"],
                    "published": row["published"],
                    "summary": row["summary"],
                    "ticker": ticker,
                    "predictions": {},
                }

            # Add prediction for the specific date
            date = row["date"]
            results[article_id]["predictions"][date] = {
                "prediction": row["prediction"],
                "confidence": row["confidence"],
            }

        results_list = list(results.values())

        return jsonify(results_list)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
