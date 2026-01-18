"""
Structured logging configuration for the Kiosk Show Replacement application.

This module provides:
- JSON formatted logging for production environments
- Correlation ID inclusion in all log entries
- Request/response logging middleware
- Log level configuration
"""

import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict

from flask import Flask, Response, g, has_request_context, request


class CorrelationIdFilter(logging.Filter):
    """Logging filter that adds correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id to the log record.

        Args:
            record: The log record to modify

        Returns:
            True (always allows the record through)
        """
        if has_request_context():
            record.correlation_id = getattr(g, "correlation_id", "-")
        else:
            record.correlation_id = "-"
        return True


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging.

    Formats log records as JSON objects for easy parsing by log aggregation
    systems like ELK, Splunk, or CloudWatch.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON-formatted log string
        """
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "-"),
        }

        # Add location info
        if record.pathname:
            log_entry["source"] = {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from the record
        extra_keys = set(record.__dict__.keys()) - {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "correlation_id",
            "message",
            "taskName",
        }

        for key in extra_keys:
            value = getattr(record, key)
            # Only include JSON-serializable values
            try:
                json.dumps(value)
                log_entry[key] = value
            except TypeError, ValueError:
                log_entry[key] = str(value)

        return json.dumps(log_entry)


class StandardFormatter(logging.Formatter):
    """Standard text formatter with correlation ID support.

    Used for development environments where human-readable logs are preferred.
    """

    def __init__(self) -> None:
        """Initialize the formatter with a standard format."""
        super().__init__(
            fmt="%(asctime)s [%(levelname)s] [%(correlation_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def configure_logging(app: Flask, json_format: bool = False) -> None:
    """Configure application logging.

    Sets up logging handlers, formatters, and filters based on the environment.

    Args:
        app: Flask application instance
        json_format: If True, use JSON format; otherwise use standard text format
    """
    # Get or create the app logger
    logger = app.logger

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)

    # Set formatter based on environment
    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(StandardFormatter())

    # Add correlation ID filter
    handler.addFilter(CorrelationIdFilter())

    # Set log level from config
    log_level = app.config.get("LOG_LEVEL", "INFO")
    handler.setLevel(getattr(logging, log_level, logging.INFO))
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Add handler
    logger.addHandler(handler)

    # Also configure werkzeug logger
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.handlers = []
    werkzeug_handler = logging.StreamHandler(sys.stdout)
    werkzeug_handler.setFormatter(handler.formatter)
    werkzeug_handler.addFilter(CorrelationIdFilter())
    werkzeug_logger.addHandler(werkzeug_handler)

    # Don't propagate to root logger
    logger.propagate = False
    werkzeug_logger.propagate = False


def init_request_logging(app: Flask) -> None:
    """Initialize request/response logging middleware.

    Logs request start and completion with timing information.

    Args:
        app: Flask application instance
    """
    # Skip if request logging is disabled
    if not app.config.get("LOG_REQUESTS", True):
        return

    @app.before_request
    def log_request_start() -> None:
        """Log the start of each request."""
        # Skip health and metrics endpoints to reduce log noise
        if request.path in ["/health", "/health/live", "/health/ready", "/metrics"]:
            return

        g.request_log_start_time = time.perf_counter()

        app.logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                "event": "request_start",
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.user_agent.string if request.user_agent else None,
            },
        )

    @app.after_request
    def log_request_complete(response: Response) -> Response:
        """Log the completion of each request."""
        # Skip health and metrics endpoints
        if request.path in ["/health", "/health/live", "/health/ready", "/metrics"]:
            return response

        duration = None
        start_time = getattr(g, "request_log_start_time", None)
        if start_time:
            duration = time.perf_counter() - start_time

        # Determine log level based on status code
        if response.status_code >= 500:
            log_func = app.logger.error
        elif response.status_code >= 400:
            log_func = app.logger.warning
        else:
            log_func = app.logger.info

        log_func(
            f"Request completed: {request.method} {request.path} -> {response.status_code}",
            extra={
                "event": "request_complete",
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2) if duration else None,
                "content_length": response.content_length,
            },
        )

        return response


def init_logging(app: Flask) -> None:
    """Initialize all logging for the application.

    Args:
        app: Flask application instance
    """
    # Use JSON format in production, text format otherwise
    use_json = app.config.get("LOG_JSON", not app.debug)
    configure_logging(app, json_format=use_json)
    init_request_logging(app)
