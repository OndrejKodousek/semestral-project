import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("news.db")
cursor = conn.cursor()

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

conn.commit()
conn.close()

print("Database and tables created successfully! Data inserted.")
