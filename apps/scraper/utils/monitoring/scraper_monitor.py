"""
Scraper Monitor - Track scraper health and performance
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger()


class ScraperHealthStatus(Enum):
    """Scraper health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DOWN = "down"


@dataclass
class ScraperMetrics:
    """Scraper performance metrics"""
    scraper_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    items_scraped: int = 0
    errors_count: int = 0
    avg_response_time: float = 0.0
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        if self.total_requests == 0:
            return 0.0
        return self.errors_count / self.total_requests


class ScraperMonitor:
    """
    Monitor scraper health and performance.

    Tracks:
    - Request success/failure rates
    - Response times
    - Data quality
    - Errors and exceptions
    """

    def __init__(self, scraper_name: str):
        self.scraper_name = scraper_name
        self.metrics = ScraperMetrics(scraper_name=scraper_name)
        self.health_status = ScraperHealthStatus.HEALTHY

    def record_request(self, success: bool, response_time: float = 0.0):
        """Record request attempt"""
        self.metrics.total_requests += 1
        self.metrics.last_run = datetime.now()

        if success:
            self.metrics.successful_requests += 1
            self.metrics.last_success = datetime.now()

            # Update avg response time
            if self.metrics.avg_response_time == 0:
                self.metrics.avg_response_time = response_time
            else:
                self.metrics.avg_response_time = (
                    self.metrics.avg_response_time * 0.9 + response_time * 0.1
                )
        else:
            self.metrics.failed_requests += 1

        self._update_health_status()

    def record_items(self, count: int):
        """Record items scraped"""
        self.metrics.items_scraped += count

    def record_error(self, error_type: str = "unknown"):
        """Record error"""
        self.metrics.errors_count += 1
        self.metrics.last_error = datetime.now()

        logger.warning(
            "scraper_error",
            scraper=self.scraper_name,
            error_type=error_type,
            total_errors=self.metrics.errors_count
        )

        self._update_health_status()

    def _update_health_status(self):
        """Update health status based on metrics"""
        success_rate = self.metrics.success_rate
        error_rate = self.metrics.error_rate

        if success_rate >= 0.95:
            self.health_status = ScraperHealthStatus.HEALTHY
        elif success_rate >= 0.80:
            self.health_status = ScraperHealthStatus.DEGRADED
        elif success_rate >= 0.50:
            self.health_status = ScraperHealthStatus.UNHEALTHY
        else:
            self.health_status = ScraperHealthStatus.DOWN

    def get_health_report(self) -> Dict:
        """Get health report"""
        return {
            'scraper': self.scraper_name,
            'status': self.health_status.value,
            'success_rate': round(self.metrics.success_rate, 2),
            'error_rate': round(self.metrics.error_rate, 2),
            'total_requests': self.metrics.total_requests,
            'items_scraped': self.metrics.items_scraped,
            'avg_response_time': round(self.metrics.avg_response_time, 2),
            'last_run': self.metrics.last_run.isoformat() if self.metrics.last_run else None,
            'last_success': self.metrics.last_success.isoformat() if self.metrics.last_success else None
        }

    def should_alert(self) -> bool:
        """Check if should send alert"""
        return self.health_status in (ScraperHealthStatus.UNHEALTHY, ScraperHealthStatus.DOWN)
