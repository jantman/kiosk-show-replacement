"""
Flask middleware for request handling.

This module provides middleware functions for the Flask application,
including correlation ID generation and request logging.
"""

import uuid
from typing import Optional

from flask import Flask, Response, g, request


class CorrelationIdMiddleware:
    """Middleware that adds correlation IDs to requests.

    The correlation ID is either extracted from the X-Correlation-ID header
    (if provided by the client) or generated automatically. It is then
    stored in Flask's g object and added to the response headers.
    """

    HEADER_NAME = "X-Correlation-ID"

    def __init__(self, app: Optional[Flask] = None):
        """Initialize the middleware.

        Args:
            app: Optional Flask application instance
        """
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize the middleware with a Flask app.

        Args:
            app: Flask application instance
        """
        app.before_request(self._before_request)
        app.after_request(self._after_request)

    def _before_request(self) -> None:
        """Extract or generate correlation ID before request processing."""
        # Try to get correlation ID from header, or generate a new one
        correlation_id = request.headers.get(self.HEADER_NAME)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Store in Flask's g object for access throughout request lifecycle
        g.correlation_id = correlation_id

    def _after_request(self, response: Response) -> Response:
        """Add correlation ID to response headers.

        Args:
            response: Flask response object

        Returns:
            Response with correlation ID header added
        """
        correlation_id = getattr(g, "correlation_id", None)
        if correlation_id:
            response.headers[self.HEADER_NAME] = correlation_id
        return response


def get_correlation_id() -> Optional[str]:
    """Get the correlation ID for the current request.

    This function can be called from anywhere within a request context
    to retrieve the current correlation ID.

    Returns:
        The correlation ID if within a request context, None otherwise
    """
    return getattr(g, "correlation_id", None)


def init_middleware(app: Flask) -> None:
    """Initialize all middleware for the application.

    Args:
        app: Flask application instance
    """
    # Initialize correlation ID middleware
    CorrelationIdMiddleware(app)

    # Add request logging if in debug mode
    if app.debug:

        @app.before_request
        def log_request_info() -> None:
            """Log incoming request details in debug mode."""
            correlation_id = get_correlation_id()
            app.logger.debug(
                f"Request: {request.method} {request.path}",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.path,
                    "remote_addr": request.remote_addr,
                },
            )

        @app.after_request
        def log_response_info(response: Response) -> Response:
            """Log outgoing response details in debug mode."""
            correlation_id = get_correlation_id()
            app.logger.debug(
                f"Response: {response.status_code}",
                extra={
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                },
            )
            return response
