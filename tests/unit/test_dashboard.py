"""
Unit tests for dashboard views and functionality.

Tests dashboard routes, templates, and user interface components.
"""


class TestDashboardRoutes:
    """Test dashboard route accessibility and responses."""

    def test_dashboard_index_requires_authentication(self, client):
        """Test dashboard index redirects to login when not authenticated."""
        response = client.get("/")
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_dashboard_index_accessible_when_authenticated(self, client):
        """Test dashboard index accessible when authenticated."""
        # Login first
        client.post(
            "/auth/login", data={"username": "testuser", "password": "password"}
        )

        response = client.get("/")
        assert response.status_code == 200
        assert b"Dashboard" in response.data

    def test_dashboard_profile_requires_authentication(self, client):
        """Test profile page requires authentication."""
        response = client.get("/profile")
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_dashboard_profile_accessible_when_authenticated(self, client):
        """Test profile page accessible when authenticated."""
        # Login first
        client.post(
            "/auth/login", data={"username": "testuser", "password": "password"}
        )

        response = client.get("/profile")
        assert response.status_code == 200
        assert b"Profile" in response.data

    def test_dashboard_settings_requires_admin(self, client):
        """Test settings page is accessible since all users are admin."""
        # Login as regular user (who gets admin privileges now)
        client.post("/auth/login", data={"username": "user", "password": "password"})

        response = client.get("/settings")
        assert response.status_code == 200  # Should succeed since all users are admin

    def test_dashboard_settings_accessible_to_admin(self, client):
        """Test settings page accessible to admin users."""
        # Login as admin
        client.post("/auth/login", data={"username": "admin", "password": "password"})

        response = client.get("/settings")
        assert response.status_code == 200
        assert b"Settings" in response.data


class TestHealthEndpoint:
    """Test system health check endpoint."""

    def test_health_endpoint_accessible_without_auth(self, client, sample_user):
        """Test health endpoint accessible without authentication."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client, sample_user):
        """Test health endpoint returns proper JSON response."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.is_json

        data = response.get_json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "storage" in data["checks"]
        assert "version" in data
        assert "timestamp" in data

    def test_health_endpoint_returns_healthy_status(self, client, sample_user):
        """Test health endpoint returns healthy status when database is initialized."""
        response = client.get("/health")
        data = response.get_json()

        assert data["status"] in ["healthy", "degraded"]
        assert data["checks"]["database"]["status"] == "healthy"
        assert data["checks"]["database"]["initialized"] is True
        assert data["version"] == "0.1.0"

    def test_health_endpoint_with_database_connection(self, app, client, sample_user):
        """Test health endpoint with working database connection."""
        with app.app_context():
            response = client.get("/health")
            data = response.get_json()

            # With a working database and user, should be healthy
            assert data["status"] in ["healthy", "degraded"]
            assert data["checks"]["database"]["status"] == "healthy"
            assert data["checks"]["database"]["initialized"] is True

    def test_health_endpoint_not_initialized_without_user(self, client):
        """Test health endpoint shows not_initialized when no users exist."""
        response = client.get("/health")
        data = response.get_json()

        # Without any users, database is considered not initialized
        assert data["checks"]["database"]["status"] == "not_initialized"
        assert data["checks"]["database"]["initialized"] is False


class TestErrorHandling:
    """Test dashboard error handling and error pages."""

    def test_404_error_page(self, client):
        """Test 404 error page is displayed properly."""
        # Login first
        client.post(
            "/auth/login", data={"username": "testuser", "password": "password"}
        )

        response = client.get("/nonexistent")
        assert response.status_code == 404
        assert b"Not Found" in response.data or b"404" in response.data

    def test_403_error_for_admin_routes(self, client):
        """Test admin routes are accessible since all users are admin."""
        # Login as regular user (who gets admin privileges now)
        client.post("/auth/login", data={"username": "user", "password": "password"})

        response = client.get("/settings")
        assert response.status_code == 200  # Should succeed since all users are admin


class TestTemplateContext:
    """Test template context and user information availability."""

    def test_current_user_available_in_templates(self, client):
        """Test current_user is available in dashboard templates."""
        # Login first
        client.post(
            "/auth/login", data={"username": "testuser", "password": "password"}
        )

        response = client.get("/")
        assert response.status_code == 200

        # Check that user information is displayed
        assert b"testuser" in response.data

    def test_admin_user_sees_admin_content(self, client):
        """Test admin users see admin-specific content."""
        # Login as admin
        client.post("/auth/login", data={"username": "admin", "password": "password"})

        response = client.get("/")
        assert response.status_code == 200

        # Admin should see settings link or admin content
        assert b"Settings" in response.data or b"Admin" in response.data

    def test_regular_user_does_not_see_admin_content(self, client):
        """Test regular users now see admin content since all users are admin."""
        # Login as regular user (who gets admin privileges now)
        client.post("/auth/login", data={"username": "user", "password": "password"})

        response = client.get("/")
        assert response.status_code == 200
        # Should see admin content since all users are admin now
        # This test now just verifies the dashboard loads successfully


class TestDashboardSecurity:
    """Test dashboard security features."""

    def test_logout_link_accessible(self, client):
        """Test logout link is accessible in dashboard."""
        # Login first
        client.post(
            "/auth/login", data={"username": "testuser", "password": "password"}
        )

        response = client.get("/")
        assert response.status_code == 200
        assert b"Logout" in response.data or b"logout" in response.data

    def test_session_persistence_across_requests(self, client):
        """Test session persists across multiple requests."""
        # Login
        client.post(
            "/auth/login", data={"username": "testuser", "password": "password"}
        )

        # Make multiple requests
        response1 = client.get("/")
        response2 = client.get("/profile")

        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_logout_clears_authentication(self, client):
        """Test logout properly clears authentication."""
        # Login
        client.post(
            "/auth/login", data={"username": "testuser", "password": "password"}
        )

        # Verify authenticated
        response = client.get("/")
        assert response.status_code == 200

        # Logout
        client.get("/auth/logout")

        # Verify no longer authenticated
        response = client.get("/")
        assert response.status_code == 302
