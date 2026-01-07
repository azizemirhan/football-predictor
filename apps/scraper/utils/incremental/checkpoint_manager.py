"""
Checkpoint Manager - Track scraping progress and enable resumption
"""

import json
import hashlib
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import structlog

logger = structlog.get_logger()


@dataclass
class Checkpoint:
    """Scraping checkpoint"""
    scraper_name: str
    checkpoint_type: str  # 'page', 'date', 'offset', 'cursor'
    value: Any
    total_items: int = 0
    scraped_items: int = 0
    last_updated: Optional[datetime] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        if self.last_updated:
            data['last_updated'] = self.last_updated.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Checkpoint':
        """Create from dictionary"""
        if data.get('last_updated'):
            data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


class CheckpointManager:
    """
    Manage scraping checkpoints for resumable scraping.

    Features:
    - Save/load checkpoints
    - Track progress
    - Handle failures and resumption
    - Multiple checkpoint strategies
    """

    def __init__(self, checkpoint_dir: str = ".checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        scraper_name: str,
        checkpoint: Checkpoint
    ) -> str:
        """
        Save checkpoint to disk.

        Args:
            scraper_name: Name of the scraper
            checkpoint: Checkpoint data

        Returns:
            Checkpoint ID
        """
        checkpoint.last_updated = datetime.now()

        # Generate checkpoint file name
        checkpoint_id = self._generate_checkpoint_id(scraper_name)
        filepath = self.checkpoint_dir / f"{checkpoint_id}.json"

        # Save to file
        with open(filepath, 'w') as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

        logger.info(
            "checkpoint_saved",
            scraper=scraper_name,
            checkpoint_id=checkpoint_id,
            progress=f"{checkpoint.scraped_items}/{checkpoint.total_items}"
        )

        return checkpoint_id

    def load_checkpoint(
        self,
        scraper_name: str
    ) -> Optional[Checkpoint]:
        """
        Load most recent checkpoint for scraper.

        Args:
            scraper_name: Name of the scraper

        Returns:
            Checkpoint or None if not found
        """
        checkpoint_id = self._generate_checkpoint_id(scraper_name)
        filepath = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not filepath.exists():
            logger.debug("checkpoint_not_found", scraper=scraper_name)
            return None

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            checkpoint = Checkpoint.from_dict(data)

            logger.info(
                "checkpoint_loaded",
                scraper=scraper_name,
                progress=f"{checkpoint.scraped_items}/{checkpoint.total_items}"
            )

            return checkpoint

        except Exception as e:
            logger.error("checkpoint_load_error", scraper=scraper_name, error=str(e))
            return None

    def delete_checkpoint(self, scraper_name: str):
        """Delete checkpoint for scraper"""
        checkpoint_id = self._generate_checkpoint_id(scraper_name)
        filepath = self.checkpoint_dir / f"{checkpoint_id}.json"

        if filepath.exists():
            filepath.unlink()
            logger.info("checkpoint_deleted", scraper=scraper_name)

    def update_progress(
        self,
        scraper_name: str,
        scraped_items: int,
        value: Any = None
    ):
        """
        Update checkpoint progress.

        Args:
            scraper_name: Name of the scraper
            scraped_items: Number of items scraped
            value: New checkpoint value
        """
        checkpoint = self.load_checkpoint(scraper_name)

        if checkpoint:
            checkpoint.scraped_items = scraped_items
            if value is not None:
                checkpoint.value = value
            self.save_checkpoint(scraper_name, checkpoint)

    def get_progress_percentage(self, scraper_name: str) -> float:
        """Get scraping progress percentage"""
        checkpoint = self.load_checkpoint(scraper_name)

        if not checkpoint or checkpoint.total_items == 0:
            return 0.0

        return (checkpoint.scraped_items / checkpoint.total_items) * 100

    def list_checkpoints(self) -> list:
        """List all checkpoints"""
        checkpoints = []

        for filepath in self.checkpoint_dir.glob("*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                checkpoints.append(Checkpoint.from_dict(data))
            except Exception as e:
                logger.warning("checkpoint_read_error", file=filepath, error=str(e))

        return checkpoints

    def cleanup_old_checkpoints(self, days: int = 7):
        """Remove checkpoints older than N days"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        removed = 0

        for filepath in self.checkpoint_dir.glob("*.json"):
            if filepath.stat().st_mtime < cutoff:
                filepath.unlink()
                removed += 1

        if removed > 0:
            logger.info("checkpoints_cleaned", removed=removed, days=days)

    def _generate_checkpoint_id(self, scraper_name: str) -> str:
        """Generate unique checkpoint ID for scraper"""
        return hashlib.md5(scraper_name.encode()).hexdigest()[:16]
