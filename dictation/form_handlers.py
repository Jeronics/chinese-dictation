"""
Form handlers for processing user inputs across different dictation session types.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from flask import request, session, flash
from .corrector import Corrector


class FormHandler:
    """Base class for form handling across different session types."""
    
    def __init__(self, corrector: Corrector):
        self.corrector = corrector
    
    def validate_user_input(self, user_input: str) -> Tuple[bool, str]:
        """
        Validate user input and return (is_valid, error_message).
        
        Args:
            user_input: The user's input string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not user_input:
            return True, ""  # Empty input is valid (user can skip)
        
        # Basic validation - could be extended
        if len(user_input.strip()) > 1000:  # Reasonable limit
            return False, "Input too long. Please keep it under 1000 characters."
        
        return True, ""
    
    def process_single_input(self, user_input: str, correct_text: str) -> Dict[str, Any]:
        """
        Process a single user input against correct text.
        
        Args:
            user_input: User's input
            correct_text: Correct text to compare against
            
        Returns:
            Dictionary with correction results
        """
        if not user_input.strip():
            return {
                "correction": "",
                "accuracy": 0,
                "correct_segments": [],
                "user_input": user_input
            }
        
        correction, stripped_user, stripped_correct, correct_segments = self.corrector.compare(
            user_input.strip(), correct_text
        )
        
        accuracy = round(len(correct_segments) / len(stripped_correct) * 100) if len(stripped_correct) > 0 else 0
        
        return {
            "correction": correction,
            "accuracy": accuracy,
            "correct_segments": correct_segments,
            "user_input": user_input.strip()
        }


