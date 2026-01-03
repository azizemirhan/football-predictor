"""
Circuit Breaker Pattern - Prevent cascading failures
"""

import time
import asyncio
from enum import Enum
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing - reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation.

    Protects against cascading failures by:
    - Failing fast when service is down
    - Automatically recovering when service is back
    - Tracking failure/success rates

    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures - reject requests
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,  # Open after N failures
        success_threshold: int = 2,   # Close after N successes in half-open
        timeout: float = 60.0,         # Seconds to wait before half-open
        expected_exception: type = Exception
    ):
        """
        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures before opening
            success_threshold: Number of successes before closing from half-open
            timeout: Seconds to wait in open state before trying half-open
            expected_exception: Exception type to catch
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        self.opened_at: Optional[float] = None

    def __call__(self, func: Callable) -> Callable:
        """Decorator usage"""
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        return wrapper

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        # Check if we can make the call
        if not self._can_attempt():
            self.stats.rejected_requests += 1
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is {self.state.value}"
            )

        self.stats.total_requests += 1

        try:
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # Success
            self._on_success()
            return result

        except self.expected_exception as e:
            # Failure
            self._on_failure()
            raise

    def _can_attempt(self) -> bool:
        """Check if we can attempt a request"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout passed
            if self.opened_at and (time.time() - self.opened_at) >= self.timeout:
                logger.info(
                    "circuit_breaker_half_open",
                    name=self.name,
                    timeout=self.timeout
                )
                self.state = CircuitState.HALF_OPEN
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Allow limited attempts in half-open
            return True

        return False

    def _on_success(self):
        """Handle successful request"""
        self.stats.successful_requests += 1
        self.stats.consecutive_successes += 1
        self.stats.consecutive_failures = 0
        self.stats.last_success_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            if self.stats.consecutive_successes >= self.success_threshold:
                self._close()

        logger.debug(
            "circuit_breaker_success",
            name=self.name,
            state=self.state.value,
            consecutive_successes=self.stats.consecutive_successes
        )

    def _on_failure(self):
        """Handle failed request"""
        self.stats.failed_requests += 1
        self.stats.consecutive_failures += 1
        self.stats.consecutive_successes = 0
        self.stats.last_failure_time = datetime.now()

        if self.state == CircuitState.CLOSED:
            if self.stats.consecutive_failures >= self.failure_threshold:
                self._open()

        elif self.state == CircuitState.HALF_OPEN:
            # Failure in half-open -> back to open
            self._open()

        logger.warning(
            "circuit_breaker_failure",
            name=self.name,
            state=self.state.value,
            consecutive_failures=self.stats.consecutive_failures
        )

    def _open(self):
        """Open the circuit"""
        self.state = CircuitState.OPEN
        self.opened_at = time.time()

        logger.error(
            "circuit_breaker_opened",
            name=self.name,
            consecutive_failures=self.stats.consecutive_failures,
            timeout=self.timeout
        )

    def _close(self):
        """Close the circuit"""
        self.state = CircuitState.CLOSED
        self.opened_at = None
        self.stats.consecutive_failures = 0
        self.stats.consecutive_successes = 0

        logger.info(
            "circuit_breaker_closed",
            name=self.name
        )

    def reset(self):
        """Manually reset circuit breaker"""
        self.state = CircuitState.CLOSED
        self.opened_at = None
        self.stats = CircuitBreakerStats()

        logger.info("circuit_breaker_reset", name=self.name)

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'total_requests': self.stats.total_requests,
            'successful_requests': self.stats.successful_requests,
            'failed_requests': self.stats.failed_requests,
            'rejected_requests': self.stats.rejected_requests,
            'success_rate': (
                self.stats.successful_requests / self.stats.total_requests
                if self.stats.total_requests > 0 else 0
            ),
            'consecutive_failures': self.stats.consecutive_failures,
            'consecutive_successes': self.stats.consecutive_successes,
            'last_failure_time': (
                self.stats.last_failure_time.isoformat()
                if self.stats.last_failure_time else None
            ),
            'last_success_time': (
                self.stats.last_success_time.isoformat()
                if self.stats.last_success_time else None
            )
        }


class CircuitBreakerManager:
    """Manage multiple circuit breakers"""

    def __init__(self):
        self.breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        **kwargs
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker"""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self.breakers[name]

    def get_all_stats(self) -> dict:
        """Get stats for all circuit breakers"""
        return {
            name: breaker.get_stats()
            for name, breaker in self.breakers.items()
        }

    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()


# Global circuit breaker manager
circuit_breaker_manager = CircuitBreakerManager()
