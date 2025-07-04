from dotenv import load_dotenv
import os
load_dotenv()

import uuid

from flask import Blueprint, render_template, request, session, redirect
from .app_context import DictationContext
from .corrector import Corrector
from supabase import create_client

# Configuració de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

dictation_bp = Blueprint("dictation", __name__)
ctx = DictationContext()
corrector = Corrector()

# --- Helper functions for character progress tracking ---
def update_character_progress(user_id, hanzi, hsk_level, correct):
    # Fetch existing record
    result = supabase.table("character_progress").select("*") \
        .eq("user_id", user_id).eq("hanzi", hanzi).execute()
    if result.data:
        progress = result.data[0]
        correct_count = progress["correct_count"] + (1 if correct else 0)
        fail_count = progress["fail_count"] + (0 if correct else 1)
        # Determine new status
        if correct_count >= 3:
            status = "known"
        elif fail_count >= 2:
            status = "failed"
        else:
            status = "learning"
        supabase.table("character_progress").update({
            "correct_count": correct_count,
            "fail_count": fail_count,
            "status": status,
            "last_seen": "now()"
        }).eq("user_id", user_id).eq("hanzi", hanzi).execute()
    else:
        supabase.table("character_progress").insert({
            "user_id": user_id,
            "hanzi": hanzi,
            "hsk_level": hsk_level,
            "correct_count": 1 if correct else 0,
            "fail_count": 0 if correct else 1,
            "status": "known" if correct else "failed",
            "last_seen": "now()"
        }).execute()

def get_user_character_status(user_id):
    # Returns a dict: {hanzi: status}
    result = supabase.table("character_progress").select("hanzi, status").eq("user_id", user_id).execute()
    return {row["hanzi"]: row["status"] for row in result.data} if result.data else {}

def render_dictation_result(user_input, sentence_data, session_score_key, show_next=False, current=None, total=None):
    correction, stripped_user, stripped_correct, correct_segments = corrector.compare(user_input, sentence_data["chinese"])
    lev = corrector.levenshtein(stripped_user, stripped_correct)
    distance = (len(stripped_correct) - lev) * 10 // len(stripped_correct) if stripped_correct else 0
    accuracy = round(len(correct_segments)/len(stripped_correct)*100)
    is_correct = stripped_user == correct_segments

    session[session_score_key] += 1
    user_id = session.get("user_id")

    # Update character progress for each hanzi in the sentence
    for hanzi in set(sentence_data["chinese"]):
        match = next((entry for entry in ctx.hsk_data if entry["hanzi"] == hanzi), None)
        if match:
            hsk_level = match["hsk_level"]
            # If the hanzi is in the correct_segments, mark as correct, else as failed
            correct = hanzi in correct_segments
            update_character_progress(user_id, hanzi, hsk_level, correct)

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
    try:
        response = supabase.table("character_progress") \
            .select("hsk_level, status") \
            .eq("user_id", user_id).execute()
        # Count known, failed, and learning per HSK level
        stats = {}
        for row in response.data:
            level = row["hsk_level"]
            status = row["status"]
            if level not in stats:
                stats[level] = {"known": 0, "failed": 0, "learning": 0}
            stats[level][status] += 1
    except Exception as e:
        print("Error loading progress from Supabase:", e)
        stats = {}
    # Prepare levels for dashboard
    levels = []
    for hsk_level, total in ctx.hsk_totals.items():
        level_stats = stats.get(hsk_level, {"known": 0, "failed": 0, "learning": 0})
        percent = int(100 * level_stats["known"] / total) if total else 0
        levels.append({
            "level": hsk_level,
            "known": level_stats["known"],
            "failed": level_stats["failed"],
            "learning": level_stats["learning"],
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

            supabase.table("progress").update({
                "user_id": new_user_id
            }).eq("user_id", old_guest_id).execute()


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

@dictation_bp.route("/hsk/<level>")
def hsk_level_detail(level):
    user_id = session.get("user_id")
    # Get all hanzi for this level
    hanzi_list = [item for item in ctx.hsk_data if item["hsk_level"] == level]
    # Get user progress for these hanzi
    result = supabase.table("character_progress").select("hanzi, correct_count, fail_count, status").eq("user_id", user_id).execute()
    progress = {row["hanzi"]: row for row in result.data} if result.data else {}
    # Prepare data for template
    char_data = []
    for item in hanzi_list:
        hanzi = item["hanzi"]
        p = progress.get(hanzi)
        if p:
            status = p["status"]
            correct_count = p["correct_count"]
            fail_count = p["fail_count"]
        else:
            status = "unseen"
            correct_count = 0
            fail_count = 0
        char_data.append({
            "hanzi": hanzi,
            "status": status,
            "correct_count": correct_count,
            "fail_count": fail_count
        })
    return render_template("hsk_level_detail.html", level=level, char_data=char_data, min=min)
