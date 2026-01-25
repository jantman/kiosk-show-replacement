"""
Health check endpoints for the Kiosk Show Replacement application.

This module provides comprehensive health check endpoints for monitoring
and container orchestration (Kubernetes readiness/liveness probes).

Endpoints:
- /health - Overall health status
- /health/db - Database connectivity check
- /health/storage - Storage availability and disk space
- /health/ready - Readiness probe (can accept traffic)
- /health/live - Liveness probe (is running)
"""

import os
import shutil
import time
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from flask import Blueprint, Response, current_app, jsonify

health_bp = Blueprint("health", __name__)


def _get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def _check_database() -> Dict[str, Any]:
    """Check database connectivity, initialization status, and measure latency.

    Returns:
        Dictionary with status, latency_ms, initialized flag, and optional error
    """
    from .app import db

    try:
        start = time.perf_counter()
        # Execute a simple query to verify connectivity
        db.session.execute(db.text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000

        # Check if the database is initialized (User table exists and has data)
        initialized = _check_database_initialized()

        result = {
            "status": "healthy" if initialized else "not_initialized",
            "latency_ms": round(latency_ms, 2),
            "initialized": initialized,
        }

        if not initialized:
            result["message"] = (
                "Database tables exist but no admin user found. "
                "Run 'flask cli init-db' to initialize the database."
            )

        return result
    except Exception as e:
        error_str = str(e)
        current_app.logger.error(f"Database health check failed: {e}")

        # Detect specific initialization issues
        if "no such table" in error_str.lower():
            return {
                "status": "not_initialized",
                "initialized": False,
                "error": "Database tables do not exist",
                "message": (
                    "Database has not been initialized. "
                    "Run 'flask cli init-db' to create tables and admin user."
                ),
            }

        return {
            "status": "unhealthy",
            "initialized": False,
            "error": error_str,
        }


def _check_database_initialized() -> bool:
    """Check if the database has been properly initialized.

    Returns:
        True if database is initialized with required tables and admin user
    """
    from .app import db

    try:
        # Check if User table exists and has at least one user
        # Note: The table is named 'users' (plural) in the database
        result = db.session.execute(db.text("SELECT COUNT(*) FROM users")).scalar()
        return result is not None and result > 0
    except Exception:
        return False


def _check_storage() -> Dict[str, Any]:
    """Check storage availability and disk space.

    Returns:
        Dictionary with status, free_space_mb, total_space_mb, and optional error
    """
    try:
        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")

        # Ensure directory exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder, exist_ok=True)

        # Check disk space
        disk_usage = shutil.disk_usage(upload_folder)
        free_mb = disk_usage.free / (1024 * 1024)
        total_mb = disk_usage.total / (1024 * 1024)
        used_percent = (disk_usage.used / disk_usage.total) * 100

        # Consider unhealthy if less than 100MB free or >95% used
        min_free_mb = current_app.config.get("HEALTH_MIN_FREE_SPACE_MB", 100)
        max_used_percent = current_app.config.get("HEALTH_MAX_DISK_USAGE_PERCENT", 95)

        if free_mb < min_free_mb or used_percent > max_used_percent:
            status = "degraded"
        else:
            status = "healthy"

        # Test write access
        test_file = os.path.join(upload_folder, ".health_check")
        try:
            with open(test_file, "w") as f:
                f.write("health check")
            os.remove(test_file)
            writable = True
        except Exception:
            writable = False
            status = "unhealthy"

        return {
            "status": status,
            "free_space_mb": round(free_mb, 2),
            "total_space_mb": round(total_mb, 2),
            "used_percent": round(used_percent, 2),
            "writable": writable,
            "path": upload_folder,
        }
    except Exception as e:
        current_app.logger.error(f"Storage health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def _get_overall_status(checks: Dict[str, Dict[str, Any]]) -> str:
    """Determine overall health status from individual checks.

    Args:
        checks: Dictionary of check results

    Returns:
        'healthy', 'degraded', or 'unhealthy'
    """
    statuses = [check.get("status", "unknown") for check in checks.values()]

    if all(s == "healthy" for s in statuses):
        return "healthy"
    elif any(s == "unhealthy" for s in statuses):
        return "unhealthy"
    else:
        return "degraded"


@health_bp.route("/health")
def health_check() -> Tuple[Response, int]:
    """Overall health check endpoint.

    Returns 200 if healthy/degraded, 503 if unhealthy.

    Response format:
    {
        "status": "healthy|degraded|unhealthy",
        "timestamp": "ISO8601",
        "version": "x.y.z",
        "checks": {
            "database": {"status": "healthy", "latency_ms": 5},
            "storage": {"status": "healthy", "free_space_mb": 1024}
        }
    }
    """
    from . import __version__

    checks = {
        "database": _check_database(),
        "storage": _check_storage(),
    }

    status = _get_overall_status(checks)

    response = {
        "status": status,
        "timestamp": _get_timestamp(),
        "version": __version__,
        "checks": checks,
    }

    status_code = 200 if status != "unhealthy" else 503
    return jsonify(response), status_code


@health_bp.route("/health/db")
def health_database() -> Tuple[Response, int]:
    """Database health check endpoint.

    Returns 200 if database is accessible and initialized, 503 otherwise.
    Includes detailed information about database initialization status.
    """
    result = _check_database()
    result["timestamp"] = _get_timestamp()

    # Return 200 only if database is healthy AND initialized
    if result["status"] == "healthy":
        status_code = 200
    elif result["status"] == "not_initialized":
        status_code = 503
    else:
        status_code = 503

    return jsonify(result), status_code


@health_bp.route("/health/storage")
def health_storage() -> Tuple[Response, int]:
    """Storage health check endpoint.

    Returns 200 if storage is healthy/degraded, 503 if unhealthy.
    """
    result = _check_storage()
    result["timestamp"] = _get_timestamp()

    status_code = 200 if result["status"] != "unhealthy" else 503
    return jsonify(result), status_code


@health_bp.route("/health/ready")
def health_ready() -> Tuple[Response, int]:
    """Readiness probe for Kubernetes.

    Indicates whether the application is ready to receive traffic.
    Checks database connectivity and initialization status.

    Returns 200 if ready, 503 if not ready.
    """
    db_check = _check_database()

    if db_check["status"] == "healthy":
        return (
            jsonify(
                {
                    "status": "ready",
                    "timestamp": _get_timestamp(),
                    "database_initialized": db_check.get("initialized", True),
                }
            ),
            200,
        )
    elif db_check["status"] == "not_initialized":
        return (
            jsonify(
                {
                    "status": "not_ready",
                    "timestamp": _get_timestamp(),
                    "reason": "database_not_initialized",
                    "message": db_check.get(
                        "message",
                        "Database not initialized. Run 'flask cli init-db'.",
                    ),
                    "database_initialized": False,
                }
            ),
            503,
        )
    else:
        return (
            jsonify(
                {
                    "status": "not_ready",
                    "timestamp": _get_timestamp(),
                    "reason": "database_unavailable",
                    "message": db_check.get("error", "Database unavailable"),
                    "database_initialized": False,
                }
            ),
            503,
        )


@health_bp.route("/health/live")
def health_live() -> Tuple[Response, int]:
    """Liveness probe for Kubernetes.

    Indicates whether the application is running.
    This is a simple check that always returns 200 if the app is responsive.

    Returns 200 if alive.
    """
    return (
        jsonify(
            {
                "status": "alive",
                "timestamp": _get_timestamp(),
            }
        ),
        200,
    )
