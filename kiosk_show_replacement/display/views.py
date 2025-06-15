"""
Display views for the Kiosk.show Replacement application.

This module handles the core display functionality for kiosk devices including:
- Display registration and auto-discovery
- Resolution detection and management
- Slideshow rendering and playback
- Display heartbeat and status monitoring
- Default slideshow assignment logic

Designed for reliability on kiosk hardware with minimal JavaScript dependencies.
"""

from datetime import datetime, timezone
from typing import Optional, Union

from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    request,
)

from ..models import Display, Slideshow, SlideshowItem, db

# Create the display blueprint
display_bp = Blueprint(
    "display",
    __name__,
    url_prefix="/display",
    template_folder="../templates/display",
)


@display_bp.route("/")
def index() -> str:
    """Main display interface landing page."""
    return render_template("display/index.html")


@display_bp.route("/<string:display_name>/info")
def display_info(display_name: str) -> str:
    """Display information and status page."""
    display = get_or_create_display(display_name)
    update_display_heartbeat(display)

    slideshow = get_display_slideshow(display)
    slides = get_slideshow_items(slideshow.id) if slideshow else []
    slides_data = [slide.to_dict() for slide in slides]

    return render_template(
        "display/index.html",
        display=display,
        slideshow=slideshow,
        slides=slides_data,
        now=datetime.now(timezone.utc),
    )


@display_bp.route("/<string:display_name>")
def display_interface(display_name: str) -> Union[str, Response]:
    """
    Main display interface for a specific display.

    Handles display registration, slideshow assignment, and rendering.
    """
    # Get or create display
    display = get_or_create_display(display_name)

    # Update heartbeat
    update_display_heartbeat(display)

    # Get assigned slideshow or default
    slideshow = get_display_slideshow(display)

    if not slideshow:
        # No slideshow available - show configuration page
        return render_template(
            "display/configure.html",
            display=display,
            available_slideshows=get_available_slideshows(),
        )

    # Get slideshow items
    slides = get_slideshow_items(slideshow.id)

    if not slides:
        # No slides in slideshow - show empty state
        return render_template(
            "display/no_content.html",
            display=display,
            slideshow=slideshow,
        )

    # Log display activity
    current_app.logger.info(
        "Display slideshow rendered",
        extra={
            "display_id": display.id,
            "display_name": display.name,
            "slideshow_id": slideshow.id,
            "slideshow_name": slideshow.name,
            "slide_count": len(slides),
            "action": "slideshow_render",
        },
    )

    # Convert slides to JSON-serializable format
    slides_data = [slide.to_dict() for slide in slides]

    # Render slideshow display
    return render_template(
        "display/slideshow.html",
        display=display,
        slideshow=slideshow,
        slides=slides_data,
    )


@display_bp.route("/<string:display_name>/heartbeat", methods=["POST"])
def update_heartbeat(display_name: str) -> Response:
    """
    Update display heartbeat and resolution information.

    Expected JSON payload:
    {
        "resolution": {"width": 1920, "height": 1080},
        "user_agent": "Browser info",
        "timestamp": "ISO timestamp"
    }
    """
    try:
        # Parse JSON data with error handling
        try:
            data = request.get_json() or {}
        except Exception:
            # Invalid JSON
            return jsonify({"status": "error", "message": "Invalid JSON data"}), 400

        # Get or create display
        display = get_or_create_display(display_name)

        # Update heartbeat timestamp
        display.last_seen_at = datetime.now(timezone.utc)

        # Update resolution if provided (handle both direct fields and resolution object)
        width = data.get("width")
        height = data.get("height")
        
        # Also check for resolution object format
        resolution = data.get("resolution")
        if resolution and isinstance(resolution, dict):
            width = width or resolution.get("width")
            height = height or resolution.get("height")

        # Update resolution fields if provided
        if width is not None:
            display.resolution_width = int(width)
        if height is not None:
            display.resolution_height = int(height)

        # Update user agent if provided
        user_agent = data.get("user_agent")
        if user_agent:
            # Store in a display metadata field if we add one later
            pass

        db.session.commit()

        current_app.logger.debug(
            "Display heartbeat updated",
            extra={
                "display_id": display.id,
                "display_name": display.name,
                "resolution": f"{display.resolution_width}x{display.resolution_height}",
                "action": "heartbeat_update",
            },
        )

        return jsonify(
            {"status": "success", "timestamp": display.last_seen_at.isoformat()}
        )

    except Exception as e:
        current_app.logger.error(
            "Failed to update display heartbeat",
            extra={
                "display_name": display_name,
                "error": str(e),
                "action": "heartbeat_error",
            },
        )
        return jsonify({"status": "error", "message": str(e)}), 500


