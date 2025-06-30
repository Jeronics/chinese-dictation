from dotenv import load_dotenv
import os
load_dotenv()

import uuid

from flask import Blueprint, render_template, request, session, g
import sqlite3
from .app_context import DictationContext
from .corrector import Corrector
import os
from flask import request, redirect, session, render_template
from supabase import create_client

dictation_bp = Blueprint("dictation", __name__)
ctx = DictationContext()
corrector = Corrector()

### ──────── DATABASE CONNECTION ────────

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("progress.db")
    return g.db

@dictation_bp.teardown_app_request
def close_connection(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()

### ──────── DICTATION RESULT RENDERING ────────

def render_dictation_result(user_input, sentence_data, session_score_key, show_next=False, current=None, total=None):
    correction, stripped_user, stripped_correct, correct_segments = corrector.compare(user_input, sentence_data["chinese"])
    lev = corrector.levenshtein(stripped_user, stripped_correct)
    distance = (len(stripped_correct) - lev) * 10 // len(stripped_correct) if stripped_correct else 0
    accuracy = round(len(correct_segments)/len(stripped_correct)*100)
    is_correct = stripped_user == correct_segments

    if lev > 1:
        session[session_score_key] += 1
        user_id = session.get("user_id")
        db = get_db()

        for hanzi in set(correct_segments):
            hsk_level = ctx.hsk_lookup.get(hanzi)
            if hsk_level:
                db.execute("""
                    INSERT INTO progress (user_id, character, hsk_level, correct_count)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(user_id, character) DO UPDATE SET correct_count = correct_count + 1
                """, (user_id, hanzi, hsk_level))
        db.commit()

    return render_template(
        "index.html",
        correct_sentence=sentence_data["chinese"],
        result="✅ Correct!" if is_correct else "❌ Try again.",
        correction=correction,
        accuracy=accuracy,
        score=session[session_score_key],
        level=session.get("level", 1),
        difficulty=sentence_data["difficulty"],
        show_result=True,
        audio_file=ctx.audio_path(sentence_data["id"], sentence_data["difficulty"]),
        translation=sentence_data["translation"],
        pinyin=sentence_data["pinyin"],
        session_mode=show_next,
        current=current,
        total=total,
        show_next_button=show_next,
    )

### ──────── ROUTES ────────

@dictation_bp.route("/")
def menu():
    
    # clear HSK level, session_ids, etc.
    for key in ["session_ids", "session_index", "session_score", "hsk_level"]:
        session.pop(key, None)

    return render_template("menu.html")

@dictation_bp.route("/practice/<sid>", methods=["GET", "POST"])
def practice(sid):
    if "score" not in session:
        session.update(score=0, level=1)

    s = ctx.get_sentence(sid)
    s["id"] = sid
    if not ctx.audio_path(sid, s["difficulty"]):
        return "Missing audio file", 500

    if request.method == "POST":
        user_input = request.form["user_input"].strip()
        return render_dictation_result(user_input, s, session_score_key="score")

    return render_template("index.html",
        correct_sentence=s["chinese"],
        audio_file=ctx.audio_path(sid, s["difficulty"]),
        score=session["score"],
        level=session.get("level", 1),
        difficulty=s["difficulty"],
        show_result=False
    )

@dictation_bp.route("/session", methods=["GET", "POST"])
def session_practice():
    if "session_ids" not in session:
        level = request.args.get("hsk")
        session.update(
            hsk_level=level,
            session_ids=ctx.get_random_ids(level=level),
            session_index=0,
            session_score=0
        )

    if request.method == "POST" and "next" in request.form:
        session["session_index"] += 1
        if session["session_index"] >= 5:
            score = session["session_score"]
            level = session.get("hsk_level")
            session.clear()
            for key in ["session_ids", "session_index", "session_score", "hsk_level"]:
                session.pop(key, None)
            return render_template("session_summary.html", score=score, total=5, level=level)

    sid = session["session_ids"][session["session_index"]]
    s = ctx.get_sentence(sid)
    s["id"] = sid
    if not ctx.audio_path(sid, s["difficulty"]):
        return "Missing audio file", 500

    if request.method == "POST" and "user_input" in request.form:
        user_input = request.form["user_input"].strip()
        return render_dictation_result(
            user_input, s,
            session_score_key="session_score",
            show_next=True,
            current=session["session_index"] + 1,
            total=5
        )

    return render_template("index.html",
        correct_sentence=s["chinese"],
        audio_file=ctx.audio_path(sid, s["difficulty"]),
        score=session["session_score"],
        level=session.get("level", 1),
        difficulty=s["difficulty"],
        show_result=False,
        session_mode=True,
        current=session["session_index"] + 1,
        total=5
    )

@dictation_bp.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    
    db = get_db()
    cursor = db.execute("""
        SELECT hsk_level,
               COUNT(*) AS learned
        FROM progress
        WHERE user_id = ? AND correct_count >= 1
        GROUP BY hsk_level
    """, (user_id,))
    learned_data = {row[0]: row[1] for row in cursor.fetchall()}

    levels = []
    for hsk_level, total in ctx.hsk_totals.items():
        learned = learned_data.get(hsk_level, 0)
        percent = int(100 * learned / total) if total else 0
        levels.append({
            "level": hsk_level,
            "learned": learned,
            "total": total,
            "percent": percent
        })

    return render_template("dashboard.html", levels=levels)


supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

@dictation_bp.before_app_request
def assign_guest_user_id():
    if "user_id" not in session:
        session["user_id"] = f"guest-{uuid.uuid4()}"

@dictation_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            result = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            user = result.user
            old_guest_id = session.get("user_id")
            new_user_id = user.id

            # Actualitzar progrés de guest → nou user_id
            db = get_db()
            db.execute("""
                UPDATE progress SET user_id = ?
                WHERE user_id = ?
            """, (new_user_id, old_guest_id))
            db.commit()

            session["user_id"] = new_user_id
            session["email"] = user.email
            return redirect("/")
        except Exception as e:
            return f"Login failed: {e}"


    return render_template("login.html")

@dictation_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            result = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            return redirect("/login")
        except Exception as e:
            return f"Signup failed: {e}"

    return render_template("signup.html")

@dictation_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
