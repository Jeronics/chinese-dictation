from traceback import print_tb
from dotenv import load_dotenv
import os
load_dotenv()

import uuid
from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, request, session, redirect, flash, url_for, g
from functools import wraps
from .app_context import DictationContext
from .corrector import Corrector
from .db_helpers import (
    update_character_progress,
    get_user_character_status,
    update_daily_work_registry,
    get_daily_work_stats,
    get_daily_session_count
)
from .utils import login_required
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
    level = request.args.get("hsk")
    if level and isinstance(level, str) and level.startswith("HSK"):
        level = int(level.replace("HSK", ""))
    elif level:
        level = int(level)
    if level:
        session.update(
            hsk_level=level,
            session_ids=ctx.get_random_ids(level=level),
            session_index=0,
            session_score=0
        )
    elif "session_ids" not in session:
        level = None
        session.update(
            hsk_level=level,
            session_ids=ctx.get_random_ids(level=level),
            session_index=0,
            session_score=0
        )

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
            for key in ["session_ids", "session_index", "session_score", "hsk_level", "accuracy_scores"]:
                session.pop(key, None)
            return render_template("session_summary.html", total=5, level=level, daily_stats=daily_stats, average_accuracy=round(average_accuracy, 1))

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
    try:
        # Get all user progress for all hanzi
        progress_rows = supabase.table("character_progress") \
            .select("hanzi, hsk_level, grade") \
            .eq("user_id", user_id).execute().data or []
        # Map hanzi to grade for quick lookup
        hanzi_to_grade = {row["hanzi"]: row["grade"] for row in progress_rows}
        # For each HSK level, count known, learning, failed, unseen
        levels = []
        for hsk_level, total in ctx.hsk_totals.items():
            # Get all hanzi for this level
            hanzi_list = [item["hanzi"] for item in ctx.hsk_data if item["hsk_level"] == hsk_level]
            known = learning = failed = unseen = 0
            for hanzi in hanzi_list:
                grade = hanzi_to_grade.get(hanzi, None)
                if grade is None:
                    unseen += 1
                elif grade == -1:
                    failed += 1
                elif grade in [0, 1]:
                    learning += 1
                elif grade in [2, 3]:
                    known += 1
            known_pct = int(100 * known / total) if total else 0
            failed_pct = int(100 * failed / total) if total else 0
            unseen_pct = int(100 * unseen / total) if total else 0
            levels.append({
                "level": hsk_level,
                "known": known,
                "failed": failed,
                "learning": learning,
                "unseen": unseen,
                "total": total,
                "percent": known_pct
            })
    except Exception as e:
        logging.error("Error loading progress from Supabase:", e)
        levels = []
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

