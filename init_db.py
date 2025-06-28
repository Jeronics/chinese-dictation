import sqlite3
import os

def init_db():
    db_path = os.environ.get("DB_PATH", "progress.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            user_id TEXT,
            character TEXT,
            hsk_level TEXT,
            correct_count INTEGER,
            PRIMARY KEY (user_id, character)
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
