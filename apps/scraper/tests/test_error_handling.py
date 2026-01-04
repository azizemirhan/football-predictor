"""
Tests for Error Handling utilities
"""

import pytest
import asyncio
from apps.scraper.utils.error_handling import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
    ExponentialBackoffStrategy,
    RetryContext,
    ErrorClassifier,
    ErrorType,
    ErrorSeverity
)


class TestCircuitBreaker:
    """Test Circuit Breaker"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state"""
        cb = CircuitBreaker("test", failure_threshold=3)

        async def successful_func():
            return "success"

        result = await cb.call(successful_func)
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures"""
        cb = CircuitBreaker("test", failure_threshold=3)

        async def failing_func():
            raise Exception("Test error")

        # Cause failures
        for _ in range(3):
            try:
                await cb.call(failing_func)
            except Exception:
                pass

        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_breaker_rejects_when_open(self):
        """Test circuit breaker rejects requests when open"""
        cb = CircuitBreaker("test", failure_threshold=2)

        async def failing_func():
            raise Exception("Test error")

        # Open the circuit
        for _ in range(2):
            try:
                await cb.call(failing_func)
            except Exception:
                pass

        # Should reject now
        with pytest.raises(CircuitBreakerError):
            await cb.call(failing_func)


class TestRetryStrategy:
    """Test Retry Strategies"""

    def test_exponential_backoff_should_retry(self):
        """Test exponential backoff retry decision"""
        strategy = ExponentialBackoffStrategy(max_attempts=3)

        context = RetryContext(attempt=1, total_attempts=0)
        assert strategy.should_retry(context) is True

        context.attempt = 3
        assert strategy.should_retry(context) is False

    def test_exponential_backoff_wait_time(self):
        """Test exponential backoff wait time calculation"""
        strategy = ExponentialBackoffStrategy(
            base_delay=1.0,
            multiplier=2.0,
            jitter=False
        )

        context = RetryContext(attempt=1, total_attempts=0)
        wait_time = strategy.get_wait_time(context)
        assert wait_time == 1.0

        context.attempt = 2
        wait_time = strategy.get_wait_time(context)
        assert wait_time == 2.0

        context.attempt = 3
        wait_time = strategy.get_wait_time(context)
        assert wait_time == 4.0


class TestErrorClassifier:
    """Test Error Classifier"""

    def test_classify_network_error(self):
        """Test classification of network errors"""
        error = ConnectionError("Network error")
        classification = ErrorClassifier.classify(error)

        assert classification.error_type == ErrorType.NETWORK
        assert classification.severity == ErrorSeverity.MEDIUM
        assert classification.should_retry is True

    def test_classify_timeout_error(self):
        """Test classification of timeout errors"""
        error = TimeoutError("Request timeout")
        classification = ErrorClassifier.classify(error)

        assert classification.error_type == ErrorType.TIMEOUT
        assert classification.severity == ErrorSeverity.MEDIUM
        assert classification.should_retry is True

    def test_get_retry_delay(self):
        """Test retry delay calculation"""
        classification = ErrorClassifier.classify(ConnectionError())

        delay = ErrorClassifier.get_retry_delay(classification, attempt=1)
        assert delay > 0

        # Should increase with attempts
        delay2 = ErrorClassifier.get_retry_delay(classification, attempt=2)
        assert delay2 > delay


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
