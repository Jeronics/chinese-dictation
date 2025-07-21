import os
from flask import Flask
from markupsafe import Markup
from .routes import dictation_bp
import re

# Carrega les variables d'entorn des del fitxer `.env`
from dotenv import load_dotenv
load_dotenv()

def clickable_hanzi(text):
    # This regex will find Chinese characters
    hanzi_re = re.compile(r'[\u4e00-\u9fff]')
    
    def repl(m):
        char = m.group(0)
        return f'<span class="hanzi-char" onclick="showStrokeOrder(\'{char}\')">{char}</span>'

    # Use the regex to replace all Chinese characters with the clickable version
    return Markup(hanzi_re.sub(repl, text))

def create_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static")
    )
    app.secret_key = os.environ.get("SECRET_KEY", "dev")
    app.jinja_env.filters["clickable_hanzi"] = clickable_hanzi
    app.register_blueprint(dictation_bp)
    # Register the admin dashboard blueprint
    from admin_dashboard import admin_bp as admin_dashboard_bp
    app.register_blueprint(admin_dashboard_bp)
    return app
