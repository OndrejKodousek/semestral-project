import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect("data/news.db")
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

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS summarized_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    summarized_analysis_id INTEGER NOT NULL,
    date DATE NOT NULL,
    prediction FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    FOREIGN KEY (summarized_analysis_id) REFERENCES summarized_analysis(id) ON DELETE CASCADE -- Added ON DELETE CASCADE
);
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS lstm_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    prediction_made_date DATETIME NOT NULL,
    prediction_target_date DATE NOT NULL, -- Date the value applies to (actual or predicted)
    value FLOAT NOT NULL,                -- Stores actual or predicted value
    is_reference INTEGER NOT NULL DEFAULT 0 -- 0 = Prediction, 1 = Actual reference value
);
"""
)

# --- Indices (adjust if needed, maybe add is_actual) ---
cursor.execute(
    """
CREATE INDEX IF NOT EXISTS idx_lstm_ticker_target_date
ON lstm_predictions (ticker, prediction_target_date);
"""
)

cursor.execute(
    """
CREATE INDEX IF NOT EXISTS idx_lstm_ticker_made_date
ON lstm_predictions (ticker, prediction_made_date);
"""
)

# Optional index including is_actual might be useful
cursor.execute(
    """
CREATE INDEX IF NOT EXISTS idx_lstm_ticker_made_actual_target
ON lstm_predictions (ticker, prediction_made_date, is_reference, prediction_target_date);
"""
)


conn.commit()
conn.close()
