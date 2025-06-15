"""
API v1 endpoints for the Kiosk.show Replacement application.

This module contains all version 1 REST API endpoints:
- Slideshow CRUD operations
- Slideshow item management
- Display management

All endpoints require authentication and return consistent JSON responses.
"""

from typing import Any, Dict, List, Optional, T@api_v1_bp.route("/slideshows/<int:slideshow_id>/items", methods=["GET"])
@require_auth
def list_slideshow_items(slideshow_id: int) -> Tuple[Response, int]:
    """List all items in a slideshow."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        slideshow = Slideshow.query.get(slideshow_id)
        if not slideshow:
            return api_error("Slideshow not found", 404)
        
        if not slideshow.is_active:
            return api_error("Slideshow not found", 404)lask import Blueprint, Response, jsonify, request, current_app
from functools import wraps

from ..auth.decorators import login_required, get_current_user
from ..app import db
from ..models import Display, Slideshow, SlideshowItem, User

# Create API v1 blueprint
api_v1_bp = Blueprint("api_v1", __name__)


# API Response Helpers
def api_response(data: Any = None, message: str = None, status_code: int = 200) -> Tuple[Response, int]:
    """Create a consistent API response format."""
    response = {}
    
    if data is not None:
        response["data"] = data
    
    if message:
        response["message"] = message
    
    response["success"] = 200 <= status_code < 400
    
    return jsonify(response), status_code


def api_error(message: str, status_code: int = 400, errors: Dict[str, Any] = None) -> Tuple[Response, int]:
    """Create a consistent API error response."""
    response = {
        "success": False,
        "message": message,
    }
    
    if errors:
        response["errors"] = errors
    
    return jsonify(response), status_code


def validate_json_request() -> Dict[str, Any]:
    """Validate that request contains valid JSON data."""
    if not request.is_json:
        raise ValueError("Content-Type must be application/json")
    
    data = request.get_json()
    if data is None:
        raise ValueError("Request body must contain valid JSON")
    
    return data


def api_auth_required(f):
    """API authentication decorator that returns JSON errors."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return login_required(f)(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"API authentication error: {e}")
            return api_error("Authentication required", 401)
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
        
        # All users can see all active slideshows
        slideshows = Slideshow.query.filter_by(is_active=True).all()
        
        slideshow_data = []
        for slideshow in slideshows:
            data = slideshow.to_dict()
            data["item_count"] = len([item for item in slideshow.items if item.is_active])
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
        
        data = validate_json_request()
        
        # Validate required fields
        if not data.get("name"):
            return api_error("Name is required", 400, {"name": "This field is required"})
        
        if len(data["name"].strip()) < 1:
            return api_error("Name cannot be empty", 400, {"name": "Name cannot be empty"})
        
        # Check for duplicate names globally (since all users can see all slideshows)
        existing = Slideshow.query.filter_by(
            name=data["name"].strip(),
            is_active=True
        ).first()
        
        if existing:
            return api_error("Slideshow name already exists", 400, {"name": "A slideshow with this name already exists"})
        
        # Create slideshow
        slideshow = Slideshow(
            name=data["name"].strip(),
            description=data.get("description", "").strip(),
            owner_id=current_user.id,
            created_by_id=current_user.id,
            default_item_duration=data.get("default_item_duration", 30),
            is_active=True,
            is_default=False  # Will be set explicitly via separate endpoint
        )
        
        db.session.add(slideshow)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} created slideshow: {slideshow.name}")
        return api_response(slideshow.to_dict(), "Slideshow created successfully", 201)
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating slideshow: {e}")
        return api_error("Failed to create slideshow", 500)


