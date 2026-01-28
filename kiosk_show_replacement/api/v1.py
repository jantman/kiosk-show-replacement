"""
API v1 endpoints for the Kiosk.show Replacement application.

This module contains all version 1 REST API endpoints:
- Slideshow CRUD operations
- Slideshow item management
- Display management

All endpoints require authentication and return consistent JSON responses.
"""

from typing import Any, Callable, Dict, Optional, Tuple

from flask import Blueprint, Response, current_app, request, session
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Unauthorized

from ..auth.decorators import get_current_user
from ..exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
)
from ..ical_service import get_or_create_feed, refresh_all_feeds, refresh_feed
from ..models import (
    AssignmentHistory,
    Display,
    DisplayConfigurationTemplate,
    Slideshow,
    SlideshowItem,
    User,
    db,
)
from ..sse import (
    create_display_event,
    create_slideshow_event,
    create_sse_response,
    create_system_event,
    require_sse_auth,
    sse_manager,
)
from ..storage import get_storage_manager
from .helpers import api_error, api_response

# Create API v1 blueprint
api_v1_bp = Blueprint("api_v1", __name__)


# =============================================================================
# Authentication Decorator for API
# =============================================================================


def api_auth_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to require authentication for API endpoints.

    Raises AuthenticationError if the user is not authenticated,
    which will be caught by the global error handler.
    """
    from functools import wraps

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not get_current_user():
            raise AuthenticationError()
        return f(*args, **kwargs)

    return decorated_function


# =============================================================================
# Slideshow API Endpoints
# =============================================================================


@api_v1_bp.route("/slideshows", methods=["GET"])
@api_auth_required
def list_slideshows() -> Tuple[Response, int]:
    """List all slideshows - every user can see every slideshow."""
    # Get all active slideshows - no ownership filtering
    # Order by updated_at DESC so most recently updated appear first
    # (matches "Recent Slideshows" label in dashboard)
    slideshows = (
        Slideshow.query.filter_by(is_active=True)
        .order_by(Slideshow.updated_at.desc())
        .all()
    )

    # Convert to dict with computed fields
    slideshow_data = []
    for slideshow in slideshows:
        data = slideshow.to_dict()
        # Add computed fields
        data["item_count"] = len([item for item in slideshow.items if item.is_active])
        slideshow_data.append(data)

    return api_response(slideshow_data, "Slideshows retrieved successfully")


@api_v1_bp.route("/slideshows", methods=["POST"])
@api_auth_required
def create_slideshow() -> Tuple[Response, int]:
    """Create a new slideshow."""
    current_user = get_current_user()
    assert current_user is not None  # Guaranteed by @api_auth_required

    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    name = data.get("name", "").strip()
    if not name:
        raise ValidationError("Slideshow name is required", field="name")

    # Check for global duplicate names (not per-user)
    existing = Slideshow.query.filter_by(name=name, is_active=True).first()
    if existing:
        raise ValidationError("A slideshow with this name already exists", field="name")

    try:
        # Check if this slideshow should be set as default
        is_default = data.get("is_default", False)

        # If setting as default, clear any existing default first
        if is_default:
            Slideshow.query.filter_by(is_default=True).update({"is_default": False})

        slideshow = Slideshow(
            name=name,
            description=data.get("description", ""),
            default_item_duration=data.get(
                "default_item_duration", 30
            ),  # Support custom duration
            transition_type=data.get("transition_type", "fade"),
            owner_id=current_user.id,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
            is_active=True,
            is_default=is_default,
        )

        db.session.add(slideshow)
        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} created slideshow: {slideshow.name}"
        )
        return api_response(slideshow.to_dict(), "Slideshow created successfully", 201)

    except IntegrityError:
        db.session.rollback()
        raise ValidationError("A slideshow with this name already exists", field="name")


@api_v1_bp.route("/slideshows/<int:slideshow_id>", methods=["GET"])
@api_auth_required
def get_slideshow_by_id(slideshow_id: int) -> Tuple[Response, int]:
    """Get a specific slideshow with its items - all users can view all slideshows."""
    slideshow = db.session.get(Slideshow, slideshow_id)
    if not slideshow or not slideshow.is_active:
        raise NotFoundError(
            "Slideshow not found", resource_type="slideshow", resource_id=slideshow_id
        )

    # Get slideshow data with items
    result = slideshow.to_dict()
    result["items"] = [item.to_dict() for item in slideshow.items if item.is_active]

    return api_response(result, "Slideshow retrieved successfully")


@api_v1_bp.route("/slideshows/<int:slideshow_id>", methods=["PUT"])
@api_auth_required
def update_slideshow(slideshow_id: int) -> Tuple[Response, int]:
    """Update a slideshow - all users can modify all slideshows."""
    current_user = get_current_user()
    assert current_user is not None  # Guaranteed by @api_auth_required

    slideshow = db.session.get(Slideshow, slideshow_id)
    if not slideshow or not slideshow.is_active:
        raise NotFoundError(
            "Slideshow not found", resource_type="slideshow", resource_id=slideshow_id
        )

    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    # Update fields if provided
    if "name" in data:
        name = data["name"].strip()
        if not name:
            raise ValidationError("Slideshow name cannot be empty", field="name")

        # Check for global duplicate names (exclude current slideshow)
        existing = Slideshow.query.filter(
            Slideshow.name == name,
            Slideshow.is_active,
            Slideshow.id != slideshow_id,
        ).first()
        if existing:
            raise ValidationError(
                "A slideshow with this name already exists", field="name"
            )

        slideshow.name = name

    if "description" in data:
        slideshow.description = data["description"]

    if "default_item_duration" in data:
        duration = data["default_item_duration"]
        if not isinstance(duration, int) or duration < 1:
            raise ValidationError(
                "Default item duration must be a positive integer",
                field="default_item_duration",
            )
        slideshow.default_item_duration = duration

    if "transition_type" in data:
        slideshow.transition_type = data["transition_type"]

    if "is_active" in data:
        slideshow.is_active = data["is_active"]

    if "is_default" in data:
        is_default = data["is_default"]
        if is_default:
            # Clear any existing default slideshow
            Slideshow.query.filter(
                Slideshow.is_default == True,  # noqa: E712
                Slideshow.id != slideshow_id,
            ).update({"is_default": False})
        slideshow.is_default = is_default

    try:
        slideshow.updated_by_id = current_user.id
        db.session.commit()

        # Broadcast SSE event for slideshow update
        broadcast_slideshow_update(
            slideshow,
            "updated",
            {"updated_by": current_user.username, "updated_fields": list(data.keys())},
        )

        current_app.logger.info(
            f"User {current_user.username} updated slideshow: {slideshow.name}"
        )
        return api_response(slideshow.to_dict(), "Slideshow updated successfully")

    except IntegrityError:
        db.session.rollback()
        raise ValidationError("A slideshow with this name already exists", field="name")


@api_v1_bp.route("/slideshows/<int:slideshow_id>", methods=["DELETE"])
@api_auth_required
def delete_slideshow(slideshow_id: int) -> Tuple[Response, int]:
    """Delete a slideshow (soft delete) - all users can delete all slideshows."""
    current_user = get_current_user()
    assert current_user is not None  # Guaranteed by @api_auth_required

    slideshow = db.session.get(Slideshow, slideshow_id)
    if not slideshow or not slideshow.is_active:
        raise NotFoundError(
            "Slideshow not found", resource_type="slideshow", resource_id=slideshow_id
        )

    # Check if slideshow is assigned to any displays
    assigned_displays = Display.query.filter_by(current_slideshow_id=slideshow_id).all()
    if assigned_displays:
        display_names = [d.name for d in assigned_displays]
        raise ValidationError(
            f"Cannot delete slideshow: it is assigned to displays: "
            f"{', '.join(display_names)}",
            details={"assigned_displays": display_names},
        )

    # Soft delete the slideshow and its items
    slideshow.is_active = False
    slideshow.updated_by_id = current_user.id

    for item in slideshow.items:
        item.is_active = False
        item.updated_by_id = current_user.id

    db.session.commit()

    current_app.logger.info(
        f"User {current_user.username} deleted slideshow: {slideshow.name}"
    )
    return api_response(None, "Slideshow deleted successfully")


@api_v1_bp.route("/slideshows/<int:slideshow_id>/set-default", methods=["POST"])
@api_auth_required
def set_default_slideshow(slideshow_id: int) -> Tuple[Response, int]:
    """Set a slideshow as the default slideshow."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        slideshow = db.session.get(Slideshow, slideshow_id)
        if not slideshow or not slideshow.is_active:
            return api_error("Slideshow not found", 404)

        # Clear any existing default
        Slideshow.query.filter_by(is_default=True).update({"is_default": False})

        # Set this slideshow as default
        slideshow.is_default = True
        slideshow.updated_by_id = current_user.id

        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} set slideshow {slideshow.name} as default"
        )
        return api_response(slideshow.to_dict(), "Default slideshow set successfully")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error setting default slideshow {slideshow_id}: {e}")
        return api_error("Failed to set default slideshow", 500)


