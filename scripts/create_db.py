"""
@file create_db.py
@brief Database schema creation script.

This script creates the SQLite database schema for the stock news analysis system.
It defines all tables needed for storing articles, analyses, predictions, and LSTM results.
"""

import sqlite3
from datetime import datetime, timedelta

# Establish database connection
conn = sqlite3.connect("data/news.db")
cursor = conn.cursor()

# Create articles table
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    priority INTEGER NOT NULL,
    link TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    published DATETIME NOT NULL,
    source TEXT NOT NULL,
    content TEXT NOT NULL
);
"""
)

# Create analysis table
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    published DATETIME NOT NULL,
    ticker TEXT NOT NULL,
    stock TEXT NOT NULL,
    summary TEXT NOT NULL,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
"""
)

# Create predictions table
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER NOT NULL,
    date DATE NOT NULL,
    prediction FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    FOREIGN KEY (analysis_id) REFERENCES analysis(id)
);
"""
)

# Create summarized_analysis table
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS summarized_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    ticker TEXT NOT NULL,
    last_updated DATETIME NOT NULL,
    summary_text TEXT NOT NULL,
    UNIQUE(model_name, ticker)
);
"""
)

# Create summarized_predictions table
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS summarized_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summarized_analysis_id INTEGER NOT NULL,
    date DATE NOT NULL,
    prediction FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    FOREIGN KEY (summarized_analysis_id) REFERENCES summarized_analysis(id) ON DELETE CASCADE
);
"""
)

# Create lstm_predictions table
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS lstm_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    prediction_made_date DATETIME NOT NULL,
    prediction_target_date DATE NOT NULL,
    value FLOAT NOT NULL,
    is_reference INTEGER NOT NULL DEFAULT 0
);
"""
)

# Commit changes and close connection
conn.commit()
conn.close()