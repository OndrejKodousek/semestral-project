import json
import os


files = os.listdir("data")
input_file_paths = []
for file in files:
    filepath = "data/" + file
    input_file_paths.append(filepath)


for input_path in input_file_paths:
    with open(input_path, "r") as f:
        data = json.load(f)

    ticker = data.get("ticker", "N/A")

    model_name = data.get("modelUsedForSumAnalysis", "N/A")
    labels = data.get("labels", [])
    datasets = data.get("datasets", {})
    real_changes = datasets.get("realPercentageChange", [])

    valid_real_data = {}
    dates_with_real_data = set()
    for date, real_value in zip(labels, real_changes):
        if real_value is not None:
            valid_real_data[date] = real_value
            dates_with_real_data.add(date)

    filtered_predictions_by_source = []
    original_predictions = datasets.get("predictionsBySource", [])

    # Individual articles
    for source_pred in original_predictions:
        predictions = 0
        source_name = source_pred.get("source", "Unknown Source")
        original_preds_dict = source_pred.get("predictionsPercent", {})
        filtered_preds_for_source = {}

        for date, pred_value in original_preds_dict.items():
            if date in dates_with_real_data and pred_value is not None:
                filtered_preds_for_source[date] = pred_value
                predictions += 1
            if predictions >= 3:
                break

        if filtered_preds_for_source:
            filtered_predictions_by_source.append(
                {
                    "source": source_name,
                    "predictionsPercent": filtered_preds_for_source,
                }
            )

    simplified_data = {
        "ticker": ticker,
        "modelName": model_name,
        "realData": valid_real_data,
        "predictionsBySource": filtered_predictions_by_source,
    }

    base, ext = os.path.splitext(input_path)
    model_name = model_name.replace("/", "-")

    output_path = f"data_filtered/{ticker}-{model_name}.json"

    print(model_name)

    with open(output_path, "w") as f:
        json.dump(simplified_data, f, indent=2)

    print(f"Successfully created simplified file: {output_path}")


print("\n--- Processing Complete ---")
