"""
Error Classification - Classify and handle different error types
"""

from enum import Enum
from typing import Optional, Type
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"          # Minor, can continue
    MEDIUM = "medium"    # Significant, should investigate
    HIGH = "high"        # Critical, immediate action needed
    CRITICAL = "critical"  # System failure, alert required


class ErrorType(Enum):
    """Error types"""
    NETWORK = "network"              # Network/connection errors
    TIMEOUT = "timeout"              # Request timeouts
    RATE_LIMIT = "rate_limit"        # Rate limiting
    AUTHENTICATION = "authentication"  # Auth errors
    AUTHORIZATION = "authorization"    # Permission errors
    NOT_FOUND = "not_found"          # Resource not found
    SERVER_ERROR = "server_error"    # Server 5xx errors
    CLIENT_ERROR = "client_error"    # Client 4xx errors
    PARSING = "parsing"              # Data parsing errors
    VALIDATION = "validation"        # Data validation errors
    CAPTCHA = "captcha"              # CAPTCHA/anti-bot
    CLOUDFLARE = "cloudflare"        # Cloudflare protection
    PROXY = "proxy"                  # Proxy errors
    UNKNOWN = "unknown"              # Unclassified


@dataclass
class ErrorClassification:
    """Error classification result"""
    error_type: ErrorType
    severity: ErrorSeverity
    should_retry: bool
    retry_after: Optional[float] = None  # Seconds
    requires_alert: bool = False
    message: str = ""


class ErrorClassifier:
    """
    Classify errors to determine appropriate handling.

    Determines:
    - Error type
    - Severity level
    - Whether to retry
    - Alert requirements
    """

    @staticmethod
    def classify(exception: Exception, context: Optional[dict] = None) -> ErrorClassification:
        """
        Classify an exception.

        Args:
            exception: The exception to classify
            context: Optional context information

        Returns:
            ErrorClassification
        """
        context = context or {}

        # Network/connection errors
        if isinstance(exception, (ConnectionError, ConnectionResetError, ConnectionRefusedError)):
            return ErrorClassification(
                error_type=ErrorType.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                should_retry=True,
                message="Network connection error"
            )

        # Timeout errors
        if isinstance(exception, TimeoutError):
            return ErrorClassification(
                error_type=ErrorType.TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
                should_retry=True,
                message="Request timeout"
            )

        # HTTP errors
        if hasattr(exception, 'response'):
            return ErrorClassifier._classify_http_error(exception)

        # Parsing errors
        if isinstance(exception, (ValueError, KeyError, AttributeError)):
            return ErrorClassification(
                error_type=ErrorType.PARSING,
                severity=ErrorSeverity.LOW,
                should_retry=False,
                message="Data parsing error"
            )

        # Unknown errors
        return ErrorClassification(
            error_type=ErrorType.UNKNOWN,
            severity=ErrorSeverity.HIGH,
            should_retry=False,
            requires_alert=True,
            message=f"Unknown error: {type(exception).__name__}"
        )

    @staticmethod
    def _classify_http_error(exception: Exception) -> ErrorClassification:
        """Classify HTTP errors by status code"""
        status = getattr(exception.response, 'status_code', None)

        if not status:
            return ErrorClassification(
                error_type=ErrorType.UNKNOWN,
                severity=ErrorSeverity.MEDIUM,
                should_retry=True,
                message="HTTP error without status code"
            )

        # 401 Unauthorized
        if status == 401:
            return ErrorClassification(
                error_type=ErrorType.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                should_retry=False,
                requires_alert=True,
                message="Authentication failed"
            )

        # 403 Forbidden
        if status == 403:
            # Check if it's Cloudflare
            headers = getattr(exception.response, 'headers', {})
            if 'cf-ray' in headers or 'cloudflare' in str(exception).lower():
                return ErrorClassification(
                    error_type=ErrorType.CLOUDFLARE,
                    severity=ErrorSeverity.HIGH,
                    should_retry=True,
                    retry_after=60.0,  # Wait longer for Cloudflare
                    message="Cloudflare protection detected"
                )

            return ErrorClassification(
                error_type=ErrorType.AUTHORIZATION,
                severity=ErrorSeverity.MEDIUM,
                should_retry=False,
                message="Access forbidden"
            )

        # 404 Not Found
        if status == 404:
            return ErrorClassification(
                error_type=ErrorType.NOT_FOUND,
                severity=ErrorSeverity.LOW,
                should_retry=False,
                message="Resource not found"
            )

        # 429 Rate Limit
        if status == 429:
            retry_after = None
            headers = getattr(exception.response, 'headers', {})
            if 'Retry-After' in headers:
                try:
                    retry_after = float(headers['Retry-After'])
                except ValueError:
                    retry_after = 60.0

            return ErrorClassification(
                error_type=ErrorType.RATE_LIMIT,
                severity=ErrorSeverity.MEDIUM,
                should_retry=True,
                retry_after=retry_after or 60.0,
                message="Rate limit exceeded"
            )

        # 5xx Server Errors
        if 500 <= status < 600:
            # 503 Service Unavailable
            if status == 503:
                severity = ErrorSeverity.HIGH
                retry_after = 30.0
            else:
                severity = ErrorSeverity.MEDIUM
                retry_after = None

            return ErrorClassification(
                error_type=ErrorType.SERVER_ERROR,
                severity=severity,
                should_retry=True,
                retry_after=retry_after,
                requires_alert=(status == 503),
                message=f"Server error: {status}"
            )

        # Other 4xx Client Errors
        if 400 <= status < 500:
            return ErrorClassification(
                error_type=ErrorType.CLIENT_ERROR,
                severity=ErrorSeverity.LOW,
                should_retry=False,
                message=f"Client error: {status}"
            )

        # Other status codes
        return ErrorClassification(
            error_type=ErrorType.UNKNOWN,
            severity=ErrorSeverity.MEDIUM,
            should_retry=True,
            message=f"HTTP error: {status}"
        )

    @staticmethod
    def should_alert(classification: ErrorClassification, error_count: int = 1) -> bool:
        """
        Determine if should send alert.

        Args:
            classification: Error classification
            error_count: Number of consecutive errors

        Returns:
            True if should alert
        """
        # Always alert for critical errors
        if classification.requires_alert:
            return True

        # Alert for high severity if multiple errors
        if classification.severity == ErrorSeverity.HIGH and error_count >= 3:
            return True

        # Alert for medium severity if many errors
        if classification.severity == ErrorSeverity.MEDIUM and error_count >= 10:
            return True

        return False

    @staticmethod
    def get_retry_delay(
        classification: ErrorClassification,
        attempt: int,
        base_delay: float = 1.0
    ) -> float:
        """
        Get retry delay based on classification.

        Args:
            classification: Error classification
            attempt: Retry attempt number
            base_delay: Base delay in seconds

        Returns:
            Delay in seconds
        """
        if classification.retry_after:
            return classification.retry_after

        # Different delays based on error type
        if classification.error_type == ErrorType.RATE_LIMIT:
            return base_delay * (3 ** attempt)  # Aggressive backoff

        if classification.error_type == ErrorType.CLOUDFLARE:
            return base_delay * (4 ** attempt)  # Very aggressive backoff

        if classification.error_type == ErrorType.SERVER_ERROR:
            return base_delay * (2 ** attempt)  # Standard exponential backoff

        # Default exponential backoff
        return base_delay * (2 ** (attempt - 1))


