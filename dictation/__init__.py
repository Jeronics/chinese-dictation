import os
from flask import Flask
from .routes import dictation_bp

# Carrega les variables d'entorn des del fitxer `.env`
from dotenv import load_dotenv
load_dotenv()

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    app.secret_key = "dev-key"
    app.register_blueprint(dictation_bp)

    return app
