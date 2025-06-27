import sqlite3

conn = sqlite3.connect("progress.db")
conn.execute("""
CREATE TABLE IF NOT EXISTS progress (
    user_id TEXT,
    character TEXT,
    hsk_level TEXT,
    correct_count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, character)
)
""")
conn.commit()
conn.close()

print("✅ Base de dades inicialitzada correctament.")
