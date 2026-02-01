"""
Main application views for the Kiosk.show Replacement application.

This module contains the main application routes including:
- Dashboard/home page
- General navigation routes
- Application status and health endpoints
"""

from typing import Any

from flask import Blueprint, redirect, render_template, url_for

from ..auth.decorators import get_current_user, login_required

# Create main blueprint
bp = Blueprint("main", __name__)


@bp.route("/")
def index() -> Any:
    """
    Application home page.

    Returns:
        Response: Redirect to React admin interface
    """
    # Always redirect to React admin interface
    # React handles authentication state and shows login if needed
    return redirect("/admin/")


@bp.route("/dashboard")
@login_required
def dashboard() -> Any:
    """
    Main dashboard page for authenticated users.

    Returns:
        Response: Dashboard template with user information
    """
    user = get_current_user()

    # Basic dashboard data - will be enhanced in future milestones
    dashboard_data = {
        "user": user,
        "total_slideshows": 0,  # Placeholder - will be populated from database
        "total_displays": 0,  # Placeholder - will be populated from database
        "online_displays": 0,  # Placeholder - will be populated from database
    }

    return render_template("main/dashboard.html", **dashboard_data)


@bp.route("/about")
def about() -> Any:
    """
    About page with application information.

    Returns:
        Response: About page template
    """
    app_info = {
        "version": "0.1.0",
        "description": "A modern replacement for kiosk.show with enhanced features",
        "milestone": "Milestone 3: Basic Flask Application and Authentication",
    }

    return render_template("main/about.html", **app_info)
