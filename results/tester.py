import json
import math
import pandas as pd

# Define file paths (adjust if necessary)
file_paths = [
    "data/LMT-gemini-2.5-flash-preview-04-17-2025-04-28T16-35-36-892Z.json",
]


# Define evaluation metrics functions
def calculate_mae(actual, predicted):
    """Calculates Mean Absolute Error."""
    errors = [
        abs(a - p) for a, p in zip(actual, predicted) if a is not None and p is not None
    ]
    return sum(errors) / len(errors) if errors else None


def calculate_rmse(actual, predicted):
    """Calculates Root Mean Squared Error."""
    squared_errors = [
        (a - p) ** 2
        for a, p in zip(actual, predicted)
        if a is not None and p is not None
    ]
    return (
        math.sqrt(sum(squared_errors) / len(squared_errors)) if squared_errors else None
    )


def calculate_directional_accuracy(actual, predicted):
    """Calculates Directional Accuracy based on SIGN of cumulative values."""
    correct_sign = 0
    total_comparisons = 0
    for a, p in zip(actual, predicted):
        # Only compare if both values are valid numbers
        if a is not None and p is not None:
            total_comparisons += 1
            # Check if prediction and actual have the same sign (or both are zero)
            if (a > 0 and p > 0) or (a < 0 and p < 0) or (a == 0 and p == 0):
                correct_sign += 1
    return (correct_sign / total_comparisons * 100) if total_comparisons > 0 else None


# --- Main Processing Loop ---
all_results = []

