"""
@file scraper_library.py
@brief Utility functions for web scraping operations.

This module provides common functions used across scraping scripts including:
- Database operations
- Web driver management
- Text processing utilities
- Randomization helpers
"""

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
from pathlib import Path

# Global webdriver instance
driver = None


def get_project_root():
    """
    @brief Locates the project root directory by searching for .git marker.

    @return Path object pointing to project root directory
    @throws SystemExit if root directory cannot be found
    """
    marker = ".git"
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker).exists():
            return parent
    print("ERROR: Failed to find root folder of project")
    exit(1)


def execute_query(
    query, params=None, timeout=300.0, query_type="SELECT", use_row_factory=True
):
    """
    @brief Executes a SQL query against the database.

    @param query SQL query string
    @param params Parameters for parameterized queries
    @param timeout Database timeout in seconds
    @param query_type Type of query ('SELECT', 'INSERT', 'UPDATE', 'DELETE')
    @param use_row_factory Whether to use sqlite3.Row factory
    @return Query results for SELECT, affected rows count for others
    """
    try:
        if query_type not in {"SELECT", "INSERT", "UPDATE", "DELETE"}:
            raise ValueError(
                "query_type must be one of 'SELECT', 'INSERT', 'UPDATE', 'DELETE'"
            )

        db_path = os.path.join(get_project_root(), "data", "news.db")
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
    """
    @brief Initializes and returns a headless Chrome webdriver.

    @return Configured WebDriver instance
    """
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
    """
    @brief Conditional logging function.

    @param text Message to log
    """
    if True is False:
        print(text)


def random_delay(min_seconds=1, max_seconds=5):
    """
    @brief Introduces a random delay between operations.

    @param min_seconds Minimum delay in seconds
    @param max_seconds Maximum delay in seconds
    """
    time.sleep(random.uniform(min_seconds, max_seconds))


def random_click(element, driver):
    """
    @brief Performs a randomized click action on an element.

    @param element WebElement to click
    @param driver WebDriver instance
    """
    action = ActionChains(driver)
    x_offset = random.randint(-10, 10)
    y_offset = random.randint(-10, 10)
    action.move_to_element_with_offset(element, x_offset, y_offset).click().perform()


def extract_text(element):
    """
    @brief Extracts text content from HTML element.

    @param element WebElement containing content
    @return Concatenated text from all <p> tags
    """
    p_tags = element.find_elements(By.CSS_SELECTOR, "p")
    return "".join(tag.get_attribute("innerHTML") for tag in p_tags)


def purify_text(input_text):
    """
    @brief Cleans and normalizes text content.

    @param input_text Raw HTML or text input
    @return Cleaned ASCII text
    """
    soup = BeautifulSoup(input_text, "html.parser")
    text = soup.get_text().strip()

    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ASCII", "ignore").decode("ASCII")

    return ascii_text


def shorten_string(link, max_length=80):
    """
    @brief Shortens a string to specified length with ellipsis.

    @param link Input string to shorten
    @param max_length Maximum length of output string
    @return Shortened string with ellipsis
    """
    if len(link) <= max_length:
        spaces = max_length - len(link)
        return link + (" " * spaces)
    part_length = (max_length - 3) // 2
    return link[:part_length] + "..." + link[-part_length:]


def extract_domain(link):
    """
    @brief Extracts domain name from URL.

    @param link Full URL
    @return Base domain without www prefix
    """
    parsed_url = urlparse(link)
    netloc = parsed_url.netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc


def logToFile(string):
    """
    @brief Logs message to scraper log file.

    @param string Message to log
    """
    file_path = os.path.join(get_project_root(), "scraper", "scraper_log.log")

    with open(file_path, "a+") as f:
        line = f"{string}\n"
        f.write(line)
