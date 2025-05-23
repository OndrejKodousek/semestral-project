#!/usr/bin/env python3
"""
@file prediction_analysis.py
@brief Analyze prediction accuracy across models, sources, and tickers
@details This script processes JSON prediction files to generate:
         - Accuracy trends over time
         - Model/source performance comparisons
         - Detailed CSV tables of metrics
"""

import json
import os
import glob
import csv
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import argparse
from matplotlib.ticker import MaxNLocator


def load_data(data_dir, max_day=12, min_articles_per_source=1):
    """
    @brief Load and process prediction data from JSON files
    @param data_dir Directory containing JSON prediction files
    @param max_day Maximum prediction day to include in analysis
    @param min_articles_per_source Minimum articles required per source
    @return Dictionary containing processed metrics
    """
    print(f"Processing JSON files in {data_dir}...")

    day_metrics = defaultdict(lambda: {"errors": [], "count": 0})
    model_day_metrics = defaultdict(lambda: defaultdict(list))
    source_day_metrics = defaultdict(lambda: defaultdict(list))
    model_counts = defaultdict(lambda: defaultdict(int))
    source_counts = defaultdict(lambda: defaultdict(int))
    model_overall = defaultdict(list)
    source_overall = defaultdict(list)
    ticker_metrics = defaultdict(lambda: defaultdict(list))
    source_article_counts = defaultdict(int)
    source_valid_articles = defaultdict(set)

    file_paths = glob.glob(os.path.join(data_dir, "*.json"))
    print(f"Found {len(file_paths)} JSON files")

    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Skipping {os.path.basename(file_path)}: {str(e)}")
            continue

        model = data.get("model")

        ticker = os.path.basename(file_path).split("_")[0]
        predictions_by_article = data.get("predictionsByArticle", [])

        if not model or not predictions_by_article:
            continue

        for article_data in predictions_by_article:
            source = article_data.get("source")
            article_date = article_data.get(
                "articleDate"
            )  # Using date as article identifier
            predictions = article_data.get("predictions", {})

            if not source or not predictions:
                continue

            # Check if article has at least one valid prediction with real data
            has_valid_prediction = any(
                day_pred.get("real") is not None for day_pred in predictions.values()
            )

            if has_valid_prediction:
                # Use source + article_date as unique article identifier
                article_id = f"{source}_{article_date}"
                source_valid_articles[source].add(article_id)

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
                ):
                    continue

                percentage_error = abs(prediction - real) / abs(real)

                # Track metrics by day (all models/sources)
                day_metrics[day]["errors"].append(percentage_error)
                day_metrics[day]["count"] += 1

                # Track metrics by model and day
                model_day_metrics[model][day].append(percentage_error)
                model_counts[model][day] += 1
                model_overall[model].append(percentage_error)

                # Track metrics by source and day
                source_day_metrics[source][day].append(percentage_error)
                source_counts[source][day] += 1
                source_overall[source].append(percentage_error)

                # Track metrics by ticker
                ticker_metrics[ticker][day].append(percentage_error)

    # Count valid articles per source
    for source, articles in source_valid_articles.items():
        source_article_counts[source] = len(articles)

    return {
        "day_metrics": day_metrics,
        "model_day_metrics": model_day_metrics,
        "source_day_metrics": source_day_metrics,
        "model_counts": model_counts,
        "source_counts": source_counts,
        "model_overall": model_overall,
        "source_overall": source_overall,
        "ticker_metrics": ticker_metrics,
        "source_article_counts": source_article_counts,
    }


