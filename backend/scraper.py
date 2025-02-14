import os
import feedparser
import json
import random
import time
import unicodedata
import shutil

from bs4 import BeautifulSoup
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchDriverException

# Firefox struggles to dynamically load content
#from selenium.webdriver.firefox.service import Service
#from webdriver_manager.firefox import GeckoDriverManager
#options = webdriver.FirefoxOptions()
#options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
#options.add_argument("--headless")
#driver = webdriver.Firefox(
#    service=Service(GeckoDriverManager().install()), options=options
#)

# Chrome works but has irrelevant TF warnings + it's chrome 
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
)
#driver = webdriver.Chrome(
#    service=Service(ChromeDriverManager().install()), options=options
#)

try:
  #in case we are on x86_64 we do not need the chromeservice workaround,
  #so try the normal way first
  driver = webdriver.Chrome(options=options)
except NoSuchDriverException:
#  chromedriver_path = shutil.which("chromedriver") #/usr/bin/chromedriver
  chromedriver_path = "/usr/bin/chromedriver"
  service = webdriver.ChromeService(executable_path=chromedriver_path)
  driver = webdriver.Chrome(options=options, service=service)

#from selenium.webdriver.chrome.service import Service
#from webdriver_manager.chrome import ChromeDriverManager
#
#options = webdriver.ChromeOptions()
#options.add_argument("--headless")
#options.add_argument(
#    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
#)
#
#driver = webdriver.Chrome(
#    service=Service(ChromeDriverManager().install()), options=options
#)




def log(text):
    if True is False:
        print(text)

def scrape_yahoo_finance_article(link):
    """Scrape the content of an article from Yahoo Finance."""
    driver.get(link)
    random_delay()

    log(f"Starting scraping {link}")
    log(f"Handling cookies")

    try:
        reject_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.reject-all"))
        )
        random_click(reject_button)
        random_delay()
        log(f"Rejected cookies")

    except TimeoutException:
        log(f"There was no cookies")
        pass


    log(f"Finding article")
    try:
        main = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.article-wrap"))
        )
        log(f"Article found")
    except TimeoutException:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.upsell-content"))
            )
            return "ERROR-PAYWALL"
        except TimeoutException:
            return "ERROR-UNKNOWN-STATE"

    log(f"Finding read more button")
    try:
        read_more_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.readmore-button"))
        )
        random_click(read_more_button)
        random_delay()
        log(f"Clicked read more")

    except TimeoutException:
        log(f"Read more not found")
        pass


    log(f"Finding body")
    body = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.body"))
    )

    raw_text = extract_text(body)
    return raw_text

def scrape_investors_article(link):
    """Scrape the content of an article from Investors.com."""
    driver.get(link)
    random_delay()

    try:
        body = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.single-post-content"))
        )
    except TimeoutException:
        return "ERROR-UNKNOWN-STATE"

    text = extract_text(body)

    index = text.find("YOU MAY ALSO LIKE")
    if index != -1:
        text = text[:index]

    return text

def random_delay(min_seconds=1, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def random_click(element):
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

def load_scraped_articles(file_path="data/articles.json"):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_scraped_articles(articles, file_path="data/articles.json"):
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
    with open("data/failed_scrape.log", "a+") as f:
        line = f"{string}\n"
        f.write(line)

def main():
    rss_url = "https://finance.yahoo.com/news/rssindex"
    feed = feedparser.parse(rss_url)

    # Load already scraped articles
    scraped_articles = load_scraped_articles()
    scraped_links = {article["link"] for article in scraped_articles}

    new_articles = []
    for entry in feed.entries:
        link = entry.link

        # Skip if the article has already been scraped
        if link in scraped_links:
            continue

        if "finance.yahoo.com/research/reports/" in link:
            # Premium article
            continue

        print(f"Scraping {shorten_string(link)}", end="", flush=True)


        domain = extract_domain(link)

        if domain == "finance.yahoo.com":
            content = scrape_yahoo_finance_article(link)
        elif domain == "investors.com":
            content = scrape_investors_article(link)
        else:
            print(f" | FAILED, unsupported source: {domain}")
            continue

        if "ERROR" in content:
            if content == "ERROR-PAYWALL":
                print(f" | FAILED, premium article")
                logToFile(f"FAILED, premium article, {link}")
                continue
            else:
                print(f" | FAILED, unknown error")
                logToFile(f"FAILED, unknown error {link}")
                continue

        news_entry = {
            "priority": str(0),
            "title": purify_text(entry.title),
            "link": link,
            "published": entry.published,
            "source": entry.source.title if hasattr(entry, "source") else "Yahoo News",
            "content": purify_text(content),
        }

        new_articles.append(news_entry)
        print(f" | SUCCESS")

    if new_articles:
        scraped_articles.extend(new_articles)
        save_scraped_articles(scraped_articles)
        print(f"Saved {len(new_articles)} new articles")

    driver.quit()

if __name__ == "__main__":
    main()