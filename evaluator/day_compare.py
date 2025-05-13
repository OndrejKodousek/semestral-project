import json
import os
import glob
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import shutil

# Global variable to store MAPE metrics
day_metrics = defaultdict(lambda: {"errors": [], "count": 0})

days_range = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
days_keys_range = [f"day{day}" for day in days_range]


def calculate_day_metrics():
    """Process JSON files and calculate MAPE by day."""
    file_paths = glob.glob(os.path.join("data", "*.json"))
    print(f"Found {len(file_paths)} JSON files to process")

    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Skipping file {file_path}: {str(e)}")
            continue

        predictions_by_article = data.get("predictionsByArticle", [])
        if not predictions_by_article:
            continue

        for article_data in predictions_by_article:
            predictions = article_data.get("predictions", {})
            if not predictions:
                continue

            for date, values in predictions.items():
                prediction = values.get("prediction")
                real = values.get("real")
                day = values.get("predictionDay")

                if (
                    day not in days_range
                    or real is None
                    or prediction is None
                    or real == 0
                ):
                    continue

                day_key = f"day{day}"
                percentage_error = abs(prediction - real) / abs(real)
                day_metrics[day_key]["errors"].append(percentage_error)
                day_metrics[day_key]["count"] += 1


def print_day_results():
    """Print day comparison results."""
    print("\nDay Comparison Results (MAPE)")
    print("=" * 70)

    if not day_metrics:
        print("No valid data processed to evaluate predictions.")
        return

    print("\nPrediction Day Comparison (Aggregated across all models & sources)")
    print("-" * 70)

    grand_total_errors = []
    grand_total_count = 0

    for day_key in days_keys_range:
        metrics = day_metrics.get(day_key, {"errors": [], "count": 0})
        if metrics["count"] > 0:
            mape = np.mean(metrics["errors"]) * 100
            print(
                f"  Day {day_key[-1]} | n={metrics['count']:<7} | MAPE: {mape:>6.2f}%"
            )
            grand_total_errors.extend(metrics["errors"])
            grand_total_count += metrics["count"]
        else:
            print(f"  Day {day_key[-1]} | n={0:<7} | MAPE:    N/A")

    if grand_total_count > 0:
        overall_mape = np.mean(grand_total_errors) * 100
        print(
            f"\n  Overall (All Days) | n={grand_total_count:<7} | MAPE: {overall_mape:>6.2f}%"
        )
    print("-" * 70)


def generate_day_graphs():
    """Generate visualization graphs for day comparison."""
    output_dir = "day_graphs"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nGenerating day comparison graphs in '{output_dir}/'...")

    # Generate day comparison plot
    mape_by_day = []
    counts = []
    valid_days = []

    for day_key in days_keys_range:
        metrics = day_metrics.get(day_key, {"errors": [], "count": 0})
        if metrics["count"] > 0:
            mape_by_day.append(np.mean(metrics["errors"]) * 100)
            counts.append(metrics["count"])
            valid_days.append(day_key)

    if not valid_days:
        print("No valid day data to plot.")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(valid_days, mape_by_day, color="lightgreen")
    ax.set_ylabel("MAPE (%)")
    ax.set_title("Day Comparison - MAPE (Aggregated across all models & sources)")
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Add text labels
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.2f}%",
            ha="center",
            va="bottom",
            fontsize=9,
        )
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            ax.get_ylim()[0] * 0.95,
            f"n={counts[i]}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "day_comparison_mape.png"))
    plt.close(fig)


def main():
    data_dir = "data"
    if not os.path.isdir(data_dir):
        print(f"Error: '{data_dir}' directory not found.")
        return

    calculate_day_metrics()
    print_day_results()
    generate_day_graphs()


if __name__ == "__main__":
    main()
