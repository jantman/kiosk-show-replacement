"""
API module for the Kiosk.show Replacement application.

This module contains REST API endpoints and related functionality for:
- Slideshow CRUD operations
- Display management 
- File upload handling
- Authentication endpoints
- Real-time event streaming via Server-Sent Events

The API follows RESTful principles with JSON request/response format
and proper HTTP status codes. All endpoints include comprehensive
input validation and error handling.
"""

__all__ = []

"""
API Blueprint for kiosk-show-replacement.

This module provides REST API endpoints for managing slideshows and slide items.
"""

from flask import Blueprint, request, jsonify
from ..app import db
from ..models import Slideshow, SlideItem

bp = Blueprint('api', __name__)


@bp.route('/slideshows', methods=['GET'])
def list_slideshows():
    """List all slideshows."""
    slideshows = Slideshow.query.filter_by(is_active=True).all()
    return jsonify([slideshow.to_dict() for slideshow in slideshows])


@bp.route('/slideshows', methods=['POST'])
def create_slideshow():
    """Create a new slideshow."""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    slideshow = Slideshow(
        name=data['name'],
        description=data.get('description', '')
    )
    
    try:
        db.session.add(slideshow)
        db.session.commit()
        return jsonify(slideshow.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/slideshows/<int:slideshow_id>', methods=['GET'])
def get_slideshow(slideshow_id):
    """Get a specific slideshow with its slides."""
    slideshow = Slideshow.query.get_or_404(slideshow_id)
    
    result = slideshow.to_dict()
    result['slides'] = [slide.to_dict() for slide in slideshow.slides if slide.is_active]
    
    return jsonify(result)


@bp.route('/slideshows/<int:slideshow_id>/slides', methods=['POST'])
def add_slide(slideshow_id):
    """Add a new slide to a slideshow."""
    slideshow = Slideshow.query.get_or_404(slideshow_id)
    data = request.get_json()
    
    if not data or not data.get('content_type'):
        return jsonify({'error': 'Content type is required'}), 400
    
    slide = SlideItem(
        slideshow_id=slideshow_id,
        title=data.get('title'),
        content_type=data['content_type'],
        content_url=data.get('content_url'),
        content_text=data.get('content_text'),
        display_duration=data.get('display_duration', 30),
        order_index=data.get('order_index', 0)
    )
    
    try:
        db.session.add(slide)
        db.session.commit()
        return jsonify(slide.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/slides/<int:slide_id>', methods=['PUT'])
def update_slide(slide_id):
    """Update a slide."""
    slide = SlideItem.query.get_or_404(slide_id)
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Update fields
    for field in ['title', 'content_url', 'content_text', 'display_duration', 'order_index']:
        if field in data:
            setattr(slide, field, data[field])
    
    try:
        db.session.commit()
        return jsonify(slide.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@bp.route('/slides/<int:slide_id>', methods=['DELETE'])
def delete_slide(slide_id):
    """Delete a slide (soft delete by setting is_active=False)."""
    slide = SlideItem.query.get_or_404(slide_id)
    
    slide.is_active = False
    
    try:
        db.session.commit()
        return jsonify({'message': 'Slide deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
