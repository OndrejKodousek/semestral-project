import json
import google.generativeai as genai
import config
import re

from database import fetch_sum_analysis_data, increment_priority, get_db_connection
from google.api_core import exceptions


def process_article_google(entry, model):

    genai.configure(api_key=config.API_KEY_GEMINI)

    model = genai.GenerativeModel(
        model_name=model, system_instruction=config.SYSTEM_INSTRUCTION_INDIVIDUAL
    )

    try:
        response = model.generate_content([entry["content"]])
    except exceptions.ResourceExhausted as e:
        print(f" | FAILED, reached quota")
        return None
    except exceptions.ServerError as e:
        print(f" | FAILED, input too large for model")
        return None

    response_text = response.text

    if "ERROR-01" in response_text:
        print(f" | FAILED, couldn't determine relevant stock for article")
        increment_priority(entry["id"])
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

    return {**entry, **data}


def process_article_google_sum(model_name, prompt):

    genai.configure(api_key=config.API_KEY_GEMINI)

    model = genai.GenerativeModel(
        model_name=model_name, system_instruction=config.SYSTEM_INSTRUCTION_AGGREGATED
    )

    prompt_text = str(prompt)

    try:
        response = model.generate_content(prompt_text)

    except exceptions.ResourceExhausted as e:
        print(f" | FAILED, reached quota")
        return None

    except exceptions.ServerError as e:
        print(f" | FAILED, input too large for model")
        return None

    response_text = response.text

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

    return data