@api_v1_bp.route("/slideshows/<int:slideshow_id>", methods=["GET"])
@api_auth_required
def get_slideshow(slideshow_id: int) -> Tuple[Response, int]:
    """Get a specific slideshow with its items - all users can view all slideshows."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        slideshow = Slideshow.query.get(slideshow_id)
        if not slideshow:
            return api_error("Slideshow not found", 404)
        
        if not slideshow.is_active:
            return api_error("Slideshow not found", 404)
        
        # Get slideshow data with items
        result = slideshow.to_dict()
        result["items"] = [
            item.to_dict() for item in slideshow.items 
            if item.is_active
        ]
        
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
        
        slideshow = Slideshow.query.get(slideshow_id)
        if not slideshow:
            return api_error("Slideshow not found", 404)
        
        if not slideshow.is_active:
            return api_error("Slideshow not found", 404)
        
        data = validate_json_request()
        
        # Validate name if provided
        if "name" in data:
            if not data["name"] or len(data["name"].strip()) < 1:
                return api_error("Name cannot be empty", 400, {"name": "Name cannot be empty"})
            
            # Check for duplicate names globally (excluding current slideshow)
            existing = Slideshow.query.filter_by(
                name=data["name"].strip(),
                is_active=True
            ).filter(Slideshow.id != slideshow_id).first()
            
            if existing:
                return api_error("Slideshow name already exists", 400, {"name": "A slideshow with this name already exists"})
        
        # Update fields
        updatable_fields = ["name", "description", "default_item_duration"]
        for field in updatable_fields:
            if field in data:
                if field == "name":
                    setattr(slideshow, field, data[field].strip())
                elif field == "description":
                    setattr(slideshow, field, data[field].strip())
                else:
                    setattr(slideshow, field, data[field])
        
        slideshow.updated_by_id = current_user.id
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} updated slideshow: {slideshow.name}")
        return api_response(slideshow.to_dict(), "Slideshow updated successfully")
        
    except ValueError as e:
        return api_error(str(e), 400)
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
        
        slideshow = Slideshow.query.get(slideshow_id)
        if not slideshow:
            return api_error("Slideshow not found", 404)
        
        if not slideshow.is_active:
            return api_error("Slideshow not found", 404)
        
        # Check if slideshow is assigned to any displays
        assigned_displays = Display.query.filter_by(current_slideshow_id=slideshow_id).all()
        if assigned_displays:
            display_names = [d.name for d in assigned_displays]
            return api_error(
                f"Cannot delete slideshow assigned to displays: {', '.join(display_names)}", 
                400,
                {"displays": display_names}
            )
        
        # Soft delete the slideshow and its items
        slideshow.is_active = False
        slideshow.updated_by_id = current_user.id
        
        for item in slideshow.items:
            item.is_active = False
        
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} deleted slideshow: {slideshow.name}")
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
        
        slideshow = Slideshow.query.get(slideshow_id)
        if not slideshow:
            return api_error("Slideshow not found", 404)
        
        if not slideshow.is_active:
            return api_error("Slideshow not found", 404)
        
        # Remove default flag from all other slideshows (globally)
        Slideshow.query.filter_by(is_default=True).update({"is_default": False})
        
        # Set this slideshow as default
        slideshow.is_default = True
        slideshow.updated_by_id = current_user.id
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} set slideshow {slideshow.name} as default")
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
    """List all items in a slideshow."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        slideshow = Slideshow.query.get(slideshow_id)
        if not slideshow:
            return api_error("Slideshow not found", 404)
        
        if not slideshow.is_active:
            return api_error("Slideshow not found", 404)
        
        items = [
            item.to_dict() for item in slideshow.items 
            if item.is_active
        ]
        
        return api_response(items, "Slideshow items retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error listing items for slideshow {slideshow_id}: {e}")
        return api_error("Failed to retrieve slideshow items", 500)


@api_v1_bp.route("/slideshows/<int:slideshow_id>/items", methods=["POST"])
@api_auth_required
def create_slideshow_item(slideshow_id: int) -> Tuple[Response, int]:
    """Add a new item to a slideshow."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        slideshow = Slideshow.query.get(slideshow_id)
        if not slideshow:
            return api_error("Slideshow not found", 404)
        
        # Check permissions
        if not current_user.is_admin and slideshow.owner_id != current_user.id:
            return api_error("Access denied", 403)
        
        if not slideshow.is_active:
            return api_error("Slideshow not found", 404)
        
        data = validate_json_request()
        
        # Validate required fields
        errors = {}
        if not data.get("content_type"):
            errors["content_type"] = "Content type is required"
        elif data["content_type"] not in ["image", "video", "url", "text"]:
            errors["content_type"] = "Content type must be one of: image, video, url, text"
        
        # Validate content based on type
        content_type = data.get("content_type")
        if content_type in ["image", "video", "url"]:
            if not data.get("content_url"):
                errors["content_url"] = "Content URL is required for this content type"
        elif content_type == "text":
            if not data.get("content_text"):
                errors["content_text"] = "Content text is required for text content type"
        
        if errors:
            return api_error("Validation failed", 400, errors)
        
        # Get next order index
        max_order = db.session.query(db.func.max(SlideshowItem.order_index)).filter_by(
            slideshow_id=slideshow_id,
            is_active=True
        ).scalar()
        next_order = (max_order or 0) + 1
        
        # Create slideshow item
        item = SlideshowItem(
            slideshow_id=slideshow_id,
            title=data.get("title", "").strip(),
            content_type=content_type,
            content_url=data.get("content_url", "").strip() if data.get("content_url") else None,
            content_text=data.get("content_text", "").strip() if data.get("content_text") else None,
            display_duration=data.get("display_duration") or slideshow.default_item_duration,
            order_index=data.get("order_index", next_order),
            is_active=True,
            created_by_id=current_user.id
        )
        
        db.session.add(item)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} added item to slideshow {slideshow.name}")
        return api_response(item.to_dict(), "Slideshow item created successfully", 201)
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating item for slideshow {slideshow_id}: {e}")
        return api_error("Failed to create slideshow item", 500)


@api_v1_bp.route("/slideshow-items/<int:item_id>", methods=["PUT"])
@api_auth_required
def update_slideshow_item(item_id: int) -> Tuple[Response, int]:
    """Update a slideshow item."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        item = SlideshowItem.query.get(item_id)
        if not item:
            return api_error("Slideshow item not found", 404)
        
        # Check permissions via slideshow ownership
        slideshow = item.slideshow
        if not current_user.is_admin and slideshow.owner_id != current_user.id:
            return api_error("Access denied", 403)
        
        if not item.is_active:
            return api_error("Slideshow item not found", 404)
        
        data = validate_json_request()
        
        # Validate content type if provided
        if "content_type" in data and data["content_type"] not in ["image", "video", "url", "text"]:
            return api_error("Invalid content type", 400, {"content_type": "Content type must be one of: image, video, url, text"})
        
        # Update fields
        updatable_fields = ["title", "content_type", "content_url", "content_text", "display_duration", "order_index"]
        for field in updatable_fields:
            if field in data:
                if field in ["title", "content_url", "content_text"] and data[field] is not None:
                    setattr(item, field, str(data[field]).strip())
                else:
                    setattr(item, field, data[field])
        
        item.updated_by_id = current_user.id
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} updated slideshow item {item_id}")
        return api_response(item.to_dict(), "Slideshow item updated successfully")
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating slideshow item {item_id}: {e}")
        return api_error("Failed to update slideshow item", 500)


