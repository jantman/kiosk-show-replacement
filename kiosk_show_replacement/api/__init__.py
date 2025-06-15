"""
API module for the Kiosk.show Replacement application.

This module provides RESTful API endpoints for:
- Slideshow management (CRUD operations)
- Slideshow item management 
- Display management and monitoring

The API is versioned with v1 endpoints available at /api/v1/*
"""

from flask import Blueprint

# Create main API blueprint
api_bp = Blueprint('api', __name__)

# Import and register v1 endpoints
from .v1 import api_v1_bp

# Register v1 blueprint under /v1 prefix
api_bp.register_blueprint(api_v1_bp, url_prefix='/v1')

# API root endpoint for version discovery
@api_bp.route('/')
def api_root():
    """API root endpoint providing version information."""
    return {
        'message': 'Kiosk.show Replacement API',
        'versions': {
            'v1': '/api/v1/'
        },
        'documentation': '/api/v1/docs'
    }

# Health check for API
@api_bp.route('/health')
def api_health():
    """API health check endpoint."""
    return {
        'status': 'healthy',
        'api_version': 'v1',
        'endpoints': [
            '/api/v1/slideshows',
            '/api/v1/displays',
            '/api/v1/slideshow-items'
        ]
    }