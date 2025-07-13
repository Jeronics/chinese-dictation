from dotenv import load_dotenv
import os
load_dotenv()

import uuid

from flask import Blueprint, render_template, request, session, redirect, flash
from .app_context import DictationContext
from .corrector import Corrector
from supabase import create_client

# Configuració de Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
if SUPABASE_URL is None or SUPABASE_KEY is None:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")
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

def render_dictation_result(user_input, sentence_data, session_score_key, show_next=False, current=None, total=None, is_story_part=False, story_context=None, story_title=None, story_difficulty=None):
    correction, stripped_user, stripped_correct, correct_segments = corrector.compare(user_input, sentence_data["chinese"])
    lev = corrector.levenshtein(stripped_user, stripped_correct)
    distance = (len(stripped_correct) - lev) * 10 // len(stripped_correct) if stripped_correct else 0
    accuracy = round(len(correct_segments)/len(stripped_correct)*100)
    is_correct = stripped_user == correct_segments

    session[session_score_key] += 1
    user_id = session.get("user_id")

    # Only update character progress for logged-in users (not guests)
    if user_id and not str(user_id).startswith("guest-"):
        for hanzi in set(sentence_data["chinese"]):
            match = next((entry for entry in ctx.hsk_data if entry["hanzi"] == hanzi), None)
            if match:
                hsk_level = match["hsk_level"]
                # If the hanzi is in the correct_segments, mark as correct, else as failed
                correct = hanzi in correct_segments
                update_character_progress(user_id, hanzi, hsk_level, correct)
    else:
        print("[INFO] Not saving progress: user is not logged in.")

    # Determine audio file path based on whether it's a story part or regular sentence
    if is_story_part:
        audio_file = ctx.story_audio_path(sentence_data["id"])
    else:
        audio_file = ctx.audio_path(sentence_data["id"], sentence_data["difficulty"])

    # Determine difficulty based on whether it's a story part or regular sentence
    if is_story_part and story_difficulty:
        difficulty = story_difficulty
    else:
        difficulty = sentence_data.get("difficulty", "Unknown")
    
    return render_template(
        "index.html",
        correct_sentence=sentence_data["chinese"],
        result="✅ Correct!" if is_correct else "❌ Try again.",
        correction=correction,
        accuracy=accuracy,
        score=session[session_score_key],
        level=session.get("level", 1),
        difficulty=difficulty,
        show_result=True,
        audio_file=audio_file,
        translation=sentence_data["translation"],
        pinyin=sentence_data["pinyin"],
        session_mode=show_next,
        current=current,
        total=total,
        show_next_button=show_next,
        story_mode=is_story_part,
        story_context=story_context,
        story_title=story_title
    )

### ──────── ROUTES ────────

@dictation_bp.route("/")
def menu():
    
    # clear HSK level, session_ids, etc.
    for key in ["session_ids", "session_index", "session_score", "hsk_level"]:
        session.pop(key, None)

    # Get saved stories for logged-in users
    saved_stories = []
    user_id = session.get("user_id")
    if user_id and not str(user_id).startswith("guest-"):
        try:
            result = supabase.table("story_progress").select("story_id").eq("user_id", user_id).execute()
            saved_stories = [row["story_id"] for row in result.data] if result.data else []
        except Exception as e:
            print(f"Error loading saved stories: {e}")
            saved_stories = []

    print(f"Debug: Loading menu with {len(ctx.stories)} stories")
    print(f"Debug: Stories keys: {list(ctx.stories.keys())}")
    print(f"Debug: HSK totals: {ctx.hsk_totals}")
    return render_template("menu.html", stories=ctx.stories, saved_stories=saved_stories, hsk_totals=ctx.hsk_totals)



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

@dictation_bp.before_app_request
def assign_guest_user_id():
    if "user_id" not in session:
        session["user_id"] = f"guest-{uuid.uuid4()}"

@dictation_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        print(f"Login attempt for email: {email}")
        print(f"Supabase URL: {SUPABASE_URL}")
        print(f"Supabase Key exists: {SUPABASE_KEY is not None}")
        
        try:
            result = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            user = result.user
            if user is None:
                raise Exception("No user returned from Supabase.")
            
            print(f"Login successful for user: {user.id}")
            old_guest_id = session.get("user_id")
            new_user_id = user.id

            # Update character progress for guest user
            try:
                supabase.table("character_progress").update({
                    "user_id": new_user_id
                }).eq("user_id", old_guest_id).execute()
                print(f"Updated character progress from {old_guest_id} to {new_user_id}")
            except Exception as e:
                print(f"Warning: Could not update character progress: {e}")

            session["user_id"] = new_user_id
            session["email"] = user.email
            return redirect("/")
        except Exception as e:
            print(f"Login error: {e}")
            error = f"Login failed: {str(e)}"

    return render_template("login.html", error=error)

@dictation_bp.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        print(f"Signup attempt for email: {email}")
        
        try:
            result = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            print(f"Signup successful for user: {result.user.id if result.user else 'No user'}")
            return redirect("/login")
        except Exception as e:
            print(f"Signup error: {e}")
            error = f"Signup failed: {str(e)}"

    return render_template("signup.html", error=error)

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