@api_v1_bp.route("/slideshow-items/<int:item_id>", methods=["DELETE"])
@api_auth_required
def delete_slideshow_item(item_id: int) -> Tuple[Response, int]:
    """Delete a slideshow item (soft delete)."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        item = SlideshowItem.query.get(item_id)
        if not item:
            return api_error("Slideshow item not found", 404)
        
        # Check permissions via slideshow ownership
        slideshow = item.slideshow
        if not current_user.is_admin and slideshow.owner_id != current_user.id:
            return api_error("Access denied", 403)
        
        if not item.is_active:
            return api_error("Slideshow item not found", 404)
        
        # Soft delete
        item.is_active = False
        item.updated_by_id = current_user.id
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} deleted slideshow item {item_id}")
        return api_response(None, "Slideshow item deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting slideshow item {item_id}: {e}")
        return api_error("Failed to delete slideshow item", 500)


@api_v1_bp.route("/slideshow-items/<int:item_id>/reorder", methods=["POST"])
@api_auth_required
def reorder_slideshow_item(item_id: int) -> Tuple[Response, int]:
    """Reorder a slideshow item."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        item = SlideshowItem.query.get(item_id)
        if not item:
            return api_error("Slideshow item not found", 404)
        
        # Check permissions via slideshow ownership
        slideshow = item.slideshow
        if not current_user.is_admin and slideshow.owner_id != current_user.id:
            return api_error("Access denied", 403)
        
        if not item.is_active:
            return api_error("Slideshow item not found", 404)
        
        data = validate_json_request()
        
        if "new_order" not in data:
            return api_error("new_order is required", 400)
        
        new_order = data["new_order"]
        if not isinstance(new_order, int) or new_order < 1:
            return api_error("new_order must be a positive integer", 400)
        
        # Get all active items in the slideshow
        all_items = SlideshowItem.query.filter_by(
            slideshow_id=slideshow.id,
            is_active=True
        ).order_by(SlideshowItem.order_index).all()
        
        if new_order > len(all_items):
            return api_error(f"new_order cannot be greater than {len(all_items)}", 400)
        
        # Remove the item from its current position
        all_items.remove(item)
        
        # Insert the item at the new position (convert to 0-based index)
        all_items.insert(new_order - 1, item)
        
        # Update order indices
        for i, reordered_item in enumerate(all_items):
            reordered_item.order_index = i + 1
            reordered_item.updated_by_id = current_user.id
        
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} reordered slideshow item {item_id} to position {new_order}")
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
        
        # Admin users can see all displays, regular users see only their own
        if current_user.is_admin:
            displays = Display.query.all()
        else:
            displays = Display.query.filter_by(owner_id=current_user.id).all()
        
        display_data = []
        for display in displays:
            data = display.to_dict()
            data["online"] = display.is_online
            if display.current_slideshow_id:
                slideshow = Slideshow.query.get(display.current_slideshow_id)
                if slideshow:
                    data["current_slideshow"] = {
                        "id": slideshow.id,
                        "name": slideshow.name
                    }
            display_data.append(data)
        
        return api_response(display_data, "Displays retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error listing displays: {e}")
        return api_error("Failed to retrieve displays", 500)


