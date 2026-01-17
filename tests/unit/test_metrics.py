"""
Tests for Prometheus metrics endpoint.

This module tests:
- /metrics endpoint
- MetricsCollector class
- Metric recording functions
"""

import pytest

from kiosk_show_replacement.metrics import (
    MetricsCollector,
    metrics_collector,
    record_database_error,
    record_storage_error,
)


class TestMetricsEndpoint:
    """Tests for the /metrics endpoint."""

    def test_metrics_endpoint_returns_200(self, app, client):
        """Test metrics endpoint returns 200."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_endpoint_returns_text_plain(self, app, client):
        """Test metrics endpoint returns text/plain content type."""
        response = client.get("/metrics")
        assert "text/plain" in response.content_type

    def test_metrics_contains_http_requests_help(self, app, client):
        """Test metrics output contains HTTP requests metric definition."""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        assert "# HELP http_requests_total" in data
        assert "# TYPE http_requests_total counter" in data

    def test_metrics_contains_http_duration_help(self, app, client):
        """Test metrics output contains HTTP duration metric definition."""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        assert "# HELP http_request_duration_seconds" in data
        assert "# TYPE http_request_duration_seconds histogram" in data

    def test_metrics_contains_sse_connections(self, app, client):
        """Test metrics output contains SSE connections gauge."""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        assert "# HELP active_sse_connections" in data
        assert "# TYPE active_sse_connections gauge" in data
        assert "active_sse_connections" in data

    def test_metrics_contains_error_counters(self, app, client):
        """Test metrics output contains error counters."""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        assert "database_errors_total" in data
        assert "storage_errors_total" in data

    def test_metrics_records_request(self, app, client):
        """Test that making a request records metrics."""
        # Make a request to trigger metrics
        client.get("/health")

        # Check metrics endpoint
        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        # Should have recorded the /health request
        assert 'endpoint="/health"' in data


class TestMetricsCollector:
    """Tests for the MetricsCollector class."""

    def test_inc_http_requests(self):
        """Test incrementing HTTP request counter."""
        collector = MetricsCollector()
        collector.inc_http_requests("GET", "/test", 200)
        collector.inc_http_requests("GET", "/test", 200)
        collector.inc_http_requests("POST", "/test", 201)

        output = collector.get_metrics_text()
        assert 'http_requests_total{method="GET",endpoint="/test",status="200"} 2' in output
        assert 'http_requests_total{method="POST",endpoint="/test",status="201"} 1' in output

    def test_observe_http_duration(self):
        """Test recording HTTP request duration."""
        collector = MetricsCollector()
        collector.observe_http_duration("/test", 0.1)
        collector.observe_http_duration("/test", 0.2)

        output = collector.get_metrics_text()
        assert 'http_request_duration_seconds_sum{endpoint="/test"}' in output
        assert 'http_request_duration_seconds_count{endpoint="/test"} 2' in output

    def test_observe_http_duration_buckets(self):
        """Test HTTP duration histogram buckets."""
        collector = MetricsCollector()
        collector.observe_http_duration("/test", 0.05)  # Should be in 0.05 bucket and above

        output = collector.get_metrics_text()
        # Should have incremented buckets >= 0.05
        assert 'http_request_duration_seconds_bucket{endpoint="/test",le="0.05"} 1' in output
        assert 'http_request_duration_seconds_bucket{endpoint="/test",le="0.1"} 1' in output

    def test_inc_database_errors(self):
        """Test incrementing database error counter."""
        collector = MetricsCollector()
        collector.inc_database_errors()
        collector.inc_database_errors()

        output = collector.get_metrics_text()
        assert "database_errors_total 2" in output

    def test_inc_storage_errors(self):
        """Test incrementing storage error counter."""
        collector = MetricsCollector()
        collector.inc_storage_errors()

        output = collector.get_metrics_text()
        assert "storage_errors_total 1" in output

    def test_set_sse_connections(self):
        """Test setting SSE connection count."""
        collector = MetricsCollector()
        collector.set_sse_connections(5)

        output = collector.get_metrics_text()
        assert "active_sse_connections 5" in output

        # Update the count
        collector.set_sse_connections(3)
        output = collector.get_metrics_text()
        assert "active_sse_connections 3" in output

    def test_thread_safety(self):
        """Test that collector is thread-safe."""
        import threading

        collector = MetricsCollector()
        errors = []

        def increment_requests():
            try:
                for _ in range(100):
                    collector.inc_http_requests("GET", "/test", 200)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=increment_requests) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        output = collector.get_metrics_text()
        assert 'http_requests_total{method="GET",endpoint="/test",status="200"} 1000' in output


class TestMetricRecordingFunctions:
    """Tests for convenience metric recording functions."""

    def test_record_database_error(self, app):
        """Test recording database error via convenience function."""
        # Reset collector state by recording the current count
        with app.app_context():
            initial_output = metrics_collector.get_metrics_text()
            initial_count = int(
                [
                    line.split()[-1]
                    for line in initial_output.split("\n")
                    if line.startswith("database_errors_total")
                ][0]
            )

            record_database_error()

            output = metrics_collector.get_metrics_text()
            new_count = int(
                [
                    line.split()[-1]
                    for line in output.split("\n")
                    if line.startswith("database_errors_total")
                ][0]
            )
            assert new_count == initial_count + 1

    def test_record_storage_error(self, app):
        """Test recording storage error via convenience function."""
        with app.app_context():
            initial_output = metrics_collector.get_metrics_text()
            initial_count = int(
                [
                    line.split()[-1]
                    for line in initial_output.split("\n")
                    if line.startswith("storage_errors_total")
                ][0]
            )

            record_storage_error()

            output = metrics_collector.get_metrics_text()
            new_count = int(
                [
                    line.split()[-1]
                    for line in output.split("\n")
                    if line.startswith("storage_errors_total")
                ][0]
            )
            assert new_count == initial_count + 1


class TestDisplayHeartbeatMetrics:
    """Tests for display heartbeat metrics."""

    def test_display_heartbeat_metrics_included(self, app, client, auth_client):
        """Test that display heartbeat metrics are included."""
        # Create a display first
        auth_client.post(
            "/api/v1/displays",
            json={"name": "metrics-test-display"},
        )

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        assert "# HELP display_heartbeat_age_seconds" in data
        assert "# TYPE display_heartbeat_age_seconds gauge" in data
