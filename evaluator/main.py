import json
import os
import glob
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import argparse
from matplotlib.ticker import MaxNLocator


class PredictionAnalyzer:
    def __init__(self):
        self.day_metrics = defaultdict(lambda: {"errors": [], "count": 0})
        self.model_day_metrics = defaultdict(lambda: defaultdict(list))
        self.source_day_metrics = defaultdict(lambda: defaultdict(list))
        self.model_counts = defaultdict(lambda: defaultdict(int))
        self.source_counts = defaultdict(lambda: defaultdict(int))
        self.model_overall = defaultdict(list)
        self.source_overall = defaultdict(list)
        self.ticker_metrics = defaultdict(lambda: defaultdict(list))

    def load_data(
        self, data_dir, max_day=12, min_articles_per_source=1, max_include_day=3
    ):
        """Load and process all JSON files in the data directory."""
        file_paths = glob.glob(os.path.join(data_dir, "*.json"))
        print(f"Found {len(file_paths)} JSON files to process")

        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Skipping file {file_path}: {str(e)}")
                continue

            model = data.get("model")
            if model == "gemini-1.5-flash-8b":
                continue  # Skip this model as in original scripts

            # Extract ticker from filename (e.g., "META_gemini-1.5-flash_2025-05-13.json")
            ticker = os.path.basename(file_path).split("_")[0]
            predictions_by_article = data.get("predictionsByArticle", [])

            if not model or not predictions_by_article:
                continue

            for article_data in predictions_by_article:
                source = article_data.get("source")
                predictions = article_data.get("predictions", {})

                if (
                    not source
                    or not predictions
                    or len(predictions) < min_articles_per_source
                ):
                    continue

                for date, values in predictions.items():
                    prediction = values.get("prediction")
                    real = values.get("real")
                    day = values.get("predictionDay")

                    if (
                        day is None
                        or day < 1
                        or day > max_day
                        or real is None
                        or prediction is None
                        or real == 0
                        or day > max_include_day
                    ):  # New condition to filter by max_include_day
                        continue

                    percentage_error = abs(prediction - real) / abs(real)

                    # Track metrics by day (all models/sources)
                    self.day_metrics[day]["errors"].append(percentage_error)
                    self.day_metrics[day]["count"] += 1

                    # Track metrics by model and day
                    self.model_day_metrics[model][day].append(percentage_error)
                    self.model_counts[model][day] += 1
                    self.model_overall[model].append(percentage_error)

                    # Track metrics by source and day
                    self.source_day_metrics[source][day].append(percentage_error)
                    self.source_counts[source][day] += 1
                    self.source_overall[source].append(percentage_error)

                    # Track metrics by ticker
                    self.ticker_metrics[ticker][day].append(percentage_error)

    def plot_accuracy_over_time(self, min_datapoints=10, output_dir="graphs"):
        """Create the primary graph showing accuracy degradation over time."""
        os.makedirs(output_dir, exist_ok=True)

        days = sorted(self.day_metrics.keys())
        if not days:
            print("No day data to plot.")
            return

        # Calculate overall MAPE by day
        day_mape = []
        day_counts = []
        for day in days:
            if self.day_metrics[day]["count"] >= min_datapoints:
                day_mape.append(np.mean(self.day_metrics[day]["errors"]) * 100)
                day_counts.append(self.day_metrics[day]["count"])
            else:
                day_mape.append(np.nan)
                day_counts.append(0)

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(
            days, day_mape, marker="o", linestyle="-", color="b", label="All Models"
        )

        # Add count annotations
        for i, day in enumerate(days):
            if day_counts[i] > 0:
                ax.text(
                    day,
                    day_mape[i],
                    f"n={day_counts[i]}",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        ax.set_xlabel("Prediction Day")
        ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
        ax.set_title("Prediction Accuracy Degradation Over Time")
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "accuracy_over_time.png"))
        plt.close()

    def plot_model_accuracy_over_time(self, min_datapoints=10, output_dir="graphs"):
        """Create line plot showing accuracy over time for each model."""
        os.makedirs(output_dir, exist_ok=True)

        days = sorted(self.day_metrics.keys())
        if not days:
            print("No model-day data to plot.")
            return

        # Filter models with sufficient data
        valid_models = [
            model
            for model in self.model_day_metrics
            if sum(self.model_counts[model].values()) >= min_datapoints
        ]

        if not valid_models:
            print("No models meet the minimum datapoint requirement.")
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        for model in sorted(valid_models):
            model_mape = []
            model_counts = []
            for day in days:
                if (
                    day in self.model_day_metrics[model]
                    and len(self.model_day_metrics[model][day]) >= min_datapoints
                ):
                    model_mape.append(np.mean(self.model_day_metrics[model][day]) * 100)
                    model_counts.append(len(self.model_day_metrics[model][day]))
                else:
                    model_mape.append(np.nan)
                    model_counts.append(0)

            display_name = model.replace("meta-llama/", "")
            line = ax.plot(
                days, model_mape, marker="o", linestyle="-", label=display_name
            )

            # Add count annotations
            for i, day in enumerate(days):
                if model_counts[i] > 0:
                    ax.text(
                        day,
                        model_mape[i],
                        f"n={model_counts[i]}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        color=line[0].get_color(),
                    )

        ax.set_xlabel("Prediction Day")
        ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
        ax.set_title(f"Model Accuracy Over Time (Min {min_datapoints} datapoints)")
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "model_accuracy_over_time.png"))
        plt.close()

    def plot_source_accuracy_over_time(self, min_datapoints=10, output_dir="graphs"):
        """Create line plot showing accuracy over time for each source."""
        os.makedirs(output_dir, exist_ok=True)

        days = sorted(self.day_metrics.keys())
        if not days:
            print("No source-day data to plot.")
            return

        # Filter sources with sufficient data
        valid_sources = [
            source
            for source in self.source_day_metrics
            if sum(self.source_counts[source].values()) >= min_datapoints
        ]

        if not valid_sources:
            print("No sources meet the minimum datapoint requirement.")
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        for source in sorted(valid_sources):
            source_mape = []
            source_counts = []
            for day in days:
                if (
                    day in self.source_day_metrics[source]
                    and len(self.source_day_metrics[source][day]) >= min_datapoints
                ):
                    source_mape.append(
                        np.mean(self.source_day_metrics[source][day]) * 100
                    )
                    source_counts.append(len(self.source_day_metrics[source][day]))
                else:
                    source_mape.append(np.nan)
                    source_counts.append(0)

            line = ax.plot(days, source_mape, marker="o", linestyle="-", label=source)

            # Add count annotations
            for i, day in enumerate(days):
                if source_counts[i] > 0:
                    ax.text(
                        day,
                        source_mape[i],
                        f"n={source_counts[i]}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                        color=line[0].get_color(),
                    )

        ax.set_xlabel("Prediction Day")
        ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
        ax.set_title(f"Source Accuracy Over Time (Min {min_datapoints} datapoints)")
        ax.grid(True, linestyle="--", alpha=0.7)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "source_accuracy_over_time.png"))
        plt.close()

    def plot_model_comparison(self, min_datapoints=10, output_dir="graphs"):
        """Create bar chart comparing model accuracy."""
        os.makedirs(output_dir, exist_ok=True)

        # Calculate overall MAPE for each model
        model_stats = []
        for model, errors in self.model_overall.items():
            if len(errors) >= min_datapoints:
                mape = np.mean(errors) * 100
                display_name = model.replace("meta-llama/", "")
                model_stats.append((display_name, mape, len(errors)))

        if not model_stats:
            print("No models meet the minimum datapoint requirement.")
            return

        # Sort by MAPE
        model_stats.sort(key=lambda x: x[1])
        model_names = [m[0] for m in model_stats]
        model_mapes = [m[1] for m in model_stats]
        model_counts = [m[2] for m in model_stats]

        # Create figure
        fig, ax = plt.subplots(figsize=(max(10, len(model_names) * 0.7), 6))
        bars = ax.bar(model_names, model_mapes, color="skyblue")

        # Add value labels
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.2f}%",
                ha="center",
                va="bottom",
            )
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                ax.get_ylim()[0] * 0.95,
                f"n={model_counts[i]}",
                ha="center",
                va="bottom",
            )

        ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
        ax.set_title(f"Model Accuracy Comparison (Min {min_datapoints} datapoints)")
        plt.xticks(rotation=45, ha="right")
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "model_comparison.png"))
        plt.close()

    def plot_source_comparison(self, min_datapoints=10, output_dir="graphs"):
        """Create bar chart comparing source accuracy."""
        os.makedirs(output_dir, exist_ok=True)

        # Calculate overall MAPE for each source
        source_stats = []
        for source, errors in self.source_overall.items():
            if len(errors) >= min_datapoints:
                mape = np.mean(errors) * 100
                source_stats.append((source, mape, len(errors)))

        if not source_stats:
            print("No sources meet the minimum datapoint requirement.")
            return

        # Sort by MAPE
        source_stats.sort(key=lambda x: x[1])
        source_names = [s[0] for s in source_stats]
        source_mapes = [s[1] for s in source_stats]
        source_counts = [s[2] for s in source_stats]

        # Create figure
        fig, ax = plt.subplots(figsize=(max(10, len(source_names) * 0.7), 6))
        bars = ax.bar(source_names, source_mapes, color="lightgreen")

        # Add value labels
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.2f}%",
                ha="center",
                va="bottom",
            )
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                ax.get_ylim()[0] * 0.95,
                f"n={source_counts[i]}",
                ha="center",
                va="bottom",
            )

        ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
        ax.set_title(f"Source Accuracy Comparison (Min {min_datapoints} datapoints)")
        plt.xticks(rotation=90, ha="center")
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        plt.subplots_adjust(bottom=0.4)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "source_comparison.png"))
        plt.close()

    def print_summary_stats(self, min_datapoints=10):
        """Print summary statistics to console."""
        print("\nSummary Statistics")
        print("=" * 70)

        # Model statistics
        print("\nModel Performance:")
        print("-" * 70)
        model_stats = []
        for model, errors in self.model_overall.items():
            if len(errors) >= min_datapoints:
                mape = np.mean(errors) * 100
                display_name = model.replace("meta-llama/", "")
                model_stats.append((display_name, mape, len(errors)))

        for name, mape, count in sorted(model_stats, key=lambda x: x[1]):
            print(f"  {name:<25} | MAPE: {mape:>6.2f}% | n: {count:<5}")

        # Source statistics
        print("\nSource Performance:")
        print("-" * 70)
        source_stats = []
        for source, errors in self.source_overall.items():
            if len(errors) >= min_datapoints:
                mape = np.mean(errors) * 100
                source_stats.append((source, mape, len(errors)))

        for source, mape, count in sorted(source_stats, key=lambda x: x[1]):
            print(f"  {source:<25} | MAPE: {mape:>6.2f}% | n: {count:<5}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze prediction accuracy across models and sources"
    )
    parser.add_argument(
        "--data-dir", type=str, default="data", help="Directory containing JSON files"
    )
    parser.add_argument(
        "--max-day",
        type=int,
        default=12,
        help="Maximum prediction day to analyze (1-12)",
    )
    parser.add_argument(
        "--max-include-day",
        type=int,
        default=3,
        help="Maximum day to include in analysis (1-12)",
    )
    parser.add_argument(
        "--min-datapoints",
        type=int,
        default=10,
        help="Minimum number of datapoints required for inclusion",
    )
    parser.add_argument(
        "--min-articles",
        type=int,
        default=1,
        help="Minimum number of articles required per source",
    )
    args = parser.parse_args()

    analyzer = PredictionAnalyzer()
    analyzer.load_data(
        args.data_dir, args.max_day, args.min_articles, args.max_include_day
    )
    analyzer.print_summary_stats(args.min_datapoints)

    if args.max_include_day == 12:
        analyzer.plot_accuracy_over_time(args.min_datapoints)
        analyzer.plot_model_accuracy_over_time(args.min_datapoints)
        analyzer.plot_source_accuracy_over_time(args.min_datapoints)
    analyzer.plot_model_comparison(args.min_datapoints)
    analyzer.plot_source_comparison(args.min_datapoints)


if __name__ == "__main__":
    main()


# python main.py --max-day 12 --max-include-day 12 --min-datapoints 100 --min-articles 10
