import os
import json


def main():
    files = os.listdir("api_data")

    known_stocks = {}  # Dictionary to ensure unique tickers

    for file in files:
        if not file.endswith(".json") or file == "known_stocks.json":
            continue
        file_path = os.path.join("api_data", file)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for dat in data:

            # Couple few quick fixes to remove cases where LLM was having a moment
            if dat['ticker'] == "" or dat['stock'] == "":
                continue
            if dat['ticker'] == None or dat['stock'] == None:
                continue
            if dat['ticker'].lower() == "none" or dat['stock'].lower() == "none":
                continue
            if len(dat['ticker']) > 10 or len(dat['stock']) > 40:
                continue 

            ticker = dat.get("ticker", "").strip()
            company = dat.get("stock", "").strip()

            if not ticker or not company:  # Skip empty or None values
                continue

            if ticker not in known_stocks:
                known_stocks[ticker] = company

    # Convert dictionary to array format
    formatted_stocks = [f"{ticker} ({company})" for ticker, company in sorted(known_stocks.items())]

    with open("api_data/known_stocks.json", "w", encoding="utf-8") as f:
        json.dump(formatted_stocks, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
