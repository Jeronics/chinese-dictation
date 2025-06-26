from flask import Blueprint, render_template, request, session, g
import sqlite3
from .app_context import DictationContext
from .corrector import Corrector

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
    correction, stripped_user, stripped_correct = corrector.compare(user_input, sentence_data["chinese"])
    lev = corrector.levenshtein(stripped_user, stripped_correct)
    distance = (len(stripped_correct) - lev) * 10 // len(stripped_correct) if stripped_correct else 0
    is_correct = stripped_user == stripped_correct

    if is_correct:
        session[session_score_key] += 1
        user_id = session.get("user_id", "guest")

        for hanzi in set(stripped_correct):
            hsk_level = ctx.hsk_lookup.get(hanzi)
            if hsk_level:
                db = get_db()
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
        distance=distance,
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
    user_id = session.get("user_id", "guest")
    db = get_db()
    cursor = db.execute("""
        SELECT hsk_level,
               COUNT(*) AS total,
               SUM(CASE WHEN correct_count >= 3 THEN 1 ELSE 0 END) AS learned
        FROM progress
        WHERE user_id = ?
        GROUP BY hsk_level
        ORDER BY hsk_level
    """, (user_id,))
    data = cursor.fetchall()

    levels = []
    for row in data:
        hsk, total, learned = row
        percent = int(100 * learned / total) if total else 0
        levels.append({
            "level": hsk,
            "learned": learned,
            "total": total,
            "percent": percent
        })

    return render_template("dashboard.html", levels=levels)
