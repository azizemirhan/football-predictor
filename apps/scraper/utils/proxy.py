"""
Proxy Pool Manager - Manage and rotate proxies
"""

import random
import asyncio
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import structlog
import httpx

logger = structlog.get_logger()


class ProxyProtocol(Enum):
    """Proxy protocols"""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


@dataclass
class ProxyInfo:
    """Proxy information and statistics"""
    url: str
    protocol: ProxyProtocol
    location: Optional[str] = None

    # Statistics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_used: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None

    # Health
    is_healthy: bool = True
    consecutive_failures: int = 0
    avg_response_time: float = 0.0

    # Cooldown
    cooldown_until: Optional[datetime] = None

    def __post_init__(self):
        if isinstance(self.protocol, str):
            self.protocol = ProxyProtocol(self.protocol)

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def is_available(self) -> bool:
        """Check if proxy is available"""
        if not self.is_healthy:
            return False

        if self.cooldown_until and datetime.now() < self.cooldown_until:
            return False

        return True

    def record_success(self, response_time: float):
        """Record successful request"""
        self.total_requests += 1
        self.successful_requests += 1
        self.consecutive_failures = 0
        self.last_used = datetime.now()
        self.last_success = datetime.now()

        # Update avg response time
        if self.avg_response_time == 0:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = (self.avg_response_time * 0.9) + (response_time * 0.1)

    def record_failure(self, cooldown_seconds: int = 60):
        """Record failed request"""
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.last_used = datetime.now()
        self.last_failure = datetime.now()

        # Mark unhealthy after 3 consecutive failures
        if self.consecutive_failures >= 3:
            self.is_healthy = False
            logger.warning("proxy_marked_unhealthy", proxy=self.url)

        # Set cooldown
        self.cooldown_until = datetime.now() + timedelta(seconds=cooldown_seconds)

    def reset_health(self):
        """Reset health status"""
        self.is_healthy = True
        self.consecutive_failures = 0
        self.cooldown_until = None


