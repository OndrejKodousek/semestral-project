import json
import os
import re
import sqlite3

from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app) 

def extract_ticker(company_string):
    match = re.match(r"^([A-Z]+)", company_string)
    return match.group(1) if match else None

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    try:
        model = request.args.get('model')
        if not model:
            return jsonify({"error": "Model parameter is required"}), 400

        conn = sqlite3.connect('data/news.db')  # Replace with your database path
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        cursor = conn.cursor()

        cursor.execute('''
              SELECT an.ticker, an.stock
              FROM analysis AS an
              WHERE an.model_name = ?
            ''', (model,))

        rows = cursor.fetchall()
        conn.close()

        # Create strings in the format "TICKER (Stock Name)"
        stocks = [f"{row['ticker']} ({row['stock']})" for row in rows]

        return jsonify(stocks)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error"}), 500



@app.route('/api/analysis', methods=['GET'])
def get_results():
    try:
        # Extract query parameters
        ticker_with_name = request.args.get('ticker')  # e.g., "BABA (Alibaba Group Holding Ltd.)"
        model = request.args.get('model')

        # Validate required parameters
        if not ticker_with_name or not model:
            return jsonify({"error": "Ticker and model parameters are required"}), 400

        # Extract the ticker symbol using regex
        ticker_match = re.match(r"^([A-Z]+)\s*\(.*\)$", ticker_with_name)
        if not ticker_match:
            return jsonify({"error": "Invalid ticker format"}), 400

        ticker = ticker_match.group(1)  # Extract "BABA" from "BABA (Alibaba Group Holding Ltd.)"
        #print(f"Extracted ticker: {ticker}")

        # Connect to the SQLite database
        conn = sqlite3.connect('data/news.db')  # Replace with your database path
        conn.row_factory = sqlite3.Row  # Allows accessing columns by name
        cursor = conn.cursor()

        # Query the database for analysis data
        query = '''
            SELECT 
                a.title, 
                a.source, 
                a.link, 
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
        '''
        cursor.execute(query, (ticker, model))

        rows = cursor.fetchall()
        conn.close()

        # Log the number of rows returned

        # Format the results
        results = []
        for row in rows:
            entry = {
                "title": row['title'],
                "source": row['source'],
                "link": row['link'],
                "predictions": {
                    "1_day": {
                        "prediction": row['pred_1_day'],
                        "confidence": row['conf_1_day']
                    },
                    "2_day": {
                        "prediction": row['pred_2_day'],
                        "confidence": row['conf_2_day']
                    },
                    "3_day": {
                        "prediction": row['pred_3_day'],
                        "confidence": row['conf_3_day']
                    },
                    "4_day": {
                        "prediction": row['pred_4_day'],
                        "confidence": row['conf_4_day']
                    },
                    "5_day": {
                        "prediction": row['pred_5_day'],
                        "confidence": row['conf_5_day']
                    },
                    "6_day": {
                        "prediction": row['pred_6_day'],
                        "confidence": row['conf_6_day']
                    },
                    "7_day": {
                        "prediction": row['pred_7_day'],
                        "confidence": row['conf_7_day']
                    }
                }
            }
            results.append(entry)

        return jsonify(results)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"error": "Unexpected error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
