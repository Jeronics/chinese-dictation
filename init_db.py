import os
import sqlite3

if not os.path.exists("progress.db"):
    conn = sqlite3.connect("progress.db")
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
    print("Database created.")
else:
    print("Database already exists.")