for file_path in file_paths:
    print(f"\n--- Processing File: {file_path} ---")
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        ticker = data.get("ticker", "N/A")
        labels = data.get("labels", [])
        datasets = data.get("datasets", {})
        real_changes = datasets.get("realPercentageChange", [])

        # Create a DataFrame for real data
        real_df = pd.DataFrame({"Date": labels, "RealChange": real_changes})
        real_df["Date"] = pd.to_datetime(real_df["Date"])
        real_df.set_index("Date", inplace=True)
        # Ensure data is sorted by date for directional accuracy calculation
        real_df.sort_index(inplace=True)

        # --- Evaluate Individual Source Predictions ---
        predictions_by_source = datasets.get("predictionsBySource", [])
        print(
            f"\nEvaluating {len(predictions_by_source)} individual sources for {ticker}:"
        )
        for i, source_pred in enumerate(predictions_by_source):
            source_name = source_pred.get("source", f"Unknown Source {i+1}")
            predictions_dict = source_pred.get("predictionsPercent", {})

            pred_df = pd.DataFrame(
                list(predictions_dict.items()), columns=["Date", "Prediction"]
            )
            pred_df["Date"] = pd.to_datetime(pred_df["Date"])
            pred_df.set_index("Date", inplace=True)
            pred_df.sort_index(inplace=True)  # Sort prediction dates

            merged_df = real_df.join(pred_df, how="inner")
            # Drop rows where either real or prediction is initially null for MAE/RMSE
            eval_df = merged_df.dropna()

            if not eval_df.empty:
                actual_vals = eval_df["RealChange"].tolist()
                predicted_vals = eval_df["Prediction"].tolist()

                mae = calculate_mae(actual_vals, predicted_vals)
                rmse = calculate_rmse(actual_vals, predicted_vals)

                # For directional accuracy, use the full merged df (before dropna)
                # as we need consecutive points, even if one intermediate point was NaN
                dir_acc_actual = merged_df["RealChange"].tolist()
                dir_acc_predicted = merged_df["Prediction"].tolist()
                dir_acc = calculate_directional_accuracy(
                    dir_acc_actual, dir_acc_predicted
                )

                result = {
                    "Ticker": ticker,
                    "Source": f"{source_name} (Source {i+1})",
                    "Type": "Individual",
                    "MAE": mae,
                    "RMSE": rmse,
                    "Directional Accuracy (%)": dir_acc,
                    "Data Points Compared": len(eval_df),  # Points used for MAE/RMSE
                }
                all_results.append(result)
            # else:
            # print(f"  {source_name} (Source {i+1}): No overlapping data points found for MAE/RMSE evaluation.")

        # --- Evaluate Summarized Analysis ---
        summarized_analysis = datasets.get("summarizedAnalysis", {})
        if summarized_analysis and "predictionsPercent" in summarized_analysis:
            print(f"\nEvaluating Summarized Analysis for {ticker}:")
            summary_preds = summarized_analysis["predictionsPercent"]
            pred_df = pd.DataFrame(
                list(summary_preds.items()), columns=["Date", "Prediction"]
            )
            pred_df["Date"] = pd.to_datetime(pred_df["Date"])
            pred_df.set_index("Date", inplace=True)
            pred_df.sort_index(inplace=True)
            merged_df = real_df.join(pred_df, how="inner")
            eval_df = merged_df.dropna()

            if not eval_df.empty:
                actual_vals = eval_df["RealChange"].tolist()
                predicted_vals = eval_df["Prediction"].tolist()
                mae = calculate_mae(actual_vals, predicted_vals)
                rmse = calculate_rmse(actual_vals, predicted_vals)
                dir_acc_actual = merged_df["RealChange"].tolist()
                dir_acc_predicted = merged_df["Prediction"].tolist()
                dir_acc = calculate_directional_accuracy(
                    dir_acc_actual, dir_acc_predicted
                )
                result = {
                    "Ticker": ticker,
                    "Source": "Summarized Analysis",
                    "Type": "Summary",
                    "MAE": mae,
                    "RMSE": rmse,
                    "Directional Accuracy (%)": dir_acc,
                    "Data Points Compared": len(eval_df),
                }
                all_results.append(result)
            # else:
            # print("  Summarized Analysis: No overlapping data points found for MAE/RMSE.")

        # --- Evaluate LSTM Analysis ---
        lstm_analysis = datasets.get("lstmAnalysis", {})
        if lstm_analysis and "predictionsPercent" in lstm_analysis:
            print(f"\nEvaluating LSTM Analysis for {ticker}:")
            lstm_preds = lstm_analysis["predictionsPercent"]
            pred_df = pd.DataFrame(
                list(lstm_preds.items()), columns=["Date", "Prediction"]
            )
            pred_df["Date"] = pd.to_datetime(pred_df["Date"])
            pred_df.set_index("Date", inplace=True)
            pred_df.sort_index(inplace=True)
            merged_df = real_df.join(pred_df, how="inner")
            eval_df = merged_df.dropna()

            if not eval_df.empty:
                actual_vals = eval_df["RealChange"].tolist()
                predicted_vals = eval_df["Prediction"].tolist()
                mae = calculate_mae(actual_vals, predicted_vals)
                rmse = calculate_rmse(actual_vals, predicted_vals)
                dir_acc_actual = merged_df["RealChange"].tolist()
                dir_acc_predicted = merged_df["Prediction"].tolist()
                dir_acc = calculate_directional_accuracy(
                    dir_acc_actual, dir_acc_predicted
                )
                result = {
                    "Ticker": ticker,
                    "Source": "LSTM Analysis",
                    "Type": "LSTM",
                    "MAE": mae,
                    "RMSE": rmse,
                    "Directional Accuracy (%)": dir_acc,
                    "Data Points Compared": len(eval_df),
                }
                all_results.append(result)
            # else:
            # print("  LSTM Analysis: No overlapping data points found for MAE/RMSE.")

    except FileNotFoundError:
        print(f"Error: File not found - {file_path}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
    except Exception as e:
        print(f"An unexpected error occurred processing {file_path}: {e}")


# --- Display Combined Results ---
if all_results:
    results_df = pd.DataFrame(all_results)
    results_df.sort_values(by=["Ticker", "Type", "RMSE"], inplace=True)
    pd.options.display.float_format = "{:.4f}".format
    print("\n\n--- Combined Evaluation Results ---")
    # Ensure Directional Accuracy is formatted nicely, handling None
    results_df["Directional Accuracy (%)"] = results_df[
        "Directional Accuracy (%)"
    ].apply(lambda x: f"{x:.2f}" if x is not None else "N/A")
    print(results_df.to_string(index=False))
else:
    print("\nNo evaluation results were generated.")