# =============================================================================
# Slideshow Item API Endpoints
# =============================================================================


@api_v1_bp.route("/slideshows/<int:slideshow_id>/items", methods=["GET"])
@api_auth_required
def list_slideshow_items(slideshow_id: int) -> Tuple[Response, int]:
    """List all items in a slideshow - all users can view all slideshow items."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        slideshow = db.session.get(Slideshow, slideshow_id)
        if not slideshow:
            return api_error("Slideshow not found", 404)

        if not slideshow.is_active:
            return api_error("Slideshow not found", 404)

        items = [item.to_dict() for item in slideshow.items if item.is_active]

        return api_response(items, "Slideshow items retrieved successfully")

    except Exception as e:
        current_app.logger.error(
            f"Error listing items for slideshow {slideshow_id}: {e}"
        )
        return api_error("Failed to retrieve slideshow items", 500)


@api_v1_bp.route("/slideshows/<int:slideshow_id>/items", methods=["POST"])
@api_auth_required
def create_slideshow_item(slideshow_id: int) -> Tuple[Response, int]:
    """Create a new slideshow item - all users can create items in all slideshows."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        slideshow = db.session.get(Slideshow, slideshow_id)
        if not slideshow or not slideshow.is_active:
            return api_error("Slideshow not found", 404)

        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)

        content_type = data.get("content_type", "").strip()
        if not content_type:
            return api_error("Content type is required", 400)

        if content_type not in ["image", "video", "url", "text", "skedda"]:
            return api_error("Invalid content type", 400)

        # Validate scale_factor if provided (only meaningful for URL slides)
        scale_factor = data.get("scale_factor")
        if scale_factor is not None:
            if (
                not isinstance(scale_factor, int)
                or scale_factor < 10
                or scale_factor > 100
            ):
                return api_error(
                    "Scale factor must be an integer between 10 and 100", 400
                )

        # Validate video URL if content_type is video and URL is provided (no file)
        content_url = (
            data.get("content_url", "").strip() if data.get("content_url") else ""
        )
        content_file_path = (
            data.get("content_file_path", "").strip()
            if data.get("content_file_path")
            else ""
        )

        if content_type == "video" and content_url and not content_file_path:
            # Validate the video URL format and codec
            storage = get_storage_manager()
            is_valid, duration, codec_info, error_message = storage.validate_video_url(
                content_url
            )
            if not is_valid:
                return api_error(error_message, 400)

        # Handle skedda (iCal) content type
        ical_feed_id = None
        ical_refresh_minutes = None
        if content_type == "skedda":
            ical_url = data.get("ical_url", "").strip() if data.get("ical_url") else ""
            if not ical_url:
                return api_error("iCal URL is required for skedda content type", 400)

            # Validate URL format
            if not ical_url.startswith(("http://", "https://")):
                return api_error("iCal URL must be a valid HTTP/HTTPS URL", 400)

            # Get or create the feed
            feed = get_or_create_feed(ical_url)
            ical_feed_id = feed.id

            # Get refresh interval (optional, defaults to 15 minutes in service layer)
            ical_refresh_minutes = data.get("ical_refresh_minutes")
            if ical_refresh_minutes is not None:
                if (
                    not isinstance(ical_refresh_minutes, int)
                    or ical_refresh_minutes < 1
                    or ical_refresh_minutes > 1440
                ):
                    return api_error(
                        "Refresh interval must be between 1 and 1440 minutes", 400
                    )

            # Trigger initial fetch to validate URL works
            if not refresh_feed(feed):
                error_msg = feed.last_error or "Failed to fetch iCal data from URL"
                return api_error(f"iCal URL validation failed: {error_msg}", 400)

        # Get the next order index
        max_order = (
            db.session.query(db.func.max(SlideshowItem.order_index))
            .filter_by(slideshow_id=slideshow_id, is_active=True)
            .scalar()
            or 0
        )

        item = SlideshowItem(
            slideshow_id=slideshow_id,
            title=data.get("title", ""),
            content_type=content_type,
            content_url=data.get("content_url"),
            content_text=data.get("content_text"),
            content_file_path=data.get("content_file_path"),
            display_duration=data.get("display_duration"),
            order_index=max_order + 1,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
            is_active=data.get("is_active", True),
            scale_factor=scale_factor,
            ical_feed_id=ical_feed_id,
            ical_refresh_minutes=ical_refresh_minutes,
        )

        db.session.add(item)
        db.session.commit()

        # Broadcast slideshow update to displays showing this slideshow
        broadcast_slideshow_update(
            slideshow,
            "updated",
            {"updated_by": current_user.username, "item_created": item.id},
        )

        current_app.logger.info(
            f"User {current_user.username} created item in slideshow {slideshow.name}"
        )
        return api_response(item.to_dict(), "Slideshow item created successfully", 201)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error creating item for slideshow {slideshow_id}: {e}"
        )
        return api_error("Failed to create slideshow item", 500)


@api_v1_bp.route("/slideshow-items/<int:item_id>", methods=["PUT"])
@api_auth_required
def update_slideshow_item(item_id: int) -> Tuple[Response, int]:
    """Update a slideshow item - all users can update all items."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        item = db.session.get(SlideshowItem, item_id)
        if not item or not item.is_active:
            return api_error("Slideshow item not found", 404)

        slideshow = item.slideshow
        if not slideshow.is_active:
            return api_error("Slideshow item not found", 404)

        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)

        # Update fields if provided
        if "title" in data:
            item.title = data["title"]
        if "content_type" in data:
            item.content_type = data["content_type"]
        if "content_url" in data:
            item.content_url = data["content_url"]
        if "content_text" in data:
            item.content_text = data["content_text"]
        if "content_file_path" in data:
            item.content_file_path = data["content_file_path"]
        if "display_duration" in data:
            item.display_duration = data["display_duration"]
        if "is_active" in data:
            item.is_active = data["is_active"]
        if "scale_factor" in data:
            scale_factor = data["scale_factor"]
            if scale_factor is not None:
                if (
                    not isinstance(scale_factor, int)
                    or scale_factor < 10
                    or scale_factor > 100
                ):
                    return api_error(
                        "Scale factor must be an integer between 10 and 100", 400
                    )
            item.scale_factor = scale_factor

        # Validate video URL if updating to video type with URL (no file)
        # Determine effective values (new value if provided, otherwise existing)
        effective_content_type = data.get("content_type", item.content_type)
        effective_content_url = data.get("content_url", item.content_url) or ""
        effective_content_file_path = (
            data.get("content_file_path", item.content_file_path) or ""
        )

        # Strip whitespace for comparison
        if isinstance(effective_content_url, str):
            effective_content_url = effective_content_url.strip()
        if isinstance(effective_content_file_path, str):
            effective_content_file_path = effective_content_file_path.strip()

        # Only validate if:
        # 1. Content type is video
        # 2. URL is being set/changed (in the request data)
        # 3. No file path is set
        if (
            effective_content_type == "video"
            and "content_url" in data
            and effective_content_url
            and not effective_content_file_path
        ):
            storage = get_storage_manager()
            is_valid, duration, codec_info, error_message = storage.validate_video_url(
                effective_content_url
            )
            if not is_valid:
                return api_error(error_message, 400)

        # Handle skedda (iCal) content type updates
        if effective_content_type == "skedda":
            # Update ical_url if provided
            if "ical_url" in data:
                ical_url = (
                    data.get("ical_url", "").strip() if data.get("ical_url") else ""
                )
                if not ical_url:
                    return api_error(
                        "iCal URL is required for skedda content type", 400
                    )

                # Validate URL format
                if not ical_url.startswith(("http://", "https://")):
                    return api_error("iCal URL must be a valid HTTP/HTTPS URL", 400)

                # Check if URL is changing
                current_url = item.ical_feed.url if item.ical_feed else None
                if ical_url != current_url:
                    # Get or create the new feed
                    feed = get_or_create_feed(ical_url)
                    item.ical_feed_id = feed.id

                    # Trigger fetch to validate URL works
                    if not refresh_feed(feed):
                        error_msg = (
                            feed.last_error or "Failed to fetch iCal data from URL"
                        )
                        return api_error(
                            f"iCal URL validation failed: {error_msg}", 400
                        )

            # Update refresh interval if provided
            if "ical_refresh_minutes" in data:
                ical_refresh_minutes = data.get("ical_refresh_minutes")
                if ical_refresh_minutes is not None:
                    if (
                        not isinstance(ical_refresh_minutes, int)
                        or ical_refresh_minutes < 1
                        or ical_refresh_minutes > 1440
                    ):
                        return api_error(
                            "Refresh interval must be between 1 and 1440 minutes", 400
                        )
                item.ical_refresh_minutes = ical_refresh_minutes

            # Validate required feed exists if changing to skedda type
            if (
                "content_type" in data
                and item.content_type == "skedda"
                and not item.ical_feed_id
            ):
                return api_error("iCal URL is required for skedda content type", 400)

        item.updated_by_id = current_user.id
        db.session.commit()

        # Broadcast slideshow update to displays showing this slideshow
        broadcast_slideshow_update(
            slideshow,
            "updated",
            {"updated_by": current_user.username, "item_updated": item.id},
        )

        current_app.logger.info(
            f"User {current_user.username} updated item {item.title}"
        )
        return api_response(item.to_dict(), "Slideshow item updated successfully")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating slideshow item {item_id}: {e}")
        return api_error("Failed to update slideshow item", 500)


@api_v1_bp.route("/slideshow-items/<int:item_id>", methods=["DELETE"])
@api_auth_required
def delete_slideshow_item(item_id: int) -> Tuple[Response, int]:
    """Delete a slideshow item (soft delete) - all users can delete all items."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        item = db.session.get(SlideshowItem, item_id)
        if not item or not item.is_active:
            return api_error("Slideshow item not found", 404)

        slideshow = item.slideshow
        if not slideshow.is_active:
            return api_error("Slideshow item not found", 404)

        # Soft delete
        item.is_active = False
        item.updated_by_id = current_user.id
        db.session.commit()

        # Broadcast slideshow update to displays showing this slideshow
        broadcast_slideshow_update(
            slideshow,
            "updated",
            {"updated_by": current_user.username, "item_deleted": item.id},
        )

        current_app.logger.info(
            f"User {current_user.username} deleted item {item.title}"
        )
        return api_response(None, "Slideshow item deleted successfully")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting slideshow item {item_id}: {e}")
        return api_error("Failed to delete slideshow item", 500)


