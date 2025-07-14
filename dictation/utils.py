from functools import wraps
from flask import session, flash, redirect, url_for
from typing import Callable, Any

def login_required(f: Callable) -> Callable:
    """
    Decorator to require user login for a Flask route. Redirects to login if not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs) -> Any:
        if not session.get("user_id"):
            flash("Please log in to access this feature.", "warning")
            return redirect(url_for("dictation.login"))
        return f(*args, **kwargs)
    return decorated_function 