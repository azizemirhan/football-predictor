"""
Celery Tasks - Scheduled scraping and processing tasks
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
import structlog

from .celery_config import app
from scrapers.flashscore import FlashscoreScraper
from scrapers.sofascore import SofascoreScraper
from scrapers.odds.odds_scraper import OddsScraper
from processors.data_processor import DataProcessor
from utils.database import DatabaseManager

logger = structlog.get_logger()


def run_async(coro):
    """Helper to run async functions in Celery tasks"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ============================
# SCRAPING TASKS
# ============================

@app.task(bind=True, max_retries=3)
def scrape_fixtures(self):
    """Scrape upcoming fixtures from multiple sources"""
    logger.info("task_started", task="scrape_fixtures")
    
    try:
        all_fixtures = []
        
        # Flashscore
        async def scrape_flashscore():
            async with FlashscoreScraper() as scraper:
                return await scraper.scrape("fixtures")
        
        flashscore_fixtures = run_async(scrape_flashscore())
        all_fixtures.extend(flashscore_fixtures)
        
        # Sofascore
        async def scrape_sofascore():
            async with SofascoreScraper() as scraper:
                return await scraper.scrape("fixtures")
        
        sofascore_fixtures = run_async(scrape_sofascore())
        all_fixtures.extend(sofascore_fixtures)
        
        # Process and save
        processor = DataProcessor()
        processed = processor.process_matches(all_fixtures)
        
        db = DatabaseManager()
        saved_count = db.save_matches(processed)
        
        logger.info(
            "task_completed",
            task="scrape_fixtures",
            scraped=len(all_fixtures),
            saved=saved_count
        )
        
        return {"scraped": len(all_fixtures), "saved": saved_count}
        
    except Exception as e:
        logger.error("task_failed", task="scrape_fixtures", error=str(e))
        self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@app.task(bind=True, max_retries=3)
def scrape_results(self):
    """Scrape recent match results"""
    logger.info("task_started", task="scrape_results")
    
    try:
        all_results = []
        
        # Flashscore
        async def scrape_flashscore():
            async with FlashscoreScraper() as scraper:
                return await scraper.scrape("results")
        
        flashscore_results = run_async(scrape_flashscore())
        all_results.extend(flashscore_results)
        
        # Sofascore
        async def scrape_sofascore():
            async with SofascoreScraper() as scraper:
                return await scraper.scrape("results")
        
        sofascore_results = run_async(scrape_sofascore())
        all_results.extend(sofascore_results)
        
        # Process and save
        processor = DataProcessor()
        processed = processor.process_matches(all_results)
        
        db = DatabaseManager()
        saved_count = db.update_match_results(processed)
        
        logger.info(
            "task_completed",
            task="scrape_results",
            scraped=len(all_results),
            saved=saved_count
        )
        
        return {"scraped": len(all_results), "saved": saved_count}
        
    except Exception as e:
        logger.error("task_failed", task="scrape_results", error=str(e))
        self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@app.task(bind=True)
def scrape_live_matches(self):
    """Scrape currently live matches"""
    logger.info("task_started", task="scrape_live_matches")
    
    try:
        async def scrape_live():
            async with SofascoreScraper() as scraper:
                return await scraper.scrape("live")
        
        live_matches = run_async(scrape_live())
        
        if live_matches:
            db = DatabaseManager()
            db.update_live_matches(live_matches)
            
            # Publish to Redis for real-time updates
            # redis_client.publish("live_updates", json.dumps(live_matches))
        
        logger.info(
            "task_completed",
            task="scrape_live_matches",
            live_count=len(live_matches)
        )
        
        return {"live_matches": len(live_matches)}
        
    except Exception as e:
        logger.error("task_failed", task="scrape_live_matches", error=str(e))
        return {"error": str(e)}


