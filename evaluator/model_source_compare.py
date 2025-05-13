import json
import os
import glob
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import shutil
import argparse

# Global variables to store metrics
model_metrics = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
source_metrics = defaultdict(lambda: {"errors": [], "count": 0})


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Compare models and sources with optional day limit and minimum datapoints"
    )
    parser.add_argument(
        "--max-day",
        type=int,
        default=12,
        help="Maximum day to include in analysis (1-12)",
    )
    parser.add_argument(
        "--min-datapoints",
        type=int,
        default=10,
        help="Minimum number of datapoints required to include a model or source in analysis",
    )
    return parser.parse_args()


def calculate_metrics(max_day, min_datapoints):
    """Process JSON files and calculate metrics up to specified day."""
    file_paths = glob.glob(os.path.join("data", "*.json"))
    print(f"Found {len(file_paths)} JSON files to process (days 1-{max_day})")

    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Skipping file {file_path}: {str(e)}")
            continue

        model = data.get("model")
        if model == "gemini-1.5-flash-8b":
            continue
        predictions_by_article = data.get("predictionsByArticle", [])

        if not model or not predictions_by_article:
            continue

        for article_data in predictions_by_article:
            source = article_data.get("source")
            predictions = article_data.get("predictions", {})

            if not source or not predictions:
                continue

            for date, values in predictions.items():
                prediction = values.get("prediction")
                real = values.get("real")
                day = values.get("predictionDay")

                if (
                    day is None
                    or day > max_day
                    or real is None
                    or prediction is None
                    or real == 0
                ):
                    continue

                day_key = f"day{day}"
                percentage_error = abs(prediction - real) / abs(real)

                # Model metrics
                if not model_metrics[model][day_key][source]:
                    model_metrics[model][day_key][source].update(
                        {"percentage_errors": [], "count": 0}
                    )
                model_metrics[model][day_key][source]["percentage_errors"].append(
                    percentage_error
                )
                model_metrics[model][day_key][source]["count"] += 1

                # Source metrics (aggregated across models)
                source_metrics[source]["errors"].append(percentage_error)
                source_metrics[source]["count"] += 1

    # Calculate final MAPE for models
    for model, day_data in model_metrics.items():
        for day, sources_data in day_data.items():
            for source, metrics in sources_data.items():
                if metrics and metrics["count"] > 0:
                    metrics["mape"] = np.mean(metrics["percentage_errors"]) * 100


def print_results(max_day, min_datapoints):
    """Print model and source comparison results."""
    print(
        f"\nModel and Source Comparison Results (Days 1-{max_day}, Min Datapoints: {min_datapoints})"
    )
    print("=" * 70)

    if not model_metrics and not source_metrics:
        print("No valid data processed to evaluate predictions.")
        return

    # Print source comparison
    print("\nSource Comparison (Aggregated across all models)")
    print("-" * 70)

    sorted_sources = sorted(source_metrics.items(), key=lambda item: item[0])
    for source, metrics in sorted_sources:
        if metrics["count"] >= min_datapoints:
            mape = np.mean(metrics["errors"]) * 100
            print(
                f"  Source: {source:<25} | n={metrics['count']:<7} | MAPE: {mape:>6.2f}%"
            )

    # Print model comparison
    print("\nModel Comparison (Aggregated across all sources)")
    print("-" * 70)

    model_overalls = []
    for model, day_data in sorted(model_metrics.items()):
        # Calculate model overall
        all_errors = []
        total_count = 0
        for day, sources_data in day_data.items():
            for source, metrics in sources_data.items():
                if metrics.get("count", 0) > 0:
                    all_errors.extend(metrics["percentage_errors"])
                    total_count += metrics["count"]

        if total_count >= min_datapoints:
            mape = np.mean(all_errors) * 100
            display_model = model.replace("meta-llama/", "")
            print(
                f"  Model: {display_model:<25} | n={total_count:<7} | MAPE: {mape:>6.2f}%"
            )
            model_overalls.append((display_model, mape, total_count))

    print("-" * 70)


def generate_graphs(max_day, min_datapoints):
    """Generate model and source comparison graphs."""
    output_dir = "model_source_graphs"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    print(f"\nGenerating model/source graphs in '{output_dir}/'...")

    # Generate model comparison plot
    model_data = []
    for model, day_data in sorted(model_metrics.items()):
        all_errors = []
        total_count = 0
        for day, sources_data in day_data.items():
            for source, metrics in sources_data.items():
                if metrics.get("count", 0) > 0:
                    all_errors.extend(metrics["percentage_errors"])
                    total_count += metrics["count"]

        if total_count >= min_datapoints:
            mape = np.mean(all_errors) * 100
            display_model = model.replace("meta-llama/", "")
            model_data.append((display_model, mape, total_count))

    if model_data:
        fig, ax = plt.subplots(figsize=(max(8, len(model_data) * 0.8), 6))
        model_names = [m[0] for m in model_data]
        mapes = [m[1] for m in model_data]
        counts = [m[2] for m in model_data]

        bars = ax.bar(model_names, mapes, color="coral")
        ax.set_ylabel("MAPE (%)")
        ax.set_title(
            f"Model Comparison (Days 1-{max_day}, Min Datapoints: {min_datapoints})"
        )
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=45, ha="right")

        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{height:.2f}%",
                ha="center",
                va="bottom",
            )
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                ax.get_ylim()[0] * 0.95,
                f"n={counts[i]}",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()
        plt.savefig(
            os.path.join(
                output_dir, f"model_comparison_days_1_{max_day}_min{min_datapoints}.png"
            )
        )
        plt.close(fig)

    # Generate source comparison plot
    sorted_sources = sorted(source_metrics.items(), key=lambda item: item[0])
    sources = [s[0] for s in sorted_sources if s[1]["count"] >= min_datapoints]
    mapes = [
        np.mean(s[1]["errors"]) * 100
        for s in sorted_sources
        if s[1]["count"] >= min_datapoints
    ]
    counts = [s[1]["count"] for s in sorted_sources if s[1]["count"] >= min_datapoints]

    if sources:
        fig_width = max(10, len(sources) * 0.7)
        fig, ax = plt.subplots(figsize=(fig_width, 7))

        bars = ax.bar(sources, mapes, color="skyblue")
        ax.set_ylabel("MAPE (%)")
        ax.set_title(
            f"Source Comparison (Days 1-{max_day}, Min Datapoints: {min_datapoints})"
        )
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=90, ha="center")

        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{height:.2f}%",
                ha="center",
                va="bottom",
            )
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                ax.get_ylim()[0] * 0.95,
                f"n={counts[i]}",
                ha="center",
                va="bottom",
            )

        plt.subplots_adjust(bottom=0.35)
        plt.tight_layout()
        plt.savefig(
            os.path.join(
                output_dir,
                f"source_comparison_days_1_{max_day}_min{min_datapoints}.png",
            )
        )
        plt.close(fig)


def main():
    args = parse_arguments()
    max_day = args.max_day
    min_datapoints = args.min_datapoints

    data_dir = "data"
    if not os.path.isdir(data_dir):
        print(f"Error: '{data_dir}' directory not found.")
        return

    calculate_metrics(max_day, min_datapoints)
    print_results(max_day, min_datapoints)
    generate_graphs(max_day, min_datapoints)


if __name__ == "__main__":
    main()
