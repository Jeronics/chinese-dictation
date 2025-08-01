from traceback import print_tb
from dotenv import load_dotenv
import os
load_dotenv()

import uuid
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request, session, redirect, flash, url_for, g, send_from_directory
from functools import wraps
from .app_context import DictationContext
from .corrector import Corrector
from .db_helpers import (
    update_character_progress,
    get_user_character_status,
    update_daily_work_registry,
    get_daily_work_stats,
    get_daily_session_count,
    get_user_progress_summary
)
from .utils import login_required
from .session_manager import SessionManager
from .route_helpers import handle_session_actions, get_session_context, handle_session_completion, validate_session_access, handle_conversation_submit_all
from .base_session_handler import StorySessionHandler, ConversationSessionHandler
from supabase import create_client
import logging
import smtplib
from email.mime.text import MIMEText
from .session import HSKSession, StorySession, ConversationSession

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
session_manager = SessionManager(ctx, supabase)
story_handler = StorySessionHandler(session_manager)
conversation_handler = ConversationSessionHandler(session_manager)

# --- Helper functions for character progress tracking ---
# (Moved to db_helpers.py)

# --- Helper functions for daily work tracking ---
# (Moved to db_helpers.py)

def get_gradient_feedback(accuracy):
    if accuracy == 100:
        return ("Perfect!", "#00ff00")  # Extremely bright green
    elif accuracy >= 85:
        return ("Very Good!", "#00cc00")  # Bright green
    elif accuracy >= 70:
        return ("Good!", "#008000")       # Dull green  
    elif accuracy >= 50:
        return ("Getting Better!", "#ffa500") # orange
    elif accuracy >= 25:
        return ("Needs Practice..", "#ffa500") # orange
    else:
        return ("Poor..", "#c62828")        # red



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
    saved_conversations = []
    user_id = session.get("user_id")
    if user_id:
        try:
            result = supabase.table("story_progress").select("story_id").eq("user_id", user_id).execute()
            saved_stories = [row["story_id"] for row in result.data] if result.data else []
        except Exception as e:
            logging.error(f"Error loading saved stories: {e}")
            saved_stories = []
        
        try:
            result = supabase.table("conversation_progress").select("conversation_id").eq("user_id", user_id).execute()
            saved_conversations = [str(row["conversation_id"]) for row in result.data] if result.data else []
        except Exception as e:
            logging.error(f"Error loading saved conversations: {e}")
            saved_conversations = []

    return render_template("index.html", stories=ctx.stories, saved_stories=saved_stories, 
                         conversations=ctx.conversations, saved_conversations=saved_conversations,
                         hsk_totals=ctx.hsk_totals)

@dictation_bp.route("/session", methods=["GET", "POST"])
def session_practice():
    """
    Main dictation practice session route. Handles session state, user answers, and session summary.
    """
    # Only initialize session if a level parameter is provided (new session request)
    hsk_level_param = request.args.get("hsk")
    if hsk_level_param:
        level = session_manager.initialize_hsk_session(hsk_level_param)
    else:
        # Use existing session level
        level = session.get("hsk_level")
    
    hsk_session = HSKSession(ctx)

    if request.method == "POST" and "next" in request.form:
        hsk_session.advance()
        if hsk_session.get_current_index() >= 5:
            average_accuracy = 0
            accuracy_scores = session.get("accuracy_scores", [])
            user_id = session.get("user_id")
            if accuracy_scores:
                average_accuracy = sum(accuracy_scores) / len(accuracy_scores)
            if user_id and accuracy_scores:
                update_daily_work_registry(user_id, "practice", average_accuracy, 5)
            daily_stats = get_daily_work_stats(user_id) if user_id else {"today_sentences_above_7": 0, "today_total_sentences": 0, "current_streak": 0, "last_7_days": []}
            session_manager.clear_session_data('hsk')
            return render_template("summary_regular.html", total=5, level=level, daily_stats=daily_stats, average_accuracy=round(average_accuracy, 1))

    sid = hsk_session.get_current_id()
    s = ctx.get_sentence(sid)
    s["id"] = sid
    if not ctx.audio_path(sid, s["hsk_level"]):
        return "Missing audio file", 500

    if request.method == "POST" and "user_input" in request.form:
        user_input = request.form["user_input"].strip()
        return render_template("session_regular.html", **hsk_session.update_score(user_input))
    
    return render_template("session_regular.html", **hsk_session.get_context())

