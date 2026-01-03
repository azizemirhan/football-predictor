"""
Football Predictor Scrapers
"""

from .base import BaseScraper, PlaywrightScraper
from .flashscore import FlashscoreScraper
from .sofascore import SofascoreScraper

__all__ = [
    "BaseScraper",
    "PlaywrightScraper",
    "FlashscoreScraper",
    "SofascoreScraper",
]
