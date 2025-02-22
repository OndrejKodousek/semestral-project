import sqlite3

conn = sqlite3.connect("news.db")
cursor = conn.cursor()

# cursor.execute(
#    """
# CREATE TABLE IF NOT EXISTS articles (
#    id INTEGER PRIMARY KEY AUTOINCREMENT,
#    priority INTEGER NOT NULL,
#    link TEXT UNIQUE NOT NULL,
#    title TEXT NOT NULL,
#    published DATETIME NOT NULL,
#    source TEXT NOT NULL,
#    content TEXT NOT NULL
# );
# """
# )
# TODO: It might be possible to use JSON data structure
cursor.execute(
    """
CREATE TABLE analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    published DATETIME NOT NULL,
    ticker TEXT NOT NULL,
    stock TEXT NOT NULL,
    summary TEXT NOT NULL,
    pred_1_day FLOAT NOT NULL,  -- Prediction for 1 day
    conf_1_day FLOAT NOT NULL,  -- Confidence for 1 day
    pred_2_day FLOAT NOT NULL,  -- Prediction for 2 days
    conf_2_day FLOAT NOT NULL,  -- Confidence for 2 days
    pred_3_day FLOAT NOT NULL,  -- Prediction for 3 days
    conf_3_day FLOAT NOT NULL,  -- Confidence for 3 days
    pred_4_day FLOAT NOT NULL,  -- Prediction for 4 days
    conf_4_day FLOAT NOT NULL,  -- Confidence for 4 days
    pred_5_day FLOAT NOT NULL,  -- Prediction for 5 days
    conf_5_day FLOAT NOT NULL,  -- Confidence for 5 days
    pred_6_day FLOAT NOT NULL,  -- Prediction for 6 days
    conf_6_day FLOAT NOT NULL,  -- Confidence for 6 days
    pred_7_day FLOAT NOT NULL,  -- Prediction for 7 days
    conf_7_day FLOAT NOT NULL,  -- Confidence for 7 days
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
"""
)

conn.commit()
conn.close()

print("Database and tables created successfully!")
