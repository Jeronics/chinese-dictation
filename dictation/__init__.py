import os
import sqlite3
from flask import Flask
from .routes import dictation_bp


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")


    db_path = os.environ.get("DB_PATH", "progress.db")
    app.config["DB_PATH"] = db_path

    # ✅ Initialize the DB at app startup
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                user_id TEXT,
                character TEXT,
                hsk_level TEXT,
                correct_count INTEGER,
                PRIMARY KEY (user_id, character)
            )
        """)
        conn.commit()

    app.secret_key = "dev-key"
    app.register_blueprint(dictation_bp)

    return app