@api_v1_bp.route("/slideshow-items/<int:item_id>/reorder", methods=["POST"])
@api_auth_required
def reorder_slideshow_item(item_id: int) -> Tuple[Response, int]:
    """Reorder a slideshow item - all users can reorder all items."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        item = db.session.get(SlideshowItem, item_id)
        if not item or not item.is_active:
            return api_error("Slideshow item not found", 404)

        slideshow = item.slideshow
        if not slideshow.is_active:
            return api_error("Slideshow item not found", 404)

        data = request.get_json()
        if not data or "new_order" not in data:
            return api_error("New order position is required", 400)

        new_order = data["new_order"]
        if not isinstance(new_order, int) or new_order < 1:
            return api_error("Invalid order position", 400)

        # Reorder logic (simplified)
        old_order = item.order_index
        item.order_index = new_order

        # Update other items' order indices as needed
        if new_order > old_order:
            # Moving down: decrease order of items in between
            items_to_update = SlideshowItem.query.filter(
                SlideshowItem.slideshow_id == slideshow.id,
                SlideshowItem.order_index <= new_order,
                SlideshowItem.order_index > old_order,
                SlideshowItem.is_active,
                SlideshowItem.id != item_id,
            ).all()
            for reordered_item in items_to_update:
                reordered_item.order_index -= 1
                reordered_item.updated_by_id = current_user.id
        else:
            # Moving up: increase order of items in between
            items_to_update = SlideshowItem.query.filter(
                SlideshowItem.slideshow_id == slideshow.id,
                SlideshowItem.order_index >= new_order,
                SlideshowItem.order_index < old_order,
                SlideshowItem.is_active,
                SlideshowItem.id != item_id,
            ).all()
            for reordered_item in items_to_update:
                reordered_item.order_index += 1
                reordered_item.updated_by_id = current_user.id

        item.updated_by_id = current_user.id
        db.session.commit()

        # Broadcast slideshow update to displays showing this slideshow
        broadcast_slideshow_update(
            slideshow,
            "updated",
            {"updated_by": current_user.username, "item_reordered": item.id},
        )

        current_app.logger.info(
            f"User {current_user.username} reordered item {item.title}"
        )
        return api_response(item.to_dict(), "Slideshow item reordered successfully")

    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error reordering slideshow item {item_id}: {e}")
        return api_error("Failed to reorder slideshow item", 500)


@api_v1_bp.route("/slideshow-items/<int:item_id>/skedda-data", methods=["GET"])
@api_auth_required
def get_slideshow_item_skedda_data(item_id: int) -> Tuple[Response, int]:
    """Get formatted Skedda calendar data for a slideshow item.

    Query parameters:
        date (optional): Date to display in YYYY-MM-DD format, defaults to today
    """
    from datetime import datetime

    from ..ical_service import get_skedda_calendar_data

    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        item = db.session.get(SlideshowItem, item_id)
        if not item or not item.is_active:
            return api_error("Slideshow item not found", 404)

        if item.content_type != "skedda":
            return api_error("This item is not a Skedda calendar", 400)

        # Parse optional date parameter
        target_date = None
        date_str = request.args.get("date")
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return api_error("Invalid date format. Use YYYY-MM-DD", 400)

        # Get formatted calendar data
        data = get_skedda_calendar_data(item, target_date=target_date)

        return api_response(data, "Skedda calendar data retrieved successfully")

    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        current_app.logger.error(f"Error getting skedda data for item {item_id}: {e}")
        return api_error("Failed to retrieve calendar data", 500)


@api_v1_bp.route("/ical-feeds/refresh", methods=["POST"])
@api_auth_required
def refresh_all_ical_feeds() -> Tuple[Response, int]:
    """Refresh all iCal feeds in the database.

    This endpoint can be called by external schedulers (cron, systemd timer, etc.)
    to proactively refresh all calendar data.

    Returns:
        JSON with refresh results:
        {
            "refreshed": 3,
            "errors": [
                {"feed_id": 2, "url": "...", "error": "Connection timeout"}
            ]
        }
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        result = refresh_all_feeds()

        if result["errors"]:
            current_app.logger.warning(
                f"iCal feed refresh completed with {len(result['errors'])} errors"
            )
        else:
            current_app.logger.info(
                f"iCal feed refresh completed: {result['refreshed']} feeds refreshed"
            )

        return api_response(result, "iCal feeds refresh completed")

    except Exception as e:
        current_app.logger.error(f"Error refreshing iCal feeds: {e}")
        return api_error("Failed to refresh iCal feeds", 500)


# =============================================================================
# Display Management API Endpoints
# =============================================================================


@api_v1_bp.route("/displays", methods=["GET"])
@api_auth_required
def list_displays() -> Tuple[Response, int]:
    """List all displays."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        displays = Display.query.all()
        display_data = [display.to_dict() for display in displays]

        return api_response(display_data, "Displays retrieved successfully")

    except Exception as e:
        current_app.logger.error(f"Error listing displays: {e}")
        return api_error("Failed to retrieve displays", 500)


@api_v1_bp.route("/displays/status", methods=["GET"])
@api_auth_required
def list_displays_status() -> Tuple[Response, int]:
    """Get status of all displays.

    Returns enhanced display status information including connection quality,
    SSE connection state, and missed heartbeats - used by the monitoring page.
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        displays = Display.query.all()
        display_status_data = [display.to_status_dict() for display in displays]

        return api_response(
            display_status_data, "Display status retrieved successfully"
        )

    except Exception as e:
        current_app.logger.error(f"Error getting display status: {e}")
        return api_error("Failed to retrieve display status", 500)


@api_v1_bp.route("/displays/<int:display_id>/status", methods=["GET"])
@api_auth_required
def get_display_status(display_id: int) -> Tuple[Response, int]:
    """Get status of a specific display.

    Args:
        display_id: The ID of the display to get status for

    Returns enhanced display status information including connection quality,
    SSE connection state, and missed heartbeats.
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        display = db.session.get(Display, display_id)
        if not display:
            return api_error(f"Display with ID {display_id} not found", 404)

        return api_response(
            display.to_status_dict(),
            f"Status for display '{display.name}' retrieved successfully",
        )

    except Exception as e:
        current_app.logger.error(f"Error getting display status: {e}")
        return api_error("Failed to retrieve display status", 500)


@api_v1_bp.route("/displays", methods=["POST"])
@api_auth_required
def create_display() -> Tuple[Response, int]:
    """Create a new display."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)

        # Validate required fields
        name = data.get("name")
        if not name:
            return api_error("Display name is required", 400)

        # Check if display with this name already exists
        existing_display = Display.query.filter_by(name=name).first()
        if existing_display:
            return api_error(f"Display with name '{name}' already exists", 409)

        # Validate show_info_overlay if provided
        show_info_overlay = data.get("show_info_overlay", False)
        if not isinstance(show_info_overlay, bool):
            return api_error("show_info_overlay must be a boolean", 400)

        # Create new display
        display = Display(
            name=name,
            description=data.get("description"),
            location=data.get("location"),
            resolution_width=data.get("resolution_width"),
            resolution_height=data.get("resolution_height"),
            rotation=data.get("rotation", 0),
            show_info_overlay=show_info_overlay,
            owner_id=current_user.id,
            created_by_id=current_user.id,
            current_slideshow_id=data.get("current_slideshow_id"),
        )

        # Validate data through model validators
        try:
            db.session.add(display)
            db.session.flush()  # Trigger validation without committing
        except ValueError as ve:
            return api_error(f"Validation error: {str(ve)}", 400)

        db.session.commit()

        current_app.logger.info(
            "Display created successfully",
            extra={
                "display_id": display.id,
                "display_name": display.name,
                "created_by": current_user.username,
                "action": "display_created",
            },
        )

        return api_response(display.to_dict(), "Display created successfully", 201)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating display: {e}")
        return api_error("Failed to create display", 500)


