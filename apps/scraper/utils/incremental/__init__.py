"""
Incremental Scraping - Delta scraping and checkpointing
"""

from .checkpoint_manager import CheckpointManager, Checkpoint
from .delta_scraper import DeltaScraper, ScrapeSession

__all__ = [
    'CheckpointManager',
    'Checkpoint',
    'DeltaScraper',
    'ScrapeSession'
]