class ErrorTracker:
    """Track error occurrences and patterns"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.errors: list[ErrorClassification] = []
        self.error_counts: dict[ErrorType, int] = {}

    def add_error(self, classification: ErrorClassification):
        """Add error to tracker"""
        self.errors.append(classification)

        # Maintain window size
        if len(self.errors) > self.window_size:
            self.errors.pop(0)

        # Update counts
        error_type = classification.error_type
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

    def get_error_rate(self) -> float:
        """Get current error rate"""
        if not self.errors:
            return 0.0
        return len(self.errors) / self.window_size

    def get_most_common_error(self) -> Optional[ErrorType]:
        """Get most common error type"""
        if not self.error_counts:
            return None
        return max(self.error_counts, key=self.error_counts.get)

    def get_consecutive_errors(self, error_type: Optional[ErrorType] = None) -> int:
        """Get consecutive error count"""
        count = 0
        for error in reversed(self.errors):
            if error_type is None or error.error_type == error_type:
                count += 1
            else:
                break
        return count

    def should_pause_scraping(self) -> bool:
        """Determine if should pause scraping"""
        # Pause if error rate > 80%
        if self.get_error_rate() > 0.8:
            return True

        # Pause if too many critical errors
        critical_count = sum(
            1 for e in self.errors
            if e.severity == ErrorSeverity.CRITICAL
        )
        if critical_count >= 5:
            return True

        # Pause if many Cloudflare errors
        cf_count = self.get_consecutive_errors(ErrorType.CLOUDFLARE)
        if cf_count >= 3:
            return True

        return False

    def reset(self):
        """Reset tracker"""
        self.errors.clear()
        self.error_counts.clear()
