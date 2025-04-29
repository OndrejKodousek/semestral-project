import json
import config
import re

from database import fetch_sum_analysis_data, increment_priority, get_db_connection
from groq import Groq, RateLimitError, APIStatusError


def process_article_groq(article, model):
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
        print(f" | FAILED (SUM), reached quota")
        return None
    except APIStatusError as e:
        print(f" | FAILED (SUM), API status error: {e}")
        return None
    except Exception as e:
        print(f" | FAILED (SUM), Unexpected error: {e}")
        return None

    if "ERROR-01" in response_text:
        print(f" | FAILED (SUM), couldn't determine relevant stock for summary")
        # Note: incrementPriority might need adjustment if 'article_id' isn't directly available
        # incrementPriority(article["id"]) # This likely needs context adjustment
        return None

    match = re.search(r"\{(.*?)\}", response_text, re.DOTALL)
    if not match:
        print(f" | FAILED (SUM), couldn't find proper JSON in response")
        return None

    extracted_content = "{" + match.group(1) + "}"

    try:
        data = json.loads(extracted_content)
    except json.decoder.JSONDecodeError:
        print(f" | FAILED (SUM), response has bad JSON format")
        return None

    return data