class HSKFormHandler(FormHandler):
    """Handler for HSK session form processing."""
    
    def process_hsk_input(self, user_input: str, sentence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process HSK session user input.
        
        Args:
            user_input: User's input
            sentence: Sentence data from context
            
        Returns:
            Dictionary with correction results and session context
        """
        # Validate input
        is_valid, error_msg = self.validate_user_input(user_input)
        if not is_valid:
            flash(error_msg, "error")
            return {"error": error_msg}
        
        # Process correction
        result = self.process_single_input(user_input, sentence["chinese"])
        
        # Update session with accuracy score
        accuracy_scores = session.get("accuracy_scores", [])
        accuracy_scores.append(result["accuracy"])
        session["accuracy_scores"] = accuracy_scores
        
        # Mark current sentence as correct/incorrect for tracking
        current_index = session.get("session_index", 0)
        session[f"sentence_{current_index}_correct"] = result["accuracy"] >= 70
        
        return {
            "correction": result["correction"],
            "accuracy": result["accuracy"],
            "user_input": result["user_input"],
            "sentence": sentence,
            "feedback": self._get_feedback(result["accuracy"])
        }
    
    def _get_feedback(self, accuracy: int) -> Tuple[str, str]:
        """Get feedback message and color based on accuracy."""
        if accuracy >= 90:
            return ("Excellent!", "#2e7d32")  # green
        elif accuracy >= 80:
            return ("Good job!", "#388e3c")   # light green
        elif accuracy >= 70:
            return ("Not bad!", "#f57c00")    # orange
        elif accuracy >= 50:
            return ("Keep trying!", "#f57c00") # orange
        else:
            return ("Poor..", "#c62828")      # red


class StoryFormHandler(FormHandler):
    """Handler for story session form processing."""
    
    def process_story_input(self, user_input: str, story_part: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process story session user input.
        
        Args:
            user_input: User's input
            story_part: Story part data
            
        Returns:
            Dictionary with correction results and session context
        """
        # Validate input
        is_valid, error_msg = self.validate_user_input(user_input)
        if not is_valid:
            flash(error_msg, "error")
            return {"error": error_msg}
        
        # Process correction
        result = self.process_single_input(user_input, story_part["chinese"])
        
        # Update session with accuracy score
        accuracy_scores = session.get("accuracy_scores", [])
        accuracy_scores.append(result["accuracy"])
        session["accuracy_scores"] = accuracy_scores
        
        # Mark current part as correct/incorrect for tracking
        current_index = session.get("story_session_index", 0)
        session[f"story_part_{current_index}_correct"] = result["accuracy"] >= 70
        
        return {
            "correction": result["correction"],
            "accuracy": result["accuracy"],
            "user_input": result["user_input"],
            "story_part": story_part,
            "feedback": self._get_feedback(result["accuracy"])
        }
    
    def _get_feedback(self, accuracy: int) -> Tuple[str, str]:
        """Get feedback message and color based on accuracy."""
        if accuracy >= 90:
            return ("Excellent!", "#2e7d32")
        elif accuracy >= 80:
            return ("Good job!", "#388e3c")
        elif accuracy >= 70:
            return ("Not bad!", "#f57c00")
        elif accuracy >= 50:
            return ("Keep trying!", "#f57c00")
        else:
            return ("Poor..", "#c62828")


class ConversationFormHandler(FormHandler):
    """Handler for conversation session form processing."""
    
    def process_conversation_input(self, user_input: str, sentence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process conversation session user input.
        
        Args:
            user_input: User's input
            sentence: Sentence data from conversation
            
        Returns:
            Dictionary with correction results and session context
        """
        # Validate input
        is_valid, error_msg = self.validate_user_input(user_input)
        if not is_valid:
            flash(error_msg, "error")
            return {"error": error_msg}
        
        # Process correction
        result = self.process_single_input(user_input, sentence["chinese"])
        
        # Update session with accuracy score
        accuracy_scores = session.get("accuracy_scores", [])
        accuracy_scores.append(result["accuracy"])
        session["accuracy_scores"] = accuracy_scores
        
        return {
            "correction": result["correction"],
            "accuracy": result["accuracy"],
            "user_input": result["user_input"],
            "sentence": sentence,
            "feedback": self._get_feedback(result["accuracy"])
        }
    
    def process_conversation_batch(self, conversation: Dict[str, Any], user_inputs: Dict[str, str]) -> Dict[str, Any]:
        """
        Process multiple conversation inputs at once (for "Submit All" functionality).
        
        Args:
            conversation: Conversation data
            user_inputs: Dictionary mapping sentence_id to user input
            
        Returns:
            Dictionary with all correction results
        """
        all_corrections = []
        total_accuracy = 0
        total_sentences = len(conversation["sentences"])
        
        for sentence in conversation["sentences"]:
            sentence_id = str(sentence["id"])
            user_input = user_inputs.get(sentence_id, "")
            
            # Process each sentence
            result = self.process_single_input(user_input, sentence["chinese"])
            total_accuracy += result["accuracy"]
            
            all_corrections.append({
                "sentence_id": sentence_id,
                "chinese": sentence["chinese"],
                "user_input": user_input,
                "correction": result["correction"],
                "pinyin": sentence["pinyin"],
                "translation": sentence["english"],
                "accuracy": result["accuracy"],
                "speaker": sentence["speaker"]
            })
        
        # Calculate average accuracy
        average_accuracy = total_accuracy / total_sentences if total_sentences > 0 else 0
        
        # Update session with accuracy scores
        session["accuracy_scores"] = [corr["accuracy"] for corr in all_corrections]
        
        return {
            "all_corrections": all_corrections,
            "average_accuracy": average_accuracy,
            "total_sentences": total_sentences
        }
    
    def _get_feedback(self, accuracy: int) -> Tuple[str, str]:
        """Get feedback message and color based on accuracy."""
        if accuracy >= 90:
            return ("Excellent!", "#2e7d32")
        elif accuracy >= 80:
            return ("Good job!", "#388e3c")
        elif accuracy >= 70:
            return ("Not bad!", "#f57c00")
        elif accuracy >= 50:
            return ("Keep trying!", "#f57c00")
        else:
            return ("Poor..", "#c62828")


class AuthenticationFormHandler:
    """Handler for authentication form processing."""
    
    def validate_login_form(self, email: str, password: str) -> Tuple[bool, str]:
        """
        Validate login form inputs.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email or not email.strip():
            return False, "Email is required."
        
        if not password:
            return False, "Password is required."
        
        # Basic email validation
        if "@" not in email or "." not in email:
            return False, "Please enter a valid email address."
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters long."
        
        return True, ""
    
    def validate_signup_form(self, email: str, password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Validate signup form inputs.
        
        Args:
            email: User's email
            password: User's password
            confirm_password: Password confirmation
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Basic validation
        is_valid, error_msg = self.validate_login_form(email, password)
        if not is_valid:
            return False, error_msg
        
        # Check password confirmation
        if password != confirm_password:
            return False, "Passwords do not match."
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."
        
        return True, "" 