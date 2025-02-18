import os
import json

def main():
    files = os.listdir("api_data")

    known_stocks = {}

    for file in files:
        if not file.endswith(".json") or file == "known_stocks.json":
            continue
        file_path = os.path.join("api_data", file)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for dat in data:

            # Couple quick fixes to remove some cases where LLM was having a moment
            try:
                invalid_values = {"", None, "none", "null", "undefined", "unknown"}

                ticker = str(dat.get("ticker", "")).strip().lower()
                stock = str(dat.get("stock", "")).strip().lower()

                if ticker in invalid_values or stock in invalid_values:
                    continue

                # Suspicious values, LLM was probably just yapping
                if len(ticker) > 10 or len(stock) > 40:
                    continue
            except KeyError:
                continue

            ticker = dat.get("ticker", "").strip()
            company = dat.get("stock", "").strip()

            if not ticker or not company:
                continue

            if ticker not in known_stocks:
                known_stocks[ticker] = company

    # Convert dictionary to array format
    formatted_stocks = [f"{ticker} ({company})" for ticker, company in sorted(known_stocks.items())]

    with open("api_data/known_stocks.json", "w", encoding="utf-8") as f:
        json.dump(formatted_stocks, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()
