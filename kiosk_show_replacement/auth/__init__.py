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

from flask import Blueprint

from .decorators import (
    admin_required,
    clear_session,
    get_current_user,
    get_current_user_id,
    is_admin,
    is_authenticated,
    login_required,
    refresh_session_user_data,
)
from .views import bp

__all__ = [
    "bp",
    "login_required",
    "admin_required",
    "is_authenticated",
    "is_admin",
    "get_current_user",
    "get_current_user_id",
    "refresh_session_user_data",
    "clear_session",
]
