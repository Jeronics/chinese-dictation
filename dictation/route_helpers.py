"""
Route helpers for common patterns and utilities used across dictation routes.
"""

import logging
from typing import Dict, Any, Optional
from flask import flash, redirect, url_for, session


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