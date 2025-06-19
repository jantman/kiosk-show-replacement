"""
API v1 endpoints for the Kiosk.show Replacement application.

This module contains all version 1 REST API endpoints:
- Slideshow CRUD operations
- Slideshow item management
- Display management

All endpoints require authentication and return consistent JSON responses.
"""

from typing import Any, List, Tuple

from flask import Blueprint, Response, current_app, jsonify, request, session
from sqlalchemy.exc import IntegrityError

from ..auth.decorators import get_current_user
from ..models import Display, DisplayConfigurationTemplate, Slideshow, SlideshowItem, User, db

# Create API v1 blueprint
api_v1_bp = Blueprint("api_v1", __name__)

# =============================================================================
# API Response Helpers
# =============================================================================


def api_response(
    data: Any = None, message: str = None, status_code: int = 200
) -> Tuple[Response, int]:
    """Create a standardized API response."""
    response = {
        "success": True
    }  # Always include success field for successful responses
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return jsonify(response), status_code


def api_error(
    message: str, status_code: int = 400, errors: List[str] = None
) -> Tuple[Response, int]:
    """Create a standardized API error response."""
    response = {"success": False, "error": message}
    if errors:
        response["errors"] = errors
    else:
        response["errors"] = [message]  # Tests expect "errors" field
    response["message"] = message  # Tests also expect "message" field
    return jsonify(response), status_code


# =============================================================================
# Authentication Decorator for API
# =============================================================================


def api_auth_required(f):
    """Decorator to require authentication for API endpoints."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_current_user():
            return api_error("Authentication required", 401)
        return f(*args, **kwargs)

    return decorated_function


# =============================================================================
# Slideshow API Endpoints
# =============================================================================


@api_v1_bp.route("/slideshows", methods=["GET"])
@api_auth_required
def list_slideshows() -> Tuple[Response, int]:
    """List all slideshows - every user can see every slideshow."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        # Get all active slideshows - no ownership filtering
        slideshows = Slideshow.query.filter_by(is_active=True).all()

        # Convert to dict with computed fields
        slideshow_data = []
        for slideshow in slideshows:
            data = slideshow.to_dict()
            # Add computed fields
            data["item_count"] = len(
                [item for item in slideshow.items if item.is_active]
            )
            slideshow_data.append(data)

        return api_response(slideshow_data, "Slideshows retrieved successfully")

    except Exception as e:
        current_app.logger.error(f"Error listing slideshows: {e}")
        return api_error("Failed to retrieve slideshows", 500)


@api_v1_bp.route("/slideshows", methods=["POST"])
@api_auth_required
def create_slideshow() -> Tuple[Response, int]:
    """Create a new slideshow."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)

        name = data.get("name", "").strip()
        if not name:
            return api_error("Slideshow name is required", 400)

        # Check for global duplicate names (not per-user)
        existing = Slideshow.query.filter_by(name=name, is_active=True).first()
        if existing:
            return api_error("A slideshow with this name already exists", 400)

        slideshow = Slideshow(
            name=name,
            description=data.get("description", ""),
            default_item_duration=data.get(
                "default_item_duration", 30
            ),  # Support custom duration
            owner_id=current_user.id,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
            is_active=True,
            is_default=False,
        )

        db.session.add(slideshow)
        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} created slideshow: {slideshow.name}"
        )
        return api_response(slideshow.to_dict(), "Slideshow created successfully", 201)

    except IntegrityError:
        db.session.rollback()
        return api_error("A slideshow with this name already exists", 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating slideshow: {e}")
        return api_error("Failed to create slideshow", 500)


@api_v1_bp.route("/slideshows/<int:slideshow_id>", methods=["GET"])
@api_auth_required
def get_slideshow_by_id(slideshow_id: int) -> Tuple[Response, int]:
    """Get a specific slideshow with its items - all users can view all slideshows."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        slideshow = db.session.get(Slideshow, slideshow_id)
        if not slideshow or not slideshow.is_active:
            return api_error("Slideshow not found", 404)

        # Get slideshow data with items
        result = slideshow.to_dict()
        result["items"] = [item.to_dict() for item in slideshow.items if item.is_active]

        return api_response(result, "Slideshow retrieved successfully")

    except Exception as e:
        current_app.logger.error(f"Error retrieving slideshow {slideshow_id}: {e}")
        return api_error("Failed to retrieve slideshow", 500)


