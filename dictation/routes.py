from dotenv import load_dotenv
import os
load_dotenv()

import uuid
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request, session, redirect, flash, url_for
from functools import wraps
from .app_context import DictationContext
from .corrector import Corrector
from .db_helpers import (
    update_character_progress,
    get_user_character_status,
    update_daily_work_registry,
    get_daily_work_stats
)
from .utils import login_required
from supabase import create_client
import logging

logging.basicConfig(level=logging.INFO)

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
# (Moved to db_helpers.py)

# --- Helper functions for daily work tracking ---
# (Moved to db_helpers.py)

def render_dictation_result(user_input, sentence_data, session_score_key, show_next=False, current=None, total=None, is_story_part=False, story_context=None, story_title=None, story_difficulty=None):
    """
    Render the result page for a dictation attempt, showing correction, accuracy, and updating user progress.
    Handles both regular sentences and story parts.
    """
    correction, stripped_user, stripped_correct, correct_segments = corrector.compare(user_input, sentence_data["chinese"])
    lev = corrector.levenshtein(stripped_user, stripped_correct)
    distance = (len(stripped_correct) - lev) * 10 // len(stripped_correct) if stripped_correct else 0
    accuracy = round(len(correct_segments)/len(stripped_correct)*100)
    is_correct = stripped_user == correct_segments

    session[session_score_key] += 1
    user_id = session.get("user_id")

    # Update character progress for logged-in users
    if user_id:
        for hanzi in set(sentence_data["chinese"]):
            match = next((entry for entry in ctx.hsk_data if entry["hanzi"] == hanzi), None)
            if match:
                hsk_level = match["hsk_level"]
                # If the hanzi is in the correct_segments, mark as correct, else as failed
                correct = hanzi in correct_segments
                update_character_progress(user_id, hanzi, hsk_level, correct)
        
        # Store accuracy scores in session for later averaging
        # Initialize accuracy tracking if not exists
        if "accuracy_scores" not in session:
            session["accuracy_scores"] = []
        
        # Store the distance score (0-10 scale) for this sentence
        session["accuracy_scores"].append(distance)
        logging.debug(f"Added distance score {distance} to accuracy_scores. Current scores: {session['accuracy_scores']}")

    # Determine audio file path based on whether it's a story part or regular sentence
    if is_story_part:
        # Extract story_id and part_number from sentence_data['id']
        try:
            parts = sentence_data["id"].split('_')
            story_id = parts[1]
            part_number = int(parts[2])
        except Exception:
            story_id = None
            part_number = None
        audio_file = ctx.story_audio_path(story_id, part_number) if story_id and part_number else None
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
        result="Correct!" if is_correct else "Try again.",
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
    """
    Main menu route. Clears session state and loads available stories and HSK totals for the user.
    """
    # clear HSK level, session_ids, etc.
    for key in ["session_ids", "session_index", "session_score", "hsk_level"]:
        session.pop(key, None)

    # Get saved stories for logged-in users
    saved_stories = []
    user_id = session.get("user_id")
    if user_id:
        try:
            result = supabase.table("story_progress").select("story_id").eq("user_id", user_id).execute()
            saved_stories = [row["story_id"] for row in result.data] if result.data else []
        except Exception as e:
            logging.error(f"Error loading saved stories: {e}")
            saved_stories = []

    return render_template("menu.html", stories=ctx.stories, saved_stories=saved_stories, hsk_totals=ctx.hsk_totals)



@dictation_bp.route("/session", methods=["GET", "POST"])
def session_practice():
    """
    Main dictation practice session route. Handles session state, user answers, and session summary.
    """
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
            user_id = session.get("user_id")
            
            # Calculate average accuracy for the session
            average_accuracy = 0
            logging.debug(f"Session accuracy_scores: {session.get('accuracy_scores', 'Not found')}")
            logging.debug(f"User ID: {user_id}")
            if user_id and "accuracy_scores" in session and session["accuracy_scores"]:
                average_accuracy = sum(session["accuracy_scores"]) / len(session["accuracy_scores"])
                logging.debug(f"Calculated average accuracy: {average_accuracy}")
                # Update daily work registry with session average
                update_daily_work_registry(user_id, "practice", average_accuracy, 5)
            else:
                logging.debug(f"No accuracy scores found or user not logged in")
            
            # Get daily work stats for summary
            daily_stats = get_daily_work_stats(user_id) if user_id else {"today_sentences_above_7": 0, "today_total_sentences": 0, "current_streak": 0, "last_7_days": []}
            
            # Clear session data
            for key in ["session_ids", "session_index", "session_score", "hsk_level", "accuracy_scores"]:
                session.pop(key, None)
            return render_template("session_summary.html", score=score, total=5, level=level, daily_stats=daily_stats, average_accuracy=round(average_accuracy, 1))

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
@login_required
def dashboard():
    """
    User dashboard showing HSK progress and daily work statistics.
    """
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
        logging.error("Error loading progress from Supabase:", e)
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
    
    # Get daily work statistics
    daily_stats = get_daily_work_stats(user_id) if user_id else {"today_sentences_above_7": 0, "today_total_sentences": 0, "current_streak": 0, "last_7_days": []}
    
    return render_template("dashboard.html", levels=levels, daily_stats=daily_stats)

@dictation_bp.before_app_request
def check_user_authentication():
    """
    (Optional) Hook for enforcing authentication before each request. Currently a no-op.
    """
    # No guest users - users must be logged in to use the app
    pass