@api_v1_bp.route("/displays/<int:display_id>", methods=["GET"])
@api_auth_required
def get_display(display_id: int) -> Tuple[Response, int]:
    """Get details for a specific display."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        display = Display.query.get(display_id)
        if not display:
            return api_error("Display not found", 404)
        
        # Check permissions (admin can see all, users can see their own or unowned displays)
        if not current_user.is_admin and display.owner_id and display.owner_id != current_user.id:
            return api_error("Access denied", 403)
        
        data = display.to_dict()
        data["online"] = display.is_online
        
        # Include current slideshow details
        if display.current_slideshow_id:
            slideshow = Slideshow.query.get(display.current_slideshow_id)
            if slideshow:
                data["current_slideshow"] = slideshow.to_dict()
        
        return api_response(data, "Display retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving display {display_id}: {e}")
        return api_error("Failed to retrieve display", 500)


@api_v1_bp.route("/displays/<int:display_id>", methods=["PUT"])
@api_auth_required
def update_display(display_id: int) -> Tuple[Response, int]:
    """Update a display (primarily for slideshow assignment)."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        display = Display.query.get(display_id)
        if not display:
            return api_error("Display not found", 404)
        
        # Check permissions
        if not current_user.is_admin and display.owner_id and display.owner_id != current_user.id:
            return api_error("Access denied", 403)
        
        data = validate_json_request()
        
        # Handle slideshow assignment
        if "slideshow_id" in data:
            slideshow_id = data["slideshow_id"]
            
            if slideshow_id is not None:
                # Validate slideshow exists and user has access
                slideshow = Slideshow.query.get(slideshow_id)
                if not slideshow:
                    return api_error("Slideshow not found", 400, {"slideshow_id": "Invalid slideshow ID"})
                
                if not slideshow.is_active:
                    return api_error("Slideshow is not active", 400, {"slideshow_id": "Slideshow is not active"})
                
                # Check slideshow permissions
                if not current_user.is_admin and slideshow.owner_id != current_user.id:
                    return api_error("Access denied to slideshow", 403)
            
            display.current_slideshow_id = slideshow_id
        
        # Handle ownership assignment (admin only)
        if "owner_id" in data and current_user.is_admin:
            owner_id = data["owner_id"]
            if owner_id is not None:
                owner = User.query.get(owner_id)
                if not owner:
                    return api_error("Owner not found", 400, {"owner_id": "Invalid user ID"})
            display.owner_id = owner_id
        
        # Update other fields
        updatable_fields = ["location", "notes"]
        for field in updatable_fields:
            if field in data:
                setattr(display, field, str(data[field]).strip() if data[field] else None)
        
        display.updated_by_id = current_user.id
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} updated display {display.name}")
        
        # Return updated display data
        result = display.to_dict()
        result["online"] = display.is_online
        if display.current_slideshow_id:
            slideshow = Slideshow.query.get(display.current_slideshow_id)
            if slideshow:
                result["current_slideshow"] = slideshow.to_dict()
        
        return api_response(result, "Display updated successfully")
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating display {display_id}: {e}")
        return api_error("Failed to update display", 500)


@api_v1_bp.route("/displays/<int:display_id>", methods=["DELETE"])
@api_auth_required
def delete_display(display_id: int) -> Tuple[Response, int]:
    """Delete a display."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        display = Display.query.get(display_id)
        if not display:
            return api_error("Display not found", 404)
        
        # Check permissions
        if not current_user.is_admin and display.owner_id and display.owner_id != current_user.id:
            return api_error("Access denied", 403)
        
        display_name = display.name
        db.session.delete(display)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} deleted display {display_name}")
        return api_response(None, "Display deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting display {display_id}: {e}")
        return api_error("Failed to delete display", 500)


# =============================================================================
# API Status and Health Endpoints
# =============================================================================

@api_v1_bp.route("/status", methods=["GET"])
def api_status() -> Tuple[Response, int]:
    """Get API status information."""
    try:
        from datetime import datetime, timezone
        from ... import __version__
        
        # Test database connection
        db.session.execute(db.text("SELECT 1"))
        
        status_data = {
            "api_version": "v1",
            "app_version": __version__,
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": "connected"
        }
        
        return api_response(status_data, "API is healthy")
        
    except Exception as e:
        current_app.logger.error(f"API health check failed: {e}")
        return api_error("API is unhealthy", 503, {"database": "disconnected"})
