import sqlite3
import re
import os
import traceback
import random
import copy
import json
import time
from google import genai
from openai import OpenAI
from groq import Groq, RateLimitError, APIStatusError

script_dir = os.path.dirname(os.path.abspath(__file__))

# Connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect('data/news.db', timeout=30)  # Increase timeout to 30 seconds
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

# Load processed articles from the database
def load_processed_articles(model):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch processed articles for the given model
    cursor.execute('''
        SELECT article_id FROM analysis WHERE model_name = ?
    ''', (model,))
    processed_articles = cursor.fetchall()
    processed_article_ids = {row['article_id'] for row in processed_articles}

    conn.close()
    return processed_article_ids

# Save processed articles to the database
def save_processed_articles(article_id, model, data):
    max_retries = 5
    retry_delay = 1  # Start with 1 second delay

    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert analysis results into the analysis table
            cursor.execute('''
                INSERT INTO analysis (
                article_id, model_name, published, ticker, stock, 
                pred_1_day, pred_2_day, pred_3_day, pred_4_day, pred_5_day, pred_6_day, pred_7_day,
                conf_1_day, conf_2_day, conf_3_day, conf_4_day, conf_5_day, conf_6_day, conf_7_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article_id,
                model,
                data.get('published'),
                data.get('ticker'),
                data.get('stock'),
                data.get('prediction_1_day'),
                data.get('prediction_2_day'),
                data.get('prediction_3_day'),
                data.get('prediction_4_day'),
                data.get('prediction_5_day'),
                data.get('prediction_6_day'),
                data.get('prediction_7_day'),
                data.get('confidence_1_day'),
                data.get('confidence_2_day'),
                data.get('confidence_3_day'),
                data.get('confidence_4_day'),
                data.get('confidence_5_day'),
                data.get('confidence_6_day'),
                data.get('confidence_7_day'),
            ))
            conn.commit()
            cursor.close()
            conn.close()
            break  # Success, exit the retry loop

        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print(f"Database locked, retrying in {retry_delay} seconds (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                raise e  # Re-raise other errors
    else:
        raise Exception("Failed to save processed articles after multiple retries")

def logToFile(string):
    file_path = os.path.join(script_dir, "..", "data", "failed_processor.log")
    with open(file_path, "a+") as f:
        line = f"{string}\n"
        f.write(line)

def process_article(entry, model, system_instruction):
    file_path = os.path.join(script_dir, "..", "data", "API_KEY_GEMINI")
    with open(file_path, "r") as f:
        api_key = f.readline().strip()

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
        error_details = traceback.format_exc()
        logToFile(error_details)
        return f"ERROR-{e.code}", None

    except genai.errors.ServerError as e:
        error_details = traceback.format_exc()
        logToFile(error_details)
        return f"ERROR-{e.code}", None

    response_text = response.candidates[0].content.parts[0].text

    if "ERROR-01" in response_text:
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
        return "ERROR-03", None

    return None, {**entry, **data}

def shorten_string(link, max_length=60):
    if len(link) <= max_length:
        return link
    part_length = (max_length - 3) // 2
    return link[:part_length] + "..." + link[-part_length:]

def str_to_int(string):
    matches = re.findall(r"\d+", str(string))
    integer = int(matches[0])
    return integer

def process_article_groq(article, model, system_instruction):
    file_path = os.path.join(script_dir, "..", "data", "API_KEY_GROQ")
    with open(file_path, "r") as f:
        api_key = f.readline().strip()

    client = Groq(api_key=api_key)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": article["content"]},
                {"role": "system", "content": system_instruction},
            ],
            model=model,
        )

    except RateLimitError as e:
        error_details = traceback.format_exc()
        logToFile(error_details)
        return f"ERROR-429", None
    except APIStatusError as e:
        error_details = traceback.format_exc()
        logToFile(error_details)
        return f"ERROR-413", None
    except:
        return f"ERROR-00", None

    response_text = chat_completion.choices[0].message.content

    if "ERROR-01" in response_text:
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
        return "ERROR-03", None

    return None, {**article, **data}

def process_article_openrouter(article, model, system_instruction):
    file_path = os.path.join(script_dir, "..", "data", "API_KEY_OPENROUTER")
    with open(file_path, "r") as f:
        api_key = f.readline().strip()

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "user", "content": article["content"]},
                {"role": "system", "content": system_instruction},
            ],
            model=model,
        )
        if chat_completion.choices == None:
            error_code = str(chat_completion.error['code'])
            if error_code == "429":
                error_details = traceback.format_exc()
                logToFile(error_details)
                return f"ERROR-429", None
            elif error_code == "413":
                error_details = traceback.format_exc()
                logToFile(error_details)
                return f"ERROR-413", None
            raise TypeError

    except:
        return f"ERROR-00", None

    response_text = chat_completion.choices[0].message.content

    if "ERROR-01" in response_text:
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
        return "ERROR-03", None

    return None, {**article, **data}

def isValidData(data):
    try:
        required_keys = [
            "stock", "ticker",
            "prediction_1_day", "prediction_2_day", "prediction_3_day",
            "prediction_4_day", "prediction_5_day", "prediction_6_day", "prediction_7_day",
            "confidence_1_day", "confidence_2_day", "confidence_3_day",
            "confidence_4_day", "confidence_5_day", "confidence_6_day", "confidence_7_day"
        ]
        
        # Check if all required keys are present
        for key in required_keys:
            if key not in data:
                return False  # Missing key

        # Validate stock and ticker
        invalid_strings = {"", "none", "unknown", "null", "N/A", "error"}
        if str(data["stock"]).strip().lower() in invalid_strings:
            return False
        if str(data["ticker"]).strip().lower() in invalid_strings:
            return False

        # Validate predictions and confidences
        for i in range(1, 8):
            # Convert prediction to float
            prediction_key = f"prediction_{i}_day"
            try:
                prediction_value = float(data[prediction_key])
            except (ValueError, TypeError):
                return False  # Invalid number format

            # Check if prediction is within realistic range
            if not (-1.0 <= prediction_value <= 1.0):
                return False

            # Convert confidence to float
            confidence_key = f"confidence_{i}_day"
            try:
                confidence_value = float(data[confidence_key])
            except (ValueError, TypeError):
                return False  # Invalid number format

            # Check if confidence is within the expected range
            if not (0.00 <= confidence_value <= 1.00):
                return False

        return True  # All checks passed

    except Exception as e:
        print(f"Validation error: {e}")  # Debugging: Print the exception
        return False


def main():
    file_path = os.path.join(script_dir, "..", "data", "system_instruction.txt")
    with open(file_path, "r") as f:
        system_instruction = f.read().strip()

    models = [
        "gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite-preview",
        "gemini-2.0-pro-exp", "gemini-2.0-flash-exp", "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant", "llama3-70b-8192", "llama3-8b-8192", "gemma2-9b-it",
        "mixtral-8x7b-32768", "deepseek/deepseek-chat:free"
    ]

    total_new_processed_entries = 0

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all articles from the database
    cursor.execute('SELECT * FROM articles ORDER BY priority ASC')
    articles = cursor.fetchall()
    conn.close()

    for model in models:
        processed_article_ids = load_processed_articles(model)

        # Process only unprocessed articles
        new_processed_articles = []
        for article in articles:
            if article['id'] in processed_article_ids:
                continue
            if article['priority'] > 20:
                continue

            print(f"Processing article {shorten_string(article['link'], 60-len(model))} with {model}", end="", flush=True)

            if "gemini" in model:
                error_code, processed_entry = process_article(article, model, system_instruction)
            elif "deepseek/deepseek-chat:free" == model:
                error_code, processed_entry = process_article_openrouter(article, model, system_instruction)
            else:
                error_code, processed_entry = process_article_groq(article, model, system_instruction)

            if error_code:
                if error_code == "ERROR-01":
                    print(f" | FAILED, couldn't determine relevant stock for article")
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('UPDATE articles SET priority = priority + 1 WHERE id = ?', (article['id'],))
                    conn.commit()
                    conn.close()
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
            elif isValidData(processed_entry):
                print(f" | SUCCESS")
                save_processed_articles(article['id'], model, processed_entry)
            else:
                print(f" | FAILED, data format is invalid")

    print(f"Processed {total_new_processed_entries} new entries")

if __name__ == "__main__":
    main()