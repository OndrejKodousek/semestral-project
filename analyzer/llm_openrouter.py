import json
import config
import re

from database import fetch_sum_analysis_data, increment_priority, get_db_connection
from openai import OpenAI


def process_article_openrouter(article, model):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1", api_key=config.API_KEY_OPENROUTER
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": article["content"]},
            {"role": "system", "content": config.SYSTEM_INSTRUCTION_INDIVIDUAL},
        ],
        model=model,
    )
    if chat_completion.choices == None:
        error_code = str(chat_completion.error["code"])
        if error_code == "429":
            print(f" | FAILED, reached quota")
            return None
        elif error_code == "413":
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


def processed_article_openrouter_sum(model, prompt):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1", api_key=config.API_KEY_OPENROUTER
    )

    prompt_text = str(prompt)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": prompt_text},
                {"role": "system", "content": config.SYSTEM_INSTRUCTION_AGGREGATED},
            ],
            model=model,
        )

        if chat_completion.choices is None:
            error_info = getattr(chat_completion, "error", {})
            error_code = (
                str(error_info.get("code", "Unknown"))
                if isinstance(error_info, dict)
                else "Unknown"
            )

            if error_code == "429":
                print(f" | FAILED (SUM), reached quota")
            elif error_code == "413":
                print(f" | FAILED (SUM), input too large for model")
            else:
                print(f" | FAILED (SUM), Unknown API error: {error_code}")
            return None

        response_text = chat_completion.choices[0].message.content

    except RateLimitError:
        print(f" | FAILED (SUM), reached quota (RateLimitError)")
        return None
    except APIError as e:
        if hasattr(e, "status_code") and e.status_code == 413:
            print(f" | FAILED (SUM), input too large for model (APIError 413)")
        else:
            print(f" | FAILED (SUM), API error: {e}")
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
