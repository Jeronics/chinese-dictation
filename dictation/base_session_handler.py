"""
Base session handler for common session patterns across different dictation types.
"""

from typing import Dict, Any, Optional, Callable
from flask import request, session, render_template, redirect, flash, url_for
from .session_manager import SessionManager
from .route_helpers import handle_session_actions, validate_session_access, handle_session_completion


class BaseSessionHandler:
    """Base class for handling different types of dictation sessions."""
    
    def __init__(self, session_manager: SessionManager, session_type: str, template_name: str, summary_template: str):
        self.session_manager = session_manager
        self.session_type = session_type
        self.template_name = template_name
        self.summary_template = summary_template
    
    def handle_session(self, identifier: str, user_id: Optional[str] = None) -> Any:
        """
        Handle a session request with common logic for all session types.
        
        Args:
            identifier: Session identifier (story_id, conversation_id, etc.)
            user_id: Optional user ID for logged-in users
            
        Returns:
            Rendered template or redirect response
        """
        # Handle session actions (resume_later, restart)
        redirect_url = handle_session_actions(self.session_type, identifier, user_id, self.session_manager)
        if redirect_url:
            return redirect(redirect_url)
        
        # Validate session access
        error = validate_session_access(self.session_type, identifier, self.session_manager)
        if error:
            flash(error, "error")
            return redirect(url_for("dictation.menu"))
        
        # Initialize or resume session
        init_result = self._initialize_session(identifier, user_id)
        if "error" in init_result:
            flash(init_result["error"], "error")
            return redirect(url_for("dictation.menu"))
        
        if init_result.get("resumed"):
            self._show_resume_message(identifier, init_result)
        
        # Handle session logic
        return self._handle_session_logic(identifier, user_id)
    
    def _initialize_session(self, identifier: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Initialize session based on session type."""
        if self.session_type == "story":
            return self.session_manager.initialize_story_session(identifier, user_id)
        elif self.session_type == "conversation":
            return self.session_manager.initialize_conversation_session(identifier, user_id)
        else:
            return {"error": f"Unknown session type: {self.session_type}"}
    
    def _show_resume_message(self, identifier: str, init_result: Dict[str, Any]) -> None:
        """Show resume message based on session type."""
        if self.session_type == "story":
            story = self.session_manager.ctx.get_story(identifier)
            flash(f"Resuming '{story['title']}' from part {init_result['index'] + 1} of {init_result['total']}", "info")
        elif self.session_type == "conversation":
            conversation = self.session_manager.ctx.get_conversation(identifier)
            flash(f"Resuming '{conversation['topic']}' from sentence {init_result['index'] + 1} of {init_result['total']}", "info")
    
    def _handle_session_logic(self, identifier: str, user_id: Optional[str] = None) -> Any:
        """Handle session-specific logic. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement _handle_session_logic")
    
    def _handle_completion(self, identifier: str, user_id: Optional[str], total_items: int, average_accuracy: float, **kwargs) -> Dict[str, Any]:
        """Handle session completion with common logic."""
        completion_context = handle_session_completion(
            self.session_type, identifier, user_id, self.session_manager, total_items, average_accuracy
        )
        
        # Clear session data
        self.session_manager.clear_session_data(self.session_type)
        
        return completion_context


class StorySessionHandler(BaseSessionHandler):
    """Handler for story sessions."""
    
    def __init__(self, session_manager: SessionManager):
        super().__init__(session_manager, "story", "session_story.html", "summary_story.html")
    
    def _handle_session_logic(self, story_id: str, user_id: Optional[str] = None) -> Any:
        """Handle story session logic."""
        from .session import StorySession
        
        # Initialize story group scores if needed
        if "story_group_scores" not in session or session.get("story_id") != story_id:
            session["story_group_scores"] = []
        
        story_session_obj = StorySession(self.session_manager.ctx)
        story = self.session_manager.ctx.get_story(story_id)
        
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
                
                # Handle session completion
                completion_context = self._handle_completion(story_id, user_id, total, average_accuracy)
                
                # Clear per-sentence correctness keys
                for i in range(len(story["parts"])):
                    session.pop(f"story_part_{i}_correct", None)
                
                return render_template(self.summary_template, 
                                     score=score, 
                                     story=story, 
                                     story_id=story_id, 
                                     **completion_context)
        
        # Handle user input
        if request.method == "POST" and "user_input" in request.form:
            user_input = request.form["user_input"].strip()
            return render_template(self.template_name, **story_session_obj.update_score(user_input))
        
        # Return session context
        return render_template(self.template_name, **story_session_obj.get_context())


class ConversationSessionHandler(BaseSessionHandler):
    """Handler for conversation sessions."""
    
    def __init__(self, session_manager: SessionManager):
        super().__init__(session_manager, "conversation", "session_conversation.html", "summary_conversation.html")
    
    def _handle_session_logic(self, conversation_id: str, user_id: Optional[str] = None) -> Any:
        """Handle conversation session logic."""
        from .session import ConversationSession
        
        conversation_session_obj = ConversationSession(self.session_manager.ctx)
        conversation = self.session_manager.ctx.get_conversation(conversation_id)
        
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
                
                # Handle session completion
                completion_context = self._handle_completion(conversation_id, user_id, total, average_accuracy)
                
                return render_template(self.summary_template, 
                                     score=score, 
                                     conversation=conversation, 
                                     conversation_id=conversation_id, 
                                     **completion_context)
        
        # Handle user input
        if request.method == "POST" and "user_input" in request.form:
            user_input = request.form["user_input"].strip()
            return render_template(self.template_name, **conversation_session_obj.update_score(user_input))
        
        # Return session context
        return render_template(self.template_name, **conversation_session_obj.get_context()) 