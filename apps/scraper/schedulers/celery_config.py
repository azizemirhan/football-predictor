"""
Celery Configuration - Task queue for scheduled scraping
"""

import os
from celery import Celery
from celery.schedules import crontab

# Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create Celery app
app = Celery(
    "football_predictor",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "schedulers.tasks"
    ]
)

# Celery configuration
app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max per task
    task_soft_time_limit=540,  # Soft limit 9 minutes
    
    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Celery Beat Schedule - Periodic tasks
app.conf.beat_schedule = {
    # Scrape fixtures every 6 hours
    "scrape-fixtures": {
        "task": "schedulers.tasks.scrape_fixtures",
        "schedule": crontab(minute=0, hour="*/6"),
        "options": {"queue": "scraping"}
    },
    
    # Scrape results every hour during match days
    "scrape-results": {
        "task": "schedulers.tasks.scrape_results",
        "schedule": crontab(minute=30),
        "options": {"queue": "scraping"}
    },
    
    # Scrape live matches every 2 minutes during match hours
    "scrape-live": {
        "task": "schedulers.tasks.scrape_live_matches",
        "schedule": crontab(minute="*/2"),
        "options": {"queue": "live"}
    },
    
    # Scrape odds every 15 minutes
    "scrape-odds": {
        "task": "schedulers.tasks.scrape_odds",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "scraping"}
    },
    
    # Scrape news every 30 minutes
    "scrape-news": {
        "task": "schedulers.tasks.scrape_news",
        "schedule": crontab(minute="*/30"),
        "options": {"queue": "scraping"}
    },
    
    # Update team ratings daily at 3 AM
    "update-ratings": {
        "task": "schedulers.tasks.update_team_ratings",
        "schedule": crontab(minute=0, hour=3),
        "options": {"queue": "processing"}
    },
    
    # Generate predictions daily at 4 AM
    "generate-predictions": {
        "task": "schedulers.tasks.generate_predictions",
        "schedule": crontab(minute=0, hour=4),
        "options": {"queue": "processing"}
    },
    
    # Calculate value bets hourly
    "calculate-value-bets": {
        "task": "schedulers.tasks.calculate_value_bets",
        "schedule": crontab(minute=0),
        "options": {"queue": "processing"}
    },
    
    # Data cleanup weekly
    "data-cleanup": {
        "task": "schedulers.tasks.cleanup_old_data",
        "schedule": crontab(minute=0, hour=2, day_of_week=0),
        "options": {"queue": "maintenance"}
    }
}

# Task routing
app.conf.task_routes = {
    "schedulers.tasks.scrape_*": {"queue": "scraping"},
    "schedulers.tasks.update_*": {"queue": "processing"},
    "schedulers.tasks.generate_*": {"queue": "processing"},
    "schedulers.tasks.calculate_*": {"queue": "processing"},
    "schedulers.tasks.cleanup_*": {"queue": "maintenance"},
}

if __name__ == "__main__":
    app.start()
