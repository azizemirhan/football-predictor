"""
Error Handling utilities for scrapers
"""

from .circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitState
from .retry_strategy import (
    RetryStrategy,
    ExponentialBackoffStrategy,
    FibonacciBackoffStrategy,
    AdaptiveRetryStrategy
)
from .error_classifier import ErrorClassifier, ErrorSeverity, ErrorType

__all__ = [
    'CircuitBreaker',
    'CircuitBreakerError',
    'CircuitState',
    'RetryStrategy',
    'ExponentialBackoffStrategy',
    'FibonacciBackoffStrategy',
    'AdaptiveRetryStrategy',
    'ErrorClassifier',
    'ErrorSeverity',
    'ErrorType'
]
