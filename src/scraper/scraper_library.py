import os
import random
import time
import unicodedata
import sqlite3
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchDriverException
from typing import Optional, List, Dict, Union

driver = None
script_dir = os.path.dirname(os.path.abspath(__file__))

def execute_query(
    query: str,
    params: Optional[tuple] = None,
    db_path: str = 'data/news.db',
    timeout: float = 5.0,
    query_type: str = "SELECT",
    use_row_factory: bool = True
) -> Optional[Union[List[Dict], int]]:
    try:
        if query_type not in {"SELECT", "INSERT", "UPDATE", "DELETE"}:
            raise ValueError("query_type must be one of 'SELECT', 'INSERT', 'UPDATE', 'DELETE'")

        conn = sqlite3.connect(db_path, timeout=timeout)
        if use_row_factory:
            conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if query_type != "SELECT":
            conn.commit()
            affected_rows = cursor.rowcount 
        else:
            affected_rows = None

        if query_type == "SELECT":
            results = cursor.fetchall()
            if use_row_factory:
                results = [dict(row) for row in results]
        else:
            results = None

        cursor.close()
        conn.close()

        return results if query_type == "SELECT" else affected_rows

    except (sqlite3.Error, ValueError) as e:
        print(f"An error occurred: {e}")
        return None

def getDriver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    )
    try:
      driver = webdriver.Chrome(options=options)
    except NoSuchDriverException:
      chromedriver_path = "/usr/bin/chromedriver"
      service = webdriver.ChromeService(executable_path=chromedriver_path)
      driver = webdriver.Chrome(options=options, service=service)

    return driver

def log(text):
    if True is False:
        print(text)

def random_delay(min_seconds=1, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def random_click(element, driver):
    action = ActionChains(driver)
    x_offset = random.randint(-10, 10)
    y_offset = random.randint(-10, 10)
    action.move_to_element_with_offset(element, x_offset, y_offset).click().perform()

def extract_text(element):
    p_tags = element.find_elements(By.CSS_SELECTOR, "p")
    return "".join(tag.get_attribute("innerHTML") for tag in p_tags)

def purify_text(input_text):
    soup = BeautifulSoup(input_text, "html.parser")
    text = soup.get_text().strip()

    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ASCII", "ignore").decode("ASCII")

    return ascii_text

def shorten_string(link, max_length=80):
    if len(link) <= max_length:
        spaces = max_length - len(link)
        return link + (" " * spaces)
    part_length = (max_length - 3) // 2
    return link[:part_length] + "..." + link[-part_length:]

def extract_domain(link):
    parsed_url = urlparse(link)
    netloc = parsed_url.netloc
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    return netloc

def logToFile(string):
    file_path = os.path.join(script_dir, "..", "data", "failed_scrape.log")

    with open(file_path, "a+") as f:
        line = f"{string}\n"
        f.write(line)