"""
Tests for error handling infrastructure.

This module tests:
- Custom exception classes
- API error response formatting
- Correlation ID middleware
- Error handlers
"""

from kiosk_show_replacement.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseError,
    ExternalServiceError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    StorageError,
    ValidationError,
)


class TestAppException:
    """Tests for the base AppException class."""

    def test_default_values(self):
        """Test default exception values."""
        exc = AppException()
        assert exc.message == "An unexpected error occurred"
        assert exc.error_code == "INTERNAL_ERROR"
        assert exc.status_code == 500
        assert exc.details == {}

    def test_custom_message(self):
        """Test exception with custom message."""
        exc = AppException(message="Custom error")
        assert exc.message == "Custom error"
        assert str(exc) == "Custom error"

    def test_custom_error_code(self):
        """Test exception with custom error code."""
        exc = AppException(error_code="CUSTOM_CODE")
        assert exc.error_code == "CUSTOM_CODE"

    def test_details(self):
        """Test exception with details."""
        details = {"field": "username", "reason": "too short"}
        exc = AppException(details=details)
        assert exc.details == details

    def test_to_dict(self):
        """Test exception serialization to dict."""
        exc = AppException(
            message="Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
        )
        result = exc.to_dict()
        assert result["code"] == "TEST_ERROR"
        assert result["message"] == "Test error"
        assert result["details"] == {"key": "value"}

    def test_to_dict_no_details(self):
        """Test exception serialization without details."""
        exc = AppException(message="Test error")
        result = exc.to_dict()
        assert "details" not in result


class TestValidationError:
    """Tests for ValidationError."""

    def test_default_values(self):
        """Test default validation error values."""
        exc = ValidationError()
        assert exc.message == "Validation failed"
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.status_code == 400

    def test_with_field(self):
        """Test validation error with field name."""
        exc = ValidationError(message="Invalid value", field="email")
        assert exc.message == "Invalid value"
        assert exc.details["field"] == "email"


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_default_values(self):
        """Test default not found error values."""
        exc = NotFoundError()
        assert exc.message == "Resource not found"
        assert exc.error_code == "NOT_FOUND"
        assert exc.status_code == 404

    def test_with_resource_info(self):
        """Test not found error with resource information."""
        exc = NotFoundError(
            message="Slideshow not found",
            resource_type="slideshow",
            resource_id=123,
        )
        assert exc.details["resource_type"] == "slideshow"
        assert exc.details["resource_id"] == 123


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_values(self):
        """Test default authentication error values."""
        exc = AuthenticationError()
        assert exc.message == "Authentication required"
        assert exc.error_code == "AUTHENTICATION_REQUIRED"
        assert exc.status_code == 401


class TestAuthorizationError:
    """Tests for AuthorizationError."""

    def test_default_values(self):
        """Test default authorization error values."""
        exc = AuthorizationError()
        assert exc.message == "Access denied"
        assert exc.error_code == "ACCESS_DENIED"
        assert exc.status_code == 403

    def test_with_permission(self):
        """Test authorization error with required permission."""
        exc = AuthorizationError(
            message="Cannot delete",
            required_permission="admin",
        )
        assert exc.details["required_permission"] == "admin"


class TestConflictError:
    """Tests for ConflictError."""

    def test_default_values(self):
        """Test default conflict error values."""
        exc = ConflictError()
        assert exc.message == "Resource conflict"
        assert exc.error_code == "CONFLICT"
        assert exc.status_code == 409

    def test_with_field(self):
        """Test conflict error with conflicting field."""
        exc = ConflictError(
            message="Name already exists",
            conflicting_field="name",
        )
        assert exc.details["conflicting_field"] == "name"


class TestStorageError:
    """Tests for StorageError."""

    def test_default_values(self):
        """Test default storage error values."""
        exc = StorageError()
        assert exc.message == "Storage operation failed"
        assert exc.error_code == "STORAGE_ERROR"
        assert exc.status_code == 500

    def test_with_operation_info(self):
        """Test storage error with operation details."""
        exc = StorageError(
            message="Upload failed",
            operation="upload",
            file_path="/uploads/image.png",
        )
        assert exc.details["operation"] == "upload"
        assert exc.details["file_path"] == "/uploads/image.png"


class TestDatabaseError:
    """Tests for DatabaseError."""

    def test_default_values(self):
        """Test default database error values."""
        exc = DatabaseError()
        assert exc.message == "Database operation failed"
        assert exc.error_code == "DATABASE_ERROR"
        assert exc.status_code == 500
        assert exc.is_retryable is False

    def test_retryable_error(self):
        """Test retryable database error."""
        exc = DatabaseError(
            message="Connection lost",
            operation="query",
            is_retryable=True,
        )
        assert exc.is_retryable is True
        assert exc.details["retryable"] is True