class ProxyPool:
    """
    Manage pool of proxies with rotation and health checking.

    Features:
    - Automatic rotation
    - Health checking
    - Performance tracking
    - Automatic retry with different proxies
    """

    def __init__(
        self,
        proxies: Optional[List[str]] = None,
        rotation_strategy: str = "round_robin",  # or "random", "performance"
        health_check_interval: int = 300  # seconds
    ):
        self.proxies: List[ProxyInfo] = []
        self.rotation_strategy = rotation_strategy
        self.health_check_interval = health_check_interval
        self.current_index = 0

        if proxies:
            self.add_proxies(proxies)

    def add_proxy(self, proxy_url: str, protocol: ProxyProtocol = ProxyProtocol.HTTP):
        """Add proxy to pool"""
        proxy_info = ProxyInfo(url=proxy_url, protocol=protocol)
        self.proxies.append(proxy_info)
        logger.info("proxy_added", url=proxy_url, total=len(self.proxies))

    def add_proxies(self, proxy_urls: List[str]):
        """Add multiple proxies"""
        for url in proxy_urls:
            # Auto-detect protocol
            if url.startswith('socks5'):
                protocol = ProxyProtocol.SOCKS5
            elif url.startswith('socks4'):
                protocol = ProxyProtocol.SOCKS4
            elif url.startswith('https'):
                protocol = ProxyProtocol.HTTPS
            else:
                protocol = ProxyProtocol.HTTP

            self.add_proxy(url, protocol)

    def get_proxy(self) -> Optional[ProxyInfo]:
        """
        Get next proxy based on rotation strategy.

        Returns:
            ProxyInfo or None if no available proxies
        """
        available = [p for p in self.proxies if p.is_available]

        if not available:
            logger.warning("no_available_proxies")
            return None

        if self.rotation_strategy == "random":
            return random.choice(available)

        elif self.rotation_strategy == "performance":
            # Choose proxy with best performance
            return max(available, key=lambda p: p.success_rate - p.avg_response_time)

        else:  # round_robin
            # Find next available proxy starting from current index
            for _ in range(len(self.proxies)):
                proxy = self.proxies[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.proxies)

                if proxy.is_available:
                    return proxy

            return None

    def record_success(self, proxy: ProxyInfo, response_time: float):
        """Record successful request for proxy"""
        proxy.record_success(response_time)
        logger.debug(
            "proxy_success",
            url=proxy.url,
            success_rate=round(proxy.success_rate, 2),
            response_time=round(response_time, 2)
        )

    def record_failure(self, proxy: ProxyInfo):
        """Record failed request for proxy"""
        proxy.record_failure()
        logger.warning(
            "proxy_failure",
            url=proxy.url,
            consecutive_failures=proxy.consecutive_failures
        )

    async def health_check(self, test_url: str = "https://httpbin.org/ip"):
        """
        Check health of all proxies.

        Args:
            test_url: URL to test proxies against
        """
        logger.info("proxy_health_check_started", total=len(self.proxies))

        async def check_proxy(proxy: ProxyInfo):
            try:
                start = asyncio.get_event_loop().time()

                async with httpx.AsyncClient(
                    proxies={proxy.protocol.value: proxy.url},
                    timeout=10.0
                ) as client:
                    response = await client.get(test_url)
                    response.raise_for_status()

                response_time = asyncio.get_event_loop().time() - start

                # Proxy is healthy
                if not proxy.is_healthy:
                    proxy.reset_health()
                    logger.info("proxy_recovered", url=proxy.url)

                proxy.record_success(response_time)

            except Exception as e:
                logger.debug("proxy_health_check_failed", url=proxy.url, error=str(e))
                proxy.record_failure(cooldown_seconds=300)

        # Check all proxies concurrently
        await asyncio.gather(*[check_proxy(p) for p in self.proxies])

        healthy_count = sum(1 for p in self.proxies if p.is_healthy)
        logger.info(
            "proxy_health_check_completed",
            healthy=healthy_count,
            total=len(self.proxies)
        )

    async def auto_health_check(self, test_url: str = "https://httpbin.org/ip"):
        """Automatically check health at intervals"""
        while True:
            await self.health_check(test_url)
            await asyncio.sleep(self.health_check_interval)

    def get_stats(self) -> Dict:
        """Get proxy pool statistics"""
        healthy = [p for p in self.proxies if p.is_healthy]
        available = [p for p in self.proxies if p.is_available]

        return {
            'total_proxies': len(self.proxies),
            'healthy_proxies': len(healthy),
            'available_proxies': len(available),
            'avg_success_rate': (
                sum(p.success_rate for p in self.proxies) / len(self.proxies)
                if self.proxies else 0
            ),
            'proxies': [
                {
                    'url': p.url,
                    'is_healthy': p.is_healthy,
                    'is_available': p.is_available,
                    'success_rate': round(p.success_rate, 2),
                    'total_requests': p.total_requests,
                    'avg_response_time': round(p.avg_response_time, 2)
                }
                for p in self.proxies
            ]
        }

    def remove_unhealthy(self, min_success_rate: float = 0.3):
        """Remove consistently unhealthy proxies"""
        before = len(self.proxies)

        self.proxies = [
            p for p in self.proxies
            if p.success_rate >= min_success_rate or p.total_requests < 10
        ]

        removed = before - len(self.proxies)
        if removed > 0:
            logger.info("unhealthy_proxies_removed", count=removed)


class ProxyRotator:
    """
    Simple proxy rotator for use in scrapers.

    Usage:
        rotator = ProxyRotator(['http://proxy1:8080', 'http://proxy2:8080'])
        proxy = rotator.get_next()
    """

    def __init__(self, proxies: List[str]):
        self.pool = ProxyPool(proxies, rotation_strategy="round_robin")

    def get_next(self) -> Optional[str]:
        """Get next proxy URL"""
        proxy = self.pool.get_proxy()
        return proxy.url if proxy else None

    def report_success(self, proxy_url: str, response_time: float = 1.0):
        """Report successful use of proxy"""
        proxy = next((p for p in self.pool.proxies if p.url == proxy_url), None)
        if proxy:
            self.pool.record_success(proxy, response_time)

    def report_failure(self, proxy_url: str):
        """Report failed use of proxy"""
        proxy = next((p for p in self.pool.proxies if p.url == proxy_url), None)
        if proxy:
            self.pool.record_failure(proxy)
