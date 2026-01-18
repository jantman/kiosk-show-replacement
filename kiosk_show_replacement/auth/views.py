"""
Authentication views for the Kiosk.show Replacement application.

This module contains Flask routes for user authentication including:
- Login and logout endpoints
- Session management
- User creation during login process
- Authentication status checks

Implements permissive authentication where any username/password combination
is accepted, creating users dynamically as needed.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, cast

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import IntegrityError

from ..app import db
from ..models import User

# Create authentication blueprint
bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.app_context_processor
def inject_current_user() -> dict[str, Optional[User]]:
    """Make current_user available in all templates."""
    from .decorators import get_current_user

    return dict(current_user=get_current_user())


@bp.route("/login", methods=["GET", "POST"])
def login() -> Any:
    """
    Handle user login with permissive authentication.

    GET: Display login form
    POST: Process login credentials (any username/password accepted)

    Returns:
        Response: Login form template or redirect to dashboard
    """
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Basic validation
        if not username:
            flash("Username is required", "error")
            return render_template("auth/login.html")

        if not password:
            flash("Password is required", "error")
            return render_template("auth/login.html")

        # Permissive authentication - accept any valid username/password
        user = _get_or_create_user(username, password)

        if user:
            # Log successful login
            user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()

            # Set up session
            session["user_id"] = user.id
            session["username"] = user.username
            session["is_admin"] = user.is_admin

            current_app.logger.info(
                "User login successful",
                extra={
                    "user_id": user.id,
                    "username": user.username,
                    "action": "login",
                    "ip_address": request.remote_addr,
                },
            )

            flash(f"Welcome, {user.username}!", "success")

            # Redirect to next page or dashboard
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))
        else:
            flash("Login failed. Please try again.", "error")

    return render_template("auth/login.html")


@bp.route("/logout")
def logout() -> Any:
    """
    Handle user logout.

    Returns:
        Response: Redirect to login page
    """
    user_id = session.get("user_id")
    username = session.get("username")

    # Clear session
    session.clear()

    if user_id:
        current_app.logger.info(
            "User logout",
            extra={
                "user_id": user_id,
                "username": username,
                "action": "logout",
                "ip_address": request.remote_addr,
            },
        )

    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))


@bp.route("/status")
def status() -> Dict[str, Any]:
    """
    Check authentication status.

    Returns:
        Dict: JSON response with authentication status
    """
    is_authenticated = "user_id" in session
    user_info = None

    if is_authenticated:
        user_info = {
            "id": session.get("user_id"),
            "username": session.get("username"),
            "is_admin": session.get("is_admin", False),
        }

    return {
        "authenticated": is_authenticated,
        "user": user_info,
    }


def _get_or_create_user(username: str, password: str) -> Optional[User]:
    """
    Get existing user or create new user with permissive authentication.

    Args:
        username: The username to authenticate
        password: The password (accepted for any non-empty value)

    Returns:
        User: The authenticated user object, or None if creation failed
    """
    try:
        # Check if user already exists
        user = cast(Optional[User], User.query.filter_by(username=username).first())

        if user:
            # For existing users, just update their password hash if needed
            # In permissive mode, we accept any password but store the latest one
            if not user.check_password(password):
                user.set_password(password)
                user.updated_at = datetime.now(timezone.utc)
                db.session.commit()

                current_app.logger.info(
                    "User password updated during login",
                    extra={
                        "user_id": user.id,
                        "username": user.username,
                        "action": "password_update",
                    },
                )

            return user
        else:
            # Create new user with provided credentials
            # All users get admin privileges in permissive mode
            new_user = User(
                username=username,
                email=None,  # Email not required for permissive auth
                is_admin=True,
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            current_app.logger.info(
                "New user created during login",
                extra={
                    "user_id": new_user.id,
                    "username": new_user.username,
                    "action": "user_creation",
                    "ip_address": request.remote_addr,
                },
            )

            return new_user

    except IntegrityError as e:
        # Handle race condition where user was created between check and insert
        db.session.rollback()

        current_app.logger.warning(
            "User creation failed due to integrity error, retrying",
            extra={
                "username": username,
                "action": "user_creation_retry",
                "error": str(e),
            },
        )

        # Try to get the user that was created by another request
        user = cast(Optional[User], User.query.filter_by(username=username).first())
        if user and user.check_password(password):
            return user

        return None

    except Exception as e:
        db.session.rollback()

        current_app.logger.error(
            "Unexpected error during user authentication",
            extra={
                "username": username,
                "action": "authentication_error",
                "error": str(e),
            },
        )

        return None
