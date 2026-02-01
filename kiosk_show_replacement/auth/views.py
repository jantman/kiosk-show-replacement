"""
Authentication views for the Kiosk.show Replacement application.

This module contains Flask routes for user authentication including:
- Login and logout endpoints
- Session management
- Authentication status checks

Implements real authentication where users must exist in the database
and provide correct credentials to log in.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional, Union, cast

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
    Handle user login with real authentication.

    GET: Display login form
    POST: Process login credentials (validates against database)

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

        # Real authentication - validate credentials
        try:
            user = _authenticate_user(username, password)
        except RuntimeError as e:
            # Database initialization error
            error_message = str(e)
            flash(error_message, "error")
            return render_template("auth/login.html")

        if user is None:
            # Authentication failed - invalid credentials
            flash("Invalid username or password", "error")
            return render_template("auth/login.html")

        if user == "inactive":
            # User account is inactive
            flash("Account is inactive. Please contact an administrator.", "error")
            return render_template("auth/login.html")

        # At this point, user must be a User object (not None or "inactive")
        # Type narrowing: cast to User for mypy
        authenticated_user = cast(User, user)

        # Authentication successful
        authenticated_user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

        # Set up session
        session["user_id"] = authenticated_user.id
        session["username"] = authenticated_user.username
        session["is_admin"] = authenticated_user.is_admin

        current_app.logger.info(
            "User login successful",
            extra={
                "user_id": authenticated_user.id,
                "username": authenticated_user.username,
                "action": "login",
                "ip_address": request.remote_addr,
            },
        )

        flash(f"Welcome, {authenticated_user.username}!", "success")

        # Redirect to next page or dashboard
        next_page = request.args.get("next")
        if next_page:
            return redirect(next_page)
        return redirect(url_for("dashboard.index"))

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


def _authenticate_user(
    username: str, password: str
) -> Union[User, Literal["inactive"], None]:
    """
    Authenticate user against database credentials.

    Args:
        username: The username to authenticate
        password: The password to verify

    Returns:
        User: The authenticated user object if credentials are valid
        None: If user not found or password is incorrect
        "inactive": If user exists but account is inactive

    Raises:
        RuntimeError: If database is not initialized
    """
    try:
        # Look up user by username
        user = cast(Optional[User], User.query.filter_by(username=username).first())

        if not user:
            # User does not exist
            current_app.logger.warning(
                "Login failed: user not found",
                extra={
                    "username": username,
                    "action": "login_user_not_found",
                    "ip_address": request.remote_addr,
                },
            )
            return None

        # Check password
        if not user.check_password(password):
            current_app.logger.warning(
                "Login failed: invalid password",
                extra={
                    "user_id": user.id,
                    "username": user.username,
                    "action": "login_invalid_password",
                    "ip_address": request.remote_addr,
                },
            )
            return None

        # Check if user is active
        if not user.is_active:
            current_app.logger.warning(
                "Login failed: user account is inactive",
                extra={
                    "user_id": user.id,
                    "username": user.username,
                    "action": "login_inactive_user",
                    "ip_address": request.remote_addr,
                },
            )
            return "inactive"

        return user

    except Exception as e:
        error_str = str(e)

        # Detect database initialization issues
        if "no such table" in error_str.lower():
            current_app.logger.error(
                "Authentication failed: Database not initialized",
                extra={
                    "username": username,
                    "action": "database_not_initialized",
                    "error": error_str,
                },
            )
            # Re-raise with a specific message that can be caught by the caller
            raise RuntimeError(
                "Database not initialized. Please run 'flask cli init-db' to set up the database."
            ) from e

        current_app.logger.error(
            "Unexpected error during user authentication",
            extra={
                "username": username,
                "action": "authentication_error",
                "error": error_str,
            },
        )

        return None
