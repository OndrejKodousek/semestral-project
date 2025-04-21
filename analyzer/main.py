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
        "distil-whisper-large-v3-en",
        # Groq preview
        "deepseek-r1-distill-llama-70b",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "mistral-saba-24b",
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
                # TODO: It's biased
                continue

            ####################################################################
            # INDIVIDUAL ARTICLE

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

            print(f" | ARTICLE ANALYSIS SUCCESS")
            save_processed_articles(article["id"], model, processed_entry)

            # INDIVIDUAL ARTICLE
            ####################################################################
            # AGGREGATED ARTICLES
            ticker = str(processed_entry["ticker"])
            stock = str(processed_entry["stock"])
            print(
                shorten_string(
                    f"Running aggregated analysis for {stock} ({ticker})",
                    84,
                ),
                end="",
                flush=True,
            )

            prompt = fetch_sum_analysis_data(ticker, model)

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
            save_processed_summarized_articles(processed_entry, model, ticker)


if __name__ == "__main__":
    main()
