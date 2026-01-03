"""
Celery Schedulers
"""

from .celery_config import app
from .tasks import (
    scrape_fixtures,
    scrape_results,
    scrape_live_matches,
    scrape_odds,
    scrape_news,
    update_team_ratings,
    generate_predictions,
    calculate_value_bets,
    cleanup_old_data
)

__all__ = [
    "app",
    "scrape_fixtures",
    "scrape_results",
    "scrape_live_matches",
    "scrape_odds",
    "scrape_news",
    "update_team_ratings",
    "generate_predictions",
    "calculate_value_bets",
    "cleanup_old_data"
]
