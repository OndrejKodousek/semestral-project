import os
import json
import random
import time
import unicodedata

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchDriverException

driver = None
script_dir = os.path.dirname(os.path.abspath(__file__))

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

def load_scraped_articles():
    file_path = os.path.join(script_dir, "..", "data", "articles.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_scraped_articles(articles):
    file_path = os.path.join(script_dir, "..", "data", "articles.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=4, ensure_ascii=False)

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
