"""
Tests for Prometheus metrics endpoint.

This module tests:
- /metrics endpoint
- MetricsCollector class
- Metric recording functions
"""

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
        assert (
            'http_requests_total{method="GET",endpoint="/test",status="200"} 2'
            in output
        )
        assert (
            'http_requests_total{method="POST",endpoint="/test",status="201"} 1'
            in output
        )

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
        collector.observe_http_duration(
            "/test", 0.05
        )  # Should be in 0.05 bucket and above

        output = collector.get_metrics_text()
        # Should have incremented buckets >= 0.05
        assert (
            'http_request_duration_seconds_bucket{endpoint="/test",le="0.05"} 1'
            in output
        )
        assert (
            'http_request_duration_seconds_bucket{endpoint="/test",le="0.1"} 1'
            in output
        )

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
        assert (
            'http_requests_total{method="GET",endpoint="/test",status="200"} 1000'
            in output
        )


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


class TestDisplayMetrics:
    """Tests for comprehensive display metrics."""

    def test_display_metrics_included_in_endpoint(self, app, client, auth_client):
        """Test that display metrics are included in /metrics endpoint."""
        # Create a display first
        auth_client.post(
            "/api/v1/displays",
            json={"name": "test-metrics-display"},
        )

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        # Check all metric HELP/TYPE definitions are present
        assert "# HELP display_info" in data
        assert "# TYPE display_info gauge" in data
        assert "# HELP display_online" in data
        assert "# TYPE display_online gauge" in data
        assert "# HELP display_resolution_width_pixels" in data
        assert "# HELP display_resolution_height_pixels" in data
        assert "# HELP display_rotation_degrees" in data
        assert "# HELP display_last_seen_timestamp_seconds" in data
        assert "# HELP display_heartbeat_interval_seconds" in data
        assert "# HELP display_missed_heartbeats" in data
        assert "# HELP display_sse_connected" in data
        assert "# HELP display_is_active" in data

    def test_display_info_metric_with_labels(self, app, client, auth_client):
        """Test display_info metric includes proper labels."""
        # Create a display
        auth_client.post(
            "/api/v1/displays",
            json={"name": "info-test-display"},
        )

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        # Should have display_info metric with labels
        assert 'display_info{display_id="' in data
        assert 'display_name="info-test-display"' in data
        assert 'slideshow_id="' in data
        assert 'slideshow_name="' in data

    def test_display_online_metric(self, app, client, auth_client):
        """Test display_online metric reports correct value."""
        from datetime import datetime, timezone

        from kiosk_show_replacement.models import Display, db

        # Create a display with recent heartbeat (should be online)
        auth_client.post(
            "/api/v1/displays",
            json={"name": "online-test-display"},
        )

        # Set last_seen_at to now (so display is online)
        with app.app_context():
            display = Display.query.filter_by(name="online-test-display").first()
            display.last_seen_at = datetime.now(timezone.utc)
            db.session.commit()

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        # Find the display_online line for our display
        for line in data.split("\n"):
            if "display_online" in line and "online-test-display" in line:
                assert "} 1" in line  # Should be online (value 1)
                break
        else:
            raise AssertionError(
                "display_online metric not found for online-test-display"
            )

    def test_display_offline_metric(self, app, client, auth_client):
        """Test display_online metric reports 0 for offline display."""
        from datetime import datetime, timedelta, timezone

        from kiosk_show_replacement.models import Display, db

        # Create a display
        auth_client.post(
            "/api/v1/displays",
            json={"name": "offline-test-display"},
        )

        # Set last_seen_at to long ago (so display is offline)
        with app.app_context():
            display = Display.query.filter_by(name="offline-test-display").first()
            display.last_seen_at = datetime.now(timezone.utc) - timedelta(hours=1)
            db.session.commit()

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        # Find the display_online line for our display
        for line in data.split("\n"):
            if "display_online" in line and "offline-test-display" in line:
                assert "} 0" in line  # Should be offline (value 0)
                break
        else:
            raise AssertionError(
                "display_online metric not found for offline-test-display"
            )

    def test_display_resolution_metrics(self, app, client, auth_client):
        """Test display resolution metrics are included when set."""
        # Create a display with resolution
        auth_client.post(
            "/api/v1/displays",
            json={
                "name": "resolution-test-display",
                "resolution_width": 1920,
                "resolution_height": 1080,
            },
        )

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        # Check resolution metrics
        assert 'display_resolution_width_pixels{display_id="' in data
        assert "} 1920" in data
        assert 'display_resolution_height_pixels{display_id="' in data
        assert "} 1080" in data

    def test_display_resolution_not_included_when_null(self, app, client, auth_client):
        """Test display resolution metrics are not included when resolution is null."""
        # Create a display without resolution
        auth_client.post(
            "/api/v1/displays",
            json={"name": "no-resolution-display"},
        )

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        # Should not have resolution metrics for this display (no value set)
        # The HELP and TYPE will still be present, but no metric line for this display
        for line in data.split("\n"):
            if (
                line.startswith("display_resolution_width_pixels")
                and "no-resolution-display" in line
            ):
                raise AssertionError(
                    "Resolution width metric should not be included for display "
                    "without resolution"
                )
            if (
                line.startswith("display_resolution_height_pixels")
                and "no-resolution-display" in line
            ):
                raise AssertionError(
                    "Resolution height metric should not be included for display "
                    "without resolution"
                )

    def test_display_rotation_metric(self, app, client, auth_client):
        """Test display rotation metric."""
        # Create a display with rotation
        auth_client.post(
            "/api/v1/displays",
            json={"name": "rotation-test-display", "rotation": 90},
        )

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        for line in data.split("\n"):
            if "display_rotation_degrees" in line and "rotation-test-display" in line:
                assert "} 90" in line
                break
        else:
            raise AssertionError(
                "display_rotation_degrees metric not found for rotation-test-display"
            )

    def test_display_heartbeat_interval_metric(self, app, client, auth_client):
        """Test display heartbeat interval metric."""
        from kiosk_show_replacement.models import Display, db

        # Create a display, then set heartbeat_interval (not settable via API)
        auth_client.post(
            "/api/v1/displays",
            json={"name": "heartbeat-interval-display"},
        )

        with app.app_context():
            display = Display.query.filter_by(name="heartbeat-interval-display").first()
            display.heartbeat_interval = 120
            db.session.commit()

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        for line in data.split("\n"):
            if (
                "display_heartbeat_interval_seconds" in line
                and "heartbeat-interval-display" in line
            ):
                assert "} 120" in line
                break
        else:
            raise AssertionError("display_heartbeat_interval_seconds metric not found")

    def test_display_missed_heartbeats_metric(self, app, client, auth_client):
        """Test display missed heartbeats metric."""
        from datetime import datetime, timedelta, timezone

        from kiosk_show_replacement.models import Display, db

        # Create a display
        auth_client.post(
            "/api/v1/displays",
            json={"name": "missed-hb-display", "heartbeat_interval": 60},
        )

        # Set last_seen_at to 5 minutes ago (should have ~5 missed heartbeats)
        with app.app_context():
            display = Display.query.filter_by(name="missed-hb-display").first()
            display.last_seen_at = datetime.now(timezone.utc) - timedelta(minutes=5)
            db.session.commit()

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        for line in data.split("\n"):
            if "display_missed_heartbeats" in line and "missed-hb-display" in line:
                # Should have some missed heartbeats (5 minutes / 60 seconds = 5)
                value = int(line.split("}")[-1].strip())
                assert value >= 4  # Allow some timing variance
                break
        else:
            raise AssertionError(
                "display_missed_heartbeats metric not found for missed-hb-display"
            )

    def test_display_sse_connected_metric(self, app, client, auth_client):
        """Test display_sse_connected metric."""
        # Create a display
        auth_client.post(
            "/api/v1/displays",
            json={"name": "sse-test-display"},
        )

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        # Display should have sse_connected = 0 (no SSE connection)
        for line in data.split("\n"):
            if "display_sse_connected" in line and "sse-test-display" in line:
                assert "} 0" in line  # Not SSE connected
                break
        else:
            raise AssertionError(
                "display_sse_connected metric not found for sse-test-display"
            )

    def test_display_is_active_metric(self, app, client, auth_client):
        """Test display_is_active metric."""
        # Create an active display
        auth_client.post(
            "/api/v1/displays",
            json={"name": "active-test-display", "is_active": True},
        )

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        for line in data.split("\n"):
            if "display_is_active" in line and "active-test-display" in line:
                assert "} 1" in line  # Should be active
                break
        else:
            raise AssertionError(
                "display_is_active metric not found for active-test-display"
            )

    def test_display_info_with_slideshow(
        self, app, client, auth_client, sample_slideshow
    ):
        """Test display_info metric includes slideshow when assigned."""
        from kiosk_show_replacement.models import Display, db

        # Create a display and assign the slideshow
        response = auth_client.post(
            "/api/v1/displays",
            json={"name": "slideshow-display"},
        )
        display_id = response.get_json()["data"]["id"]

        # Assign slideshow
        with app.app_context():
            display = db.session.get(Display, display_id)
            display.current_slideshow_id = sample_slideshow.id
            db.session.commit()
            slideshow_name = sample_slideshow.name

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        for line in data.split("\n"):
            if "display_info" in line and "slideshow-display" in line:
                assert f'slideshow_id="{sample_slideshow.id}"' in line
                assert f'slideshow_name="{slideshow_name}"' in line
                break
        else:
            raise AssertionError("display_info metric not found for slideshow-display")

    def test_display_last_seen_timestamp_metric(self, app, client, auth_client):
        """Test display_last_seen_timestamp_seconds metric."""
        from datetime import datetime, timezone

        from kiosk_show_replacement.models import Display, db

        # Create a display with a known timestamp
        auth_client.post(
            "/api/v1/displays",
            json={"name": "timestamp-display"},
        )

        known_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with app.app_context():
            display = Display.query.filter_by(name="timestamp-display").first()
            display.last_seen_at = known_time
            db.session.commit()

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        for line in data.split("\n"):
            if (
                "display_last_seen_timestamp_seconds" in line
                and "timestamp-display" in line
            ):
                # The timestamp should be the Unix epoch of our known time
                expected_timestamp = known_time.timestamp()
                assert f"}} {expected_timestamp}" in line
                break
        else:
            raise AssertionError(
                "display_last_seen_timestamp_seconds metric not found for "
                "timestamp-display"
            )

    def test_display_last_seen_not_included_when_null(self, app, client, auth_client):
        """Test display_last_seen_timestamp not included when never seen."""
        # Create a display without setting last_seen_at
        auth_client.post(
            "/api/v1/displays",
            json={"name": "never-seen-display"},
        )

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        # Should not have last_seen metric for this display
        for line in data.split("\n"):
            if (
                line.startswith("display_last_seen_timestamp_seconds")
                and "never-seen-display" in line
            ):
                raise AssertionError(
                    "Last seen timestamp should not be included for display "
                    "that was never seen"
                )

    def test_no_displays_returns_empty_metrics(self, app, client):
        """Test that with no displays, metrics endpoint still works."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.data.decode("utf-8")

        # Should still have HELP/TYPE definitions even with no displays
        assert "# HELP display_info" in data
        assert "# TYPE display_info gauge" in data

    def test_special_characters_in_display_name(self, app, client, auth_client):
        """Test that special characters in display names are properly escaped."""
        # Create a display with special characters that need escaping
        auth_client.post(
            "/api/v1/displays",
            json={"name": 'display-with-"quotes"'},
        )

        response = client.get("/metrics")
        data = response.data.decode("utf-8")

        # The quotes should be escaped
        assert 'display_name="display-with-\\"quotes\\""' in data
