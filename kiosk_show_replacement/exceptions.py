"""
Custom exception hierarchy for the Kiosk Show Replacement application.

This module provides a comprehensive set of application-specific exceptions
that map to HTTP status codes and provide standardized error responses.
Each exception includes an error code, message, and optional details for
debugging and client consumption.
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception for all application-specific errors.

    All custom exceptions should inherit from this class to ensure consistent
    error handling and response formatting throughout the application.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code (e.g., 'VALIDATION_ERROR')
        status_code: HTTP status code to return
        details: Optional dictionary with additional error details
    """

    message: str = "An unexpected error occurred"
    error_code: str = "INTERNAL_ERROR"
    status_code: int = 500

    def __init__(
        self,
        message: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the exception.

        Args:
            message: Override the default message
            error_code: Override the default error code
            details: Additional error details for debugging
        """
        self.message = message or self.__class__.message
        self.error_code = error_code or self.__class__.error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON response.

        Returns:
            Dictionary containing error information
        """
        result: Dict[str, Any] = {
            "code": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


class ValidationError(AppException):
    """Exception for request validation failures.

    Raised when request data fails validation (missing fields, invalid format,
    constraint violations, etc.).
    """

    message = "Validation failed"
    error_code = "VALIDATION_ERROR"
    status_code = 400

    def __init__(
        self,
        message: Optional[str] = None,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize validation error.

        Args:
            message: Error message
            field: Name of the field that failed validation
            details: Additional validation details
        """
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message=message, details=details)


class NotFoundError(AppException):
    """Exception for resource not found errors.

    Raised when a requested resource does not exist or has been deleted.
    """

    message = "Resource not found"
    error_code = "NOT_FOUND"
    status_code = 404

    def __init__(
        self,
        message: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize not found error.

        Args:
            message: Error message
            resource_type: Type of resource (e.g., 'slideshow', 'display')
            resource_id: ID of the resource that was not found
            details: Additional details
        """
        details = details or {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id is not None:
            details["resource_id"] = resource_id
        super().__init__(message=message, details=details)


class AuthenticationError(AppException):
    """Exception for authentication failures.

    Raised when a user fails to authenticate (missing or invalid credentials).
    """

    message = "Authentication required"
    error_code = "AUTHENTICATION_REQUIRED"
    status_code = 401


class AuthorizationError(AppException):
    """Exception for authorization failures.

    Raised when an authenticated user lacks permission to perform an action.
    """

    message = "Access denied"
    error_code = "ACCESS_DENIED"
    status_code = 403

    def __init__(
        self,
        message: Optional[str] = None,
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize authorization error.

        Args:
            message: Error message
            required_permission: The permission that was required
            details: Additional details
        """
        details = details or {}
        if required_permission:
            details["required_permission"] = required_permission
        super().__init__(message=message, details=details)


class ConflictError(AppException):
    """Exception for resource conflict errors.

    Raised when an operation conflicts with the current state of a resource
    (e.g., duplicate names, integrity constraint violations).
    """

    message = "Resource conflict"
    error_code = "CONFLICT"
    status_code = 409

    def __init__(
        self,
        message: Optional[str] = None,
        conflicting_field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize conflict error.

        Args:
            message: Error message
            conflicting_field: Name of the field causing the conflict
            details: Additional details
        """
        details = details or {}
        if conflicting_field:
            details["conflicting_field"] = conflicting_field
        super().__init__(message=message, details=details)


class StorageError(AppException):
    """Exception for file storage errors.

    Raised when file operations fail (upload, read, delete, disk space, etc.).
    """

    message = "Storage operation failed"
    error_code = "STORAGE_ERROR"
    status_code = 500

    def __init__(
        self,
        message: Optional[str] = None,
        operation: Optional[str] = None,
        file_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize storage error.

        Args:
            message: Error message
            operation: The operation that failed (e.g., 'upload', 'delete')
            file_path: Path to the file involved (if applicable)
            details: Additional details
        """
        details = details or {}
        if operation:
            details["operation"] = operation
        if file_path:
            details["file_path"] = file_path
        super().__init__(message=message, details=details)


class DatabaseError(AppException):
    """Exception for database errors.

    Raised when database operations fail (connection, query, transaction, etc.).
    """

    message = "Database operation failed"
    error_code = "DATABASE_ERROR"
    status_code = 500

    def __init__(
        self,
        message: Optional[str] = None,
        operation: Optional[str] = None,
        is_retryable: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize database error.

        Args:
            message: Error message
            operation: The operation that failed
            is_retryable: Whether the operation can be retried
            details: Additional details
        """
        details = details or {}
        if operation:
            details["operation"] = operation
        details["retryable"] = is_retryable
        self.is_retryable = is_retryable
        super().__init__(message=message, details=details)


class ExternalServiceError(AppException):
    """Exception for external service failures.

    Raised when an external service (API, third-party integration) fails.
    """

    message = "External service unavailable"
    error_code = "EXTERNAL_SERVICE_ERROR"
    status_code = 502

    def __init__(
        self,
        message: Optional[str] = None,
        service_name: Optional[str] = None,
        is_retryable: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize external service error.

        Args:
            message: Error message
            service_name: Name of the external service
            is_retryable: Whether the operation can be retried
            details: Additional details
        """
        details = details or {}
        if service_name:
            details["service_name"] = service_name
        details["retryable"] = is_retryable
        self.is_retryable = is_retryable
        super().__init__(message=message, details=details)


class RateLimitError(AppException):
    """Exception for rate limit exceeded.

    Raised when a client exceeds the allowed request rate.
    """

    message = "Rate limit exceeded"
    error_code = "RATE_LIMIT_EXCEEDED"
    status_code = 429

    def __init__(
        self,
        message: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds until the client can retry
            details: Additional details
        """
        details = details or {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        self.retry_after = retry_after
        super().__init__(message=message, details=details)


class ServiceUnavailableError(AppException):
    """Exception for service unavailability.

    Raised when the service is temporarily unavailable (maintenance, overload).
    """

    message = "Service temporarily unavailable"
    error_code = "SERVICE_UNAVAILABLE"
    status_code = 503

    def __init__(
        self,
        message: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize service unavailable error.

        Args:
            message: Error message
            retry_after: Seconds until service may be available
            details: Additional details
        """
        details = details or {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        self.retry_after = retry_after
        super().__init__(message=message, details=details)
