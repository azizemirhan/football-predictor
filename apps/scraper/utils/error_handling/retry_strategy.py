"""
Advanced Retry Strategies - Beyond simple exponential backoff
"""

import time
import random
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Callable, Any, Type
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class RetryContext:
    """Context for retry attempts"""
    attempt: int
    total_attempts: int
    last_exception: Optional[Exception] = None
    elapsed_time: float = 0.0


class RetryStrategy(ABC):
    """Base class for retry strategies"""

    @abstractmethod
    def should_retry(self, context: RetryContext) -> bool:
        """Determine if should retry"""
        pass

    @abstractmethod
    def get_wait_time(self, context: RetryContext) -> float:
        """Calculate wait time before next retry"""
        pass


class ExponentialBackoffStrategy(RetryStrategy):
    """
    Exponential backoff with jitter.

    Wait time = base * (multiplier ^ attempt) + jitter
    """

    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

    def should_retry(self, context: RetryContext) -> bool:
        """Check if should retry"""
        return context.attempt < self.max_attempts

    def get_wait_time(self, context: RetryContext) -> float:
        """Calculate exponential backoff time"""
        delay = self.base_delay * (self.multiplier ** (context.attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add random jitter (±25%)
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)

        return max(0, delay)


class FibonacciBackoffStrategy(RetryStrategy):
    """
    Fibonacci backoff strategy.

    Wait times follow Fibonacci sequence: 1, 1, 2, 3, 5, 8, 13, ...
    """

    def __init__(
        self,
        max_attempts: int = 8,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    def should_retry(self, context: RetryContext) -> bool:
        return context.attempt < self.max_attempts

    def get_wait_time(self, context: RetryContext) -> float:
        """Calculate Fibonacci delay"""
        fib_num = self._fibonacci(context.attempt)
        delay = self.base_delay * fib_num
        return min(delay, self.max_delay)

    def _fibonacci(self, n: int) -> int:
        """Calculate nth Fibonacci number"""
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b


class AdaptiveRetryStrategy(RetryStrategy):
    """
    Adaptive retry strategy that adjusts based on error types.

    - Network errors: Retry with exponential backoff
    - Rate limit errors: Retry after specified wait time
    - Server errors (5xx): Retry with longer delays
    - Client errors (4xx): Don't retry (except 429)
    """

    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 120.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

    def should_retry(self, context: RetryContext) -> bool:
        """Determine if should retry based on error type"""
        if context.attempt >= self.max_attempts:
            return False

        if not context.last_exception:
            return True

        # Check exception type
        exception = context.last_exception

        # Network/connection errors - always retry
        if isinstance(exception, (ConnectionError, TimeoutError)):
            return True

        # HTTP errors
        if hasattr(exception, 'response'):
            status = getattr(exception.response, 'status_code', None)

            # Don't retry client errors (except 429 rate limit)
            if status and 400 <= status < 500:
                return status == 429  # Retry rate limits

            # Retry server errors
            if status and 500 <= status < 600:
                return True

        return True

    def get_wait_time(self, context: RetryContext) -> float:
        """Calculate adaptive wait time"""
        if not context.last_exception:
            return self.base_delay

        exception = context.last_exception

        # Check for Retry-After header
        if hasattr(exception, 'response'):
            retry_after = getattr(exception.response, 'headers', {}).get('Retry-After')
            if retry_after:
                try:
                    return float(retry_after)
                except ValueError:
                    pass

            status = getattr(exception.response, 'status_code', None)

            # Rate limit (429) - longer wait
            if status == 429:
                delay = self.base_delay * (3 ** context.attempt)
                return min(delay, self.max_delay)

            # Server errors (5xx) - exponential backoff
            if status and 500 <= status < 600:
                delay = self.base_delay * (2 ** context.attempt)
                return min(delay, self.max_delay)

        # Network errors - exponential with jitter
        delay = self.base_delay * (2 ** (context.attempt - 1))
        jitter = random.uniform(0, delay * 0.3)
        return min(delay + jitter, self.max_delay)


async def retry_with_strategy(
    func: Callable,
    strategy: RetryStrategy,
    *args,
    on_retry: Optional[Callable[[RetryContext], None]] = None,
    **kwargs
) -> Any:
    """
    Execute function with retry strategy.

    Args:
        func: Async function to execute
        strategy: Retry strategy
        on_retry: Optional callback on each retry
        *args, **kwargs: Function arguments

    Returns:
        Function result

    Raises:
        Last exception if all retries failed
    """
    context = RetryContext(attempt=0, total_attempts=0)
    start_time = time.time()
    last_exception = None

    while True:
        context.attempt += 1
        context.total_attempts += 1
        context.elapsed_time = time.time() - start_time

        try:
            result = await func(*args, **kwargs)

            if context.attempt > 1:
                logger.info(
                    "retry_success",
                    attempt=context.attempt,
                    elapsed_time=round(context.elapsed_time, 2)
                )

            return result

        except Exception as e:
            last_exception = e
            context.last_exception = e

            logger.warning(
                "retry_attempt_failed",
                attempt=context.attempt,
                error=str(e),
                error_type=type(e).__name__
            )

            # Check if should retry
            if not strategy.should_retry(context):
                logger.error(
                    "retry_exhausted",
                    total_attempts=context.attempt,
                    elapsed_time=round(context.elapsed_time, 2)
                )
                raise

            # Calculate wait time
            wait_time = strategy.get_wait_time(context)

            logger.debug(
                "retry_waiting",
                attempt=context.attempt,
                wait_time=round(wait_time, 2)
            )

            # Call on_retry callback
            if on_retry:
                on_retry(context)

            # Wait before retry
            await asyncio.sleep(wait_time)


def create_retry_decorator(
    strategy: Optional[RetryStrategy] = None,
    **strategy_kwargs
):
    """
    Create retry decorator with strategy.

    Usage:
        @create_retry_decorator(max_attempts=5)
        async def my_function():
            ...
    """
    if strategy is None:
        strategy = ExponentialBackoffStrategy(**strategy_kwargs)

    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            return await retry_with_strategy(func, strategy, *args, **kwargs)
        return wrapper

    return decorator


# Convenience decorators
def retry_exponential(max_attempts: int = 5, base_delay: float = 1.0):
    """Retry with exponential backoff"""
    return create_retry_decorator(
        ExponentialBackoffStrategy(
            max_attempts=max_attempts,
            base_delay=base_delay
        )
    )


def retry_fibonacci(max_attempts: int = 8, base_delay: float = 1.0):
    """Retry with Fibonacci backoff"""
    return create_retry_decorator(
        FibonacciBackoffStrategy(
            max_attempts=max_attempts,
            base_delay=base_delay
        )
    )


def retry_adaptive(max_attempts: int = 5):
    """Retry with adaptive strategy"""
    return create_retry_decorator(
        AdaptiveRetryStrategy(max_attempts=max_attempts)
    )
