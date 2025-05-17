"""
@file llm_groq.py
@brief Integration with Groq API for article analysis.

This module handles sending requests to Groq API for both individual
article analysis and aggregated stock analysis.
"""

import json
import config
import re

from database import fetch_sum_analysis_data, increment_priority, get_db_connection
from groq import Groq, RateLimitError, APIStatusError


def process_article_groq(article, model):
    """
    @brief Process an individual article using Groq API.

    Sends the article content to the specified model via Groq API,
    extracts JSON from the response, and validates it.

    @param article Dictionary containing article data.
    @param model The model name to use for processing.
    @return Combined dictionary of article data and analysis results, or None if processing failed.
    """
    client = Groq(api_key=config.API_KEY_GROQ)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": article["content"]},
                {"role": "system", "content": config.SYSTEM_INSTRUCTION_INDIVIDUAL},
            ],
            model=model,
        )

    except RateLimitError as e:
        print(f" | FAILED, reached quota")
        return None
    except APIStatusError as e:
        print(f" | FAILED, input too large for model")
        return None

    response_text = chat_completion.choices[0].message.content

    if "ERROR-01" in response_text:
        print(f" | FAILED, couldn't determine relevant stock for article")
        increment_priority(article["id"])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE articles SET priority = priority + 1 WHERE id = ?",
            (article["id"],),
        )
        conn.commit()
        conn.close()
        return None

    match = re.search(r"\{(.*?)\}", response_text, re.DOTALL)
    if not match:
        print(f" | FAILED, couldn't find proper JSON in response")
        return None

    extracted_content = "{" + match.group(1) + "}"

    try:
        data = json.loads(extracted_content)
    except json.decoder.JSONDecodeError:
        print(f" | FAILED, response has bad JSON format")
        return None

    return {**article, **data}


def processed_article_groq_sum(model, prompt):
    """
    @brief Process aggregated article data for a stock using Groq API.

    Sends the aggregated prompt to the specified model via Groq API,
    extracts JSON from the response, and validates it.

    @param model The model name to use for processing.
    @param prompt The aggregated prompt containing multiple articles about a stock.
    @return Dictionary containing analysis results, or None if processing failed.
    """
    client = Groq(api_key=config.API_KEY_GROQ)

    prompt_text = str(prompt)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt_text},
                {"role": "system", "content": config.SYSTEM_INSTRUCTION_AGGREGATED},
            ],
            model=model,
        )
        response_text = chat_completion.choices[0].message.content

    except RateLimitError as e:
        print(f" | FAILED, reached quota")
        return None
    except APIStatusError as e:
        print(f" | FAILED, API status error: {e}")
        return None
    except Exception as e:
        print(f" | FAILED, Unexpected error: {e}")
        return None

    if "ERROR-01" in response_text:
        print(f" | FAILED, couldn't determine relevant stock for summary")
        return None

    match = re.search(r"\{(.*?)\}", response_text, re.DOTALL)
    if not match:
        print(f" | FAILED, couldn't find proper JSON in response")
        return None

    extracted_content = "{" + match.group(1) + "}"

    try:
        data = json.loads(extracted_content)
    except json.decoder.JSONDecodeError:
        print(f" | FAILED, response has bad JSON format")
        return None

    return data