def plot_accuracy_over_time(data, max_day, min_datapoints=10, output_dir="graphs"):
    """
    @brief Plot overall prediction MAPE degradation over time
    @param data Processed metrics dictionary
    @param max_day Maximum prediction day to plot
    @param min_datapoints Minimum samples required per day
    @param output_dir Directory to save output graphs
    """
    os.makedirs(output_dir, exist_ok=True)
    day_metrics = data["day_metrics"]

    days = sorted(day for day in day_metrics.keys() if day <= max_day)
    if not days:
        print("No day data to plot.")
        return

    # Calculate overall MAPE by day
    day_mape = []
    day_counts = []
    for day in days:
        if day_metrics[day]["count"] >= min_datapoints:
            day_mape.append(np.mean(day_metrics[day]["errors"]) * 100)
            day_counts.append(day_metrics[day]["count"])
        else:
            day_mape.append(np.nan)
            day_counts.append(0)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(days, day_mape, marker="o", linestyle="-", color="b", label="All Models")

    ax.set_xlabel("Prediction Day")
    ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
    ax.set_title(
        f"Prediction MAPE Over Time (Days 1-{max_day}, Min {min_datapoints} samples/day)"
    )
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # Set axes to start at 0
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "accuracy_over_time.png"))
    plt.savefig(os.path.join(output_dir, "accuracy_over_time.pdf"))
    plt.close()


def plot_model_accuracy_over_time(
    data, max_day, min_datapoints=10, output_dir="graphs"
):
    """
    @brief Plot MAPE trends for individual models over time
    @param data Processed metrics dictionary
    @param max_day Maximum prediction day to plot
    @param min_datapoints Minimum samples required per day
    @param output_dir Directory to save output graphs
    """
    os.makedirs(output_dir, exist_ok=True)
    model_day_metrics = data["model_day_metrics"]
    model_counts = data["model_counts"]
    day_metrics = data["day_metrics"]

    days = sorted(day for day in day_metrics.keys() if day <= max_day)
    if not days:
        print("No model-day data to plot.")
        return

    # Filter models with sufficient data
    valid_models = [
        model
        for model in model_day_metrics
        if sum(model_counts[model].values()) >= min_datapoints
    ]

    if not valid_models:
        print("No models meet the minimum datapoint requirement.")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    for model in sorted(valid_models):

        model_mape = []
        valid_days = []
        for day in days:
            if (
                day in model_day_metrics[model]
                and len(model_day_metrics[model][day]) >= min_datapoints
            ):
                model_mape.append(np.mean(model_day_metrics[model][day]) * 100)
                valid_days.append(day)

        display_name = model.replace("meta-llama/", "")
        ax.plot(valid_days, model_mape, marker="2", linestyle="-", label=display_name)

    ax.set_xlabel("Prediction Day")
    ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
    ax.set_title(
        f"Model MAPE Over Time (Days 1-{max_day}, Min {min_datapoints} samples/day)"
    )
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # Set axes to start at 0
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    # Move legend inside plot at bottom right
    ax.legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "model_accuracy_over_time.png"))
    plt.savefig(os.path.join(output_dir, "model_accuracy_over_time.pdf"))
    plt.close()


def plot_source_accuracy_over_time(
    data, max_day, min_datapoints=10, output_dir="graphs"
):
    """
    @brief Plot MAPE trends for individual sources over time
    @param data Processed metrics dictionary
    @param max_day Maximum prediction day to plot
    @param min_datapoints Minimum samples required per day
    @param output_dir Directory to save output graphs
    """
    os.makedirs(output_dir, exist_ok=True)
    source_day_metrics = data["source_day_metrics"]
    source_counts = data["source_counts"]
    source_article_counts = data["source_article_counts"]
    day_metrics = data["day_metrics"]

    days = sorted(day for day in day_metrics.keys() if day <= max_day)
    if not days:
        print("No source-day data to plot.")
        return

    # Filter sources with sufficient data and at least one valid day
    valid_sources = []
    for source in source_day_metrics:
        valid_days = [
            day
            for day in days
            if (
                day in source_day_metrics[source]
                and len(source_day_metrics[source][day]) >= min_datapoints
            )
        ]
        if valid_days:
            article_count = source_article_counts.get(source, 0)
            valid_sources.append((source, valid_days, article_count))

    if not valid_sources:
        print("No sources meet the minimum datapoint requirement.")
        return

    fig, ax = plt.subplots(figsize=(12, 6))

    for source, valid_days, article_count in sorted(valid_sources, key=lambda x: x[0]):
        source_mape = []
        for day in valid_days:
            source_mape.append(np.mean(source_day_metrics[source][day]) * 100)

        # Add article count to label
        ax.plot(
            valid_days,
            source_mape,
            marker=".",
            linestyle="-",
            label=f"{source} (articles={article_count})",
        )

    ax.set_xlabel("Prediction Day")
    ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
    ax.set_title(
        f"Source MAPE Over Time (Days 1-{max_day}, Min {min_datapoints} samples/day)"
    )
    ax.grid(True, linestyle="--", alpha=0.7)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    # Set axes to start at 0
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)

    # Move legend inside plot at bottom right
    ax.legend(loc="lower right")

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "source_accuracy_over_time.png"))
    plt.savefig(os.path.join(output_dir, "source_accuracy_over_time.pdf"))
    plt.close()