@api_v1_bp.route("/displays/<int:display_id>", methods=["GET"])
@api_auth_required
def get_display(display_id: int) -> Tuple[Response, int]:
    """Get display information."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        display = db.session.get(Display, display_id)
        if not display:
            return api_error("Display not found", 404)

        return api_response(display.to_dict(), "Display retrieved successfully")

    except Exception as e:
        current_app.logger.error(f"Error retrieving display {display_id}: {e}")
        return api_error("Failed to retrieve display", 500)


@api_v1_bp.route("/displays/<int:display_id>", methods=["PUT"])
@api_auth_required
def update_display(display_id: int) -> Tuple[Response, int]:
    """Update display configuration including slideshow assignment."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        display = db.session.get(Display, display_id)
        if not display:
            return api_error("Display not found", 404)

        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)

        # Store previous slideshow ID for history tracking
        previous_slideshow_id = display.current_slideshow_id

        # Track which settings fields are being updated (for SSE broadcast)
        configuration_fields_updated = []

        # Update display fields
        if "name" in data:
            display.name = data["name"]
            configuration_fields_updated.append("name")
        if "location" in data:
            display.location = data["location"]
            configuration_fields_updated.append("location")
        if "description" in data:
            display.description = data["description"]
            configuration_fields_updated.append("description")
        if "show_info_overlay" in data:
            show_info_overlay_value = data["show_info_overlay"]
            if not isinstance(show_info_overlay_value, bool):
                return api_error("show_info_overlay must be a boolean", 400)
            display.show_info_overlay = show_info_overlay_value
            configuration_fields_updated.append("show_info_overlay")

        # Handle slideshow assignment
        slideshow_assignment_changed = False
        if "current_slideshow_id" in data:
            new_slideshow_id = data["current_slideshow_id"]

            # Validate slideshow if provided
            if new_slideshow_id is not None:
                slideshow = db.session.get(Slideshow, new_slideshow_id)
                if not slideshow or not slideshow.is_active:
                    return api_error("Slideshow not found or inactive", 404)

            # Check if assignment actually changed
            if previous_slideshow_id != new_slideshow_id:
                display.current_slideshow_id = new_slideshow_id
                slideshow_assignment_changed = True

        display.updated_by_id = current_user.id

        # Create assignment history record if slideshow assignment changed
        if slideshow_assignment_changed:
            history_record = AssignmentHistory.create_assignment_record(
                display_id=display.id,
                previous_slideshow_id=previous_slideshow_id,
                new_slideshow_id=display.current_slideshow_id,
                created_by_id=current_user.id,
                reason="Updated via display configuration",
            )
            if history_record:
                db.session.add(history_record)

        db.session.commit()

        # Broadcast SSE events for display changes
        if slideshow_assignment_changed:
            action = (
                f"assigned slideshow {display.current_slideshow_id}"
                if display.current_slideshow_id
                else "unassigned slideshow"
            )
            current_app.logger.info(
                f"User {current_user.username} {action} for display {display_id}"
            )
            # Broadcast assignment_changed event to admin and display connections
            broadcast_display_update(
                display,
                "assignment_changed",
                {
                    "previous_slideshow_id": previous_slideshow_id,
                    "new_slideshow_id": display.current_slideshow_id,
                    "assigned_by": current_user.username,
                    "reason": "Updated via display configuration",
                },
            )
        elif configuration_fields_updated:
            # Broadcast configuration_changed event when settings changed (but not assignment)
            broadcast_display_update(
                display,
                "configuration_changed",
                {
                    "updated_fields": configuration_fields_updated,
                    "updated_by": current_user.username,
                },
            )

        return api_response(display.to_dict(), "Display updated successfully")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating display {display_id}: {e}")
        return api_error("Failed to update display", 500)


@api_v1_bp.route("/displays/<string:display_name>/assign-slideshow", methods=["POST"])
@api_auth_required
def assign_slideshow_to_display(display_name: str) -> Tuple[Response, int]:
    """Assign a slideshow to a display."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        display = Display.query.filter_by(name=display_name).first()
        if not display:
            return api_error("Display not found", 404)

        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)

        # Store previous slideshow ID for history tracking
        previous_slideshow_id = display.current_slideshow_id
        new_slideshow_id = data.get("slideshow_id")

        # Validate slideshow if provided
        if new_slideshow_id is not None:
            slideshow = Slideshow.query.get(new_slideshow_id)
            if not slideshow or not slideshow.is_active:
                return api_error("Slideshow not found or inactive", 404)

        # Update display assignment
        display.current_slideshow_id = new_slideshow_id
        display.updated_by_id = current_user.id

        # Create assignment history record
        history_record = AssignmentHistory.create_assignment_record(
            display_id=display.id,
            previous_slideshow_id=previous_slideshow_id,
            new_slideshow_id=new_slideshow_id,
            created_by_id=current_user.id,
            reason=data.get("reason", "Direct slideshow assignment"),
        )

        if history_record:
            db.session.add(history_record)

        db.session.commit()

        # Broadcast SSE event for display assignment change
        broadcast_display_update(
            display,
            "assignment_changed",
            {
                "previous_slideshow_id": previous_slideshow_id,
                "new_slideshow_id": new_slideshow_id,
                "assigned_by": current_user.username,
                "reason": data.get("reason", "Direct slideshow assignment"),
            },
        )

        action = (
            f"assigned slideshow {new_slideshow_id}"
            if new_slideshow_id
            else "unassigned slideshow"
        )
        current_app.logger.info(
            f"User {current_user.username} {action} for display {display_name}"
        )
        return api_response(
            display.to_dict(), "Slideshow assignment updated successfully"
        )

    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error assigning slideshow to display {display_name}: {e}"
        )
        return api_error("Failed to assign slideshow to display", 500)


@api_v1_bp.route("/displays/<int:display_id>", methods=["DELETE"])
@api_auth_required
def delete_display(display_id: int) -> Tuple[Response, int]:
    """Delete a display."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        display = db.session.get(Display, display_id)
        if not display:
            return api_error("Display not found", 404)

        display_name = display.name
        db.session.delete(display)
        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} deleted display {display_name}"
        )
        return api_response(None, "Display deleted successfully")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting display {display_id}: {e}")
        return api_error("Failed to delete display", 500)


# =============================================================================
# Display Lifecycle Management Endpoints
# =============================================================================


@api_v1_bp.route("/displays/<int:display_id>/archive", methods=["POST"])
@api_auth_required
def archive_display(display_id: int) -> Tuple[Response, int]:
    """Archive a display."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        display = db.session.get(Display, display_id)
        if not display:
            return api_error("Display not found", 404)

        if display.is_archived:
            return api_error("Display is already archived", 400)

        display.archive(current_user)
        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} archived display {display.name}"
        )
        return api_response(display.to_dict(), "Display archived successfully")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error archiving display {display_id}: {e}")
        return api_error("Failed to archive display", 500)


@api_v1_bp.route("/displays/<int:display_id>/restore", methods=["POST"])
@api_auth_required
def restore_display(display_id: int) -> Tuple[Response, int]:
    """Restore a display from archive."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        display = db.session.get(Display, display_id)
        if not display:
            return api_error("Display not found", 404)

        if not display.is_archived:
            return api_error("Display is not archived", 400)

        display.restore()
        display.updated_by_id = current_user.id
        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} restored display {display.name}"
        )
        return api_response(display.to_dict(), "Display restored successfully")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error restoring display {display_id}: {e}")
        return api_error("Failed to restore display", 500)