class TestExternalServiceError:
    """Tests for ExternalServiceError."""

    def test_default_values(self):
        """Test default external service error values."""
        exc = ExternalServiceError()
        assert exc.message == "External service unavailable"
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exc.status_code == 502
        assert exc.is_retryable is True

    def test_with_service_name(self):
        """Test external service error with service name."""
        exc = ExternalServiceError(
            message="API timeout",
            service_name="weather-api",
            is_retryable=False,
        )
        assert exc.details["service_name"] == "weather-api"
        assert exc.is_retryable is False


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_default_values(self):
        """Test default rate limit error values."""
        exc = RateLimitError()
        assert exc.message == "Rate limit exceeded"
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert exc.status_code == 429

    def test_with_retry_after(self):
        """Test rate limit error with retry-after."""
        exc = RateLimitError(retry_after=60)
        assert exc.retry_after == 60
        assert exc.details["retry_after"] == 60


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError."""

    def test_default_values(self):
        """Test default service unavailable error values."""
        exc = ServiceUnavailableError()
        assert exc.message == "Service temporarily unavailable"
        assert exc.error_code == "SERVICE_UNAVAILABLE"
        assert exc.status_code == 503

    def test_with_retry_after(self):
        """Test service unavailable error with retry-after."""
        exc = ServiceUnavailableError(
            message="Maintenance in progress",
            retry_after=300,
        )
        assert exc.retry_after == 300


class TestCorrelationIdMiddleware:
    """Tests for correlation ID middleware."""

    def test_correlation_id_generated(self, app, client):
        """Test that correlation ID is generated for requests."""
        response = client.get("/api/v1/status")
        assert "X-Correlation-ID" in response.headers
        # Verify it's a valid UUID format
        correlation_id = response.headers["X-Correlation-ID"]
        assert len(correlation_id) == 36  # UUID format

    def test_correlation_id_preserved(self, app, client):
        """Test that provided correlation ID is preserved."""
        custom_id = "test-correlation-id-12345"
        response = client.get(
            "/api/v1/status",
            headers={"X-Correlation-ID": custom_id},
        )
        assert response.headers["X-Correlation-ID"] == custom_id

    def test_correlation_id_in_error_response(self, app, auth_client):
        """Test that correlation ID appears in error responses."""
        response = auth_client.get("/api/v1/slideshows/99999")
        assert response.status_code == 404
        data = response.json
        # Correlation ID should be in error_info
        assert "error_info" in data
        assert "correlation_id" in data["error_info"]


class TestApiErrorResponse:
    """Tests for API error response formatting."""

    def test_error_response_structure(self, app, auth_client):
        """Test that error responses have the correct structure."""
        response = auth_client.get("/api/v1/slideshows/99999")
        assert response.status_code == 404
        data = response.json

        # Check backward-compatible fields
        assert data["success"] is False
        assert "error" in data
        assert isinstance(data["error"], str)  # String for compatibility
        assert "message" in data
        assert "errors" in data
        assert isinstance(data["errors"], list)

        # Check new structured error info
        assert "error_info" in data
        assert "code" in data["error_info"]
        assert "message" in data["error_info"]
        assert "correlation_id" in data["error_info"]

    def test_validation_error_response(self, app, auth_client):
        """Test validation error response."""
        response = auth_client.post(
            "/api/v1/slideshows",
            json={},  # Missing required fields
        )
        assert response.status_code == 400
        data = response.json
        assert data["success"] is False
        assert data["error_info"]["code"] == "VALIDATION_ERROR"

    def test_not_found_error_response(self, app, auth_client):
        """Test not found error response."""
        response = auth_client.get("/api/v1/slideshows/99999")
        assert response.status_code == 404
        data = response.json
        assert data["success"] is False
        assert data["error_info"]["code"] == "NOT_FOUND"

    def test_authentication_error_response(self, app, client):
        """Test authentication error response."""
        response = client.get("/api/v1/slideshows")
        assert response.status_code == 401
        data = response.json
        assert data["success"] is False
        assert data["error_info"]["code"] == "AUTHENTICATION_REQUIRED"


class TestSuccessResponse:
    """Tests for API success response formatting."""

    def test_success_response_structure(self, app, auth_client):
        """Test that success responses have the correct structure."""
        response = auth_client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json

        assert data["success"] is True
        assert "data" in data
        assert "message" in data

    def test_success_response_has_correlation_id(self, app, auth_client):
        """Test that success responses include correlation ID."""
        response = auth_client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json

        # Correlation ID should be in response
        assert "correlation_id" in data