@dictation_bp.before_app_request
def inject_daily_session_count():
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
    story = ctx.get_story(story_id)
    if not story:
        flash("Story not found.", "error")
        return redirect(url_for("dictation.menu"))

    user_id = session.get("user_id")
    
    # Handle story actions
    if request.method == "POST":
        if "resume_later" in request.form:
            # Save current progress to database
            if user_id:
                try:
                    current_index = story_session_obj.get_current_index() if 'story_session_obj' in locals() else 0
                    supabase.table("story_progress").upsert({
                        "user_id": user_id,
                        "story_id": story_id,
                        "current_index": current_index,
                        "score": story_session_obj.get_score() if 'story_session_obj' in locals() else 0,
                        "last_updated": datetime.now().isoformat()
                    }).execute()
                    flash(f"Progress saved for '{story['title']}'", "success")
                except Exception as e:
                    logging.error(f"Error saving story progress: {e}")
                    flash("Failed to save progress.", "error")
            return redirect(url_for("dictation.menu"))
        
        elif "restart" in request.form:
            # Clear saved progress and start fresh
            if user_id:
                try:
                    supabase.table("story_progress").delete().eq("user_id", user_id).eq("story_id", story_id).execute()
                except Exception as e:
                    logging.error(f"Error clearing story progress: {e}")
            # Clear session data
            for key in ["story_session_ids", "story_session_index", "story_session_score", "story_id", "accuracy_scores", "story_group_scores"]:
                session.pop(key, None)
            flash(f"Restarted '{story['title']}'", "info")

    # Initialize or resume story session
    if "story_session_ids" not in session or session.get("story_id") != story_id:
        # Check for existing progress
        existing_progress = None
        if user_id:
            try:
                result = supabase.table("story_progress").select("*").eq("user_id", user_id).eq("story_id", story_id).execute()
                if result.data:
                    existing_progress = result.data[0]
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

    if "story_group_scores" not in session or session.get("story_id") != story_id:
        session["story_group_scores"] = []

    story_session_obj = StorySession(ctx)

    if request.method == "POST" and "next" in request.form:
        # Track per-group scores
        group_size = 5
        idx = story_session_obj.get_current_index()
        total_parts = len(story["parts"])
        # If finishing a group or the story, record the group score
        if (idx + 1) % group_size == 0 or (idx + 1) == total_parts:
            # Calculate score for this group using per-sentence correctness
            start = idx - ((idx) % group_size)
            end = idx + 1
            group_score = sum([1 for i in range(start, end) if session.get(f"story_part_{i}_correct", False)])
            # Store as out of 10 (scale up if group smaller than 5)
            group_score_scaled = int((group_score / (end - start)) * 10)
            session["story_group_scores"].append(group_score_scaled)
        story_session_obj.advance()
        if story_session_obj.get_current_index() >= len(story["parts"]):
            score = story_session_obj.get_score()
            total = len(story["parts"])
            
            # Calculate average accuracy for the story session
            average_accuracy = 0
            accuracy_scores = session.get("accuracy_scores", [])
            if accuracy_scores:
                average_accuracy = sum(accuracy_scores) / len(accuracy_scores)
            if user_id and accuracy_scores:
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
            
            # Clear per-sentence correctness keys
            for i in range(len(story["parts"])):
                session.pop(f"story_part_{i}_correct", None)
            for key in ["story_session_ids", "story_session_index", "story_session_score", "story_id", "accuracy_scores", "story_group_scores"]:
                session.pop(key, None)
            return render_template("story_summary.html", score=score, total=total, story=story, story_id=story_id, daily_stats=daily_stats, average_accuracy=round(average_accuracy, 1))

    part_id = story_session_obj.get_current_id()
    part = ctx.get_story_part(story_id, part_id)
    if not part:
        return "Story part not found", 500

    # Get all audio file paths for the story (for sequential playback)
    story_audio_files = ctx.story_all_audio_paths(story_id)

    # Get part number from part id (should be in the format story_<story_id>_<part_number>)
    try:
        part_number = int(part_id.split('_')[-1])
    except Exception:
        part_number = story_session_obj.get_current_index() + 1

    if request.method == "POST" and "user_input" in request.form:
        user_input = request.form["user_input"].strip()
        return render_template("session_story.html", **story_session_obj.update_score(user_input))

    # Get story context (previous parts only, not the current one)
    story_context = story["parts"][:story_session_obj.get_current_index()]
    
    return render_template("session_story.html", **story_session_obj.get_context())

