"""
Session Manager for handling session state across different dictation types.
Centralizes session initialization, progress saving/loading, and state management.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from .app_context import DictationContext


class SessionManager:
    """Manages session state for HSK, Story, and Conversation sessions."""
    
    def __init__(self, ctx: DictationContext, supabase_client):
        self.ctx = ctx
        self.supabase = supabase_client
    
    def clear_session_data(self, session_type: str) -> None:
        """Clear session data for a specific session type."""
        session_keys = {
            'hsk': ["session_ids", "session_index", "session_score", "hsk_level", "accuracy_scores"],
            'story': ["story_session_ids", "story_session_index", "story_session_score", "story_id", "accuracy_scores", "story_group_scores"],
            'conversation': ["conversation_session_ids", "conversation_session_index", "conversation_session_score", "conversation_id", "accuracy_scores"]
        }
        
        from flask import session
        keys_to_clear = session_keys.get(session_type, [])
        for key in keys_to_clear:
            session.pop(key, None)
    
    def initialize_hsk_session(self, level: Optional[str] = None) -> int:
        """Initialize HSK session with given level or random level."""
        from flask import session
        
        if level and isinstance(level, str) and level.startswith("HSK"):
            level = int(level.replace("HSK", ""))
        elif level:
            level = int(level)
        
        # If no level provided or session_ids not in session, initialize with random level
        if not level or "session_ids" not in session:
            level = level or None
            session.update(
                hsk_level=level,
                session_ids=self.ctx.get_random_ids(level=level),
                session_index=0,
                session_score=0
            )
        
        return level
    
    def initialize_story_session(self, story_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Initialize or resume story session."""
        from flask import session
        
        story = self.ctx.get_story(story_id)
        if not story:
            return {"error": "Story not found"}
        
        # Check if we need to initialize or resume
        if "story_session_ids" not in session or session.get("story_id") != story_id:
            existing_progress = self._load_story_progress(user_id, story_id) if user_id else None
            
            if existing_progress:
                # Resume from saved progress
                session.update(
                    story_id=story_id,
                    story_session_ids=[part["id"] for part in story["parts"]],
                    story_session_index=existing_progress["current_index"],
                    story_session_score=existing_progress["score"]
                )
                return {"resumed": True, "index": existing_progress["current_index"], "total": len(story["parts"])}
            else:
                # Initialize new story session
                session.update(
                    story_id=story_id,
                    story_session_ids=[part["id"] for part in story["parts"]],
                    story_session_index=0,
                    story_session_score=0
                )
                return {"resumed": False, "index": 0, "total": len(story["parts"])}
        
        return {"resumed": False, "index": session.get("story_session_index", 0), "total": len(story["parts"])}
    
    def initialize_conversation_session(self, conversation_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Initialize or resume conversation session."""
        from flask import session
        
        conversation = self.ctx.get_conversation(conversation_id)
        if not conversation:
            return {"error": "Conversation not found"}
        
        # Check if we need to initialize or resume
        if "conversation_session_ids" not in session or session.get("conversation_id") != conversation_id:
            existing_progress = self._load_conversation_progress(user_id, conversation_id) if user_id else None
            
            if existing_progress:
                # Resume from saved progress
                session.update(
                    conversation_id=conversation_id,
                    conversation_session_ids=[sentence["id"] for sentence in conversation["sentences"]],
                    conversation_session_index=existing_progress["current_index"],
                    conversation_session_score=existing_progress["score"]
                )
                return {"resumed": True, "index": existing_progress["current_index"], "total": len(conversation["sentences"])}
            else:
                # Initialize new conversation session
                session.update(
                    conversation_id=conversation_id,
                    conversation_session_ids=[sentence["id"] for sentence in conversation["sentences"]],
                    conversation_session_index=0,
                    conversation_session_score=0
                )
                return {"resumed": False, "index": 0, "total": len(conversation["sentences"])}
        
        return {"resumed": False, "index": session.get("conversation_session_index", 0), "total": len(conversation["sentences"])}
    
    def save_story_progress(self, user_id: str, story_id: str, current_index: int, score: int) -> bool:
        """Save story progress to database."""
        try:
            self.supabase.table("story_progress").upsert({
                "user_id": user_id,
                "story_id": story_id,
                "current_index": current_index,
                "score": score,
                "last_updated": datetime.now().isoformat()
            }).execute()
            return True
        except Exception as e:
            logging.error(f"Error saving story progress: {e}")
            return False
    
    def save_conversation_progress(self, user_id: str, conversation_id: str, current_index: int, score: int) -> bool:
        """Save conversation progress to database."""
        try:
            self.supabase.table("conversation_progress").upsert({
                "user_id": user_id,
                "conversation_id": conversation_id,
                "current_index": current_index,
                "score": score,
                "last_updated": datetime.now().isoformat()
            }).execute()
            return True
        except Exception as e:
            logging.error(f"Error saving conversation progress: {e}")
            return False
    
    def clear_story_progress(self, user_id: str, story_id: str) -> bool:
        """Clear saved story progress."""
        try:
            self.supabase.table("story_progress").delete().eq("user_id", user_id).eq("story_id", story_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error clearing story progress: {e}")
            return False
    
    def clear_conversation_progress(self, user_id: str, conversation_id: str) -> bool:
        """Clear saved conversation progress."""
        try:
            self.supabase.table("conversation_progress").delete().eq("user_id", user_id).eq("conversation_id", conversation_id).execute()
            return True
        except Exception as e:
            logging.error(f"Error clearing conversation progress: {e}")
            return False
    
    def _load_story_progress(self, user_id: str, story_id: str) -> Optional[Dict[str, Any]]:
        """Load story progress from database."""
        try:
            result = self.supabase.table("story_progress").select("*").eq("user_id", user_id).eq("story_id", story_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error loading story progress: {e}")
            return None
    
    def _load_conversation_progress(self, user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Load conversation progress from database."""
        try:
            result = self.supabase.table("conversation_progress").select("*").eq("user_id", user_id).eq("conversation_id", conversation_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error loading conversation progress: {e}")
            return None 