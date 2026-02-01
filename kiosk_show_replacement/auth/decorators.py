"""
Authentication decorators and middleware for the Kiosk.show Replacement application.

This module provides decorators and utilities for:
- Requiring authentication on routes
- Checking admin privileges
- Session management utilities
- Authentication state helpers
"""

from functools import wraps
from typing import Any, Callable, Optional, cast

from flask import current_app, g, redirect, request, session, url_for

from ..app import db
from ..models import User


def login_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require authentication for a route.

    Args:
        f: The view function to protect

    Returns:
        Callable: The decorated function that checks authentication
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not is_authenticated():
            return redirect(url_for("serve_admin"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to require admin privileges for a route.

    Args:
        f: The view function to protect

    Returns:
        Callable: The decorated function that checks admin status
    """

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not is_authenticated():
            return redirect(url_for("serve_admin"))

        if not is_admin():
            current_app.logger.warning(
                "Non-admin user attempted to access admin route",
                extra={
                    "user_id": session.get("user_id"),
                    "username": session.get("username"),
                    "route": request.endpoint,
                    "action": "unauthorized_access_attempt",
                },
            )
            # You might want to create an error template for this
            return "Access denied: Admin privileges required", 403

        return f(*args, **kwargs)

    return decorated_function


def is_authenticated() -> bool:
    """
    Check if the current user is authenticated.

    Returns:
        bool: True if user is authenticated, False otherwise
    """
    return "user_id" in session and session["user_id"] is not None


def is_admin() -> bool:
    """
    Check if the current user has admin privileges.

    Returns:
        bool: True if user is admin, False otherwise
    """
    return is_authenticated() and session.get("is_admin", False)


def get_current_user() -> Optional[User]:
    """
    Get the current authenticated user object.

    Returns:
        User: The current user object, or None if not authenticated
    """
    if not is_authenticated():
        return None

    user_id = session.get("user_id")
    if not user_id:
        return None

    # Use g to cache the user object for the request
    if not hasattr(g, "current_user"):
        g.current_user = db.session.get(User, user_id)

    return cast(Optional[User], g.current_user)


def get_current_user_id() -> Optional[int]:
    """
    Get the current authenticated user ID.

    Returns:
        int: The current user ID, or None if not authenticated
    """
    return session.get("user_id") if is_authenticated() else None


def refresh_session_user_data(user: User) -> None:
    """
    Refresh session data with current user information.

    Args:
        user: The user object to update session data from
    """
    if is_authenticated() and session.get("user_id") == user.id:
        session["username"] = user.username
        session["is_admin"] = user.is_admin

        current_app.logger.debug(
            "Session data refreshed for user",
            extra={
                "user_id": user.id,
                "username": user.username,
                "action": "session_refresh",
            },
        )


def clear_session() -> None:
    """Clear all session data."""
    user_id = session.get("user_id")
    username = session.get("username")

    session.clear()

    if user_id:
        current_app.logger.debug(
            "Session cleared",
            extra={
                "user_id": user_id,
                "username": username,
                "action": "session_clear",
            },
        )