@dictation_bp.route("/dashboard")
@login_required
def dashboard():
    """
    User dashboard showing HSK progress and daily work statistics.
    """
    user_id = session.get("user_id")
    levels = get_user_progress_summary(user_id, ctx)
    daily_stats = get_daily_work_stats(user_id) if user_id else {"today_sentences_above_7": 0, "today_total_sentences": 0, "current_streak": 0, "last_7_days": []}
    return render_template("dashboard.html", levels=levels, daily_stats=daily_stats)

@dictation_bp.before_app_request
def setup_request_context():
    """
    Setup request context including authentication and daily session count.
    """
    # No guest users - users must be logged in to use the app
    # (Currently a no-op, but could be used for authentication enforcement)
    
    # Inject daily session count
    user_id = session.get("user_id")
    if user_id:
        g.daily_session_count = get_daily_session_count(user_id)
    else:
        g.daily_session_count = None

@dictation_bp.app_context_processor
def inject_daily_session_count_context():
    return {"daily_session_count": getattr(g, "daily_session_count", None)}

@dictation_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    User login route. Handles both GET (display form) and POST (process login).
    """
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        try:
            # Authenticate with Supabase
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Store user info in session
                session["user_id"] = response.user.id
                session["email"] = response.user.email
                flash("Login successful!", "success")
                return redirect(url_for("dictation.menu"))
            else:
                flash("Invalid email or password", "error")
        except Exception as e:
            logging.error(f"Login error: {e}")
            flash("Login failed. Please try again.", "error")
    
    return render_template("login.html")

@dictation_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """
    User registration route. Handles both GET (display form) and POST (process registration).
    """
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        try:
            # Create user with Supabase
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                flash("Account created successfully! Please check your email to verify your account.", "success")
                return redirect(url_for("dictation.login"))
            else:
                flash("Registration failed. Please try again.", "error")
        except Exception as e:
            logging.error(f"Signup error: {e}")
            flash("Registration failed. Please try again.", "error")
    
    return render_template("signup.html")

@dictation_bp.route("/logout")
def logout():
    """
    User logout route. Clears session and redirects to menu.
    """
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("dictation.menu"))

@dictation_bp.route("/hsk/<level>")
@login_required
def hsk_level_detail(level):
    """
    Display detailed progress for a specific HSK level.
    """
    user_id = session.get("user_id")
    try:
        level = int(level)  # Ensure level is int for comparison
        # Get user progress for this level
        progress_rows = supabase.table("character_progress") \
            .select("hanzi, grade") \
            .eq("user_id", user_id) \
            .eq("hsk_level", level).execute().data or []
        
        # Create lookup for user grades
        user_grades = {row["hanzi"]: row["grade"] for row in progress_rows}
        
        # Get all characters for this level
        level_characters = [item for item in ctx.hsk_data if item["hsk_level"] == level]
        
        # Prepare character data with status
        char_data = []
        for char in level_characters:
            grade = user_grades.get(char["hanzi"])
            if grade is None:
                status = "unseen"
            elif grade == -1:
                status = "failed"
            elif grade in [0, 1]:
                status = "learning"
            else:
                status = "known"
            
            char_data.append({
                "hanzi": char["hanzi"],
                "status": status,
                "grade": grade
            })
        
        return render_template("hsk_level_detail.html", level=level, char_data=char_data)
        
    except Exception as e:
        logging.error(f"Error loading HSK level detail: {e}")
        flash("Error loading level details.", "error")
        return redirect(url_for("dictation.dashboard"))

@dictation_bp.route("/story/<story_id>/session", methods=["GET", "POST"])
def story_session(story_id):
    """
    Story dictation session route. Handles story progress, user answers, and session summary.
    """
    user_id = session.get("user_id")
    return story_handler.handle_session(story_id, user_id)

@dictation_bp.route("/conversation/<conversation_id>/session", methods=["GET", "POST"])
def conversation_session(conversation_id):
    """
    Conversation dictation session route. Handles conversation progress, user answers, and session summary.
    """
    user_id = session.get("user_id")
    
    # Handle "Submit All Answers" from conversation form (special case)
    if request.method == "POST":
        form_keys = list(request.form.keys())
        user_input_keys = [k for k in form_keys if k.startswith("user_input_")]
        
        if user_input_keys:
            return handle_conversation_submit_all(conversation_id, user_id, user_input_keys, ctx, corrector)
    
    return conversation_handler.handle_session(conversation_id, user_id)

@dictation_bp.route("/audio/<category>/<filename>")
def serve_audio(category, filename):
    """Serve audio files with proper caching headers"""
    if category not in ['hsk_characters', 'conversations', 'stories']:
        return "Invalid category", 400
    
    response = send_from_directory(f'static/audio_files/{category}', filename)
    response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    response.headers['Accept-Ranges'] = 'bytes'
    return response

# Legacy route for backward compatibility
@dictation_bp.route("/static/audio_files/<filename>")
def serve_legacy_audio(filename):
    """Serve audio files from legacy path for backward compatibility"""
    # Determine category from filename
    if filename.startswith('conv_'):
        category = 'conversations'
    elif filename.startswith('story_'):
        category = 'stories'
    elif '_HSK' in filename:
        category = 'hsk_characters'
    else:
        return "File not found", 404
    
    response = send_from_directory(f'static/audio_files/{category}', filename)
    response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
    response.headers['Accept-Ranges'] = 'bytes'
    return response

@dictation_bp.route("/audio/manifest.json")
def serve_audio_manifest():
    """Serve audio manifest with caching headers"""
    response = send_from_directory('static/audio_files', 'manifest.json')
    response.headers['Cache-Control'] = 'public, max-age=3600'  # 1 hour
    response.headers['Content-Type'] = 'application/json'
    return response

@dictation_bp.route("/report-correction", methods=["POST"])
def report_correction():
    """
    Route for users to report incorrect corrections.
    """
    correction_html = request.form.get("correction", "")
    correct_sentence = request.form.get("correct_sentence", "")
    input_sentence = request.form.get("user_input", "")
    corrected_sentence = correction_html  # For now, same as correction_html
    pinyin = request.form.get("pinyin", "")
    translation = request.form.get("translation", "")
    user_id = session.get("user_id")
    user_email = session.get("email", "(not logged in)")
    # Try to reconstruct audio_file from form or session
    audio_file = None
    sentence_id = None
    
    # Try to get story_id and part_id if this was from a story
    story_id = request.form.get("story_id")
    part_id = request.form.get("part_id")
    
    # Try to get conversation_id and sentence_id if this was from a conversation
    conversation_id = request.form.get("conversation_id")
    sentence_id = request.form.get("sentence_id")
    
    try:
        # Insert the reported correction into the database
        supabase.table("reported_corrections").insert({
            "user_id": user_id,
            "user_email": user_email,
            "correct_sentence": correct_sentence,
            "input_sentence": input_sentence,
            "correction_html": correction_html,
            "corrected_sentence": corrected_sentence,
            "pinyin": pinyin,
            "translation": translation,
            "sentence_id": sentence_id,
            "story_id": story_id,
            "part_id": part_id,
            "conversation_id": conversation_id,
            "created_at": datetime.now().isoformat()
        }).execute()
        
        flash("Thank you for reporting this correction! We'll review it.", "success")
    except Exception as e:
        logging.error(f"Error reporting correction: {e}")
        flash("Failed to report correction. Please try again.", "error")
    
    # Redirect back to the previous page or menu
    return redirect(request.referrer or url_for("dictation.menu"))

 