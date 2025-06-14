"""
Authentication module for the Kiosk.show Replacement application.

This module provides authentication and authorization functionality including:
- User login/logout handling
- Session management
- Authentication decorators and middleware
- Hooks for future authentication methods (OAuth, LDAP, etc.)
- User creation and management utilities

Initially implements permissive authentication where any username/password
combination is accepted, with extensibility for more secure methods.
"""

__all__ = []