@app.task(bind=True, max_retries=3)
def scrape_odds(self):
    """Scrape betting odds"""
    logger.info("task_started", task="scrape_odds")
    
    try:
        async def scrape():
            async with OddsScraper() as scraper:
                return await scraper.scrape()
        
        odds_data = run_async(scrape())
        
        processor = DataProcessor()
        processed = processor.process_odds(odds_data)
        
        db = DatabaseManager()
        saved_count = db.save_odds(processed)
        
        logger.info(
            "task_completed",
            task="scrape_odds",
            scraped=len(odds_data),
            saved=saved_count
        )
        
        return {"scraped": len(odds_data), "saved": saved_count}
        
    except Exception as e:
        logger.error("task_failed", task="scrape_odds", error=str(e))
        self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@app.task(bind=True, max_retries=3)
def scrape_news(self):
    """Scrape football news"""
    logger.info("task_started", task="scrape_news")
    
    try:
        # TODO: Implement news scraping
        logger.info("task_completed", task="scrape_news", count=0)
        return {"scraped": 0}
        
    except Exception as e:
        logger.error("task_failed", task="scrape_news", error=str(e))
        self.retry(exc=e, countdown=60 * (self.request.retries + 1))


# ============================
# PROCESSING TASKS
# ============================

@app.task(bind=True)
def update_team_ratings(self):
    """Update Elo ratings for all teams"""
    logger.info("task_started", task="update_team_ratings")
    
    try:
        db = DatabaseManager()
        
        # Get recent results
        recent_matches = db.get_recent_matches(days=1)
        
        # TODO: Update Elo ratings based on results
        updated_count = 0
        
        logger.info(
            "task_completed",
            task="update_team_ratings",
            updated=updated_count
        )
        
        return {"updated": updated_count}
        
    except Exception as e:
        logger.error("task_failed", task="update_team_ratings", error=str(e))
        return {"error": str(e)}


@app.task(bind=True)
def generate_predictions(self):
    """Generate predictions for upcoming matches"""
    logger.info("task_started", task="generate_predictions")
    
    try:
        db = DatabaseManager()
        
        # Get upcoming matches
        upcoming = db.get_upcoming_matches(days=3)
        
        # TODO: Call AI engine to generate predictions
        generated_count = 0
        
        logger.info(
            "task_completed",
            task="generate_predictions",
            matches=len(upcoming),
            generated=generated_count
        )
        
        return {"matches": len(upcoming), "generated": generated_count}
        
    except Exception as e:
        logger.error("task_failed", task="generate_predictions", error=str(e))
        return {"error": str(e)}


@app.task(bind=True)
def calculate_value_bets(self):
    """Calculate value bets based on predictions and odds"""
    logger.info("task_started", task="calculate_value_bets")
    
    try:
        db = DatabaseManager()
        
        # TODO: Calculate value bets
        value_bets_count = 0
        
        logger.info(
            "task_completed",
            task="calculate_value_bets",
            found=value_bets_count
        )
        
        return {"value_bets": value_bets_count}
        
    except Exception as e:
        logger.error("task_failed", task="calculate_value_bets", error=str(e))
        return {"error": str(e)}


# ============================
# MAINTENANCE TASKS
# ============================

@app.task(bind=True)
def cleanup_old_data(self):
    """Cleanup old data from database"""
    logger.info("task_started", task="cleanup_old_data")
    
    try:
        db = DatabaseManager()
        
        # Delete old scraping logs (older than 30 days)
        deleted_logs = db.cleanup_scraping_logs(days=30)
        
        # Delete old odds (older than 7 days)
        deleted_odds = db.cleanup_old_odds(days=7)
        
        logger.info(
            "task_completed",
            task="cleanup_old_data",
            deleted_logs=deleted_logs,
            deleted_odds=deleted_odds
        )
        
        return {
            "deleted_logs": deleted_logs,
            "deleted_odds": deleted_odds
        }
        
    except Exception as e:
        logger.error("task_failed", task="cleanup_old_data", error=str(e))
        return {"error": str(e)}
