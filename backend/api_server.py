import json
import os
import re

from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def extract_ticker(company_string):
    match = re.match(r"^([A-Z]+)", company_string)
    return match.group(1) if match else None

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    try:
        with open("api_data/known_stocks.json", 'r') as file:
            stock_names = json.load(file)
        return jsonify(stock_names)
    except FileNotFoundError:
        print("Error: The file 'api_data/known_stocks.json' was not found.")
        return jsonify([])
    except json.JSONDecodeError:
        print("Error: The file 'api_data/known_stocks.json' contains invalid JSON.")
        return jsonify([])

@app.route('/api/update', methods=['POST'])
def get_results():

    data = request.get_json()

    ticker = extract_ticker(data.get("ticker")) # Original is in NVDA (NVIDIA Corp)
    time = data.get("time") # TODO
    model = data.get("model")

    if time == "1" or time == 1:
        key_prediction = "prediction_1_day"
        key_confidence = "prediction_1_day_confidence"
    elif time == "3" or time == 3:
        key_prediction = "prediction_3_day"
        key_confidence = "prediction_3_day_confidence"
    elif time == "7" or time == 7:
        key_prediction = "prediction_7_day"
        key_confidence = "prediction_7_day_confidence"
    else:
        # TODO: Error handling
        return None

    filepath = f"api_data/processed_articles_{model}.json"

    try:
        with open(filepath, 'r') as file:
            parsed_data = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: The file '{filepath}' contains invalid JSON.")
        return []

    results = []

    if parsed_data:
        for article in parsed_data:

            if article['ticker'] != ticker:
                continue
            
            entry = {
              "title": article['title'],
              "source": article['source'],
              "prediction": article[key_prediction],
              "confidence": article[key_confidence],
              "link": article['link']
            }
            results.append(entry)

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
