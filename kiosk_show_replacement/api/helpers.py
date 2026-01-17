"""
API response helpers and error handlers.

This module provides standardized response formatting for all API endpoints,
including error handling with correlation IDs for request tracing.
"""

from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, Response, g, jsonify

from ..exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    StorageError,
    ValidationError,
)


def get_correlation_id() -> Optional[str]:
    """Get the correlation ID for the current request.

    Returns:
        The correlation ID if set, None otherwise
    """
    return getattr(g, "correlation_id", None)


def api_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200,
) -> Tuple[Response, int]:
    """Create a standardized successful API response.

    Args:
        data: Response data (will be included under 'data' key)
        message: Optional success message
        status_code: HTTP status code (default 200)

    Returns:
        Tuple of (Flask Response, status code)
    """
    response: Dict[str, Any] = {"success": True}

    if data is not None:
        response["data"] = data

    if message:
        response["message"] = message

    # Include correlation ID if available
    correlation_id = get_correlation_id()
    if correlation_id:
        response["correlation_id"] = correlation_id

    return jsonify(response), status_code


def api_error(
    message: str,
    status_code: int = 400,
    errors: Optional[List[str]] = None,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Tuple[Response, int]:
    """Create a standardized API error response.

    This function maintains backward compatibility with the existing error format
    while adding new fields for enhanced error handling.

    Args:
        message: Human-readable error message
        status_code: HTTP status code
        errors: List of error messages (for backward compatibility)
        error_code: Machine-readable error code
        details: Additional error details

    Returns:
        Tuple of (Flask Response, status code)
    """
    # Build response with backward-compatible format
    # Keep "error" as string for compatibility, add structured info separately
    response: Dict[str, Any] = {
        "success": False,
        "error": message,  # Keep as string for backward compatibility
        "message": message,
        "errors": errors if errors else [message],
    }

    # Add structured error info in a separate field
    error_info: Dict[str, Any] = {
        "code": error_code or _status_to_error_code(status_code),
        "message": message,
    }

    if details:
        error_info["details"] = details

    # Include correlation ID if available
    correlation_id = get_correlation_id()
    if correlation_id:
        error_info["correlation_id"] = correlation_id

    response["error_info"] = error_info

    return jsonify(response), status_code


def _status_to_error_code(status_code: int) -> str:
    """Map HTTP status code to a default error code.

    Args:
        status_code: HTTP status code

    Returns:
        Default error code string
    """
    code_map = {
        400: "BAD_REQUEST",
        401: "AUTHENTICATION_REQUIRED",
        403: "ACCESS_DENIED",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    return code_map.get(status_code, "UNKNOWN_ERROR")


def exception_to_response(exc: AppException) -> Tuple[Response, int]:
    """Convert an AppException to an API error response.

    Args:
        exc: The application exception

    Returns:
        Tuple of (Flask Response, status code)
    """
    return api_error(
        message=exc.message,
        status_code=exc.status_code,
        error_code=exc.error_code,
        details=exc.details if exc.details else None,
    )


def register_error_handlers(app: Flask) -> None:
    """Register error handlers for application exceptions.

    This function registers Flask error handlers for all custom exception types,
    ensuring consistent error response formatting throughout the application.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(AppException)
    def handle_app_exception(exc: AppException) -> Tuple[Response, int]:
        """Handle all AppException subclasses."""
        app.logger.warning(
            f"Application error: {exc.error_code} - {exc.message}",
            extra={
                "error_code": exc.error_code,
                "status_code": exc.status_code,
                "details": exc.details,
                "correlation_id": get_correlation_id(),
            },
        )
        return exception_to_response(exc)

    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError) -> Tuple[Response, int]:
        """Handle validation errors (400)."""
        app.logger.info(
            f"Validation error: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "correlation_id": get_correlation_id(),
            },
        )
        return exception_to_response(exc)

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(exc: NotFoundError) -> Tuple[Response, int]:
        """Handle not found errors (404)."""
        app.logger.info(
            f"Resource not found: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "correlation_id": get_correlation_id(),
            },
        )
        return exception_to_response(exc)

    @app.errorhandler(AuthenticationError)
    def handle_auth_error(exc: AuthenticationError) -> Tuple[Response, int]:
        """Handle authentication errors (401)."""
        app.logger.warning(
            f"Authentication failed: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "correlation_id": get_correlation_id(),
            },
        )
        return exception_to_response(exc)

    @app.errorhandler(AuthorizationError)
    def handle_authz_error(exc: AuthorizationError) -> Tuple[Response, int]:
        """Handle authorization errors (403)."""
        app.logger.warning(
            f"Authorization denied: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "correlation_id": get_correlation_id(),
            },
        )
        return exception_to_response(exc)

    @app.errorhandler(ConflictError)
    def handle_conflict_error(exc: ConflictError) -> Tuple[Response, int]:
        """Handle conflict errors (409)."""
        app.logger.info(
            f"Resource conflict: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "correlation_id": get_correlation_id(),
            },
        )
        return exception_to_response(exc)

    @app.errorhandler(StorageError)
    def handle_storage_error(exc: StorageError) -> Tuple[Response, int]:
        """Handle storage errors (500)."""
        app.logger.error(
            f"Storage error: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "correlation_id": get_correlation_id(),
            },
        )
        return exception_to_response(exc)

    @app.errorhandler(DatabaseError)
    def handle_database_error(exc: DatabaseError) -> Tuple[Response, int]:
        """Handle database errors (500)."""
        app.logger.error(
            f"Database error: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "details": exc.details,
                "retryable": exc.is_retryable,
                "correlation_id": get_correlation_id(),
            },
        )
        return exception_to_response(exc)

    @app.errorhandler(RateLimitError)
    def handle_rate_limit_error(exc: RateLimitError) -> Tuple[Response, int]:
        """Handle rate limit errors (429)."""
        app.logger.warning(
            f"Rate limit exceeded: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "retry_after": exc.retry_after,
                "correlation_id": get_correlation_id(),
            },
        )
        response, status_code = exception_to_response(exc)
        if exc.retry_after:
            response.headers["Retry-After"] = str(exc.retry_after)
        return response, status_code

    @app.errorhandler(ServiceUnavailableError)
    def handle_service_unavailable(
        exc: ServiceUnavailableError,
    ) -> Tuple[Response, int]:
        """Handle service unavailable errors (503)."""
        app.logger.error(
            f"Service unavailable: {exc.message}",
            extra={
                "error_code": exc.error_code,
                "retry_after": exc.retry_after,
                "correlation_id": get_correlation_id(),
            },
        )
        response, status_code = exception_to_response(exc)
        if exc.retry_after:
            response.headers["Retry-After"] = str(exc.retry_after)
        return response, status_code

    # Handle standard HTTP errors
    # Note: We don't register global 404/405/500 handlers here because they
    # would override Flask's default HTML error pages for non-API routes.
    # API-specific error handling is done through the custom exception classes.