@api_v1_bp.route("/displays/<int:display_id>/reload", methods=["POST"])
@api_auth_required
def reload_display(display_id: int) -> Tuple[Response, int]:
    """Send a reload command to a display via SSE.

    This endpoint triggers an SSE event that instructs the target display
    to reload its current slideshow. Useful when displays miss SSE event
    notifications due to network issues.
    """
    try:
        from datetime import datetime, timezone

        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        display = db.session.get(Display, display_id)
        if not display:
            return api_error("Display not found", 404)

        # Broadcast reload event to the display
        event_count = broadcast_display_update(
            display,
            "reload_requested",
            {
                "display_id": display.id,
                "display_name": display.name,
                "requested_by": current_user.username,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        current_app.logger.info(
            f"User {current_user.username} requested reload for display "
            f"{display.name} (ID: {display.id}), sent to {event_count} connections"
        )

        return api_response(
            {"display_id": display.id, "connections_notified": event_count},
            f"Reload command sent to display '{display.name}'",
        )

    except Exception as e:
        current_app.logger.error(f"Error sending reload to display {display_id}: {e}")
        return api_error("Failed to send reload command", 500)


@api_v1_bp.route("/displays/archived", methods=["GET"])
@api_auth_required
def list_archived_displays() -> Tuple[Response, int]:
    """List all archived displays."""
    try:
        displays = Display.query.filter_by(is_archived=True).all()
        display_data = [display.to_dict() for display in displays]

        return api_response(display_data, "Archived displays retrieved successfully")

    except Exception as e:
        current_app.logger.error(f"Error listing archived displays: {e}")
        return api_error("Failed to retrieve archived displays", 500)


# =============================================================================
# Assignment History API Endpoints
# =============================================================================


@api_v1_bp.route("/assignment-history", methods=["GET"])
@api_auth_required
def list_assignment_history() -> Tuple[Response, int]:
    """List assignment history records with optional filtering.

    Query parameters:
        limit: Maximum number of records to return (default: 50, max: 200)
        display_id: Filter by specific display ID
        action: Filter by action type (assign, unassign, change)
        user_id: Filter by user who made the change
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get("limit", 50)), 200)
        display_id = request.args.get("display_id", type=int)
        action = request.args.get("action")
        user_id = request.args.get("user_id", type=int)

        # Build query
        query = AssignmentHistory.query

        # Apply filters
        if display_id:
            query = query.filter(AssignmentHistory.display_id == display_id)
        if action and action in ["assign", "unassign", "change"]:
            query = query.filter(AssignmentHistory.action == action)
        if user_id:
            query = query.filter(AssignmentHistory.created_by_id == user_id)

        # Order by most recent first and apply limit
        records = query.order_by(AssignmentHistory.created_at.desc()).limit(limit).all()

        # Convert to dict for JSON response
        history_data = [record.to_dict() for record in records]

        return api_response(history_data, "Assignment history retrieved successfully")

    except ValueError:
        raise ValidationError("Invalid parameter value")
    except Exception as e:
        current_app.logger.error(f"Error listing assignment history: {e}")
        return api_error("Failed to retrieve assignment history", 500)


# =============================================================================
# Display Configuration Template Endpoints
# =============================================================================


@api_v1_bp.route("/display-templates", methods=["GET"])
@api_auth_required
def list_display_templates() -> Tuple[Response, int]:
    """List all display configuration templates."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        templates = DisplayConfigurationTemplate.query.filter_by(
            owner_id=current_user.id, is_active=True
        ).all()
        template_data = [template.to_dict() for template in templates]

        return api_response(template_data, "Templates retrieved successfully")

    except Exception as e:
        current_app.logger.error(f"Error listing display templates: {e}")
        return api_error("Failed to retrieve display templates", 500)


@api_v1_bp.route("/display-templates", methods=["POST"])
@api_auth_required
def create_display_template() -> Tuple[Response, int]:
    """Create a new display configuration template."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)

        # Validate required fields
        if not data.get("name"):
            return api_error("Template name is required", 400)

        # Check for duplicate template name
        existing_template = DisplayConfigurationTemplate.query.filter_by(
            name=data["name"], owner_id=current_user.id
        ).first()
        if existing_template:
            return api_error("Template with this name already exists", 400)

        # Create new template
        template = DisplayConfigurationTemplate(
            name=data["name"],
            description=data.get("description"),
            template_resolution_width=data.get("template_resolution_width"),
            template_resolution_height=data.get("template_resolution_height"),
            template_rotation=data.get("template_rotation", 0),
            template_heartbeat_interval=data.get("template_heartbeat_interval", 60),
            template_location=data.get("template_location"),
            is_default=data.get("is_default", False),
            owner_id=current_user.id,
            created_by_id=current_user.id,
        )

        db.session.add(template)
        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} created display template {template.name}"
        )
        return api_response(
            template.to_dict(), "Display template created successfully", 201
        )

    except ValueError as e:
        db.session.rollback()
        return api_error(str(e), 400)
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"Integrity error creating template: {e}")
        return api_error("Template with this name already exists", 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating display template: {e}")
        return api_error("Failed to create display template", 500)


@api_v1_bp.route("/display-templates/<int:template_id>", methods=["GET"])
@api_auth_required
def get_display_template(template_id: int) -> Tuple[Response, int]:
    """Get a specific display configuration template."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        template = db.session.get(DisplayConfigurationTemplate, template_id)
        if not template:
            return api_error("Template not found", 404)

        if template.owner_id != current_user.id:
            return api_error("Access denied", 403)

        return api_response(template.to_dict(), "Template retrieved successfully")

    except Exception as e:
        current_app.logger.error(f"Error getting display template {template_id}: {e}")
        return api_error("Failed to retrieve display template", 500)


@api_v1_bp.route("/display-templates/<int:template_id>", methods=["PUT"])
@api_auth_required
def update_display_template(template_id: int) -> Tuple[Response, int]:
    """Update a display configuration template."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        template = db.session.get(DisplayConfigurationTemplate, template_id)
        if not template:
            return api_error("Template not found", 404)

        if template.owner_id != current_user.id:
            return api_error("Access denied", 403)

        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)

        # Update template fields
        if "name" in data:
            # Check for duplicate name (excluding current template)
            existing_template = (
                DisplayConfigurationTemplate.query.filter_by(
                    name=data["name"], owner_id=current_user.id
                )
                .filter(DisplayConfigurationTemplate.id != template_id)
                .first()
            )
            if existing_template:
                return api_error("Template with this name already exists", 400)
            template.name = data["name"]

        if "description" in data:
            template.description = data["description"]
        if "template_resolution_width" in data:
            template.template_resolution_width = data["template_resolution_width"]
        if "template_resolution_height" in data:
            template.template_resolution_height = data["template_resolution_height"]
        if "template_rotation" in data:
            template.template_rotation = data["template_rotation"]
        if "template_heartbeat_interval" in data:
            template.template_heartbeat_interval = data["template_heartbeat_interval"]
        if "template_location" in data:
            template.template_location = data["template_location"]
        if "is_default" in data:
            template.is_default = data["is_default"]

        template.updated_by_id = current_user.id
        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} updated display template {template.name}"
        )
        return api_response(template.to_dict(), "Template updated successfully")

    except ValueError as e:
        db.session.rollback()
        return api_error(str(e), 400)
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(f"Integrity error updating template: {e}")
        return api_error("Template with this name already exists", 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating display template {template_id}: {e}")
        return api_error("Failed to update display template", 500)


@api_v1_bp.route("/display-templates/<int:template_id>", methods=["DELETE"])
@api_auth_required
def delete_display_template(template_id: int) -> Tuple[Response, int]:
    """Delete a display configuration template."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        template = db.session.get(DisplayConfigurationTemplate, template_id)
        if not template:
            return api_error("Template not found", 404)

        if template.owner_id != current_user.id:
            return api_error("Access denied", 403)

        template_name = template.name
        db.session.delete(template)
        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} deleted display template {template_name}"
        )
        return api_response(None, "Template deleted successfully")

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting display template {template_id}: {e}")
        return api_error("Failed to delete display template", 500)


