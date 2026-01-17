"""
Prometheus metrics endpoint for the Kiosk Show Replacement application.

This module provides a /metrics endpoint that exposes application metrics
in Prometheus text format for monitoring and alerting.

Metrics exposed:
- http_requests_total: Total HTTP requests by method, endpoint, and status
- http_request_duration_seconds: Request duration histogram
- active_sse_connections: Current number of SSE connections
- database_errors_total: Count of database errors
- storage_errors_total: Count of storage errors
- display_heartbeat_age_seconds: Age of last display heartbeat
"""

import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, Flask, Response, g, request

metrics_bp = Blueprint("metrics", __name__)


class MetricsCollector:
    """Thread-safe metrics collector for Prometheus-style metrics."""

    def __init__(self):
        """Initialize the metrics collector."""
        self._lock = threading.Lock()

        # Counters
        self._http_requests_total: Dict[Tuple[str, str, int], int] = defaultdict(int)
        self._database_errors_total: int = 0
        self._storage_errors_total: int = 0

        # Gauges
        self._active_sse_connections: int = 0

        # Histograms (simplified - just track sum and count per bucket)
        self._http_request_duration_sum: Dict[str, float] = defaultdict(float)
        self._http_request_duration_count: Dict[str, int] = defaultdict(int)
        self._http_request_duration_buckets: Dict[str, Dict[float, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # Histogram bucket boundaries (in seconds)
        self._duration_buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def inc_http_requests(self, method: str, endpoint: str, status_code: int) -> None:
        """Increment HTTP request counter.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: Request endpoint path
            status_code: HTTP response status code
        """
        with self._lock:
            self._http_requests_total[(method, endpoint, status_code)] += 1

    def observe_http_duration(self, endpoint: str, duration: float) -> None:
        """Record HTTP request duration.

        Args:
            endpoint: Request endpoint path
            duration: Request duration in seconds
        """
        with self._lock:
            self._http_request_duration_sum[endpoint] += duration
            self._http_request_duration_count[endpoint] += 1

            # Update histogram bucket - only increment the smallest bucket that fits
            for bucket in self._duration_buckets:
                if duration <= bucket:
                    self._http_request_duration_buckets[endpoint][bucket] += 1
                    break  # Only increment one bucket, cumulative is computed at output
            # Note: values larger than max bucket will only appear in +Inf

    def inc_database_errors(self) -> None:
        """Increment database error counter."""
        with self._lock:
            self._database_errors_total += 1

    def inc_storage_errors(self) -> None:
        """Increment storage error counter."""
        with self._lock:
            self._storage_errors_total += 1

    def set_sse_connections(self, count: int) -> None:
        """Set the number of active SSE connections.

        Args:
            count: Current number of active connections
        """
        with self._lock:
            self._active_sse_connections = count

    def get_metrics_text(self) -> str:
        """Generate Prometheus text format metrics.

        Returns:
            Metrics in Prometheus text exposition format
        """
        lines: List[str] = []

        with self._lock:
            # HTTP requests total
            lines.append("# HELP http_requests_total Total number of HTTP requests")
            lines.append("# TYPE http_requests_total counter")
            for (method, endpoint, status), count in sorted(self._http_requests_total.items()):
                # Sanitize endpoint for label
                safe_endpoint = endpoint.replace('"', '\\"')
                lines.append(
                    f'http_requests_total{{method="{method}",endpoint="{safe_endpoint}",status="{status}"}} {count}'
                )

            # HTTP request duration
            lines.append("")
            lines.append("# HELP http_request_duration_seconds HTTP request duration in seconds")
            lines.append("# TYPE http_request_duration_seconds histogram")
            for endpoint in sorted(self._http_request_duration_sum.keys()):
                safe_endpoint = endpoint.replace('"', '\\"')
                # Bucket values
                cumulative = 0
                for bucket in self._duration_buckets:
                    cumulative += self._http_request_duration_buckets[endpoint].get(bucket, 0)
                    lines.append(
                        f'http_request_duration_seconds_bucket{{endpoint="{safe_endpoint}",le="{bucket}"}} {cumulative}'
                    )
                # +Inf bucket
                total_count = self._http_request_duration_count[endpoint]
                lines.append(
                    f'http_request_duration_seconds_bucket{{endpoint="{safe_endpoint}",le="+Inf"}} {total_count}'
                )
                # Sum and count
                lines.append(
                    f'http_request_duration_seconds_sum{{endpoint="{safe_endpoint}"}} {self._http_request_duration_sum[endpoint]:.6f}'
                )
                lines.append(
                    f'http_request_duration_seconds_count{{endpoint="{safe_endpoint}"}} {total_count}'
                )

            # Active SSE connections
            lines.append("")
            lines.append("# HELP active_sse_connections Number of active SSE connections")
            lines.append("# TYPE active_sse_connections gauge")
            lines.append(f"active_sse_connections {self._active_sse_connections}")

            # Database errors
            lines.append("")
            lines.append("# HELP database_errors_total Total number of database errors")
            lines.append("# TYPE database_errors_total counter")
            lines.append(f"database_errors_total {self._database_errors_total}")

            # Storage errors
            lines.append("")
            lines.append("# HELP storage_errors_total Total number of storage errors")
            lines.append("# TYPE storage_errors_total counter")
            lines.append(f"storage_errors_total {self._storage_errors_total}")

        return "\n".join(lines) + "\n"


# Global metrics collector instance
metrics_collector = MetricsCollector()


def init_metrics(app: Flask) -> None:
    """Initialize metrics collection middleware.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def start_timer() -> None:
        """Record request start time."""
        g.request_start_time = time.perf_counter()

    @app.after_request
    def record_metrics(response: Response) -> Response:
        """Record request metrics after each request."""
        # Skip metrics endpoint to avoid recursion
        if request.path == "/metrics":
            return response

        # Record request count
        endpoint = request.path
        method = request.method
        status_code = response.status_code
        metrics_collector.inc_http_requests(method, endpoint, status_code)

        # Record request duration
        start_time = getattr(g, "request_start_time", None)
        if start_time is not None:
            duration = time.perf_counter() - start_time
            metrics_collector.observe_http_duration(endpoint, duration)

        return response


def get_display_heartbeat_metrics() -> str:
    """Get metrics for display heartbeat ages.

    Returns:
        Prometheus-formatted metrics for display heartbeats
    """
    try:
        from .app import db
        from .models import Display

        lines: List[str] = []
        lines.append("# HELP display_heartbeat_age_seconds Seconds since last display heartbeat")
        lines.append("# TYPE display_heartbeat_age_seconds gauge")

        displays = Display.query.all()
        now = datetime.now(timezone.utc)

        for display in displays:
            if display.last_seen_at:
                age = (now - display.last_seen_at).total_seconds()
            else:
                age = -1  # Never seen

            safe_name = display.name.replace('"', '\\"')
            lines.append(
                f'display_heartbeat_age_seconds{{display_id="{display.id}",display_name="{safe_name}"}} {age:.1f}'
            )

        return "\n".join(lines) + "\n"
    except Exception:
        return ""


def get_sse_connection_metrics() -> None:
    """Update SSE connection count metric."""
    try:
        from .sse import sse_manager

        stats = sse_manager.get_connection_stats()
        metrics_collector.set_sse_connections(stats.get("total_connections", 0))
    except Exception:
        pass


@metrics_bp.route("/metrics")
def metrics_endpoint() -> Response:
    """Prometheus metrics endpoint.

    Returns metrics in Prometheus text exposition format.
    """
    # Update dynamic metrics
    get_sse_connection_metrics()

    # Collect all metrics
    output = metrics_collector.get_metrics_text()

    # Add display heartbeat metrics
    output += "\n" + get_display_heartbeat_metrics()

    return Response(output, mimetype="text/plain; charset=utf-8")


# Convenience functions for recording metrics from other modules
def record_database_error() -> None:
    """Record a database error occurrence."""
    metrics_collector.inc_database_errors()


def record_storage_error() -> None:
    """Record a storage error occurrence."""
    metrics_collector.inc_storage_errors()
