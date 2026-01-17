"""
Database resilience utilities for the Kiosk Show Replacement application.

This module provides:
- Connection retry decorator with exponential backoff
- Circuit breaker pattern for persistent failures
- Transient error detection and handling
"""

import functools
import logging
import random
import threading
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Optional, Set, Type, TypeVar

from sqlalchemy.exc import (
    DBAPIError,
    DisconnectionError,
    InterfaceError,
    OperationalError,
    TimeoutError,
)

from .exceptions import DatabaseError
from .metrics import record_database_error

logger = logging.getLogger(__name__)

# Type variable for generic return type
T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


# SQLAlchemy exception types that indicate transient errors
TRANSIENT_ERRORS: Set[Type[Exception]] = {
    OperationalError,
    DisconnectionError,
    InterfaceError,
    TimeoutError,
}


def is_transient_error(exc: Exception) -> bool:
    """Check if an exception represents a transient database error.

    Transient errors are temporary failures that may succeed on retry,
    such as connection timeouts, network issues, or database restarts.

    Args:
        exc: The exception to check

    Returns:
        True if the error is transient and retryable
    """
    # Check if it's a known transient error type
    if isinstance(exc, tuple(TRANSIENT_ERRORS)):
        return True

    # Check for DBAPIError with transient-like messages
    if isinstance(exc, DBAPIError):
        error_msg = str(exc).lower()
        transient_indicators = [
            "connection",
            "timeout",
            "timed out",
            "temporarily unavailable",
            "too many connections",
            "deadlock",
            "lock wait timeout",
            "server has gone away",
            "lost connection",
            "can't connect",
            "connection refused",
            "no such host",
        ]
        return any(indicator in error_msg for indicator in transient_indicators)

    return False


class CircuitBreaker:
    """Circuit breaker for database operations.

    Prevents cascading failures by stopping requests to a failing service
    after a threshold of failures is reached.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests are rejected immediately
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3,
    ):
        """Initialize the circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            half_open_max_calls: Max calls allowed in half-open state
        """
        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max_calls = half_open_max_calls
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0

    @property
    def state(self) -> CircuitState:
        """Get the current circuit state."""
        with self._lock:
            self._check_state_transition()
            return self._state

    def _check_state_transition(self) -> None:
        """Check if state should transition based on time."""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = datetime.now(timezone.utc) - self._last_failure_time
            if elapsed >= timedelta(seconds=self._recovery_timeout):
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN state")

    def record_success(self) -> None:
        """Record a successful operation."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self._half_open_max_calls:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    logger.info("Circuit breaker closed after successful recovery")
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed operation."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now(timezone.utc)

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker re-opened after failure in half-open state"
                )
            elif (
                self._state == CircuitState.CLOSED
                and self._failure_count >= self._failure_threshold
            ):
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker opened after {self._failure_count} failures"
                )

    def allow_request(self) -> bool:
        """Check if a request should be allowed.

        Returns:
            True if request is allowed, False if circuit is open
        """
        with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.CLOSED:
                return True
            elif self._state == CircuitState.HALF_OPEN:
                return self._half_open_calls < self._half_open_max_calls
            else:  # OPEN
                return False

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0


# Global circuit breaker instance for database operations
db_circuit_breaker = CircuitBreaker()


def with_db_retry(
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 5.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    use_circuit_breaker: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for database operations with retry logic.

    Implements exponential backoff with optional jitter for retrying
    transient database errors.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff calculation
        jitter: Add random jitter to delay to prevent thundering herd
        use_circuit_breaker: Use circuit breaker to prevent cascading failures

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # Check circuit breaker
            if use_circuit_breaker and not db_circuit_breaker.allow_request():
                record_database_error()
                raise DatabaseError(
                    message="Database circuit breaker is open",
                    operation=func.__name__,
                    is_retryable=True,
                )

            last_exception: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if use_circuit_breaker:
                        db_circuit_breaker.record_success()
                    return result

                except Exception as exc:
                    last_exception = exc

                    # Only retry transient errors
                    if not is_transient_error(exc):
                        record_database_error()
                        if use_circuit_breaker:
                            db_circuit_breaker.record_failure()
                        raise

                    # Log the retry attempt
                    if attempt < max_retries:
                        delay = min(
                            base_delay * (exponential_base**attempt),
                            max_delay,
                        )
                        if jitter:
                            delay = delay * (0.5 + random.random())

                        logger.warning(
                            f"Database operation {func.__name__} failed (attempt "
                            f"{attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s: {exc}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Database operation {func.__name__} failed after "
                            f"{max_retries + 1} attempts: {exc}"
                        )
                        record_database_error()
                        if use_circuit_breaker:
                            db_circuit_breaker.record_failure()

            # All retries exhausted
            raise DatabaseError(
                message=f"Database operation failed after {max_retries + 1} attempts",
                operation=func.__name__,
                is_retryable=True,
                details={"last_error": str(last_exception)},
            )

        return wrapper

    return decorator


def execute_with_retry(
    operation: Callable[..., T],
    *args: Any,
    max_retries: int = 3,
    **kwargs: Any,
) -> T:
    """Execute a database operation with retry logic.

    Convenience function for one-off operations that don't use the decorator.

    Args:
        operation: The database operation to execute
        *args: Arguments to pass to the operation
        max_retries: Maximum number of retry attempts
        **kwargs: Keyword arguments to pass to the operation

    Returns:
        Result of the operation
    """

    @with_db_retry(max_retries=max_retries)
    def _execute() -> T:
        return operation(*args, **kwargs)

    return _execute()