def plot_model_comparison(data, max_day, min_datapoints=10, output_dir="graphs"):
    """
    @brief Generate bar chart comparing overall model MAPE
    @param data Processed metrics dictionary
    @param max_day Maximum prediction day included
    @param min_datapoints Minimum samples required per model
    @param output_dir Directory to save output graphs
    """
    os.makedirs(output_dir, exist_ok=True)
    model_overall = data["model_overall"]

    # Calculate overall MAPE for each model
    model_stats = []
    for model, errors in model_overall.items():
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

    fig, ax = plt.subplots(figsize=(max(10, len(model_names) * 0.7), 6))
    bars = ax.bar(model_names, model_mapes, color="skyblue")

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
    ax.set_title(
        f"Model MAPE Comparison (Days 1-{max_day}, Min {min_datapoints} samples)"
    )
    plt.xticks(rotation=45, ha="right")
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Set y-axis to start at 0
    ax.set_ylim(bottom=0)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "model_comparison.png"))
    plt.savefig(os.path.join(output_dir, "model_comparison.pdf"))
    plt.close()


def plot_source_comparison(data, max_day, min_articles=10, output_dir="graphs"):
    """
    @brief Generate bar chart comparing overall source MAPE
    @param data Processed metrics dictionary
    @param max_day Maximum prediction day included
    @param min_articles Minimum articles required per source
    @param output_dir Directory to save output graphs
    """
    os.makedirs(output_dir, exist_ok=True)
    source_overall = data["source_overall"]
    source_article_counts = data["source_article_counts"]

    # Calculate overall MAPE for each source
    source_stats = []
    for source, errors in source_overall.items():
        article_count = source_article_counts.get(source, 0)
        if article_count >= min_articles:
            mape = np.mean(errors) * 100
            source_stats.append((source, mape, article_count))

    if not source_stats:
        print(f"No sources meet the minimum article requirement ({min_articles}).")
        return

    # Sort by MAPE
    source_stats.sort(key=lambda x: x[1])
    source_names = [s[0] for s in source_stats]
    source_mapes = [s[1] for s in source_stats]
    source_articles = [s[2] for s in source_stats]

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
            f"n={source_articles[i]}",
            ha="center",
            va="bottom",
        )

    ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
    ax.set_title(
        f"Source MAPE Comparison (Days 1-{max_day}, Min {min_articles} articles)"
    )
    plt.xticks(rotation=90, ha="center")
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Set y-axis to start at 0
    ax.set_ylim(bottom=0)

    plt.subplots_adjust(bottom=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "source_comparison.png"))
    plt.savefig(os.path.join(output_dir, "source_comparison.pdf"))
    plt.close()


def print_summary_stats(data, max_day, min_datapoints=10):
    """
    @brief Print summary statistics to console
    @param data Processed metrics dictionary
    @param max_day Maximum prediction day included
    @param min_datapoints Minimum samples required for inclusion
    """
    print("\nSummary Statistics")
    print("=" * 70)
    print(f"Analysis Parameters: Days 1-{max_day}, Min {min_datapoints} samples")

    print("\nModel Performance:")
    print("-" * 70)
    model_stats = []
    for model, errors in data["model_overall"].items():
        if len(errors) >= min_datapoints:
            mape = np.mean(errors) * 100
            display_name = model.replace("meta-llama/", "")
            model_stats.append((display_name, mape, len(errors)))

    for name, mape, count in sorted(model_stats, key=lambda x: x[1]):
        print(f"  {name:<25} | MAPE: {mape:>6.2f}% | n: {count:<5}")

    print("\nSource Performance:")
    print("-" * 70)
    source_stats = []
    for source, errors in data["source_overall"].items():
        if len(errors) >= min_datapoints:
            mape = np.mean(errors) * 100
            source_stats.append((source, mape, len(errors)))

    for source, mape, count in sorted(source_stats, key=lambda x: x[1]):
        print(f"  {source:<25} | MAPE: {mape:>6.2f}% | n: {count:<5}")


