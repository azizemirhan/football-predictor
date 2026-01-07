"""
Advanced Rate Limiter - Adaptive rate limiting with multiple strategies
"""

import time
import asyncio
from typing import Dict, Optional
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_second: float = 1.0
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    burst_size: int = 10  # Max burst requests


class TokenBucketRateLimiter:
    """
    Token bucket algorithm for rate limiting.

    More flexible than simple counter - allows bursts while maintaining rate.
    """

    def __init__(
        self,
        rate: float,  # Tokens per second
        capacity: int  # Bucket capacity
    ):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from bucket.

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if acquired, False otherwise
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        # Calculate wait time
        wait_time = (tokens - self.tokens) / self.rate
        await asyncio.sleep(wait_time)

        self._refill()
        self.tokens -= tokens
        return True

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter.

    Tracks requests in a time window and prevents exceeding limits.
    """

    def __init__(self, window_size: int, max_requests: int):
        """
        Args:
            window_size: Window size in seconds
            max_requests: Max requests in window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()

    async def acquire(self) -> bool:
        """Acquire permission to make request"""
        now = time.time()

        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window_size:
            self.requests.popleft()

        # Check if can make request
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True

        # Calculate wait time
        oldest = self.requests[0]
        wait_time = oldest + self.window_size - now

        logger.debug(
            "rate_limit_wait",
            wait_time=round(wait_time, 2),
            requests_in_window=len(self.requests)
        )

        await asyncio.sleep(wait_time)

        # Remove old and add new
        self.requests.popleft()
        self.requests.append(time.time())
        return True


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts based on responses.

    - Slows down on rate limit errors
    - Speeds up during successful periods
    - Respects Retry-After headers
    """

    def __init__(self, base_rate: float = 1.0, min_rate: float = 0.1, max_rate: float = 10.0):
        self.base_rate = base_rate
        self.current_rate = base_rate
        self.min_rate = min_rate
        self.max_rate = max_rate

        self.token_bucket = TokenBucketRateLimiter(base_rate, int(base_rate * 10))

        self.consecutive_successes = 0
        self.consecutive_failures = 0

    async def acquire(self) -> bool:
        """Acquire permission with current rate"""
        await self.token_bucket.acquire()
        return True

    def on_success(self):
        """Called after successful request"""
        self.consecutive_successes += 1
        self.consecutive_failures = 0

        # Gradually increase rate after sustained success
        if self.consecutive_successes >= 10:
            self.increase_rate(factor=1.1)
            self.consecutive_successes = 0

    def on_rate_limit(self, retry_after: Optional[int] = None):
        """Called when rate limited"""
        self.consecutive_failures += 1
        self.consecutive_successes = 0

        if retry_after:
            # Respect Retry-After
            new_rate = 1.0 / retry_after
        else:
            # Decrease rate significantly
            new_rate = self.current_rate * 0.5

        self.set_rate(new_rate)

        logger.warning(
            "rate_limited",
            new_rate=round(self.current_rate, 2),
            retry_after=retry_after
        )

    def on_error(self):
        """Called on other errors"""
        self.consecutive_failures += 1
        self.consecutive_successes = 0

        # Slow down slightly
        if self.consecutive_failures >= 3:
            self.decrease_rate(factor=0.8)
            self.consecutive_failures = 0

    def increase_rate(self, factor: float = 1.2):
        """Increase request rate"""
        new_rate = min(self.current_rate * factor, self.max_rate)
        self.set_rate(new_rate)

    def decrease_rate(self, factor: float = 0.5):
        """Decrease request rate"""
        new_rate = max(self.current_rate * factor, self.min_rate)
        self.set_rate(new_rate)

    def set_rate(self, rate: float):
        """Set specific rate"""
        rate = max(self.min_rate, min(rate, self.max_rate))
        self.current_rate = rate
        self.token_bucket.rate = rate

        logger.info("rate_adjusted", rate=round(rate, 2))


class MultiLevelRateLimiter:
    """
    Multi-level rate limiter enforcing limits at different time scales.

    Example:
        - 2 requests/second
        - 60 requests/minute
        - 1000 requests/hour
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config

        # Create limiters for each level
        self.second_limiter = TokenBucketRateLimiter(
            rate=config.requests_per_second,
            capacity=config.burst_size
        )

        self.minute_limiter = SlidingWindowRateLimiter(
            window_size=60,
            max_requests=config.requests_per_minute
        )

        self.hour_limiter = SlidingWindowRateLimiter(
            window_size=3600,
            max_requests=config.requests_per_hour
        )

    async def acquire(self) -> bool:
        """Acquire from all limiters"""
        # Must pass all limiters
        await self.second_limiter.acquire()
        await self.minute_limiter.acquire()
        await self.hour_limiter.acquire()

        return True


class DomainRateLimiter:
    """
    Rate limiter per domain.

    Maintains separate rate limits for different domains.
    """

    def __init__(self):
        self.limiters: Dict[str, AdaptiveRateLimiter] = {}

    def get_limiter(self, domain: str, base_rate: float = 1.0) -> AdaptiveRateLimiter:
        """Get or create rate limiter for domain"""
        if domain not in self.limiters:
            self.limiters[domain] = AdaptiveRateLimiter(base_rate=base_rate)
        return self.limiters[domain]

    async def acquire(self, domain: str) -> bool:
        """Acquire for specific domain"""
        limiter = self.get_limiter(domain)
        return await limiter.acquire()

    def on_success(self, domain: str):
        """Report success for domain"""
        if domain in self.limiters:
            self.limiters[domain].on_success()

    def on_rate_limit(self, domain: str, retry_after: Optional[int] = None):
        """Report rate limit for domain"""
        limiter = self.get_limiter(domain)
        limiter.on_rate_limit(retry_after)

    def get_stats(self) -> Dict[str, Dict]:
        """Get stats for all domains"""
        return {
            domain: {
                'current_rate': round(limiter.current_rate, 2),
                'consecutive_successes': limiter.consecutive_successes,
                'consecutive_failures': limiter.consecutive_failures
            }
            for domain, limiter in self.limiters.items()
        }