@display_bp.route("/<string:display_name>/status")
def display_status(display_name: str) -> Response:
    """Get current display status and configuration."""
    display = Display.query.filter_by(name=display_name).first()

    if not display:
        # Auto-create the display if it doesn't exist
        display = get_or_create_display(display_name)

    slideshow = get_display_slideshow(display)

    status_data = {
        "name": display.name,
        "online": display.is_online,
        "resolution": {
            "width": display.resolution_width,
            "height": display.resolution_height,
        },
        "last_seen_at": display.last_seen_at.isoformat() if display.last_seen_at else None,
        "slideshow": slideshow.to_dict() if slideshow else None,
        "created_at": display.created_at.isoformat(),
    }

    return jsonify(status_data)


@display_bp.route("/<string:display_name>/slideshow/current")
def current_slideshow(display_name: str) -> Response:
    """Get current slideshow data for a display (for AJAX updates)."""
    display = Display.query.filter_by(name=display_name).first()

    if not display:
        return jsonify({"error": "Display not found"}), 404

    slideshow = get_display_slideshow(display)

    if not slideshow:
        return jsonify({"slideshow": None, "slides": []})

    slides = get_slideshow_items(slideshow.id)

    return jsonify(
        {
            "slideshow": slideshow.to_dict(),
            "slides": [slide.to_dict() for slide in slides],
            "display": {
                "id": display.id,
                "name": display.name,
                "resolution": {
                    "width": display.resolution_width,
                    "height": display.resolution_height,
                },
            },
        }
    )


@display_bp.route("/<string:display_name>/assign/<int:slideshow_id>", methods=["POST"])
def assign_slideshow(display_name: str, slideshow_id: int) -> Response:
    """Assign a slideshow to a display."""
    try:
        display = get_or_create_display(display_name)
        slideshow = Slideshow.query.get_or_404(slideshow_id)

        # Update display assignment
        display.current_slideshow_id = slideshow.id
        db.session.commit()

        current_app.logger.info(
            "Slideshow assigned to display",
            extra={
                "display_id": display.id,
                "display_name": display.name,
                "slideshow_id": slideshow.id,
                "slideshow_name": slideshow.name,
                "action": "slideshow_assignment",
            },
        )

        return jsonify(
            {
                "status": "success",
                "display_name": display.name,
                "slideshow_name": slideshow.name,
            }
        )

    except Exception as e:
        current_app.logger.error(
            "Failed to assign slideshow to display",
            extra={
                "display_name": display_name,
                "slideshow_id": slideshow_id,
                "error": str(e),
                "action": "assignment_error",
            },
        )
        return jsonify({"status": "error", "message": str(e)}), 500


# Helper Functions


def get_or_create_display(display_name: str) -> Display:
    """
    Get existing display or create new one with auto-registration.

    Implements display auto-registration on first connection as per Milestone 4.
    """
    display = Display.query.filter_by(name=display_name).first()

    if not display:
        # Auto-register new display
        display = Display(
            name=display_name,
            location=f"Auto-registered: {display_name}",
            resolution_width=None,  # No default resolution, will be set by heartbeat
            resolution_height=None,
            heartbeat_interval=30,  # 30 seconds default
            is_active=True,
            owner_id=None,  # No owner initially (supports nullable owner enhancement)
        )

        db.session.add(display)
        db.session.commit()

        current_app.logger.info(
            "New display auto-registered",
            extra={
                "display_id": display.id,
                "display_name": display.name,
                "action": "auto_registration",
            },
        )

    return display


def update_display_heartbeat(display: Display) -> None:
    """Update display last_seen_at timestamp."""
    display.last_seen_at = datetime.now(timezone.utc)
    db.session.commit()


def get_display_slideshow(display: Display) -> Optional[Slideshow]:
    """
    Get the slideshow assigned to a display.

    Priority:
    1. Display-specific assignment (current_slideshow_id)
    2. Default slideshow (is_default=True)
    3. None
    """
    # Check for specific assignment
    if display.current_slideshow_id:
        slideshow = Slideshow.query.get(display.current_slideshow_id)
        if slideshow and slideshow.is_active:
            return slideshow

    # Fall back to default slideshow
    default_slideshow = Slideshow.query.filter_by(
        is_default=True, is_active=True
    ).first()
    if default_slideshow:
        # Auto-assign default slideshow to display
        display.current_slideshow_id = default_slideshow.id
        db.session.commit()

        current_app.logger.info(
            "Default slideshow auto-assigned to display",
            extra={
                "display_id": display.id,
                "display_name": display.name,
                "slideshow_id": default_slideshow.id,
                "slideshow_name": default_slideshow.name,
                "action": "default_assignment",
            },
        )

        return default_slideshow

    return None


def get_slideshow_items(slideshow_id: int) -> list[SlideshowItem]:
    """Get active slideshow items in order."""
    return (
        SlideshowItem.query.filter_by(slideshow_id=slideshow_id, is_active=True)
        .order_by(SlideshowItem.order_index)
        .all()
    )


def get_available_slideshows() -> list[Slideshow]:
    """Get all available active slideshows for display assignment."""
    return Slideshow.query.filter_by(is_active=True).order_by(Slideshow.name).all()
