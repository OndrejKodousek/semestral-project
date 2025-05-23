"""
@file main.py
@brief Main entry point for the stock news analysis system.

This script orchestrates the process of analyzing financial news articles using
various LLM models and saving the results to a database. It processes both individual
articles and performs aggregated analysis for stocks.
"""

import random
import config

from utils import shorten_string, is_valid_data
from database import (
    get_db_connection,
    load_processed_articles,
    save_processed_articles,
    save_processed_summarized_articles,
    fetch_sum_analysis_data,
)

from llm_google import process_article_google, process_article_google_sum
from llm_groq import process_article_groq, processed_article_groq_sum
from llm_openrouter import process_article_openrouter, processed_article_openrouter_sum


def main():
    """
    @brief Main function that orchestrates the article analysis process.

    This function:
    1. Defines available LLM models
    2. Shuffles models to distribute load
    3. Fetches articles from the database
    4. For each model, processes unprocessed articles
    5. Performs individual article analysis
    6. Performs aggregated analysis for each stock
    7. Saves results to the database
    """

    models = [
        # Google AI Studio
        "gemini-2.5-flash-preview-04-17",
        "gemini-2.5-pro-preview-03-25",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        # OpenRouter
        "deepseek/deepseek-chat:free",
        # Groq
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
        # Groq preview
        "deepseek-r1-distill-llama-70b",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen-qwq-32b",
    ]

    random.shuffle(models)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM articles ORDER BY priority ASC")
    articles = cursor.fetchall()
    conn.close()

    for model in models:
        processed_article_ids = load_processed_articles(model)

        # Process only unprocessed articles
        new_processed_articles = []
        for article in articles:
            if article["id"] in processed_article_ids:
                continue
            if article["priority"] > 20:
                # Model/s have failed to analyze article too many times, something is very likely
                # wrong with the article that makes it impossible to determine ticker
                continue

            ####################################################################
            # PROCESSING INDIVIDUAL ARTICLE
            #

            print(
                f"Processing article {shorten_string(article['link'], 60-len(model))} with {model}",
                end="",
                flush=True,
            )

            if "gemini" in model:
                processed_entry = process_article_google(article, model)
            elif "deepseek/deepseek-chat:free" == model:
                processed_entry = process_article_openrouter(article, model)
            else:
                processed_entry = process_article_groq(article, model)

            if processed_entry is None:
                continue

            if not is_valid_data(processed_entry):
                print(f" | FAILED, data format is invalid")
                continue

            ret = save_processed_articles(article["id"], model, processed_entry)
            if ret is True:
                print(f" | ARTICLE ANALYSIS SUCCESS")

            #
            # PROCESSING INDIVIDUAL ARTICLE
            ####################################################################
            # PROCESSING AGGREGATED ARTICLES
            #

            ticker = str(processed_entry["ticker"])
            stock = str(processed_entry["stock"])
            print(
                shorten_string(
                    f"Running aggregated analysis for {stock} ({ticker})",
                    85,
                ),
                end="",
                flush=True,
            )

            reference_date, prompt = fetch_sum_analysis_data(ticker, model)

            if "gemini" in model:
                processed_entry = process_article_google_sum(model, prompt)
            elif "deepseek/deepseek-chat:free" == model:
                processed_entry = processed_article_openrouter_sum(model, prompt)
            else:
                processed_entry = processed_article_groq_sum(model, prompt)

            if processed_entry is None:
                continue
            if not is_valid_data(processed_entry):
                print(f" | FAILED, data format is invalid")
                continue

            print(f" | AGGREGATED ANALYSIS SUCCESS")
            save_processed_summarized_articles(
                processed_entry, model, ticker, reference_date
            )

            #
            # PROCESSING AGGREGATED ARTICLES
            ####################################################################


if __name__ == "__main__":
    main()
