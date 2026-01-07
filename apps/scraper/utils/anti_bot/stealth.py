"""
Stealth Browser - Anti-detection techniques for web scraping
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class BrowserFingerprint:
    """Browser fingerprint configuration"""
    user_agent: str
    viewport: Dict[str, int]
    platform: str
    languages: List[str]
    timezone: str
    webgl_vendor: str
    webgl_renderer: str

    @classmethod
    def generate_realistic(cls) -> 'BrowserFingerprint':
        """Generate realistic browser fingerprint"""
        platforms = [
            ('Windows NT 10.0; Win64; x64', 'Win32'),
            ('Macintosh; Intel Mac OS X 10_15_7', 'MacIntel'),
            ('X11; Linux x86_64', 'Linux x86_64')
        ]

        platform_str, navigator_platform = random.choice(platforms)

        chrome_version = random.randint(115, 122)

        user_agents = [
            f"Mozilla/5.0 ({platform_str}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36",
            f"Mozilla/5.0 ({platform_str}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36 Edg/{chrome_version}.0.0.0",
        ]

        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900}
        ]

        timezones = [
            'Europe/London',
            'America/New_York',
            'Europe/Paris',
            'America/Los_Angeles'
        ]

        return cls(
            user_agent=random.choice(user_agents),
            viewport=random.choice(viewports),
            platform=navigator_platform,
            languages=['en-US', 'en'],
            timezone=random.choice(timezones),
            webgl_vendor='Google Inc. (Intel)',
            webgl_renderer='ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.1)'
        )


class StealthBrowser:
    """
    Stealth browser with anti-detection measures.

    Techniques:
    - Realistic fingerprinting
    - Webdriver flag hiding
    - Canvas fingerprint randomization
    - WebGL fingerprint spoofing
    - Navigator property spoofing
    """

    STEALTH_SCRIPTS = """
        // Hide webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });

        // Add chrome object
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };

        // Permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );

        // Plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });

        // Languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en']
        });

        // WebGL vendor override
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Google Inc. (Intel)';
            }
            if (parameter === 37446) {
                return 'ANGLE (Intel, Intel(R) UHD Graphics 630, OpenGL 4.1)';
            }
            return getParameter.apply(this, arguments);
        };

        // Canvas fingerprint randomization
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {
            const context = this.getContext('2d');
            const imageData = context.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] += Math.floor(Math.random() * 3) - 1;
            }
            context.putImageData(imageData, 0, 0);
            return originalToDataURL.apply(this, arguments);
        };

        // Remove automation indicators
        delete navigator.__proto__.webdriver;
    """

    @staticmethod
    async def apply_stealth(page, fingerprint: Optional[BrowserFingerprint] = None):
        """
        Apply stealth measures to Playwright page.

        Args:
            page: Playwright page object
            fingerprint: Browser fingerprint (generates if None)
        """
        if fingerprint is None:
            fingerprint = BrowserFingerprint.generate_realistic()

        # Set viewport
        await page.set_viewport_size(fingerprint.viewport)

        # Set user agent
        await page.set_extra_http_headers({
            'User-Agent': fingerprint.user_agent,
            'Accept-Language': ', '.join(fingerprint.languages),
        })

        # Inject stealth scripts
        await page.add_init_script(StealthBrowser.STEALTH_SCRIPTS)

        # Override navigator properties
        await page.add_init_script(f"""
            Object.defineProperty(navigator, 'platform', {{
                get: () => '{fingerprint.platform}'
            }});

            Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
                value: function() {{
                    return {{
                        ...Intl.DateTimeFormat.prototype.resolvedOptions.apply(this),
                        timeZone: '{fingerprint.timezone}'
                    }};
                }}
            }});
        """)

        logger.info("stealth_applied",
                   platform=fingerprint.platform,
                   viewport=fingerprint.viewport)

    @staticmethod
    async def randomize_mouse_movements(page):
        """Add human-like mouse movements"""
        await page.evaluate("""
            () => {
                let mouseX = 0;
                let mouseY = 0;

                document.addEventListener('mousemove', (e) => {
                    mouseX = e.clientX;
                    mouseY = e.clientY;
                });

                // Simulate random mouse movements
                setInterval(() => {
                    const event = new MouseEvent('mousemove', {
                        clientX: mouseX + Math.random() * 10 - 5,
                        clientY: mouseY + Math.random() * 10 - 5
                    });
                    document.dispatchEvent(event);
                }, 1000 + Math.random() * 1000);
            }
        """)

    @staticmethod
    async def simulate_human_typing(page, selector: str, text: str, delay_range=(50, 150)):
        """
        Type text with human-like delays.

        Args:
            page: Playwright page
            selector: Input selector
            text: Text to type
            delay_range: (min, max) delay in ms between keystrokes
        """
        element = await page.query_selector(selector)
        if not element:
            return

        await element.click()

        for char in text:
            await element.type(char)
            delay = random.randint(*delay_range)
            await page.wait_for_timeout(delay)

    @staticmethod
    async def random_scroll(page, duration: int = 2000):
        """
        Scroll page randomly to simulate human behavior.

        Args:
            page: Playwright page
            duration: Total duration in ms
        """
        await page.evaluate(f"""
            async (duration) => {{
                const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));
                const scrollHeight = document.body.scrollHeight;
                const viewportHeight = window.innerHeight;
                const maxScroll = scrollHeight - viewportHeight;

                const steps = Math.floor(duration / 100);

                for (let i = 0; i < steps; i++) {{
                    const scrollTo = Math.random() * maxScroll;
                    window.scrollTo({{
                        top: scrollTo,
                        behavior: 'smooth'
                    }});
                    await delay(100);
                }}
            }}
        """, duration)
