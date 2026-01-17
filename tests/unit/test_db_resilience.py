"""
Tests for database resilience utilities.

This module tests:
- with_db_retry decorator
- CircuitBreaker class
- Transient error detection
"""

import time

import pytest
from sqlalchemy.exc import DisconnectionError, IntegrityError, OperationalError

from kiosk_show_replacement.db_resilience import (
    CircuitBreaker,
    CircuitState,
    db_circuit_breaker,
    execute_with_retry,
    is_transient_error,
    with_db_retry,
)
from kiosk_show_replacement.exceptions import DatabaseError


class TestIsTransientError:
    """Tests for transient error detection."""

    def test_operational_error_is_transient(self):
        """Test OperationalError is detected as transient."""
        exc = OperationalError("statement", {}, None)
        assert is_transient_error(exc) is True

    def test_disconnection_error_is_transient(self):
        """Test DisconnectionError is detected as transient."""
        exc = DisconnectionError()
        assert is_transient_error(exc) is True

    def test_integrity_error_is_not_transient(self):
        """Test IntegrityError is not transient."""
        exc = IntegrityError("statement", {}, None)
        assert is_transient_error(exc) is False

    def test_connection_message_is_transient(self):
        """Test error with connection-related message is transient."""
        exc = OperationalError("connection refused", {}, None)
        assert is_transient_error(exc) is True

    def test_timeout_message_is_transient(self):
        """Test error with timeout message is transient."""
        exc = OperationalError("query timed out", {}, None)
        assert is_transient_error(exc) is True

    def test_generic_exception_is_not_transient(self):
        """Test generic exception is not transient."""
        exc = ValueError("some error")
        assert is_transient_error(exc) is False


class TestCircuitBreaker:
    """Tests for the CircuitBreaker class."""

    def test_initial_state_is_closed(self):
        """Test circuit breaker starts in closed state."""
        cb = CircuitBreaker()
        assert cb.state == CircuitState.CLOSED

    def test_opens_after_threshold_failures(self):
        """Test circuit opens after reaching failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)

        for _ in range(3):
            cb.record_failure()

        assert cb.state == CircuitState.OPEN

    def test_stays_closed_below_threshold(self):
        """Test circuit stays closed below failure threshold."""
        cb = CircuitBreaker(failure_threshold=5)

        for _ in range(4):
            cb.record_failure()

        assert cb.state == CircuitState.CLOSED

    def test_success_resets_failure_count(self):
        """Test success resets failure count in closed state."""
        cb = CircuitBreaker(failure_threshold=3)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()  # Reset
        cb.record_failure()
        cb.record_failure()

        assert cb.state == CircuitState.CLOSED

    def test_transitions_to_half_open_after_timeout(self):
        """Test circuit transitions to half-open after recovery timeout."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        cb.record_failure()
        # Check internal state directly without triggering transition
        assert cb._state == CircuitState.OPEN

        # After timeout, should transition to half-open
        time.sleep(1.1)
        assert cb.state == CircuitState.HALF_OPEN

    def test_closes_after_successful_half_open_calls(self):
        """Test circuit closes after successful calls in half-open state."""
        cb = CircuitBreaker(
            failure_threshold=1, recovery_timeout=0, half_open_max_calls=2
        )

        cb.record_failure()
        time.sleep(0.1)  # Wait for half-open

        assert cb.state == CircuitState.HALF_OPEN
        cb.record_success()
        cb.record_success()

        assert cb.state == CircuitState.CLOSED

    def test_reopens_on_failure_in_half_open(self):
        """Test circuit reopens on failure in half-open state."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        cb.record_failure()
        time.sleep(1.1)  # Wait for half-open
        assert cb.state == CircuitState.HALF_OPEN

        cb.record_failure()
        # Check internal state directly
        assert cb._state == CircuitState.OPEN

    def test_allow_request_when_closed(self):
        """Test requests are allowed when circuit is closed."""
        cb = CircuitBreaker()
        assert cb.allow_request() is True

    def test_reject_request_when_open(self):
        """Test requests are rejected when circuit is open."""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=60)
        cb.record_failure()

        assert cb.allow_request() is False

    def test_reset_clears_state(self):
        """Test reset returns circuit to initial state."""
        cb = CircuitBreaker(failure_threshold=1)
        cb.record_failure()
        assert cb.state == CircuitState.OPEN

        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.allow_request() is True


class TestWithDbRetry:
    """Tests for the with_db_retry decorator."""

    def test_returns_result_on_success(self):
        """Test decorator returns result on successful execution."""

        @with_db_retry(max_retries=3, use_circuit_breaker=False)
        def successful_operation():
            return "success"

        result = successful_operation()
        assert result == "success"

    def test_retries_on_transient_error(self):
        """Test decorator retries on transient errors."""
        call_count = 0

        @with_db_retry(max_retries=3, base_delay=0.01, use_circuit_breaker=False)
        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise OperationalError("connection lost", {}, None)
            return "success"

        result = flaky_operation()
        assert result == "success"
        assert call_count == 3

    def test_raises_on_non_transient_error(self):
        """Test decorator raises immediately on non-transient errors."""
        call_count = 0

        @with_db_retry(max_retries=3, use_circuit_breaker=False)
        def bad_operation():
            nonlocal call_count
            call_count += 1
            raise IntegrityError("duplicate key", {}, None)

        with pytest.raises(IntegrityError):
            bad_operation()

        assert call_count == 1  # No retries

    def test_raises_database_error_after_max_retries(self):
        """Test decorator raises DatabaseError after exhausting retries."""

        @with_db_retry(max_retries=2, base_delay=0.01, use_circuit_breaker=False)
        def always_fails():
            raise OperationalError("connection refused", {}, None)

        with pytest.raises(DatabaseError) as exc_info:
            always_fails()

        assert "failed after 3 attempts" in str(exc_info.value)

    def test_respects_circuit_breaker(self):
        """Test decorator respects circuit breaker state."""

        @with_db_retry(max_retries=1, use_circuit_breaker=True)
        def operation():
            return "success"

        # Open the global circuit breaker
        db_circuit_breaker.reset()  # Start fresh
        for _ in range(5):
            db_circuit_breaker.record_failure()

        with pytest.raises(DatabaseError) as exc_info:
            operation()

        assert "circuit breaker is open" in str(exc_info.value).lower()

        # Reset for other tests
        db_circuit_breaker.reset()


class TestExecuteWithRetry:
    """Tests for the execute_with_retry function."""

    def test_executes_operation(self):
        """Test function executes the provided operation."""

        def my_operation(x, y):
            return x + y

        result = execute_with_retry(my_operation, 1, 2)
        assert result == 3

    def test_retries_transient_errors(self):
        """Test function retries on transient errors."""
        call_count = 0

        def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise OperationalError("timeout", {}, None)
            return "done"

        # Reset circuit breaker
        db_circuit_breaker.reset()

        result = execute_with_retry(flaky_operation, max_retries=3)
        assert result == "done"
        assert call_count == 2


class TestCircuitBreakerThreadSafety:
    """Tests for circuit breaker thread safety."""

    def test_concurrent_failures(self):
        """Test circuit breaker handles concurrent failures correctly."""
        import threading

        cb = CircuitBreaker(failure_threshold=10)
        errors = []

        def record_failures():
            try:
                for _ in range(5):
                    cb.record_failure()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=record_failures) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # Should have opened after 10 failures
        assert cb.state == CircuitState.OPEN