@api_v1_bp.route("/slideshows/<int:slideshow_id>", methods=["PUT"])
@api_auth_required
def update_slideshow(slideshow_id: int) -> Tuple[Response, int]:
    """Update a slideshow - all users can modify all slideshows."""
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

        # Update fields if provided
        if "name" in data:
            name = data["name"].strip()
            if not name:
                return api_error("Slideshow name cannot be empty", 400)

            # Check for global duplicate names (exclude current slideshow)
            existing = Slideshow.query.filter(
                Slideshow.name == name,
                Slideshow.is_active,
                Slideshow.id != slideshow_id,
            ).first()
            if existing:
                return api_error("A slideshow with this name already exists", 400)

            slideshow.name = name

        if "description" in data:
            slideshow.description = data["description"]

        slideshow.updated_by_id = current_user.id
        db.session.commit()

        current_app.logger.info(
            f"User {current_user.username} updated slideshow: {slideshow.name}"
        )
        return api_response(slideshow.to_dict(), "Slideshow updated successfully")

    except IntegrityError:
        db.session.rollback()
        return api_error("A slideshow with this name already exists", 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating slideshow {slideshow_id}: {e}")
        return api_error("Failed to update slideshow", 500)


@api_v1_bp.route("/slideshows/<int:slideshow_id>", methods=["DELETE"])
@api_auth_required
def delete_slideshow(slideshow_id: int) -> Tuple[Response, int]:
    """Delete a slideshow (soft delete) - all users can delete all slideshows."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)

        slideshow = db.session.get(Slideshow, slideshow_id)
        if not slideshow or not slideshow.is_active:
            return api_error("Slideshow not found", 404)

        # Check if slideshow is assigned to any displays
        assigned_displays = Display.query.filter_by(
            current_slideshow_id=slideshow_id
        ).all()
        if assigned_displays:
            display_names = [d.name for d in assigned_displays]
            return api_error(
                f"Cannot delete slideshow: it is assigned to displays: "
                f"{', '.join(display_names)}",
                400,
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

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting slideshow {slideshow_id}: {e}")
        return api_error("Failed to delete slideshow", 500)


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

        if content_type not in ["image", "video", "url", "text"]:
            return api_error("Invalid content type", 400)

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
            display_duration=data.get("display_duration", 30),
            order_index=max_order + 1,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
            is_active=True,
        )

        db.session.add(item)
        db.session.commit()

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
        if "content_url" in data:
            item.content_url = data["content_url"]
        if "content_text" in data:
            item.content_text = data["content_text"]
        if "display_duration" in data:
            item.display_duration = data["display_duration"]

        item.updated_by_id = current_user.id
        db.session.commit()

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
        from ..models import AssignmentHistory

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

        # Update display fields
        if "name" in data:
            display.name = data["name"]
        if "location" in data:
            display.location = data["location"]
        if "description" in data:
            display.description = data["description"]

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

        if slideshow_assignment_changed:
            action = (
                f"assigned slideshow {display.current_slideshow_id}"
                if display.current_slideshow_id
                else "unassigned slideshow"
            )
            current_app.logger.info(
                f"User {current_user.username} {action} for display {display_id}"
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
        from ..models import AssignmentHistory

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
        return api_response(template.to_dict(), "Display template created successfully", 201)

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


@api_v1_bp.route("/displays/<int:display_id>/apply-template/<int:template_id>", methods=["POST"])
@api_auth_required
def apply_template_to_display(display_id: int, template_id: int) -> Tuple[Response, int]:
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
        current_app.logger.error(f"Error applying template {template_id} to display {display_id}: {e}")
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
                    failed_displays.append({"id": display_id, "error": "Display not found"})
                    continue

                if display.is_archived:
                    failed_displays.append({"id": display_id, "error": "Display is archived"})
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

        return api_response(result, f"Template applied to {len(applied_displays)} displays")

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

        from sqlalchemy.exc import IntegrityError

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

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(
            "Unexpected error during API authentication",
            extra={
                "username": username,
                "action": "api_authentication_error",
                "error": str(e),
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