def save_model_performance_by_day(data, max_day, output_dir="tables"):
    """
    @brief Save model performance by day to CSV
    @param data Processed metrics dictionary
    @param max_day Maximum prediction day to include
    @param output_dir Directory to save output CSV
    """
    os.makedirs(output_dir, exist_ok=True)
    model_day_metrics = data["model_day_metrics"]
    model_counts = data["model_counts"]

    header = (
        ["Model"]
        + [f"Day {day} MAPE" for day in range(1, max_day + 1)]
        + ["Overall MAPE", "Total Samples"]
    )

    rows = []
    for model in model_day_metrics:
        row = [model.replace("meta-llama/", "")]
        total_errors = []

        for day in range(1, max_day + 1):
            if day in model_day_metrics[model]:
                mape = np.mean(model_day_metrics[model][day]) * 100
                row.append(f"{mape:.2f}%")
                total_errors.extend(model_day_metrics[model][day])
            else:
                row.append("N/A")

        if total_errors:
            overall_mape = np.mean(total_errors) * 100
            row.append(f"{overall_mape:.2f}%")
            row.append(str(len(total_errors)))
        else:
            row.extend(["N/A", "0"])

        rows.append(row)

    with open(
        os.path.join(output_dir, "model_performance_by_day.csv"), "w", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(sorted(rows, key=lambda x: x[0]))  # Sort by model name


def save_source_performance_by_day(data, max_day, output_dir="tables"):
    """
    @brief Save source performance by day to CSV
    @param data Processed metrics dictionary
    @param max_day Maximum prediction day to include
    @param output_dir Directory to save output CSV
    """
    os.makedirs(output_dir, exist_ok=True)
    source_day_metrics = data["source_day_metrics"]
    source_counts = data["source_counts"]

    header = (
        ["Source"]
        + [f"Day {day} MAPE" for day in range(1, max_day + 1)]
        + ["Overall MAPE", "Total Samples"]
    )

    rows = []
    for source in source_day_metrics:
        row = [source]
        total_errors = []

        for day in range(1, max_day + 1):
            if day in source_day_metrics[source]:
                mape = np.mean(source_day_metrics[source][day]) * 100
                row.append(f"{mape:.2f}%")
                total_errors.extend(source_day_metrics[source][day])
            else:
                row.append("N/A")

        if total_errors:
            overall_mape = np.mean(total_errors) * 100
            row.append(f"{overall_mape:.2f}%")
            row.append(str(len(total_errors)))
        else:
            row.extend(["N/A", "0"])

        rows.append(row)

    with open(
        os.path.join(output_dir, "source_performance_by_day.csv"), "w", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(sorted(rows, key=lambda x: x[0]))  # Sort by source name


def save_ticker_performance_by_day(data, max_day, output_dir="tables"):
    """
    @brief Save ticker performance by day to CSV
    @param data Processed metrics dictionary
    @param max_day Maximum prediction day to include
    @param output_dir Directory to save output CSV
    """
    os.makedirs(output_dir, exist_ok=True)
    ticker_metrics = data["ticker_metrics"]

    header = (
        ["Ticker"]
        + [f"Day {day} MAPE" for day in range(1, max_day + 1)]
        + ["Overall MAPE", "Total Samples"]
    )

    rows = []
    for ticker in ticker_metrics:
        row = [ticker]
        total_errors = []

        for day in range(1, max_day + 1):
            if day in ticker_metrics[ticker]:
                mape = np.mean(ticker_metrics[ticker][day]) * 100
                row.append(f"{mape:.2f}%")
                total_errors.extend(ticker_metrics[ticker][day])
            else:
                row.append("N/A")

        if total_errors:
            overall_mape = np.mean(total_errors) * 100
            row.append(f"{overall_mape:.2f}%")
            row.append(str(len(total_errors)))
        else:
            row.extend(["N/A", "0"])

        rows.append(row)

    with open(
        os.path.join(output_dir, "ticker_performance_by_day.csv"), "w", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(sorted(rows, key=lambda x: x[0]))  # Sort by ticker


def save_model_source_interaction(data, output_dir="tables"):
    """
    @brief Save model-source interaction metrics to CSV
    @param data Processed metrics dictionary
    @param output_dir Directory to save output CSV
    """
    os.makedirs(output_dir, exist_ok=True)
    model_source_metrics = defaultdict(lambda: defaultdict(list))

    for file_path in glob.glob(os.path.join(data["data_dir"], "*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        model = file_data.get("model")
        predictions_by_article = file_data.get("predictionsByArticle", [])

        for article in predictions_by_article:
            source = article.get("source")
            predictions = article.get("predictions", {})

            if not model or not source or not predictions:
                continue

            for day_pred in predictions.values():
                if day_pred.get("real") and day_pred.get("prediction"):
                    error = abs(day_pred["prediction"] - day_pred["real"]) / abs(
                        day_pred["real"]
                    )
                    model_source_metrics[model][source].append(error)

    header = ["Model", "Source", "MAPE", "Samples"]
    rows = []

    for model in model_source_metrics:
        clean_model = model.replace("meta-llama/", "")
        for source in model_source_metrics[model]:
            errors = model_source_metrics[model][source]
            if errors:
                mape = np.mean(errors) * 100
                rows.append([clean_model, source, f"{mape:.2f}%", len(errors)])

    with open(
        os.path.join(output_dir, "model_source_interaction.csv"), "w", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(
            sorted(rows, key=lambda x: (x[0], x[1]))
        )  # Sort by model then source


def save_model_ticker_interaction(data, output_dir="tables"):
    """
    @brief Save model-ticker interaction metrics to CSV
    @param data Processed metrics dictionary
    @param output_dir Directory to save output CSV
    """
    os.makedirs(output_dir, exist_ok=True)
    model_ticker_metrics = defaultdict(lambda: defaultdict(list))

    for file_path in glob.glob(os.path.join(data["data_dir"], "*.json")):
        ticker = os.path.basename(file_path).split("_")[0]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        model = file_data.get("model")
        predictions_by_article = file_data.get("predictionsByArticle", [])

        for article in predictions_by_article:
            predictions = article.get("predictions", {})

            if not model or not predictions:
                continue

            for day_pred in predictions.values():
                if day_pred.get("real") and day_pred.get("prediction"):
                    error = abs(day_pred["prediction"] - day_pred["real"]) / abs(
                        day_pred["real"]
                    )
                    model_ticker_metrics[model][ticker].append(error)

    header = ["Model", "Ticker", "MAPE", "Samples"]
    rows = []

    for model in model_ticker_metrics:
        clean_model = model.replace("meta-llama/", "")
        for ticker in model_ticker_metrics[model]:
            errors = model_ticker_metrics[model][ticker]
            if errors:
                mape = np.mean(errors) * 100
                rows.append([clean_model, ticker, f"{mape:.2f}%", len(errors)])

    with open(
        os.path.join(output_dir, "model_ticker_interaction.csv"), "w", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(
            sorted(rows, key=lambda x: (x[0], x[1]))
        )  # Sort by model then ticker


def save_error_trend_by_ticker(data, max_day, output_dir="tables"):
    """
    @brief Save error trends by ticker to CSV
    @param data Processed metrics dictionary
    @param max_day Maximum prediction day to include
    @param output_dir Directory to save output CSV
    """
    os.makedirs(output_dir, exist_ok=True)
    ticker_metrics = data["ticker_metrics"]

    header = (
        ["Ticker"]
        + [f"Day {day} MAPE" for day in range(1, max_day + 1)]
        + ["Slope", "Total Samples"]
    )

    rows = []
    for ticker in ticker_metrics:
        row = [ticker]
        day_values = []
        maples = []

        for day in range(1, max_day + 1):
            if day in ticker_metrics[ticker] and ticker_metrics[ticker][day]:
                mape = np.mean(ticker_metrics[ticker][day]) * 100
                row.append(f"{mape:.2f}%")
                day_values.append(day)
                maples.append(mape)
            else:
                row.append("N/A")

        # Calculate slope if we have at least 2 data points
        if len(day_values) >= 2:
            slope = np.polyfit(day_values, maples, 1)[0]
            row.append(f"{slope:.2f}")
        else:
            row.append("N/A")

        row.append(
            str(
                sum(
                    len(ticker_metrics[ticker][d])
                    for d in ticker_metrics[ticker]
                    if d <= max_day
                )
            )
        )
        rows.append(row)

    # Write to CSV
    with open(
        os.path.join(output_dir, "error_trend_by_ticker.csv"), "w", newline=""
    ) as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(sorted(rows, key=lambda x: x[0]))  # Sort by ticker


def plot_source_distribution(data, output_dir="graphs", threshold_percent=1.5):
    """
    @brief Generate a horizontal bar chart showing the distribution of articles by source
    @param data Processed metrics dictionary containing source article counts
    @param output_dir Directory to save output graphs
    @param threshold_percent Sources with percentage less than this will be grouped into "Others"
    """
    import os
    import matplotlib.pyplot as plt
    import numpy as np

    os.makedirs(output_dir, exist_ok=True)
    source_article_counts = data["source_article_counts"]

    if not source_article_counts:
        print("No source data available to plot article distribution.")
        return

    total_articles = sum(source_article_counts.values())

    sources_with_percentages = []
    for source, count in source_article_counts.items():
        percentage = (count / total_articles) * 100
        sources_with_percentages.append((source, count, percentage))

    sources_with_percentages.sort(key=lambda x: x[1], reverse=True)

    # Separate sources into main sources and others
    main_sources = []
    others_count = 0

    for source, count, percentage in sources_with_percentages:
        if percentage >= threshold_percent:
            main_sources.append((source, count, percentage))
        else:
            others_count += count

    others_percentage = (others_count / total_articles) * 100

    final_sources = main_sources
    if others_count > 0:
        final_sources.append(("Others", others_count, others_percentage))

    source_names = [s[0] for s in final_sources]
    article_counts = [s[1] for s in final_sources]
    percentages = [s[2] for s in final_sources]

    fig, ax = plt.subplots(figsize=(12, max(6, len(final_sources) * 0.4)))
    y_pos = np.arange(len(final_sources))

    bars = ax.barh(y_pos, article_counts, align="center", color="steelblue")

    if others_count > 0:
        bars[-1].set_color("lightgray")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(source_names)

    for i, (bar, percentage) in enumerate(zip(bars, percentages)):
        width = bar.get_width()
        label_text = f"{article_counts[i]} ({percentage:.1f}%)"
        ax.text(
            width + (total_articles * 0.01),
            bar.get_y() + bar.get_height() / 2,
            label_text,
            va="center",
        )

    ax.set_xlabel("Number of Articles")
    ax.set_title("Distribution of Articles by Source")
    ax.set_xlim(left=0)
    ax.grid(axis="x", linestyle="--", alpha=0.7)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "source_distribution.png"))
    plt.savefig(os.path.join(output_dir, "source_distribution.pdf"))
    plt.close()


def plot_model_comparison_combined(data_day1, data_days1to3, output_dir="graphs"):
    """
    @brief Generate combined bar chart comparing model MAPE for day1 vs days1-3
    @param data_day1 Processed metrics dictionary for day1 only
    @param data_days1to3 Processed metrics dictionary for days1-3
    @param output_dir Directory to save output graphs
    """
    os.makedirs(output_dir, exist_ok=True)

    # Get model stats for day1
    day1_stats = []
    for model, errors in data_day1["model_overall"].items():
        if len(errors) >= data_day1["min_datapoints"]:
            mape = np.mean(errors) * 100
            display_name = model.replace("meta-llama/", "")
            day1_stats.append((display_name, mape, len(errors)))

    # Get model stats for days1-3
    days1to3_stats = []
    for model, errors in data_days1to3["model_overall"].items():
        if len(errors) >= data_days1to3["min_datapoints"]:
            mape = np.mean(errors) * 100
            display_name = model.replace("meta-llama/", "")
            days1to3_stats.append((display_name, mape, len(errors)))

    # Find models that appear in both datasets
    common_models = set(m[0] for m in day1_stats) & set(m[0] for m in days1to3_stats)
    if not common_models:
        print("No common models between the two datasets")
        return

    # Create combined stats with sample counts
    combined_stats = []
    for model in common_models:
        day1_entry = next(m for m in day1_stats if m[0] == model)
        days1to3_entry = next(m for m in days1to3_stats if m[0] == model)
        combined_stats.append(
            (
                model,
                day1_entry[1],  # day1 MAPE
                days1to3_entry[1],  # days1-3 MAPE
                day1_entry[2],  # day1 count
                days1to3_entry[2],  # days1-3 count
            )
        )

    # Sort by day1 MAPE (ascending - from best to worst)
    combined_stats.sort(key=lambda x: x[1])

    model_names = [m[0] for m in combined_stats]
    day1_mapes = [m[1] for m in combined_stats]
    days1to3_mapes = [m[2] for m in combined_stats]
    day1_counts = [m[3] for m in combined_stats]
    days1to3_counts = [m[4] for m in combined_stats]

    fig, ax = plt.subplots(
        figsize=(max(10, len(model_names) * 0.8), 8)
    )  # Increased height

    x = np.arange(len(model_names))
    width = 0.35

    bars1 = ax.bar(
        x - width / 2, day1_mapes, width, label="Day 1 Only", color="skyblue"
    )
    bars2 = ax.bar(
        x + width / 2, days1to3_mapes, width, label="Days 1-3", color="lightcoral"
    )

    # Add MAPE values on top of bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.2f}%",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    for i, (day1_count, days1to3_count) in enumerate(zip(day1_counts, days1to3_counts)):
        y_pos = ax.get_ylim()[0] + (ax.get_ylim()[1] * 0.01)

        # Day 1 count
        ax.text(
            x[i] - width / 2,
            y_pos,
            f"samples={day1_count}",
            ha="center",
            va="bottom",  # Changed to bottom to place text above this point
            rotation=90,
            fontsize=8,
            color="black",
        )
        # Days 1-3 count
        ax.text(
            x[i] + width / 2,
            y_pos,
            f"samples={days1to3_count}",
            ha="center",
            va="bottom",
            rotation=90,
            fontsize=8,
            color="black",
        )

    ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
    ax.set_title("Model MAPE Comparison: Day 1 vs Days 1-3")
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=45, ha="right")
    ax.legend(loc="upper left")
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Adjust ylim to make room for the vertical sample counts
    current_ylim = ax.get_ylim()
    ax.set_ylim(bottom=current_ylim[0], top=current_ylim[1] * 1.05)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "model_comparison_combined.png"))
    plt.savefig(os.path.join(output_dir, "model_comparison_combined.pdf"))
    plt.close()


def plot_source_comparison_combined(data_day1, data_days1to3, output_dir="graphs"):
    """
    @brief Generate combined bar chart comparing source MAPE for day1 vs days1-3
    @param data_day1 Processed metrics dictionary for day1 only
    @param data_days1to3 Processed metrics dictionary for days1-3
    @param output_dir Directory to save output graphs
    """
    os.makedirs(output_dir, exist_ok=True)

    # Get source stats for day1
    day1_stats = []
    for source, errors in data_day1["source_overall"].items():
        if len(errors) >= data_day1["min_datapoints"]:
            mape = np.mean(errors) * 100
            day1_stats.append((source, mape, len(errors)))

    # Get source stats for days1-3
    days1to3_stats = []
    for source, errors in data_days1to3["source_overall"].items():
        if len(errors) >= data_days1to3["min_datapoints"]:
            mape = np.mean(errors) * 100
            days1to3_stats.append((source, mape, len(errors)))

    # Find sources that appear in both datasets
    common_sources = set(s[0] for s in day1_stats) & set(s[0] for s in days1to3_stats)
    if not common_sources:
        print("No common sources between the two datasets")
        return

    combined_stats = []
    for source in common_sources:
        day1_mape = next(s[1] for s in day1_stats if s[0] == source)
        days1to3_mape = next(s[1] for s in days1to3_stats if s[0] == source)
        article_count = data_day1["source_article_counts"].get(source, 0)
        combined_stats.append((source, day1_mape, days1to3_mape, article_count))

    # Sort by day1 MAPE (ascending - from best to worst)
    combined_stats.sort(key=lambda x: x[1])

    source_names = [s[0] for s in combined_stats]
    day1_mapes = [s[1] for s in combined_stats]
    days1to3_mapes = [s[2] for s in combined_stats]
    article_counts = [s[3] for s in combined_stats]

    fig, ax = plt.subplots(figsize=(max(10, len(source_names) * 0.8), 6))

    x = np.arange(len(source_names))
    width = 0.35

    bars1 = ax.bar(
        x - width / 2, day1_mapes, width, label="Day 1 Only", color="lightgreen"
    )
    bars2 = ax.bar(
        x + width / 2, days1to3_mapes, width, label="Days 1-3", color="mediumseagreen"
    )

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.2f}%",
                ha="center",
                va="bottom",
            )

    for i, count in enumerate(article_counts):
        ax.text(x[i], ax.get_ylim()[0], f"articles={count}", ha="center", va="bottom")

    ax.set_ylabel("Mean Absolute Percentage Error (MAPE) %")
    ax.set_title("Source MAPE Comparison: Day 1 vs Days 1-3")
    ax.set_xticks(x)
    ax.set_xticklabels(source_names, rotation=90, ha="center")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    ax.set_ylim(bottom=0)

    plt.subplots_adjust(bottom=0.4)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "source_comparison_combined.png"))
    plt.savefig(os.path.join(output_dir, "source_comparison_combined.pdf"))
    plt.close()