@dictation_bp.route("/story/<story_id>/session", methods=["GET", "POST"])
def story_session(story_id):
    # Handle both story IDs and story titles
    story = ctx.get_story(story_id)
    if not story:
        # Try to find story by title
        for sid, s in ctx.stories.items():
            if s["title"].lower().replace(" ", "_").replace("'", "") == story_id:
                story = s
                story_id = sid
                break
    
    if not story:
        return "Story not found", 404

    user_id = session.get("user_id")
    
    # Check if user wants to resume or restart
    if request.method == "POST" and "resume_later" in request.form:
        # Save current progress to database for logged-in users
        if user_id and not str(user_id).startswith("guest-"):
            try:
                # Save story progress
                supabase.table("story_progress").upsert({
                    "user_id": user_id,
                    "story_id": story_id,
                    "current_index": session.get("story_session_index", 0),
                    "score": session.get("story_session_score", 0),
                    "total_parts": len(story["parts"]),
                    "last_updated": "now()"
                }).execute()
                print(f"Saved story progress for user {user_id}, story {story_id}")
                flash(f"Progress saved! You can resume '{story['title']}' later.", "success")
            except Exception as e:
                print(f"Error saving story progress: {e}")
                flash("Failed to save progress. Please try again.", "error")
        else:
            flash("Please log in to save your progress.", "warning")
        
        # Clear session and redirect to main menu
        for key in ["story_session_ids", "story_session_index", "story_session_score", "story_id"]:
            session.pop(key, None)
        return redirect("/")
    
    if request.method == "POST" and "restart" in request.form:
        # Clear any existing progress and restart
        if user_id and not str(user_id).startswith("guest-"):
            try:
                supabase.table("story_progress").delete().eq("user_id", user_id).eq("story_id", story_id).execute()
                print(f"Cleared story progress for user {user_id}, story {story_id}")
            except Exception as e:
                print(f"Error clearing story progress: {e}")
        
        # Clear session data
        for key in ["story_session_ids", "story_session_index", "story_session_score", "story_id"]:
            session.pop(key, None)
        return redirect(f"/story/{story_id}/session")
    
    # Check for existing progress if no session data
    if "story_session_ids" not in session or session.get("story_id") != story_id:
        # Try to load existing progress for logged-in users
        existing_progress = None
        if user_id and not str(user_id).startswith("guest-"):
            try:
                result = supabase.table("story_progress").select("*").eq("user_id", user_id).eq("story_id", story_id).execute()
                if result.data:
                    existing_progress = result.data[0]
                    print(f"Found existing progress for user {user_id}, story {story_id}")
            except Exception as e:
                print(f"Error loading story progress: {e}")
        
        if existing_progress:
            # Resume from saved progress
            session.update(
                story_id=story_id,
                story_session_ids=[part["id"] for part in story["parts"]],
                story_session_index=existing_progress["current_index"],
                story_session_score=existing_progress["score"]
            )
            flash(f"Resuming '{story['title']}' from part {existing_progress['current_index'] + 1} of {len(story['parts'])}", "info")
        else:
            # Initialize new story session
            session.update(
                story_id=story_id,
                story_session_ids=[part["id"] for part in story["parts"]],
                story_session_index=0,
                story_session_score=0
            )

    if request.method == "POST" and "next" in request.form:
        session["story_session_index"] += 1
        if session["story_session_index"] >= len(story["parts"]):
            score = session["story_session_score"]
            total = len(story["parts"])
            
            # Clear story progress from database when completed
            if user_id and not str(user_id).startswith("guest-"):
                try:
                    supabase.table("story_progress").delete().eq("user_id", user_id).eq("story_id", story_id).execute()
                    print(f"Cleared completed story progress for user {user_id}, story {story_id}")
                except Exception as e:
                    print(f"Error clearing completed story progress: {e}")
            
            # Clear story session data
            for key in ["story_session_ids", "story_session_index", "story_session_score", "story_id"]:
                session.pop(key, None)
            return render_template("story_summary.html", score=score, total=total, story=story, story_id=story_id)

    part_id = session["story_session_ids"][session["story_session_index"]]
    part = ctx.get_story_part(story_id, part_id)
    if not part:
        return "Story part not found", 500

    if request.method == "POST" and "user_input" in request.form:
        user_input = request.form["user_input"].strip()
        return render_dictation_result(
            user_input, part,
            session_score_key="story_session_score",
            show_next=True,
            current=session["story_session_index"] + 1,
            total=len(story["parts"]),
            is_story_part=True,
            story_context=story["parts"][:session["story_session_index"]],
            story_title=story["title"],
            story_difficulty=story["difficulty"]
        )

    # Get story context (previous parts only, not the current one)
    story_context = story["parts"][:session["story_session_index"]]
    
    return render_template("index.html",
        correct_sentence=part["chinese"],
        audio_file=ctx.story_audio_path(part_id),  # Use story audio path
        score=session["story_session_score"],
        level=session.get("level", 1),
        difficulty=story["difficulty"],
        show_result=False,
        session_mode=True,
        current=session["story_session_index"] + 1,
        total=len(story["parts"]),
        story_mode=True,
        story_title=story["title"],
        story_context=story_context
    )
