"""
Database Manager - PostgreSQL database operations
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

logger = structlog.get_logger()


class DatabaseManager:
    """
    Manage all database operations.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://football_admin:password@localhost:5432/football_predictor"
        )
        
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    # ============================
    # MATCH OPERATIONS
    # ============================
    
    def save_matches(self, matches: List[Dict]) -> int:
        """Save or update matches in database"""
        saved_count = 0
        
        with self.get_session() as session:
            for match in matches:
                try:
                    # Check if match exists
                    existing = self._find_match(
                        session,
                        match["home_team"],
                        match["away_team"],
                        match.get("match_date")
                    )
                    
                    if existing:
                        # Update existing match
                        self._update_match(session, existing["id"], match)
                    else:
                        # Insert new match
                        self._insert_match(session, match)
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.warning("save_match_error", error=str(e))
                    continue
        
        logger.info("matches_saved", count=saved_count)
        return saved_count
    
    def _find_match(self, session: Session, home_team: str, away_team: str, 
                    match_date: Optional[str]) -> Optional[Dict]:
        """Find existing match by teams and date"""
        
        # Get team IDs
        home_id = self._get_team_id(session, home_team)
        away_id = self._get_team_id(session, away_team)
        
        if not home_id or not away_id:
            return None
        
        query = text("""
            SELECT id, uuid, status, home_score, away_score
            FROM matches
            WHERE home_team_id = :home_id
              AND away_team_id = :away_id
              AND DATE(match_date) = DATE(:match_date)
            LIMIT 1
        """)
        
        result = session.execute(query, {
            "home_id": home_id,
            "away_id": away_id,
            "match_date": match_date
        }).fetchone()
        
        if result:
            return dict(result._mapping)
        return None
    
    def _insert_match(self, session: Session, match: Dict):
        """Insert new match"""
        
        # Get team IDs
        home_id = self._get_or_create_team(session, match["home_team"])
        away_id = self._get_or_create_team(session, match["away_team"])
        
        # Get league and season IDs
        league_id = self._get_league_id(session, match.get("league", "Premier League"))
        season_id = self._get_current_season_id(session, league_id)
        
        query = text("""
            INSERT INTO matches (
                season_id, league_id, home_team_id, away_team_id,
                match_date, matchday, venue, status, external_ids
            ) VALUES (
                :season_id, :league_id, :home_id, :away_id,
                :match_date, :matchday, :venue, :status, :external_ids
            )
        """)
        
        session.execute(query, {
            "season_id": season_id,
            "league_id": league_id,
            "home_id": home_id,
            "away_id": away_id,
            "match_date": match.get("match_date"),
            "matchday": match.get("matchday"),
            "venue": match.get("venue"),
            "status": match.get("status", "scheduled"),
            "external_ids": str(match.get("external_ids", {}))
        })
    
    def _update_match(self, session: Session, match_id: int, match: Dict):
        """Update existing match"""
        
        update_fields = []
        params = {"id": match_id}
        
        if match.get("status"):
            update_fields.append("status = :status")
            params["status"] = match["status"]
        
        if match.get("home_score") is not None:
            update_fields.append("home_score = :home_score")
            params["home_score"] = match["home_score"]
        
        if match.get("away_score") is not None:
            update_fields.append("away_score = :away_score")
            params["away_score"] = match["away_score"]
        
        if match.get("minute") is not None:
            update_fields.append("minute = :minute")
            params["minute"] = match["minute"]
        
        if update_fields:
            query = text(f"""
                UPDATE matches SET {', '.join(update_fields)}, updated_at = NOW()
                WHERE id = :id
            """)
            session.execute(query, params)
    
    def update_match_results(self, matches: List[Dict]) -> int:
        """Update match results"""
        return self.save_matches(matches)
    
    def update_live_matches(self, matches: List[Dict]):
        """Update live match data"""
        with self.get_session() as session:
            for match in matches:
                try:
                    existing = self._find_match(
                        session,
                        match["home_team"],
                        match["away_team"],
                        match.get("match_date")
                    )
                    
                    if existing:
                        self._update_match(session, existing["id"], match)
                        
                except Exception as e:
                    logger.warning("update_live_error", error=str(e))
                    continue
    
    def get_upcoming_matches(self, days: int = 7) -> List[Dict]:
        """Get upcoming matches for next N days"""
        with self.get_session() as session:
            query = text("""
                SELECT m.*, 
                       ht.name as home_team_name,
                       at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE m.status = 'scheduled'
                  AND m.match_date BETWEEN NOW() AND NOW() + :interval
                ORDER BY m.match_date
            """)
            
            result = session.execute(query, {"interval": f"{days} days"})
            return [dict(row._mapping) for row in result]
    
    def get_recent_matches(self, days: int = 7) -> List[Dict]:
        """Get recent finished matches"""
        with self.get_session() as session:
            query = text("""
                SELECT m.*, 
                       ht.name as home_team_name,
                       at.name as away_team_name
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE m.status = 'finished'
                  AND m.match_date >= NOW() - :interval
                ORDER BY m.match_date DESC
            """)
            
            result = session.execute(query, {"interval": f"{days} days"})
            return [dict(row._mapping) for row in result]
    
    # ============================
    # TEAM OPERATIONS
    # ============================
    
    def _get_team_id(self, session: Session, team_name: str) -> Optional[int]:
        """Get team ID by name"""
        query = text("SELECT id FROM teams WHERE name = :name LIMIT 1")
        result = session.execute(query, {"name": team_name}).fetchone()
        return result[0] if result else None
    
    def _get_or_create_team(self, session: Session, team_name: str) -> int:
        """Get team ID or create new team"""
        team_id = self._get_team_id(session, team_name)
        
        if not team_id:
            query = text("""
                INSERT INTO teams (name, country)
                VALUES (:name, 'England')
                RETURNING id
            """)
            result = session.execute(query, {"name": team_name}).fetchone()
            team_id = result[0]
            logger.info("team_created", name=team_name, id=team_id)
        
        return team_id
    
    # ============================
    # LEAGUE/SEASON OPERATIONS
    # ============================
    
    def _get_league_id(self, session: Session, league_name: str) -> Optional[int]:
        """Get league ID by name"""
        query = text("SELECT id FROM leagues WHERE name = :name LIMIT 1")
        result = session.execute(query, {"name": league_name}).fetchone()
        return result[0] if result else None
    
    def _get_current_season_id(self, session: Session, league_id: int) -> Optional[int]:
        """Get current season ID for league"""
        query = text("""
            SELECT id FROM seasons 
            WHERE league_id = :league_id AND is_current = true 
            LIMIT 1
        """)
        result = session.execute(query, {"league_id": league_id}).fetchone()
        return result[0] if result else None
    
    # ============================
    # ODDS OPERATIONS
    # ============================
    
    def save_odds(self, odds_list: List[Dict]) -> int:
        """Save odds data"""
        saved_count = 0
        
        with self.get_session() as session:
            for odds in odds_list:
                try:
                    # Find match
                    match = self._find_match(
                        session,
                        odds["home_team"],
                        odds["away_team"],
                        odds.get("match_date")
                    )
                    
                    if not match:
                        continue
                    
                    # Insert odds
                    best = odds.get("best_odds", {})
                    query = text("""
                        INSERT INTO odds (
                            match_id, bookmaker, market_type,
                            home_odds, draw_odds, away_odds
                        ) VALUES (
                            :match_id, :bookmaker, '1x2',
                            :home_odds, :draw_odds, :away_odds
                        )
                    """)
                    
                    session.execute(query, {
                        "match_id": match["id"],
                        "bookmaker": "best",
                        "home_odds": best.get("home", 0),
                        "draw_odds": best.get("draw", 0),
                        "away_odds": best.get("away", 0)
                    })
                    
                    saved_count += 1
                    
                except Exception as e:
                    logger.warning("save_odds_error", error=str(e))
                    continue
        
        return saved_count
    
    # ============================
    # CLEANUP OPERATIONS
    # ============================
    
    def cleanup_scraping_logs(self, days: int = 30) -> int:
        """Delete old scraping logs"""
        with self.get_session() as session:
            query = text("""
                DELETE FROM scraping_logs
                WHERE started_at < NOW() - :interval
            """)
            result = session.execute(query, {"interval": f"{days} days"})
            return result.rowcount
    
    def cleanup_old_odds(self, days: int = 7) -> int:
        """Delete old odds data"""
        with self.get_session() as session:
            query = text("""
                DELETE FROM odds
                WHERE recorded_at < NOW() - :interval
            """)
            result = session.execute(query, {"interval": f"{days} days"})
            return result.rowcount