@dictation_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    User login route. Authenticates user with Supabase and sets session state.
    """
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        
        logging.info(f"Login attempt for email: {email}")
        logging.info(f"Supabase URL: {SUPABASE_URL}")
        logging.info(f"Supabase Key exists: {SUPABASE_KEY is not None}")
        
        try:
            result = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            user = result.user
            if user is None:
                raise Exception("No user returned from Supabase.")
            
            logging.info(f"Login successful for user: {user.id}")
            new_user_id = user.id

            session["user_id"] = new_user_id
            session["email"] = user.email
            return redirect("/")
        except Exception as e:
            logging.error(f"Login error: {e}")
            error = f"Login failed: {str(e)}"

    return render_template("login.html", error=error)

@dictation_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """
    User signup route. Registers a new user with Supabase.
    """
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        logging.info(f"Signup attempt for email: {email}")
        
        try:
            result = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            logging.info(f"Signup successful for user: {result.user.id if result.user else 'No user'}")
            return redirect("/login")
        except Exception as e:
            logging.error(f"Signup error: {e}")
            error = f"Signup failed: {str(e)}"

    return render_template("signup.html", error=error)

@dictation_bp.route("/logout")
def logout():
    """
    User logout route. Clears session and redirects to menu.
    """
    session.clear()
    return redirect("/")

@dictation_bp.route("/hsk/<level>")
@login_required
def hsk_level_detail(level):
    """
    Shows character progress for a specific HSK level for the logged-in user.
    """
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
    """
    Handles dictation sessions for short stories, including progress saving and resuming.
    """
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
        if user_id:
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
                logging.info(f"Saved story progress for user {user_id}, story {story_id}")
                flash(f"Progress saved! You can resume '{story['title']}' later.", "success")
            except Exception as e:
                logging.error(f"Error saving story progress: {e}")
                flash("Failed to save progress. Please try again.", "error")
        else:
            flash("Please log in to save your progress.", "warning")
        
        # Clear session and redirect to main menu
        for key in ["story_session_ids", "story_session_index", "story_session_score", "story_id", "accuracy_scores"]:
            session.pop(key, None)
        return redirect("/")
    
    if request.method == "POST" and "restart" in request.form:
        # Clear any existing progress and restart
        if user_id:
            try:
                supabase.table("story_progress").delete().eq("user_id", user_id).eq("story_id", story_id).execute()
                logging.info(f"Cleared story progress for user {user_id}, story {story_id}")
            except Exception as e:
                logging.error(f"Error clearing story progress: {e}")
        
        # Clear session data
        for key in ["story_session_ids", "story_session_index", "story_session_score", "story_id", "accuracy_scores"]:
            session.pop(key, None)
        return redirect(f"/story/{story_id}/session")
    
    # Check for existing progress if no session data
    if "story_session_ids" not in session or session.get("story_id") != story_id:
        # Try to load existing progress for logged-in users
        existing_progress = None
        if user_id:
            try:
                result = supabase.table("story_progress").select("*").eq("user_id", user_id).eq("story_id", story_id).execute()
                if result.data:
                    existing_progress = result.data[0]
                    logging.info(f"Found existing progress for user {user_id}, story {story_id}")
            except Exception as e:
                logging.error(f"Error loading story progress: {e}")
        
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
            
            # Calculate average accuracy for the story session
            average_accuracy = 0
            if user_id and "accuracy_scores" in session and session["accuracy_scores"]:
                average_accuracy = sum(session["accuracy_scores"]) / len(session["accuracy_scores"])
                # Update daily work registry with story session average
                update_daily_work_registry(user_id, "story", average_accuracy, total, story_id, total)
            
            # Clear story progress from database when completed
            if user_id:
                try:
                    supabase.table("story_progress").delete().eq("user_id", user_id).eq("story_id", story_id).execute()
                    logging.info(f"Cleared completed story progress for user {user_id}, story {story_id}")
                except Exception as e:
                    logging.error(f"Error clearing completed story progress: {e}")
            
            # Get daily work stats for summary
            daily_stats = get_daily_work_stats(user_id) if user_id else {"today_sentences_above_7": 0, "today_total_sentences": 0, "current_streak": 0, "last_7_days": []}
            
            # Clear story session data
            for key in ["story_session_ids", "story_session_index", "story_session_score", "story_id", "accuracy_scores"]:
                session.pop(key, None)
            return render_template("story_summary.html", score=score, total=total, story=story, story_id=story_id, daily_stats=daily_stats, average_accuracy=round(average_accuracy, 1))

    part_id = session["story_session_ids"][session["story_session_index"]]
    part = ctx.get_story_part(story_id, part_id)
    if not part:
        return "Story part not found", 500

    # Get all audio file paths for the story (for sequential playback)
    story_audio_files = ctx.story_all_audio_paths(story_id)

    # Get part number from part id (should be in the format story_<story_id>_<part_number>)
    try:
        part_number = int(part_id.split('_')[-1])
    except Exception:
        part_number = session["story_session_index"] + 1

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
        audio_file=ctx.story_audio_path(story_id, part_number),  # Use story audio path
        score=session["story_session_score"],
        level=session.get("level", 1),
        difficulty=story["difficulty"],
        show_result=False,
        session_mode=True,
        current=session["story_session_index"] + 1,
        total=len(story["parts"]),
        story_mode=True,
        story_title=story["title"],
        story_context=story_context,
        story_audio_files=story_audio_files
    )