@dictation_bp.route("/conversation/<conversation_id>/session", methods=["GET", "POST"])
def conversation_session(conversation_id):
    """
    Conversation dictation session route. Handles conversation progress, user answers, and session summary.
    """
    conversation = ctx.get_conversation(conversation_id)
    if not conversation:
        flash("Conversation not found.", "error")
        return redirect(url_for("dictation.menu"))

    user_id = session.get("user_id")
    
    # Handle conversation actions
    if request.method == "POST":
        if "resume_later" in request.form:
            # Save current progress to database
            if user_id:
                try:
                    current_index = conversation_session_obj.get_current_index() if 'conversation_session_obj' in locals() else 0
                    supabase.table("conversation_progress").upsert({
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "current_index": current_index,
                        "score": conversation_session_obj.get_score() if 'conversation_session_obj' in locals() else 0,
                        "last_updated": datetime.now().isoformat()
                    }).execute()
                    flash(f"Progress saved for '{conversation['topic']}'", "success")
                except Exception as e:
                    logging.error(f"Error saving conversation progress: {e}")
                    flash("Failed to save progress.", "error")
            return redirect(url_for("dictation.menu"))
        
        elif "restart" in request.form:
            # Clear saved progress and start fresh
            if user_id:
                try:
                    supabase.table("conversation_progress").delete().eq("user_id", user_id).eq("conversation_id", conversation_id).execute()
                except Exception as e:
                    logging.error(f"Error clearing conversation progress: {e}")
            # Clear session data
            for key in ["conversation_session_ids", "conversation_session_index", "conversation_session_score", "conversation_id", "accuracy_scores"]:
                session.pop(key, None)
            flash(f"Restarted '{conversation['topic']}'", "info")

    # Initialize or resume conversation session
    if "conversation_session_ids" not in session or session.get("conversation_id") != conversation_id:
        # Check for existing progress
        existing_progress = None
        if user_id:
            try:
                result = supabase.table("conversation_progress").select("*").eq("user_id", user_id).eq("conversation_id", conversation_id).execute()
                if result.data:
                    existing_progress = result.data[0]
            except Exception as e:
                logging.error(f"Error loading conversation progress: {e}")
        
        if existing_progress:
            # Resume from saved progress
            session.update(
                conversation_id=conversation_id,
                conversation_session_ids=[sentence["id"] for sentence in conversation["sentences"]],
                conversation_session_index=existing_progress["current_index"],
                conversation_session_score=existing_progress["score"]
            )
            flash(f"Resuming '{conversation['topic']}' from sentence {existing_progress['current_index'] + 1} of {len(conversation['sentences'])}", "info")
        else:
            # Initialize new conversation session
            session.update(
                conversation_id=conversation_id,
                conversation_session_ids=[sentence["id"] for sentence in conversation["sentences"]],
                conversation_session_index=0,
                conversation_session_score=0
            )

    conversation_session_obj = ConversationSession(ctx)

    if request.method == "POST" and "next" in request.form:
        conversation_session_obj.advance()
        if conversation_session_obj.get_current_index() >= len(conversation["sentences"]):
            score = conversation_session_obj.get_score()
            total = len(conversation["sentences"])
            
            # Calculate average accuracy for the conversation session
            average_accuracy = 0
            accuracy_scores = session.get("accuracy_scores", [])
            if accuracy_scores:
                average_accuracy = sum(accuracy_scores) / len(accuracy_scores)
            if user_id and accuracy_scores:
                update_daily_work_registry(user_id, "conversation", average_accuracy, total, conversation_id, total)
            
            # Clear conversation progress from database when completed
            if user_id:
                try:
                    supabase.table("conversation_progress").delete().eq("user_id", user_id).eq("conversation_id", conversation_id).execute()
                    logging.info(f"Cleared completed conversation progress for user {user_id}, conversation {conversation_id}")
                except Exception as e:
                    logging.error(f"Error clearing completed conversation progress: {e}")
            
            # Get daily work stats for summary
            daily_stats = get_daily_work_stats(user_id) if user_id else {"today_sentences_above_7": 0, "today_total_sentences": 0, "current_streak": 0, "last_7_days": []}
            
            for key in ["conversation_session_ids", "conversation_session_index", "conversation_session_score", "conversation_id", "accuracy_scores"]:
                session.pop(key, None)
            return render_template("conversation_summary.html", score=score, total=total, conversation=conversation, conversation_id=conversation_id, daily_stats=daily_stats, average_accuracy=round(average_accuracy, 1))

    # Handle "Submit All Answers" from conversation form
    if request.method == "POST":
        form_keys = list(request.form.keys())
        user_input_keys = [k for k in form_keys if k.startswith("user_input_")]
        
        if user_input_keys:
            # This is the "Submit All Answers" form
            print(f"DEBUG: Submit All Answers detected! Processing {len(user_input_keys)} inputs")
            
            conversation_session_obj = ConversationSession(ctx)
        
        # Collect all user inputs from the form
        all_inputs = {}
        for key in user_input_keys:
            sentence_id = key.replace("user_input_", "")
            value = request.form[key].strip()
            all_inputs[sentence_id] = value
            print(f"DEBUG: Input {sentence_id} = '{value}'")
        
        print(f"DEBUG: All inputs collected: {all_inputs}")
        
        # Process all inputs and calculate overall results
        total_accuracy = 0
        total_sentences = len(conversation["sentences"])
        all_corrections = []
        
        for sentence in conversation["sentences"]:
            sentence_id = str(sentence["id"])
            user_input = all_inputs.get(sentence_id, "")
            
            # Always process every sentence, even if user_input is blank
            if user_input:
                correction, stripped_user, stripped_correct, correct_segments = corrector.compare(user_input, sentence["chinese"])
                accuracy = round(len(correct_segments)/len(stripped_correct)*100) if len(stripped_correct) > 0 else 0
            else:
                correction = ""
                accuracy = 0
            total_accuracy += accuracy
            all_corrections.append({
                "sentence_id": sentence_id,
                "chinese": sentence["chinese"],
                "user_input": user_input,
                "correction": correction,
                "pinyin": sentence["pinyin"],
                "translation": sentence["english"],
                "accuracy": accuracy,
                "speaker": sentence["speaker"],
                "audio_file": ctx.conversation_audio_path(conversation_id, sentence["id"])
            })

        print(f"DEBUG: Total corrections: {len(all_corrections)}")
        
        # Calculate average accuracy
        average_accuracy = total_accuracy / total_sentences if total_sentences > 0 else 0
        
        # Update session with accuracy scores
        session["accuracy_scores"] = [corr["accuracy"] for corr in all_corrections]
        
        # Update character progress for logged-in users
        if user_id:
            hanzi_updates = []
            for correction in all_corrections:
                sentence = next((s for s in conversation["sentences"] if str(s["id"]) == correction["sentence_id"]), None)
                if sentence:
                    for hanzi in set(sentence["chinese"]):
                        match = next((entry for entry in ctx.hsk_data if entry["hanzi"] == hanzi), None)
                        if match:
                            hsk_level = match["hsk_level"]
                            if isinstance(hsk_level, str) and hsk_level.startswith("HSK"):
                                hsk_level_int = int(hsk_level.replace("HSK", ""))
                            else:
                                hsk_level_int = int(hsk_level)
                            # Determine if character was correct based on accuracy
                            correct = correction["accuracy"] >= 70  # Threshold for "correct"
                            hanzi_updates.append({
                                "hanzi": hanzi,
                                "hsk_level": hsk_level_int,
                                "correct": correct
                            })
            if hanzi_updates:
                from .db_helpers import batch_update_character_progress
                batch_update_character_progress(user_id, hanzi_updates)
        
        # Return results for display
        return render_template("conversation_correction.html", 
                             conversation_topic=conversation["topic"],
                             level=conversation["hsk_level"],
                             all_corrections=all_corrections,
                             average_accuracy=round(average_accuracy, 1),
                             total_sentences=total_sentences,
                             conversation_id=conversation_id)

    if request.method == "POST" and "user_input" in request.form:
        user_input = request.form["user_input"].strip()
        return render_template("session_conversation.html", **conversation_session_obj.update_score(user_input))
    
    return render_template("session_conversation.html", **conversation_session_obj.get_context())

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
            "user_input": input_sentence,
            "correction_html": correction_html,
            "corrected_sentence": corrected_sentence,
            "pinyin": pinyin,
            "translation": translation,
            "audio_file": audio_file,
            "sentence_id": sentence_id,
            "story_id": story_id,
            "part_id": part_id,
            "conversation_id": conversation_id,
            "reported_at": datetime.now().isoformat()
        }).execute()
        
        flash("Thank you for reporting this correction! We'll review it.", "success")
    except Exception as e:
        logging.error(f"Error reporting correction: {e}")
        flash("Failed to report correction. Please try again.", "error")
    
    # Redirect back to the previous page or menu
    return redirect(request.referrer or url_for("dictation.menu"))

@dictation_bp.route("/admin/reported-corrections")
def reported_corrections_dashboard():
    # Optionally, add admin check here
    try:
        result = supabase.table("reported_corrections").select("*").order("reported_at", desc=True).execute()
        reports = result.data or []
        return render_template("reported_corrections_dashboard.html", reports=reports)
    except Exception as e:
        logging.error(f"Error loading reported corrections: {e}")
        flash("Error loading reported corrections.", "error")
        return redirect(url_for("dictation.menu")) 