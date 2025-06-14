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

from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..app import db
from ..models import SlideItem, Slideshow

__all__ = []

bp = Blueprint("slideshow", __name__)


@bp.route("/")
def list_slideshows():
    """List all slideshows for management."""
    slideshows = Slideshow.query.all()
    return render_template("slideshow/list.html", slideshows=slideshows)


@bp.route("/create", methods=["GET", "POST"])
def create_slideshow():
    """Create a new slideshow."""
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description", "")

        if not name:
            flash("Name is required", "error")
            return render_template("slideshow/create.html")

        slideshow = Slideshow(name=name, description=description)

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
def edit_slideshow(slideshow_id):
    """Edit a slideshow and its slides."""
    slideshow = Slideshow.query.get_or_404(slideshow_id)
    slides = (
        SlideItem.query.filter_by(slideshow_id=slideshow_id)
        .order_by(SlideItem.order_index)
        .all()
    )

    return render_template("slideshow/edit.html", slideshow=slideshow, slides=slides)


@bp.route("/<int:slideshow_id>/delete", methods=["POST"])
def delete_slideshow(slideshow_id):
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
