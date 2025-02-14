import json
import re
import os
import traceback
import random
import copy

from google import genai
from groq import Groq, RateLimitError, APIStatusError


def load_processed_articles(model, file_path_template="api_data/processed_articles_{model}.json"):
    """Load already processed articles for a specific model."""
    file_path = file_path_template.format(model=model)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_processed_articles(articles, model, file_path_template="api_data/processed_articles_{model}.json"):
    """Save processed articles for a specific model."""
    file_path = file_path_template.format(model=model)
    articles_copy = copy.deepcopy(articles)

    for article in articles_copy:
        article.pop("content", None)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(articles_copy, f, indent=4, ensure_ascii=False)

def logToFile(string):
    with open("data/failed_processor.log", "a+") as f:
        line = f"{string}\n"
        f.write(line)

def process_article(entry, model, api_key, system_instruction):
    """Process an article using the LLM API."""
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            contents=[entry["content"]],
        )

    except genai.errors.ClientError as e:
        # Likely cause: Quota
        error_details = traceback.format_exc()
        logToFile(error_details)
        return f"ERROR-{e.code}", None

    except genai.errors.ServerError as e:
        # Likely cause: Server overload
        error_details = traceback.format_exc()
        logToFile(error_details)
        return f"ERROR-{e.code}", None

    response_text = response.candidates[0].content.parts[0].text

    if "ERROR-01" in response_text:
        # Couldn't identify which stock the article is talking about
        logToFile(f"link={entry['link']}, model={model}, response={response_text}")
        return "ERROR-01", None

    match = re.search(r"\{(.*?)\}", response_text, re.DOTALL)
    if not match:
        logToFile(response_text)
        return "ERROR-02", None

    extracted_content = "{" + match.group(1) + "}"

    try:
        data = json.loads(extracted_content)
    except json.decoder.JSONDecodeError:
        # Output in wrong format
        return "ERROR-03", None

    return None, {**entry, **data}

def shorten_string(link, max_length=60):
    if len(link) <= max_length:
        return link
    part_length = (max_length - 3) // 2
    return link[:part_length] + "..." + link[-part_length:]

def str_to_int(string):
    matches = re.findall(r'\d+', str(string)) 
    integer = int(matches[0])
    return integer

def process_article_groq(article, model, system_instruction):
    with open("data/API_KEY_GROQ", "r") as f:
        api_key = f.readline().strip()

    client = Groq(
        api_key=api_key,
    )

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": article["content"],
                },
                {
                  "role": "system",
                  "content": system_instruction
                },
            ],
            model=model,
        )

    except RateLimitError as e:
        error_details = traceback.format_exc()
        logToFile(error_details)
        return f"ERROR-429", None
    except APIStatusError as e:
        # TODO: error code detection - but most likely caused by too large request
        error_details = traceback.format_exc()
        logToFile(error_details)
        return f"ERROR-413", None
    except:
        return f"ERROR-00", None

    response_text = chat_completion.choices[0].message.content

    if "ERROR-01" in response_text:
        # Couldn't identify which stock the article is talking about
        logToFile(f"link={article['link']}, model={model}, response={response_text}")
        return "ERROR-01", None

    match = re.search(r"\{(.*?)\}", response_text, re.DOTALL)
    if not match:
        logToFile(response_text)
        return "ERROR-02", None

    extracted_content = "{" + match.group(1) + "}"

    try:
        data = json.loads(extracted_content)
    except json.decoder.JSONDecodeError:
        # Output in wrong format
        return "ERROR-03", None

    return None, {**article, **data}








    print(chat_completion.choices[0].message.content)

def main():
    # Load API key and system instruction
    with open("data/API_KEY_GEMINI", "r") as f:
        api_key = f.readline().strip()

    with open("data/system_instruction.txt", "r") as f:
        system_instruction = f.read().strip()

    # List of models to process articles with
    models = [
        "gemini-1.5-flash",              # 1500/day
        "gemini-2.0-flash",              # 1500/day
        "gemini-2.0-flash-lite-preview", # ???/day
        "gemini-2.0-pro-exp",            # 50/day
        "gemini-2.0-flash-exp",          # 1500/day

        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "gemma2-9b-it",
        "mixtral-8x7b-32768",
    ]

    total_new_processed_entries = 0

    with open("data/articles.json", "r", encoding="utf-8") as f:
        articles = json.load(f)

    articles = sorted(articles, key=lambda x: int(x["priority"]))

    for model in models:

        processed_articles = load_processed_articles(model)

        processed_links = {article["link"] for article in processed_articles}

        # Process only unprocessed articles
        new_processed_articles = []
        i = 0
        for article in articles:

            i += 1
            if i > 20:
                break

            if article["link"] in processed_links:
                continue
            
            print(f"Processing article {shorten_string(article['link'], 60-len(model))} with {model}", end="", flush=True)

            if str_to_int(article['priority']) > 20:
                print(f" | SKIPPED, couldn't determine relevant stock for article way too many times")
                continue
            
            if "gemini" in model:
                error_code, processed_entry = process_article(article, model, api_key, system_instruction)
            else:
                error_code, processed_entry = process_article_groq(article, model, system_instruction)

            if error_code:
                if error_code == "ERROR-01":
                    print(f" | FAILED, couldn't determine relevant stock for article")
                    # "1" -> 1 -> 1+1 -> 2 -> "2" 
                    new_priority = str_to_int(article["priority"]) + 1
                    article["priority"] = str(new_priority)

                elif error_code == "ERROR-02":
                    print(f" | FAILED, couldn't find proper JSON in response")
                elif error_code == "ERROR-03":
                    print(f" | FAILED, response has bad JSON format")
                elif error_code == "ERROR-413":
                    print(f" | FAILED, input too large for model")
                elif error_code == "ERROR-429":
                    print(f" | FAILED, reached quota")
                    break
                else:
                    print(f" | FAILED, unknown error, code {error_code}")
                continue
            else:
                new_processed_articles.append(processed_entry)
                print(f" | SUCCESS")

        if new_processed_articles:
            total_new_processed_entries += len(new_processed_articles)
            processed_articles.extend(new_processed_articles)
            save_processed_articles(processed_articles, model)

    with open("data/articles.json", "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)

    print(f"Processed {total_new_processed_entries} new entries")

if __name__ == "__main__":
    main()