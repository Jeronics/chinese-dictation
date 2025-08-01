"""
Error handling utilities for the dictation application.
"""

import logging
from typing import Dict, Any, Optional, Callable
from flask import flash, redirect, url_for, render_template, request
from functools import wraps


class ErrorHandler:
    """Centralized error handling for the application."""
    
    @staticmethod
    def handle_database_error(error: Exception, operation: str = "database operation") -> None:
        """
        Handle database-related errors.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
        """
        logging.error(f"Database error during {operation}: {error}")
        flash(f"Database error occurred. Please try again.", "error")
    
    @staticmethod
    def handle_authentication_error(error: Exception, operation: str = "authentication") -> None:
        """
        Handle authentication-related errors.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
        """
        logging.error(f"Authentication error during {operation}: {error}")
        flash(f"Authentication failed. Please check your credentials and try again.", "error")
    
    @staticmethod
    def handle_session_error(error: Exception, operation: str = "session operation") -> None:
        """
        Handle session-related errors.
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
        """
        logging.error(f"Session error during {operation}: {error}")
        flash(f"Session error occurred. Please refresh the page and try again.", "error")
    
    @staticmethod
    def handle_validation_error(error: Exception, field: str = "input") -> None:
        """
        Handle validation errors.
        
        Args:
            error: The exception that occurred
            field: The field that failed validation
        """
        logging.warning(f"Validation error for {field}: {error}")
        flash(f"Invalid {field}. Please check your input and try again.", "error")
    
    @staticmethod
    def handle_file_error(error: Exception, file_path: str = "file") -> None:
        """
        Handle file-related errors.
        
        Args:
            error: The exception that occurred
            file_path: The file that caused the error
        """
        logging.error(f"File error for {file_path}: {error}")
        flash(f"File error occurred. Please contact support if this persists.", "error")
    
    @staticmethod
    def handle_audio_error(error: Exception, audio_file: str = "audio file") -> None:
        """
        Handle audio-related errors.
        
        Args:
            error: The exception that occurred
            audio_file: The audio file that caused the error
        """
        logging.error(f"Audio error for {audio_file}: {error}")
        flash(f"Audio playback error. Please try again or contact support.", "error")


def handle_errors(operation: str = "operation", redirect_url: Optional[str] = None):
    """
    Decorator to handle errors in route functions.
    
    Args:
        operation: Description of the operation being performed
        redirect_url: URL to redirect to on error (defaults to menu)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"Error during {operation}: {e}")
                flash(f"An error occurred during {operation}. Please try again.", "error")
                return redirect(redirect_url or url_for("dictation.menu"))
        return wrapper
    return decorator


def validate_session_state(required_keys: list, session_type: str = "session"):
    """
    Decorator to validate session state before executing route.
    
    Args:
        required_keys: List of required session keys
        session_type: Type of session for error messages
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import session
            
            missing_keys = [key for key in required_keys if key not in session]
            if missing_keys:
                logging.warning(f"Missing session keys for {session_type}: {missing_keys}")
                flash(f"Invalid {session_type} state. Please start a new session.", "error")
                return redirect(url_for("dictation.menu"))
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def validate_user_input(max_length: int = 1000, required: bool = False):
    """
    Decorator to validate user input.
    
    Args:
        max_length: Maximum allowed input length
        required: Whether input is required
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from flask import request
            
            user_input = request.form.get("user_input", "").strip()
            
            if required and not user_input:
                flash("Input is required.", "error")
                return redirect(request.url)
            
            if len(user_input) > max_length:
                flash(f"Input too long. Please keep it under {max_length} characters.", "error")
                return redirect(request.url)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


class SessionValidator:
    """Utility class for validating session state."""
    
    @staticmethod
    def validate_hsk_session() -> bool:
        """Validate HSK session state."""
        from flask import session
        
        required_keys = ["session_ids", "session_index", "hsk_level"]
        return all(key in session for key in required_keys) and session["session_ids"]
    
    @staticmethod
    def validate_story_session() -> bool:
        """Validate story session state."""
        from flask import session
        
        required_keys = ["story_session_ids", "story_session_index", "story_id"]
        return all(key in session for key in required_keys) and session["story_session_ids"]
    
    @staticmethod
    def validate_conversation_session() -> bool:
        """Validate conversation session state."""
        from flask import session
        
        required_keys = ["conversation_session_ids", "conversation_session_index", "conversation_id"]
        return all(key in session for key in required_keys) and session["conversation_session_ids"]
    
    @staticmethod
    def get_session_error_message(session_type: str) -> str:
        """Get appropriate error message for session validation failure."""
        return f"Invalid {session_type} session. Please start a new session."


class InputValidator:
    """Utility class for validating user inputs."""
    
    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Validate email format."""
        if not email or not email.strip():
            return False, "Email is required."
        
        if "@" not in email or "." not in email:
            return False, "Please enter a valid email address."
        
        return True, ""
    
    @staticmethod
    def validate_password(password: str, min_length: int = 6) -> tuple[bool, str]:
        """Validate password strength."""
        if not password:
            return False, "Password is required."
        
        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters long."
        
        return True, ""
    
    @staticmethod
    def validate_chinese_input(text: str, max_length: int = 1000) -> tuple[bool, str]:
        """Validate Chinese text input."""
        if not text:
            return True, ""  # Empty input is valid
        
        if len(text) > max_length:
            return False, f"Input too long. Please keep it under {max_length} characters."
        
        # Basic Chinese character validation (simplified)
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        if chinese_chars == 0 and text.strip():
            return False, "Please enter Chinese characters."
        
        return True, ""


def safe_get_form_data(form_key: str, default: str = "") -> str:
    """
    Safely get form data with error handling.
    
    Args:
        form_key: The form field key
        default: Default value if key not found
        
    Returns:
        The form value or default
    """
    try:
        return request.form.get(form_key, default).strip()
    except Exception as e:
        logging.warning(f"Error getting form data for {form_key}: {e}")
        return default


def safe_get_session_data(session_key: str, default: Any = None) -> Any:
    """
    Safely get session data with error handling.
    
    Args:
        session_key: The session key
        default: Default value if key not found
        
    Returns:
        The session value or default
    """
    try:
        from flask import session
        return session.get(session_key, default)
    except Exception as e:
        logging.warning(f"Error getting session data for {session_key}: {e}")
        return default 