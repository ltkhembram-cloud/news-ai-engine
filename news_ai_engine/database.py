import sqlite3

DB_FILE = "news_intelligence.db"


def init_db(db_path: str = DB_FILE):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    chat_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    language TEXT DEFAULT 'Bengali',
                    delivery_hour INTEGER DEFAULT 9,
                    delivery_minute INTEGER DEFAULT 30,
                    is_active INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_interests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    topic TEXT,
                    frequency INTEGER DEFAULT 1,
                    last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, topic)
                )""")
    conn.commit()
    conn.close()


def register_or_update_user(
    chat_id: int,
    first_name: str,
    language: str = "Bengali",
    hour: int = 9,
    minute: int = 30,
    db_path: str = DB_FILE
):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""INSERT INTO users (chat_id, first_name, language, delivery_hour, delivery_minute, is_active, updated_at)
                 VALUES (?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                 ON CONFLICT(chat_id) DO UPDATE SET
                    first_name=excluded.first_name,
                    language=excluded.language,
                    delivery_hour=excluded.delivery_hour,
                    delivery_minute=excluded.delivery_minute,
                    is_active=1,
                    updated_at=CURRENT_TIMESTAMP""",
              (chat_id, first_name, language, hour, minute))
    conn.commit()
    conn.close()


def get_user_language(chat_id: int, db_path: str = DB_FILE) -> str:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT language FROM users WHERE chat_id = ?", (chat_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else "Bengali"


def log_search_interest(chat_id: int, topic: str, db_path: str = DB_FILE):
    clean_topic = topic.strip().title()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""INSERT INTO user_interests (chat_id, topic, frequency, last_searched)
                 VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                 ON CONFLICT(chat_id, topic) DO UPDATE SET
                    frequency = frequency + 1,
                    last_searched = CURRENT_TIMESTAMP""",
              (chat_id, clean_topic))
    conn.commit()
    conn.close()


def get_top_interests(chat_id: int, limit: int = 3, db_path: str = DB_FILE) -> list:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""SELECT topic FROM user_interests
                 WHERE chat_id = ?
                 ORDER BY frequency DESC, last_searched DESC
                 LIMIT ?""", (chat_id, limit))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


def get_active_subscribers(db_path: str = DB_FILE) -> list:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT chat_id, first_name, language, delivery_hour, delivery_minute FROM users WHERE is_active = 1")
    rows = c.fetchall()
    conn.close()
    return rows
