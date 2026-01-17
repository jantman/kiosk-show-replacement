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
    """Check database connectivity and measure latency.

    Returns:
        Dictionary with status, latency_ms, and optional error
    """
    from .app import db

    try:
        start = time.perf_counter()
        # Execute a simple query to verify connectivity
        db.session.execute(db.text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
        }
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


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

    Returns 200 if database is accessible, 503 otherwise.
    """
    result = _check_database()
    result["timestamp"] = _get_timestamp()

    status_code = 200 if result["status"] == "healthy" else 503
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
    Checks database connectivity to ensure requests can be processed.

    Returns 200 if ready, 503 if not ready.
    """
    db_check = _check_database()

    if db_check["status"] == "healthy":
        return (
            jsonify(
                {
                    "status": "ready",
                    "timestamp": _get_timestamp(),
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": "not_ready",
                    "timestamp": _get_timestamp(),
                    "reason": "Database unavailable",
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
