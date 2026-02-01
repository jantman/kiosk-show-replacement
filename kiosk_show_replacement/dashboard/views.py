"""
Dashboard views for the Kiosk.show Replacement application.

This module contains Flask routes and view functions for the main dashboard interface.
Provides core application functionality including user management, system monitoring,
and navigation between different application sections.
"""

from typing import Any, Dict, Union

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)
from sqlalchemy import text
from sqlalchemy.orm import joinedload
from werkzeug.wrappers import Response

from ..auth import admin_required, get_current_user, login_required
from ..models import Display, Slideshow, db

# Create the dashboard blueprint
dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/",
    template_folder="../templates/dashboard",
    static_folder="../static",
)


@dashboard_bp.route("/")
def index() -> Union[str, Response]:
    """
    Main dashboard landing page.

    Displays system overview, recent activity, and navigation options.
    Redirects to React admin interface if user is not authenticated.

    Returns:
        Union[str, Response]: Rendered template or redirect response
    """
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for("serve_admin"))

    # Get dashboard statistics
    try:
        total_displays = db.session.query(Display).count()
        active_displays = (
            db.session.query(Display).filter(Display.is_active.is_(True)).count()
        )
        total_slideshows = db.session.query(Slideshow).count()
        active_slideshows = (
            db.session.query(Slideshow).filter(Slideshow.is_active.is_(True)).count()
        )

        # Get recent displays (all displays, not user-filtered)
        recent_displays = (
            db.session.query(Display).order_by(Display.updated_at.desc()).limit(5).all()
        )

        # Get recent slideshows (all active slideshows, not user-filtered)
        # Eagerly load items to avoid DetachedInstanceError
        recent_slideshows = (
            db.session.query(Slideshow)
            .filter_by(is_active=True)
            .options(joinedload(Slideshow.items))
            .order_by(Slideshow.updated_at.desc())
            .limit(5)
            .all()
        )

        dashboard_data = {
            "total_displays": total_displays,
            "active_displays": active_displays,
            "total_slideshows": total_slideshows,
            "active_slideshows": active_slideshows,
            "recent_displays": recent_displays,
            "recent_slideshows": recent_slideshows,
            "user": current_user,
        }

    except Exception as e:
        current_app.logger.error(f"Error loading dashboard data: {e}")
        flash("Error loading dashboard data", "error")
        dashboard_data = {
            "total_displays": 0,
            "active_displays": 0,
            "total_slideshows": 0,
            "active_slideshows": 0,
            "recent_displays": [],
            "recent_slideshows": [],
            "user": current_user,
        }

    # Don't close the session here - let Flask-SQLAlchemy handle it
    # The session needs to remain open for template rendering

    return render_template("dashboard/index.html", **dashboard_data)


@dashboard_bp.route("/profile")
@login_required
def profile() -> str:
    """
    User profile page.

    Displays user account information and settings.
    Requires authentication.

    Returns:
        str: Rendered profile template
    """
    current_user = get_current_user()
    return render_template("dashboard/profile.html", user=current_user)


@dashboard_bp.route("/settings")
@login_required
@admin_required
def settings() -> str:
    """
    Application settings page.

    Displays system-wide settings and configuration options.
    Requires authentication.

    Returns:
        str: Rendered settings template
    """
    current_user = get_current_user()
    return render_template("dashboard/settings.html", user=current_user)


@dashboard_bp.route("/health")
def health() -> Dict[str, Any]:
    """
    System health check endpoint.

    Provides basic health information for monitoring and debugging.
    Does not require authentication.

    Returns:
        Dict[str, Any]: JSON response with health status
    """
    try:
        # Test database connection
        db.session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    finally:
        db.session.close()

    from datetime import datetime, timezone

    from .. import __version__

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "version": __version__,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Error handlers for the dashboard blueprint
@dashboard_bp.errorhandler(404)
def not_found(error: Exception) -> tuple[str, int]:
    """Handle 404 errors in dashboard routes."""
    return (
        render_template(
            "dashboard/error.html", error_code=404, error_message="Page not found"
        ),
        404,
    )


@dashboard_bp.errorhandler(500)
def internal_error(error: Exception) -> tuple[str, int]:
    """Handle 500 errors in dashboard routes."""
    current_app.logger.error(f"Internal server error: {error}")
    return (
        render_template(
            "dashboard/error.html",
            error_code=500,
            error_message="Internal server error",
        ),
        500,
    )
