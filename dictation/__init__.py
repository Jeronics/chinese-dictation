from flask import Flask
from .routes import dictation_bp

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = "dev-key"
    app.register_blueprint(dictation_bp)
    return app