def main():
    """Command line interface for prediction analysis."""
    parser = argparse.ArgumentParser(
        description="Analyze prediction MAPE across models and sources"
    )
    parser.add_argument(
        "--data-dir", type=str, default="data", help="Directory containing JSON files"
    )
    parser.add_argument(
        "--max-day",
        type=int,
        default=3,
        help="Maximum prediction day to analyze (1-12)",
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
    )s
    args = parser.parse_args()

    data = load_data(args.data_dir, args.max_day, args.min_articles)
    data["data_dir"] = args.data_dir

    # print_summary_stats(data, args.max_day, args.min_datapoints)

    # CSV
    # save_model_performance_by_day(data, args.max_day)
    # save_source_performance_by_day(data, args.max_day)
    # save_ticker_performance_by_day(data, args.max_day)
    # save_model_source_interaction(data)
    # save_model_ticker_interaction(data)
    # save_error_trend_by_ticker(data, args.max_day)

    # Plots
    # plot_model_accuracy_over_time(data, args.max_day, args.min_datapoints)
    # plot_source_accuracy_over_time(data, args.max_day, args.min_datapoints)
    # plot_model_comparison(data, args.max_day, args.min_datapoints)
    # plot_source_comparison(data, args.max_day, args.min_articles)
    # plot_source_distribution(data)

    data_day1 = load_data(args.data_dir, max_day=1, min_articles_per_source=1)
    data_day1["min_datapoints"] = 100
    data_day1["data_dir"] = args.data_dir

    data_days1to3 = load_data(args.data_dir, max_day=3, min_articles_per_source=1)
    data_days1to3["min_datapoints"] = 300
    data_days1to3["data_dir"] = args.data_dir

    #plot_accuracy_over_time(data, 12, 50)
    plot_model_comparison_combined(data_day1, data_days1to3)
    plot_model_accuracy_over_time(data, args.max_day, args.min_datapoints)


if __name__ == "__main__":
    main()
