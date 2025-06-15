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

from .views import display_bp

__all__ = ["display_bp"]
