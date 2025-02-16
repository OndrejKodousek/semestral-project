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

from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from scraper_library import *

driver = getDriver()

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
        random_click(reject_button, driver)
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
        random_click(read_more_button, driver)
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

def main():
    rss_url = "https://finance.yahoo.com/news/rssindex"
    feed = feedparser.parse(rss_url)

    scraped_articles = load_scraped_articles()
    already_scraped_links = {article["link"] for article in scraped_articles}

    new_articles = []
    for entry in feed.entries:
        link = entry.link

        if link in already_scraped_links:
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
        elif domain == "wsj.com":
            print(f" | FAILED, Wallstreet Journal has scraping protection")
            continue
        elif domain == "barrons.com":
            print(f" | FAILED, Barrons is paywalled")
            continue            
        else:
            print(f" | FAILED, unknown source: {domain}")
            continue

        if "ERROR" in content:
            if content == "ERROR-PAYWALL":
                print(f" | FAILED, paywalled article")
                logToFile(f"FAILED, paywalled article, {link}")
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