@api_v1_bp.route(
    "/displays/<int:display_id>/apply-template/<int:template_id>", methods=["POST"]
)
@api_auth_required
def apply_template_to_display(
    display_id: int, template_id: int
) -> Tuple[Response, int]:
    """Apply a configuration template to a display."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        display = db.session.get(Display, display_id)
        if not display:
            return api_error("Display not found", 404)

        template = db.session.get(DisplayConfigurationTemplate, template_id)
        if not template:
            return api_error("Template not found", 404)

        if template.owner_id != current_user.id:
            return api_error("Access denied", 403)

        if display.is_archived:
            return api_error("Cannot apply template to archived display", 400)

        # Apply template configuration
        config = template.to_configuration_dict()
        display.apply_configuration(config, current_user)
        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} applied template {template.name} to display {display.name}"
        )
        return api_response(display.to_dict(), "Template applied successfully")

    except ValueError as e:
        db.session.rollback()
        return api_error(str(e), 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error applying template {template_id} to display {display_id}: {e}"
        )
        return api_error("Failed to apply template", 500)


@api_v1_bp.route("/displays/bulk-apply-template", methods=["POST"])
@api_auth_required
def bulk_apply_template() -> Tuple[Response, int]:
    """Apply a configuration template to multiple displays."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)

        display_ids = data.get("display_ids", [])
        template_id = data.get("template_id")

        if not display_ids:
            return api_error("No display IDs provided", 400)
        if not template_id:
            return api_error("Template ID is required", 400)

        template = db.session.get(DisplayConfigurationTemplate, template_id)
        if not template:
            return api_error("Template not found", 404)

        if template.owner_id != current_user.id:
            return api_error("Access denied", 403)

        # Apply template to all displays
        config = template.to_configuration_dict()
        applied_displays = []
        failed_displays = []

        for display_id in display_ids:
            try:
                display = db.session.get(Display, display_id)
                if not display:
                    failed_displays.append(
                        {"id": display_id, "error": "Display not found"}
                    )
                    continue

                if display.is_archived:
                    failed_displays.append(
                        {"id": display_id, "error": "Display is archived"}
                    )
                    continue

                display.apply_configuration(config, current_user)
                applied_displays.append(display.to_dict())

            except Exception as e:
                failed_displays.append({"id": display_id, "error": str(e)})

        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} bulk applied template {template.name} to {len(applied_displays)} displays"
        )

        result = {
            "applied_displays": applied_displays,
            "failed_displays": failed_displays,
            "total_applied": len(applied_displays),
            "total_failed": len(failed_displays),
        }

        return api_response(
            result, f"Template applied to {len(applied_displays)} displays"
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error bulk applying template: {e}")
        return api_error("Failed to bulk apply template", 500)


# =============================================================================
# API Status and Health Endpoints
# =============================================================================


@api_v1_bp.route("/status", methods=["GET"])
def api_status() -> Tuple[Response, int]:
    """API status endpoint."""
    from datetime import datetime, timezone

    return api_response(
        {
            "status": "healthy",
            "api_version": "v1",  # Test expects "api_version" not "version"
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "API is operational",
    )


# =============================================================================
# Authentication API Endpoints
# =============================================================================


@api_v1_bp.route("/auth/login", methods=["POST"])
def api_login() -> Tuple[Response, int]:
    """API login endpoint that accepts JSON data."""
    data = request.get_json()

    if not data:
        return api_error("No JSON data provided", 400)

    username = data.get("username", "").strip()
    password = data.get("password", "")

    # Basic validation
    if not username:
        return api_error("Username is required", 400)

    if not password:
        return api_error("Password is required", 400)

    # Permissive authentication logic (same as web interface)
    try:
        from datetime import datetime, timezone

        # Check if user already exists
        user = User.query.filter_by(username=username).first()

        if user:
            # For existing users, accept any password but update their password hash
            # In permissive mode, we accept any password but store the latest one
            if not user.check_password(password):
                user.set_password(password)
                user.updated_at = datetime.now(timezone.utc)
                db.session.commit()

                current_app.logger.info(
                    "API user password updated during login",
                    extra={
                        "user_id": user.id,
                        "username": user.username,
                        "action": "api_password_update",
                    },
                )

            # Log successful login
            user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()

            # Set up session
            session["user_id"] = user.id
            session["username"] = user.username
            session["is_admin"] = user.is_admin

            current_app.logger.info(
                "API user login successful",
                extra={
                    "user_id": user.id,
                    "username": user.username,
                    "action": "api_login",
                    "ip_address": request.remote_addr,
                },
            )

            return api_response(user.to_dict(), "Login successful")
        else:
            # Create new user (permissive authentication)
            new_user = User(
                username=username,
                email=None,  # Email not required for permissive auth
                is_admin=True,  # All users get admin privileges in permissive mode
            )
            new_user.set_password(password)

            db.session.add(new_user)
            db.session.commit()

            # Log successful login
            new_user.last_login_at = datetime.now(timezone.utc)
            db.session.commit()

            # Set up session
            session["user_id"] = new_user.id
            session["username"] = new_user.username
            session["is_admin"] = new_user.is_admin

            current_app.logger.info(
                "API new user created and logged in",
                extra={
                    "user_id": new_user.id,
                    "username": new_user.username,
                    "action": "api_user_creation",
                    "ip_address": request.remote_addr,
                },
            )

            return api_response(new_user.to_dict(), "User created and login successful")

    except ValueError as e:
        # Handle validation errors (e.g., username too long, invalid email)
        db.session.rollback()
        current_app.logger.warning(
            "API authentication failed due to validation error",
            extra={
                "username": username,
                "action": "api_validation_error",
                "error": str(e),
            },
        )
        return api_error(str(e), 400)

    except IntegrityError:
        # Handle race condition where user was created between check and insert
        db.session.rollback()
        current_app.logger.warning(
            "User creation failed due to integrity error, retrying",
            extra={
                "username": username,
                "action": "api_user_creation_retry",
            },
        )
        # Try to get the user that was created by another request
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            # Set up session
            session["user_id"] = user.id
            session["username"] = user.username
            session["is_admin"] = user.is_admin

            return api_response(user.to_dict(), "Login successful")

        # If we still can't login after IntegrityError, return an error
        return api_error("Login failed. Please try again.", 500)

    except Exception as e:
        db.session.rollback()
        error_str = str(e)

        # Detect database initialization issues
        if "no such table" in error_str.lower():
            current_app.logger.error(
                "Login failed: Database not initialized",
                extra={
                    "username": username,
                    "action": "api_database_not_initialized",
                    "error": error_str,
                },
            )
            return api_error(
                "Database not initialized. Please run 'flask cli init-db' to set up the database.",
                503,
                error_code="DATABASE_NOT_INITIALIZED",
            )

        current_app.logger.error(
            "Unexpected error during API authentication",
            extra={
                "username": username,
                "action": "api_authentication_error",
                "error": error_str,
            },
        )
        return api_error("Login failed. Please try again.", 500)


@api_v1_bp.route("/auth/user", methods=["GET"])
@api_auth_required
def get_current_user_info() -> Tuple[Response, int]:
    """Get current authenticated user information."""
    user = get_current_user()
    if not user:
        return api_error("User not found", 404)

    return api_response(user.to_dict(), "User information retrieved successfully")


@api_v1_bp.route("/auth/logout", methods=["POST"])
@api_auth_required
def api_logout() -> Tuple[Response, int]:
    """Logout current user (clears session)."""

    session.clear()
    return api_response(message="Successfully logged out")


# =============================================================================
# File Upload API Endpoints
# =============================================================================


@api_v1_bp.route("/uploads/image", methods=["POST"])
@api_auth_required
def upload_image() -> Tuple[Response, int]:
    """Upload an image file."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        # Check if file is present
        if "file" not in request.files:
            return api_error("No file provided", 400)

        file = request.files["file"]
        if file.filename == "":
            return api_error("No file provided", 400)

        # Get slideshow_id
        slideshow_id_str = request.form.get("slideshow_id")
        if not slideshow_id_str:
            return api_error("slideshow_id is required", 400)

        # Validate slideshow_id
        try:
            slideshow_id_int = int(slideshow_id_str)
        except ValueError:
            return api_error("Invalid slideshow_id", 400)

        # Check if slideshow exists
        slideshow = db.session.get(Slideshow, slideshow_id_int)
        if not slideshow or not slideshow.is_active:
            return api_error("Slideshow not found", 404)

        # Get storage manager and upload file
        storage = get_storage_manager()

        # Validate file
        is_valid, error_message = storage.validate_file(file, "image")
        if not is_valid:
            return api_error(error_message, 400)

        # Save file
        success, message, file_info = storage.save_file(
            file, "image", current_user.id, slideshow_id_int
        )

        if not success or file_info is None:
            return api_error(message, 400)

        # Add URL to response
        file_info["url"] = storage.get_file_url(file_info["file_path"])

        current_app.logger.info(
            f"User {current_user.username} uploaded image {file_info['original_filename']} "
            f"to slideshow {slideshow.name}"
        )

        return api_response(file_info, "Image uploaded successfully", 201)

    except Exception as e:
        current_app.logger.error(f"Error uploading image: {e}")
        return api_error("Failed to upload image", 500)


@api_v1_bp.route("/uploads/video", methods=["POST"])
@api_auth_required
def upload_video() -> Tuple[Response, int]:
    """Upload a video file."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        # Check if file is present
        if "file" not in request.files:
            return api_error("No file provided", 400)

        file = request.files["file"]
        if file.filename == "":
            return api_error("No file provided", 400)

        # Get slideshow_id
        slideshow_id_str = request.form.get("slideshow_id")
        if not slideshow_id_str:
            return api_error("slideshow_id is required", 400)

        # Validate slideshow_id
        try:
            slideshow_id_int = int(slideshow_id_str)
        except ValueError:
            return api_error("Invalid slideshow_id", 400)

        # Check if slideshow exists
        slideshow = db.session.get(Slideshow, slideshow_id_int)
        if not slideshow or not slideshow.is_active:
            return api_error("Slideshow not found", 404)

        # Get storage manager and upload file
        storage = get_storage_manager()

        # Validate file
        is_valid, error_message = storage.validate_file(file, "video")
        if not is_valid:
            return api_error(error_message, 400)

        # Save file
        success, message, file_info = storage.save_file(
            file, "video", current_user.id, slideshow_id_int
        )

        if not success or file_info is None:
            return api_error(message, 400)

        # Add URL to response
        file_info["url"] = storage.get_file_url(file_info["file_path"])

        current_app.logger.info(
            f"User {current_user.username} uploaded video {file_info['original_filename']} "
            f"to slideshow {slideshow.name}"
        )

        return api_response(file_info, "Video uploaded successfully", 201)

    except Exception as e:
        current_app.logger.error(f"Error uploading video: {e}")
        return api_error("Failed to upload video", 500)


@api_v1_bp.route("/validate/video-url", methods=["POST"])
@api_auth_required
def validate_video_url() -> Tuple[Response, int]:
    """Validate a video URL for browser compatibility and extract metadata.

    This endpoint probes a remote video URL using ffprobe to:
    - Verify the URL is accessible and contains a video
    - Check that the video codec is browser-compatible
    - Extract the video duration

    Request body:
        {
            "url": "https://example.com/video.mp4"
        }

    Response (success):
        {
            "success": true,
            "data": {
                "valid": true,
                "duration_seconds": 120,
                "codec_info": {
                    "video_codec": "h264",
                    "audio_codec": "aac",
                    "container_format": "mov,mp4,m4a,3gp,3g2,mj2"
                }
            },
            "message": "Video URL is valid"
        }

    Response (invalid video):
        {
            "success": false,
            "error": "Video codec 'mpeg2video' is not supported..."
        }
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)

        url = data.get("url", "").strip()
        if not url:
            return api_error("URL is required", 400)

        # Basic URL format validation
        if not url.startswith("http://") and not url.startswith("https://"):
            return api_error("URL must start with http:// or https://", 400)

        # Get storage manager and validate the URL
        storage = get_storage_manager()
        is_valid, duration, codec_info, error_message = storage.validate_video_url(url)

        if not is_valid:
            return api_error(error_message, 400)

        # Build response data
        response_data = {
            "valid": True,
            "duration_seconds": round(duration) if duration is not None else None,
            "duration": duration,  # Exact duration as float
            "codec_info": codec_info,
        }

        current_app.logger.info(
            f"User {current_user.username} validated video URL: {url}"
        )

        return api_response(response_data, "Video URL is valid", 200)

    except Exception as e:
        current_app.logger.error(f"Error validating video URL: {e}")
        return api_error("Failed to validate video URL", 500)


@api_v1_bp.route("/uploads/stats", methods=["GET"])
@api_auth_required
def get_upload_stats() -> Tuple[Response, int]:
    """Get upload statistics."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        # Get storage manager and stats
        storage = get_storage_manager()
        stats = storage.get_storage_stats()

        # Add formatted sizes
        def format_bytes(size: float) -> str:
            for unit in ["B", "KB", "MB", "GB"]:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"

        stats["total_size_formatted"] = format_bytes(stats["total_size"])
        stats["image_size_formatted"] = format_bytes(stats["image_size"])
        stats["video_size_formatted"] = format_bytes(stats["video_size"])

        return api_response(stats, "Upload statistics retrieved successfully")

    except Exception as e:
        current_app.logger.error(f"Error getting upload stats: {e}")
        return api_error("Failed to get upload statistics", 500)


@api_v1_bp.route("/uploads/<int:file_id>", methods=["GET"])
@api_auth_required
def get_file_info(file_id: int) -> Tuple[Response, int]:
    """Get file information (placeholder - not yet implemented)."""
    return api_error("File info endpoint not yet implemented", 501)


@api_v1_bp.route("/uploads/<int:file_id>", methods=["DELETE"])
@api_auth_required
def delete_file(file_id: int) -> Tuple[Response, int]:
    """Delete uploaded file (placeholder - not yet implemented)."""
    return api_error("File deletion endpoint not yet implemented", 501)


# =============================================================================
# Server-Sent Events (SSE) Endpoints
# =============================================================================


@api_v1_bp.route("/events/admin", methods=["GET"])
def admin_events_stream() -> Response | Tuple[Response, int]:
    """Server-Sent Events stream for admin interface."""
    try:
        # Require authentication for admin events
        user_id = require_sse_auth()

        # Create SSE connection for admin
        connection = sse_manager.create_connection(
            user_id=user_id, connection_type="admin"
        )

        current_app.logger.info(f"Admin SSE connection established for user {user_id}")

        return create_sse_response(connection)

    except Unauthorized as e:
        current_app.logger.warning(f"Unauthorized SSE connection attempt: {e}")
        return api_error("Authentication required", 401)
    except Exception as e:
        current_app.logger.error(f"Error creating admin SSE connection: {e}")
        return api_error("Failed to establish SSE connection", 500)


@api_v1_bp.route("/events/display/<display_name>", methods=["GET"])
def display_events_stream(display_name: str) -> Response | Tuple[Response, int]:
    """Server-Sent Events stream for specific display."""
    try:
        # Look up display by name
        display = Display.query.filter_by(name=display_name).first()
        if not display:
            return api_error("Display not found", 404)

        # Create SSE connection for display
        connection = sse_manager.create_connection(
            user_id=None, connection_type="display"  # Displays don't have user accounts
        )

        # Store display info in connection for filtering
        connection.display_name = display_name
        connection.display_id = display.id

        current_app.logger.info(
            f"Display SSE connection established for {display_name}"
        )

        return create_sse_response(connection)

    except Exception as e:
        current_app.logger.error(f"Error creating display SSE connection: {e}")
        return api_error("Failed to establish SSE connection", 500)


@api_v1_bp.route(
    "/display/<string:display_name>/skedda-data/<int:item_id>", methods=["GET"]
)
def get_display_skedda_data(display_name: str, item_id: int) -> Tuple[Response, int]:
    """Get Skedda calendar data for a public display.

    This endpoint does not require authentication - it's meant for public
    kiosk displays. It validates that the item belongs to the display's
    currently assigned slideshow.

    Query parameters:
        date (optional): Date to display in YYYY-MM-DD format, defaults to today
    """
    from datetime import datetime

    from ..ical_service import get_skedda_calendar_data

    try:
        # Look up display by name
        display = Display.query.filter_by(name=display_name).first()
        if not display:
            return api_error("Display not found", 404)

        # Check that display has a slideshow assigned
        if not display.current_slideshow_id:
            return api_error("Display has no slideshow assigned", 400)

        # Validate that the requested item belongs to this display's slideshow
        # Use query.filter_by instead of session.get for better cross-process compatibility
        item = SlideshowItem.query.filter_by(id=item_id).first()
        if not item:
            return api_error("Slideshow item not found", 404)

        if item.slideshow_id != display.current_slideshow_id:
            return api_error("Item does not belong to this display's slideshow", 403)

        # Validate item is a skedda type
        if item.content_type != "skedda":
            return api_error("Item is not a Skedda calendar", 400)

        # Get optional date parameter
        date_str = request.args.get("date")
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return api_error("Invalid date format. Use YYYY-MM-DD", 400)
        else:
            target_date = datetime.now().date()

        # Get the calendar data (pass the item, not just the feed_id)
        calendar_data = get_skedda_calendar_data(item, target_date)

        return api_response(calendar_data, "Skedda calendar data retrieved")

    except Exception as e:
        current_app.logger.error(
            f"Error getting display skedda data for {display_name}/{item_id}: {e}"
        )
        return api_error("Failed to retrieve calendar data", 500)


@api_v1_bp.route("/events/stats", methods=["GET"])
@api_auth_required
def sse_stats() -> Tuple[Response, int]:
    """Get SSE connection statistics with detailed connection information.

    Returns data formatted for the frontend SSEDebugger component with fields:
    - total_connections, admin_connections, display_connections
    - events_sent_last_hour
    - connections[]: array with id, type, user, display, connected_at, last_ping, events_sent
    """
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        # Get basic stats
        stats = sse_manager.get_connection_stats()

        # Add events sent in last hour
        stats["events_sent_last_hour"] = sse_manager.get_events_sent_last_hour()

        # Build user lookup for converting user_id to username
        user_lookup: Dict[int, Optional[str]] = {}

        # Add detailed connection information with frontend-expected field names
        detailed_connections = []
        with sse_manager.connections_lock:
            for conn_id, conn in sse_manager.connections.items():
                # Look up username for user_id
                username = None
                if conn.user_id is not None:
                    if conn.user_id not in user_lookup:
                        from kiosk_show_replacement.models import User

                        user = db.session.get(User, conn.user_id)
                        user_lookup[conn.user_id] = user.username if user else None
                    username = user_lookup.get(conn.user_id)

                # Build connection info with frontend-expected field names
                conn_info = {
                    "id": conn_id,  # Frontend expects "id" not "connection_id"
                    "type": conn.connection_type,  # Frontend expects "type" not "connection_type"
                    "user": username,  # Frontend expects "user" (username string) not "user_id"
                    "connected_at": conn.connected_at.isoformat(),
                    "last_ping": conn.last_ping.isoformat(),  # Frontend expects "last_ping"
                    "events_sent": conn.events_sent_count,
                }

                # Add display field for display connections
                if hasattr(conn, "display_name") and conn.display_name:
                    conn_info["display"] = (
                        conn.display_name
                    )  # Frontend expects "display"

                detailed_connections.append(conn_info)

        # Add detailed connection list to stats
        stats["connections"] = detailed_connections
        stats["connection_details"] = {
            "by_type": {
                "admin": [c for c in detailed_connections if c["type"] == "admin"],
                "display": [c for c in detailed_connections if c["type"] == "display"],
            }
        }

        return api_response(stats, "SSE statistics retrieved successfully")

    except Exception as e:
        current_app.logger.error(f"Error getting SSE stats: {e}")
        return api_error("Failed to get SSE statistics", 500)


@api_v1_bp.route("/events/test", methods=["POST"])
@api_auth_required
def broadcast_test_event() -> Tuple[Response, int]:
    """Broadcast a test event for SSE debugging."""
    try:
        from datetime import datetime, timezone

        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        data = request.get_json() or {}
        event_type = data.get("type", "test_event")
        message = data.get("message", "Test event from admin interface")

        # Create test event
        test_data = {
            "message": message,
            "user_id": current_user.id,
            "username": current_user.username,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_event": True,
        }

        # Broadcast to all admin connections
        sent_count = broadcast_system_event(event_type, test_data)

        current_app.logger.info(
            f"Test event broadcast by user {current_user.username}, sent to {sent_count} connections"
        )

        return api_response(
            {
                "event_type": event_type,
                "message": message,
                "connections_notified": sent_count,
                "broadcast_at": test_data["timestamp"],
            },
            "Test event broadcast successfully",
        )

    except Exception as e:
        current_app.logger.error(f"Error broadcasting test event: {e}")
        return api_error("Failed to broadcast test event", 500)


@api_v1_bp.route("/events/disconnect", methods=["POST"])
def disconnect_sse_connection() -> Tuple[Response, int]:
    """Explicitly disconnect an SSE connection.

    This endpoint allows clients to notify the server when they are disconnecting,
    enabling immediate cleanup of the connection rather than waiting for the next
    failed write attempt. This is called via navigator.sendBeacon() during page
    unload to ensure reliable delivery.

    The connection_id serves as an authentication token - only the client that
    received this ID during connection establishment can disconnect it.
    """
    try:
        try:
            data = request.get_json()
        except Exception:
            # Handle malformed JSON or empty body with content-type: application/json
            return api_error("No data provided", 400)

        if data is None:
            return api_error("No data provided", 400)

        connection_id = data.get("connection_id")
        if not connection_id:
            return api_error("connection_id is required", 400)

        # Check if connection exists before removing
        with sse_manager.connections_lock:
            connection_exists = connection_id in sse_manager.connections

        if connection_exists:
            sse_manager.remove_connection(connection_id)
            current_app.logger.info(
                f"SSE connection {connection_id} explicitly disconnected by client"
            )
            return api_response(
                {"connection_id": connection_id, "disconnected": True},
                "Connection disconnected successfully",
            )
        else:
            # Connection already removed or never existed - not an error
            current_app.logger.debug(
                f"SSE disconnect request for unknown connection {connection_id}"
            )
            return api_response(
                {"connection_id": connection_id, "disconnected": False},
                "Connection not found (may already be disconnected)",
            )

    except Exception as e:
        current_app.logger.error(f"Error disconnecting SSE connection: {e}")
        return api_error("Failed to disconnect SSE connection", 500)


# =============================================================================
# SSE Event Broadcasting Functions
# =============================================================================


def broadcast_display_update(
    display: Display, event_type: str, additional_data: Optional[Dict[Any, Any]] = None
) -> int:
    """Broadcast display update event to admin connections and the specific display.

    Args:
        display: Updated display
        event_type: Type of update (status_changed, assignment_changed, etc.)
        additional_data: Additional event data

    Returns:
        Number of connections that received the event
    """
    data = display.to_dict()

    # Add display_name field for frontend compatibility (frontend expects display_name,
    # but to_dict() returns 'name')
    data["display_name"] = display.name

    # For assignment changes, add slideshow_id and slideshow_name fields
    # that the frontend expects (separate from the nested assigned_slideshow object)
    if additional_data:
        data.update(additional_data)
        # Map new_slideshow_id to slideshow_id for frontend compatibility
        if "new_slideshow_id" in additional_data:
            data["slideshow_id"] = additional_data["new_slideshow_id"]
            # Get slideshow name if assigned
            if additional_data["new_slideshow_id"]:
                slideshow = db.session.get(
                    Slideshow, additional_data["new_slideshow_id"]
                )
                if slideshow:
                    data["slideshow_name"] = slideshow.name

    event = create_display_event(event_type, display.id, data)

    # Send to admin connections
    admin_count = sse_manager.broadcast_event(event, connection_type="admin")

    # Also send to the specific display connection for relevant event types
    # This allows the display to reload when its configuration or assignment changes
    display_count = 0
    if event_type in (
        "assignment_changed",
        "configuration_changed",
        "reload_requested",
    ):
        with sse_manager.connections_lock:
            for conn_id, conn in sse_manager.connections.items():
                if hasattr(conn, "display_id") and conn.display_id == display.id:
                    conn.add_event(event)
                    display_count += 1

    return admin_count + display_count


def broadcast_slideshow_update(
    slideshow: Slideshow,
    event_type: str,
    additional_data: Optional[Dict[Any, Any]] = None,
) -> int:
    """Broadcast slideshow update event to admin and display connections.

    Args:
        slideshow: Updated slideshow
        event_type: Type of update (created, updated, deleted, etc.)
        additional_data: Additional event data

    Returns:
        Number of connections that received the event
    """
    data = slideshow.to_dict()
    # Add slideshow_name field for frontend compatibility (frontend expects slideshow_name,
    # but to_dict() returns 'name')
    data["slideshow_name"] = slideshow.name
    if additional_data:
        data.update(additional_data)

    event = create_slideshow_event(event_type, slideshow.id, data)

    # Send to admin connections
    admin_count = sse_manager.broadcast_event(event, connection_type="admin")

    # Send to display connections if slideshow affects them
    # The display page listens for 'slideshow.updated' events and reloads when the
    # slideshow_id matches the current slideshow. We send the same event type (not a
    # separate display.slideshow_changed event) so the display can handle it uniformly.
    display_count = 0
    if event_type in ["updated", "deleted"]:
        # Find displays using this slideshow
        displays = Display.query.filter_by(current_slideshow_id=slideshow.id).all()
        for display in displays:
            # Send the same slideshow event to specific display connections
            with sse_manager.connections_lock:
                for conn_id, conn in sse_manager.connections.items():
                    if hasattr(conn, "display_id") and conn.display_id == display.id:
                        conn.add_event(event)
                        display_count += 1

    return admin_count + display_count


def broadcast_system_event(event_type: str, data: dict) -> int:
    """Broadcast system-wide event to all connections.

    Args:
        event_type: Type of system event
        data: Event data

    Returns:
        Number of connections that received the event
    """
    event = create_system_event(event_type, data)
    return sse_manager.broadcast_event(event)


@api_v1_bp.route("/displays/<int:display_id>/heartbeat", methods=["POST"])
@api_auth_required
def update_display_heartbeat(display_id: int) -> Tuple[Response, int]:
    """Update display heartbeat to mark it as online and broadcast SSE events."""
    try:
        from datetime import datetime, timezone

        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        display = db.session.get(Display, display_id)
        if not display:
            return api_error("Display not found", 404)

        data = request.get_json() or {}

        # Check if display was previously offline
        was_online = display.is_online

        # Update heartbeat timestamp
        display.last_seen_at = datetime.now(timezone.utc)

        # Update resolution if provided
        resolution_changed = False
        resolution = data.get("resolution")
        if resolution:
            # Handle both string format "1920x1080" and dict format
            width: Optional[Any] = None
            height: Optional[Any] = None
            if isinstance(resolution, str) and "x" in resolution:
                width_str, height_str = resolution.split("x", 1)
                width, height = int(width_str), int(height_str)
            elif isinstance(resolution, dict):
                width = resolution.get("width")
                height = resolution.get("height")
            else:
                width = data.get("width")
                height = data.get("height")

            if width and display.resolution_width != int(width):
                display.resolution_width = int(width)
                resolution_changed = True
            if height and display.resolution_height != int(height):
                display.resolution_height = int(height)
                resolution_changed = True

        db.session.commit()

        # Check if display came online and broadcast SSE event
        is_now_online = display.is_online
        if not was_online and is_now_online:
            # Display came online - broadcast status change event
            try:
                broadcast_display_update(
                    display,
                    "status_changed",
                    {
                        "display_id": display.id,
                        "display_name": display.name,
                        "is_online": True,
                        "status": "online",
                        "came_online_at": display.last_seen_at.isoformat(),
                        "resolution_changed": resolution_changed,
                        "display": display.to_dict(),  # Include full display data for UI updates
                    },
                )
                current_app.logger.info(
                    f"Display {display.name} (ID: {display.id}) came online, SSE event broadcast"
                )
            except Exception as sse_error:
                current_app.logger.error(
                    f"Failed to broadcast SSE event for display {display.id}: {sse_error}"
                )

        elif resolution_changed and is_now_online:
            # Resolution changed while online
            try:
                broadcast_display_update(
                    display,
                    "configuration_changed",
                    {
                        "display_id": display.id,
                        "display_name": display.name,
                        "resolution_width": display.resolution_width,
                        "resolution_height": display.resolution_height,
                        "change_type": "resolution",
                        "display": display.to_dict(),
                    },
                )
            except Exception as sse_error:
                current_app.logger.error(
                    f"Failed to broadcast configuration SSE event for display {display.id}: {sse_error}"
                )

        current_app.logger.debug(
            f"Display heartbeat updated for {display.name} (ID: {display.id}), online: {is_now_online}"
        )

        return api_response(
            {
                "display_id": display.id,
                "timestamp": display.last_seen_at.isoformat(),
                "is_online": is_now_online,
                "was_online": was_online,
                "status_changed": not was_online and is_now_online,
            },
            "Heartbeat updated successfully",
        )

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            f"Error updating heartbeat for display {display_id}: {e}"
        )
        return api_error("Failed to update heartbeat", 500)
