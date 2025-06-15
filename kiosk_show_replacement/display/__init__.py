"""
Display module for the Kiosk.show Replacement application.

This module handles display-related functionality including:
- Display registration and auto-discovery
- Resolution detection and management
- Slideshow rendering and playback
- Content scaling and optimization
- Display heartbeat and status monitoring
- Server-side templates for kiosk devices

Optimized for reliability and performance on kiosk hardware with
minimal JavaScript dependencies and graceful error handling.

This module provides the main display interface for viewing slideshows
in kiosk mode.
"""

from typing import Union

from flask import Blueprint, Response, jsonify, render_template, request

from ..app import db
from ..models import SlideItem, Slideshow

__all__: list[str] = []

bp = Blueprint("display", __name__)


@bp.route("/")
def index() -> str:
    """Main landing page showing available slideshows."""
    slideshows = Slideshow.query.filter_by(is_active=True).all()
    return render_template("index.html", slideshows=slideshows)


@bp.route("/display/<int:slideshow_id>")
def display_slideshow(slideshow_id: int) -> str:
    """Display a slideshow in kiosk mode."""
    slideshow = Slideshow.query.get_or_404(slideshow_id)
    slides = (
        SlideItem.query.filter_by(slideshow_id=slideshow_id, is_active=True)
        .order_by(SlideItem.order_index)
        .all()
    )

    return render_template("display.html", slideshow=slideshow, slides=slides)


@bp.route("/api/slideshow/<int:slideshow_id>/slides")
def get_slideshow_slides(slideshow_id: int) -> Response:
    """API endpoint to get slides for a slideshow (for AJAX updates)."""
    slideshow = Slideshow.query.get_or_404(slideshow_id)
    slides = (
        SlideItem.query.filter_by(slideshow_id=slideshow_id, is_active=True)
        .order_by(SlideItem.order_index)
        .all()
    )

    return jsonify(
        {
            "slideshow": slideshow.to_dict(),
            "slides": [slide.to_dict() for slide in slides],
        }
    )
