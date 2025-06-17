"""
Slideshow module for the Kiosk.show Replacement application.

This module handles slideshow-related functionality including:
- Slideshow creation, editing, and management
- Slideshow item ordering and reordering
- Content type handling (images, videos, web pages)
- File upload and storage management
- Slideshow validation and business logic
- Default slideshow management

Provides both API endpoints and utilities for slideshow operations
with comprehensive validation and error handling.

This module provides web interface for managing slideshows and slides.
"""

from typing import Union

from flask import (
    Blueprint,
    Response,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from ..app import db
from ..auth.decorators import get_current_user
from ..models import Slideshow, SlideshowItem

__all__: list[str] = []

bp = Blueprint("slideshow", __name__)


@bp.route("/")
def list_slideshows() -> str:
    """List all slideshows for management. Global access."""
    slideshows = (
        Slideshow.query.filter_by(is_active=True).order_by(Slideshow.name).all()
    )
    return render_template("slideshow/list.html", slideshows=slideshows)


@bp.route("/create", methods=["GET", "POST"])
def create_slideshow() -> Union[str, Response]:
    """Create a new slideshow."""
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description", "")

        if not name:
            flash("Name is required", "error")
            return render_template("slideshow/create.html")

        # Get current user from session
        current_user = get_current_user()
        if not current_user:
            flash("You must be logged in to create a slideshow", "error")
            return redirect(url_for("auth.login"))

        slideshow = Slideshow(
            name=name,
            description=description,
            owner_id=current_user.id,
            created_by_id=current_user.id,
        )

        try:
            db.session.add(slideshow)
            db.session.commit()
            flash(f'Slideshow "{name}" created successfully', "success")
            return redirect(
                url_for("slideshow.edit_slideshow", slideshow_id=slideshow.id)
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating slideshow: {str(e)}", "error")

    return render_template("slideshow/create.html")


@bp.route("/<int:slideshow_id>/edit")
def edit_slideshow(slideshow_id: int) -> str:
    """Edit a slideshow and its slides."""
    slideshow = Slideshow.query.get_or_404(slideshow_id)
    slides = (
        SlideshowItem.query.filter_by(slideshow_id=slideshow_id)
        .order_by(SlideshowItem.order_index)
        .all()
    )

    return render_template("slideshow/edit.html", slideshow=slideshow, slides=slides)


@bp.route("/<int:slideshow_id>/delete", methods=["POST"])
def delete_slideshow(slideshow_id: int) -> Response:
    """Delete a slideshow (soft delete)."""
    slideshow = Slideshow.query.get_or_404(slideshow_id)

    slideshow.is_active = False

    try:
        db.session.commit()
        flash(f'Slideshow "{slideshow.name}" deleted successfully', "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting slideshow: {str(e)}", "error")

    return redirect(url_for("slideshow.list_slideshows"))
