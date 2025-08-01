"""
Route helpers for common patterns and utilities used across dictation routes.
"""

import logging
from typing import Dict, Any, Optional, List
from flask import flash, redirect, url_for, session, render_template, request


def handle_session_actions(session_type: str, identifier: str, user_id: Optional[str], session_manager) -> Optional[str]:
    """
    Handle common session actions (resume_later, restart) for story and conversation sessions.
    Returns redirect URL if action was handled, None otherwise.
    """
    from flask import request
    
    if request.method != "POST":
        return None
    
    if "resume_later" in request.form:
        return _handle_resume_later(session_type, identifier, user_id, session_manager)
    elif "restart" in request.form:
        return _handle_restart(session_type, identifier, user_id, session_manager)
    
    return None


def _handle_resume_later(session_type: str, identifier: str, user_id: Optional[str], session_manager) -> str:
    """Handle resume_later action."""
    if not user_id:
        flash("Please log in to save progress.", "error")
        return url_for("dictation.menu")
    
    try:
        if session_type == "story":
            current_index = session.get("story_session_index", 0)
            score = session.get("story_session_score", 0)
            success = session_manager.save_story_progress(user_id, identifier, current_index, score)
            if success:
                story = session_manager.ctx.get_story(identifier)
                flash(f"Progress saved for '{story['title']}'", "success")
            else:
                flash("Failed to save progress.", "error")
        elif session_type == "conversation":
            current_index = session.get("conversation_session_index", 0)
            score = session.get("conversation_session_score", 0)
            success = session_manager.save_conversation_progress(user_id, identifier, current_index, score)
            if success:
                conversation = session_manager.ctx.get_conversation(identifier)
                flash(f"Progress saved for '{conversation['topic']}'", "success")
            else:
                flash("Failed to save progress.", "error")
    except Exception as e:
        logging.error(f"Error saving {session_type} progress: {e}")
        flash("Failed to save progress.", "error")
    
    return url_for("dictation.menu")


def _handle_restart(session_type: str, identifier: str, user_id: Optional[str], session_manager) -> str:
    """Handle restart action."""
    if user_id:
        try:
            if session_type == "story":
                session_manager.clear_story_progress(user_id, identifier)
            elif session_type == "conversation":
                session_manager.clear_conversation_progress(user_id, identifier)
        except Exception as e:
            logging.error(f"Error clearing {session_type} progress: {e}")
    
    # Clear session data
    session_manager.clear_session_data(session_type)
    
    # Show restart message
    if session_type == "story":
        story = session_manager.ctx.get_story(identifier)
        flash(f"Restarted '{story['title']}'", "info")
    elif session_type == "conversation":
        conversation = session_manager.ctx.get_conversation(identifier)
        flash(f"Restarted '{conversation['topic']}'", "info")
    
    return url_for("dictation.menu")


def get_session_context(session_type: str, identifier: str, session_manager) -> Dict[str, Any]:
    """
    Get common session context for rendering templates.
    Returns context dict with session info and any errors.
    """
    context = {}
    
    if session_type == "story":
        story = session_manager.ctx.get_story(identifier)
        if not story:
            context["error"] = "Story not found"
            return context
        
        context.update({
            "story": story,
            "story_id": identifier,
            "total_parts": len(story["parts"])
        })
        
    elif session_type == "conversation":
        conversation = session_manager.ctx.get_conversation(identifier)
        if not conversation:
            context["error"] = "Conversation not found"
            return context
        
        context.update({
            "conversation": conversation,
            "conversation_id": identifier,
            "total_sentences": len(conversation["sentences"])
        })
    
    return context


def handle_session_completion(session_type: str, identifier: str, user_id: Optional[str], 
                            session_manager, total_items: int, average_accuracy: float) -> Dict[str, Any]:
    """
    Handle session completion logic (saving stats, clearing progress, etc.).
    Returns context for summary template.
    """
    from .db_helpers import update_daily_work_registry, get_daily_work_stats
    
    # Update daily work registry
    if user_id:
        update_daily_work_registry(user_id, session_type, average_accuracy, total_items, identifier, total_items)
        
        # Clear completed progress from database
        if session_type == "conversation":
            session_manager.clear_conversation_progress(user_id, identifier)
    
    # Get daily work stats for summary
    daily_stats = get_daily_work_stats(user_id) if user_id else {
        "today_sentences_above_7": 0, 
        "today_total_sentences": 0, 
        "current_streak": 0, 
        "last_7_days": []
    }
    
    return {
        "daily_stats": daily_stats,
        "average_accuracy": round(average_accuracy, 1),
        "total": total_items
    }


def validate_session_access(session_type: str, identifier: str, session_manager) -> Optional[str]:
    """
    Validate that the session exists and user has access.
    Returns error message if validation fails, None otherwise.
    """
    if session_type == "story":
        story = session_manager.ctx.get_story(identifier)
        if not story:
            return "Story not found."
    elif session_type == "conversation":
        conversation = session_manager.ctx.get_conversation(identifier)
        if not conversation:
            return "Conversation not found."
    
    return None


def handle_conversation_submit_all(conversation_id: str, user_id: Optional[str], user_input_keys: List[str], 
                                 ctx, corrector) -> Any:
    """
    Handle the "Submit All Answers" functionality for conversations.
    """
    conversation = ctx.get_conversation(conversation_id)
    if not conversation:
        flash("Conversation not found.", "error")
        return redirect(url_for("dictation.menu"))
    
    # Collect all user inputs from the form
    all_inputs = {}
    for key in user_input_keys:
        sentence_id = key.replace("user_input_", "")
        value = request.form[key].strip()
        all_inputs[sentence_id] = value
    
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
    
    # Calculate average accuracy
    average_accuracy = total_accuracy / total_sentences if total_sentences > 0 else 0
    
    # Update session with accuracy scores
    session["accuracy_scores"] = [corr["accuracy"] for corr in all_corrections]
    
    # Update character progress for logged-in users
    if user_id:
        from .db_helpers import batch_update_character_progress
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
            batch_update_character_progress(user_id, hanzi_updates)
    
    # Return results for display
    return render_template("correction_conversation.html", 
                         conversation_topic=conversation["topic"],
                         level=conversation["hsk_level"],
                         all_corrections=all_corrections,
                         average_accuracy=round(average_accuracy, 1),
                         total_sentences=total_sentences,
                         conversation_id=conversation_id) 