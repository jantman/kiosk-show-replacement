"""
API v1 endpoints for the Kiosk.show Replacement application.

This module contains all version 1 REST API endpoints:
- Slideshow CRUD operations
- Slideshow item management  
- Display management

All endpoints require authentication and return consistent JSON responses.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from flask import Blueprint, Response, jsonify, request, current_app
from sqlalchemy.exc import IntegrityError

from ..models import db, User, Slideshow, SlideshowItem, Display
from ..auth.decorators import login_required, get_current_user

# Create API v1 blueprint
api_v1_bp = Blueprint('api_v1', __name__)

# =============================================================================
# API Response Helpers
# =============================================================================

def api_response(data: Any = None, message: str = None, status_code: int = 200) -> Tuple[Response, int]:
    """Create a standardized API response."""
    response = {"success": True}  # Always include success field for successful responses
    if data is not None:
        response["data"] = data
    if message:
        response["message"] = message
    return jsonify(response), status_code

def api_error(message: str, status_code: int = 400, errors: List[str] = None) -> Tuple[Response, int]:
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
            default_item_duration=data.get("default_item_duration", 30),  # Support custom duration
            owner_id=current_user.id,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
            is_active=True,
            is_default=False
        )
        
        db.session.add(slideshow)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} created slideshow: {slideshow.name}")
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
        
        slideshow = Slideshow.query.get(slideshow_id)
        if not slideshow or not slideshow.is_active:
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
                Slideshow.is_active == True,
                Slideshow.id != slideshow_id
            ).first()
            if existing:
                return api_error("A slideshow with this name already exists", 400)
            
            slideshow.name = name
        
        if "description" in data:
            slideshow.description = data["description"]
        
        slideshow.updated_by_id = current_user.id
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} updated slideshow: {slideshow.name}")
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
        
        slideshow = Slideshow.query.get(slideshow_id)
        if not slideshow or not slideshow.is_active:
            return api_error("Slideshow not found", 404)
        
        # Check if slideshow is assigned to any displays
        assigned_displays = Display.query.filter_by(current_slideshow_id=slideshow_id).all()
        if assigned_displays:
            display_names = [d.name for d in assigned_displays]
            return api_error(
                f"Cannot delete slideshow: it is assigned to displays: {', '.join(display_names)}", 
                400
            )
        
        # Soft delete the slideshow and its items
        slideshow.is_active = False
        slideshow.updated_by_id = current_user.id
        
        for item in slideshow.items:
            item.is_active = False
            item.updated_by_id = current_user.id
        
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
        if not slideshow or not slideshow.is_active:
            return api_error("Slideshow not found", 404)
        
        # Clear any existing default
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
    """List all items in a slideshow - all users can view all slideshow items."""
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
    """Create a new slideshow item - all users can create items in all slideshows."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        slideshow = Slideshow.query.get(slideshow_id)
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
        max_order = db.session.query(db.func.max(SlideshowItem.order_index)).filter_by(
            slideshow_id=slideshow_id,
            is_active=True
        ).scalar() or 0
        
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
            is_active=True
        )
        
        db.session.add(item)
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} created item in slideshow {slideshow.name}")
        return api_response(item.to_dict(), "Slideshow item created successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating item for slideshow {slideshow_id}: {e}")
        return api_error("Failed to create slideshow item", 500)

@api_v1_bp.route("/slideshow-items/<int:item_id>", methods=["PUT"])
@api_auth_required
def update_slideshow_item(item_id: int) -> Tuple[Response, int]:
    """Update a slideshow item - all users can update all items."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
        
        item = SlideshowItem.query.get(item_id)
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
        
        current_app.logger.info(f"User {current_user.username} updated item {item.title}")
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
        
        item = SlideshowItem.query.get(item_id)
        if not item or not item.is_active:
            return api_error("Slideshow item not found", 404)
        
        slideshow = item.slideshow
        if not slideshow.is_active:
            return api_error("Slideshow item not found", 404)
        
        # Soft delete
        item.is_active = False
        item.updated_by_id = current_user.id
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} deleted item {item.title}")
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
        
        item = SlideshowItem.query.get(item_id)
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
                SlideshowItem.is_active == True,
                SlideshowItem.id != item_id
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
                SlideshowItem.is_active == True,
                SlideshowItem.id != item_id
            ).all()
            for reordered_item in items_to_update:
                reordered_item.order_index += 1
                reordered_item.updated_by_id = current_user.id
        
        item.updated_by_id = current_user.id
        db.session.commit()
        
        current_app.logger.info(f"User {current_user.username} reordered item {item.title}")
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
        
        display = Display.query.get(display_id)
        if not display:
            return api_error("Display not found", 404)
        
        return api_response(display.to_dict(), "Display retrieved successfully")
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving display {display_id}: {e}")
        return api_error("Failed to retrieve display", 500)

@api_v1_bp.route("/displays/<int:display_id>", methods=["PUT"])
@api_auth_required
def update_display(display_id: int) -> Tuple[Response, int]:
    """Update display slideshow assignment."""
    try:
        current_user = get_current_user()
        if not current_user:
            return api_error("Authentication required", 401)
            
        display = Display.query.get(display_id)
        if not display:
            return api_error("Display not found", 404)
        
        data = request.get_json()
        if not data:
            return api_error("No data provided", 400)
        
        slideshow_id = data.get("slideshow_id")
        if slideshow_id is not None:
            slideshow = Slideshow.query.get(slideshow_id)
            if not slideshow or not slideshow.is_active:
                return api_error("Slideshow not found", 404)
        
        display.current_slideshow_id = slideshow_id
        display.updated_by_id = current_user.id
        db.session.commit()
        
        action = f"assigned slideshow {slideshow_id}" if slideshow_id else "unassigned slideshow"
        current_app.logger.info(f"User {current_user.username} {action} for display {display_id}")
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
        
        slideshow_id = data.get("slideshow_id")
        if slideshow_id is not None:
            slideshow = Slideshow.query.get(slideshow_id)
            if not slideshow or not slideshow.is_active:
                return api_error("Slideshow not found", 404)
        
        display.current_slideshow_id = slideshow_id
        display.updated_by_id = current_user.id
        db.session.commit()
        
        action = f"assigned slideshow {slideshow_id}" if slideshow_id else "unassigned slideshow"
        current_app.logger.info(f"User {current_user.username} {action} for display {display_name}")
        return api_response(display.to_dict(), "Slideshow assignment updated successfully")
        
    except ValueError as e:
        return api_error(str(e), 400)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error assigning slideshow to display {display_name}: {e}")
        return api_error("Failed to assign slideshow to display", 500)

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
    """API status endpoint."""
    from datetime import datetime, timezone
    
    return api_response({
        "status": "healthy",
        "api_version": "v1",  # Test expects "api_version" not "version"
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, "API is operational")
