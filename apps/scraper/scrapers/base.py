"""
Base Scraper - Tüm scraper'lar için temel sınıf
"""

import asyncio
import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from ratelimit import limits, sleep_and_retry

logger = structlog.get_logger()


class BaseScraper(ABC):
    """
    Base class for all scrapers.
    Provides common functionality like rate limiting, retries, and logging.
    """
    
    # Rate limiting: calls per period
    CALLS_PER_MINUTE = 20
    
    # User agents for rotation
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, proxy_url: Optional[str] = None):
        self.proxy_url = proxy_url
        self.session: Optional[httpx.AsyncClient] = None
        self._request_count = 0
        
    async def __aenter__(self):
        await self.init_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
        
    async def init_session(self):
        """Initialize HTTP session with proxy if configured"""
        proxies = {"all://": self.proxy_url} if self.proxy_url else None
        self.session = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            proxies=proxies
        )
        logger.info("session_initialized", scraper=self.__class__.__name__)
        
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            logger.info("session_closed", scraper=self.__class__.__name__)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with random user agent"""
        return {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    @sleep_and_retry
    @limits(calls=20, period=60)
    async def _rate_limited_request(self, url: str, **kwargs) -> httpx.Response:
        """Make rate-limited request"""
        return await self.session.get(url, headers=self._get_headers(), **kwargs)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch(self, url: str, **kwargs) -> str:
        """
        Fetch URL content with retries and rate limiting.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for httpx
            
        Returns:
            HTML content as string
        """
        try:
            self._request_count += 1
            
            # Random delay between requests (1-3 seconds)
            await asyncio.sleep(random.uniform(1, 3))
            
            response = await self._rate_limited_request(url, **kwargs)
            response.raise_for_status()
            
            logger.debug(
                "fetch_success",
                url=url,
                status=response.status_code,
                request_count=self._request_count
            )
            
            return response.text
            
        except httpx.HTTPStatusError as e:
            logger.error(
                "fetch_http_error",
                url=url,
                status=e.response.status_code,
                error=str(e)
            )
            raise
        except Exception as e:
            logger.error("fetch_error", url=url, error=str(e))
            raise
    
    async def fetch_json(self, url: str, **kwargs) -> Dict:
        """
        Fetch JSON data from URL.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for httpx
            
        Returns:
            Parsed JSON as dictionary
        """
        try:
            self._request_count += 1
            await asyncio.sleep(random.uniform(1, 3))
            
            headers = self._get_headers()
            headers["Accept"] = "application/json"
            
            response = await self.session.get(url, headers=headers, **kwargs)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error("fetch_json_error", url=url, error=str(e))
            raise
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html, "lxml")
    
    @abstractmethod
    async def scrape(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """
        Main scraping method - must be implemented by subclasses.
        
        Returns:
            List of scraped data as dictionaries
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the name of this data source"""
        pass
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate scraped data.
        Override in subclasses for specific validation.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        return bool(data)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        return " ".join(text.strip().split())
    
    def parse_score(self, score_str: str) -> tuple[Optional[int], Optional[int]]:
        """Parse score string like '2-1' into tuple"""
        try:
            if not score_str or "-" not in score_str:
                return None, None
            parts = score_str.strip().split("-")
            return int(parts[0].strip()), int(parts[1].strip())
        except (ValueError, IndexError):
            return None, None
    
    def parse_date(self, date_str: str, format: str = "%Y-%m-%d") -> Optional[datetime]:
        """Parse date string to datetime"""
        try:
            return datetime.strptime(date_str.strip(), format)
        except (ValueError, AttributeError):
            return None


class PlaywrightScraper(BaseScraper):
    """
    Base class for scrapers that need JavaScript rendering.
    Uses Playwright for browser automation.
    """
    
    def __init__(self, proxy_url: Optional[str] = None, headless: bool = True):
        super().__init__(proxy_url)
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
    
    async def init_browser(self):
        """Initialize Playwright browser"""
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        
        # Browser launch options
        launch_options = {
            "headless": self.headless,
        }
        
        if self.proxy_url:
            launch_options["proxy"] = {"server": self.proxy_url}
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
        self.context = await self.browser.new_context(
            user_agent=random.choice(self.USER_AGENTS),
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await self.context.new_page()
        
        logger.info("browser_initialized", scraper=self.__class__.__name__)
    
    async def close_browser(self):
        """Close Playwright browser"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        
        logger.info("browser_closed", scraper=self.__class__.__name__)
    
    async def navigate(self, url: str, wait_selector: Optional[str] = None):
        """
        Navigate to URL and optionally wait for selector.
        
        Args:
            url: URL to navigate to
            wait_selector: CSS selector to wait for
        """
        await asyncio.sleep(random.uniform(1, 3))
        await self.page.goto(url, wait_until="domcontentloaded")
        
        if wait_selector:
            await self.page.wait_for_selector(wait_selector, timeout=10000)
        
        logger.debug("navigate_success", url=url)
    
    async def get_content(self) -> str:
        """Get current page HTML content"""
        return await self.page.content()
    
    async def scroll_to_bottom(self, delay: float = 0.5):
        """Scroll page to bottom to load lazy content"""
        await self.page.evaluate("""
            async () => {
                await new Promise((resolve) => {
                    let totalHeight = 0;
                    const distance = 100;
                    const timer = setInterval(() => {
                        const scrollHeight = document.body.scrollHeight;
                        window.scrollBy(0, distance);
                        totalHeight += distance;
                        if (totalHeight >= scrollHeight) {
                            clearInterval(timer);
                            resolve();
                        }
                    }, 100);
                });
            }
        """)
        await asyncio.sleep(delay)
