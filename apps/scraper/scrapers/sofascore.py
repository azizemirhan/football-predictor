"""
Sofascore Scraper - Detaylı maç istatistikleri ve xG verileri
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog

from .base import BaseScraper

logger = structlog.get_logger()


class SofascoreScraper(BaseScraper):
    """
    Scraper for Sofascore.com API
    Collects: matches, detailed stats, xG, lineups, player ratings
    """
    
    BASE_URL = "https://api.sofascore.com/api/v1"
    PREMIER_LEAGUE_ID = 17  # Sofascore tournament ID for Premier League
    
    def get_source_name(self) -> str:
        return "sofascore"
    
    async def scrape(self, scrape_type: str = "fixtures", **kwargs) -> List[Dict[str, Any]]:
        """
        Main scrape method.
        
        Args:
            scrape_type: One of 'fixtures', 'results', 'live', 'standings'
            **kwargs: Additional parameters (e.g., date, season_id)
        """
        await self.init_session()
        
        try:
            if scrape_type == "fixtures":
                return await self.scrape_fixtures(**kwargs)
            elif scrape_type == "results":
                return await self.scrape_results(**kwargs)
            elif scrape_type == "live":
                return await self.scrape_live_matches()
            elif scrape_type == "standings":
                return await self.scrape_standings(**kwargs)
            else:
                raise ValueError(f"Unknown scrape_type: {scrape_type}")
        finally:
            await self.close_session()
    
    async def scrape_fixtures(self, days_ahead: int = 14) -> List[Dict[str, Any]]:
        """Scrape upcoming fixtures for next N days"""
        matches = []
        
        for day_offset in range(days_ahead):
            date = datetime.now() + timedelta(days=day_offset)
            date_str = date.strftime("%Y-%m-%d")
            
            url = f"{self.BASE_URL}/sport/football/scheduled-events/{date_str}"
            
            try:
                data = await self.fetch_json(url)
                events = data.get("events", [])
                
                for event in events:
                    # Filter for Premier League
                    tournament = event.get("tournament", {})
                    if tournament.get("uniqueTournament", {}).get("id") == self.PREMIER_LEAGUE_ID:
                        match_data = self._parse_event(event)
                        if match_data:
                            matches.append(match_data)
                            
            except Exception as e:
                logger.warning("fetch_fixtures_error", date=date_str, error=str(e))
                continue
        
        logger.info("fixtures_scraped", count=len(matches), source=self.get_source_name())
        return matches
    
    async def scrape_results(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Scrape recent results"""
        matches = []
        
        for day_offset in range(days_back):
            date = datetime.now() - timedelta(days=day_offset + 1)
            date_str = date.strftime("%Y-%m-%d")
            
            url = f"{self.BASE_URL}/sport/football/scheduled-events/{date_str}"
            
            try:
                data = await self.fetch_json(url)
                events = data.get("events", [])
                
                for event in events:
                    tournament = event.get("tournament", {})
                    if tournament.get("uniqueTournament", {}).get("id") == self.PREMIER_LEAGUE_ID:
                        if event.get("status", {}).get("type") == "finished":
                            match_data = self._parse_event(event)
                            if match_data:
                                matches.append(match_data)
                                
            except Exception as e:
                logger.warning("fetch_results_error", date=date_str, error=str(e))
                continue
        
        logger.info("results_scraped", count=len(matches), source=self.get_source_name())
        return matches
    
    async def scrape_live_matches(self) -> List[Dict[str, Any]]:
        """Scrape currently live matches"""
        url = f"{self.BASE_URL}/sport/football/events/live"
        
        try:
            data = await self.fetch_json(url)
            events = data.get("events", [])
            
            live_matches = []
            for event in events:
                tournament = event.get("tournament", {})
                if tournament.get("uniqueTournament", {}).get("id") == self.PREMIER_LEAGUE_ID:
                    match_data = self._parse_event(event)
                    if match_data:
                        match_data["status"] = "live"
                        live_matches.append(match_data)
            
            logger.info("live_matches_scraped", count=len(live_matches))
            return live_matches
            
        except Exception as e:
            logger.error("fetch_live_error", error=str(e))
            return []
    
    async def scrape_match_details(self, event_id: int) -> Dict[str, Any]:
        """Scrape detailed information for a specific match"""
        details = {
            "event_id": event_id,
            "source": self.get_source_name()
        }
        
        # Basic event info
        url = f"{self.BASE_URL}/event/{event_id}"
        try:
            event_data = await self.fetch_json(url)
            details["event"] = self._parse_event(event_data.get("event", {}))
        except Exception as e:
            logger.warning("fetch_event_error", event_id=event_id, error=str(e))
        
        # Statistics
        stats_url = f"{self.BASE_URL}/event/{event_id}/statistics"
        try:
            stats_data = await self.fetch_json(stats_url)
            details["statistics"] = self._parse_statistics(stats_data)
        except Exception as e:
            logger.debug("fetch_stats_error", event_id=event_id, error=str(e))
        
        # Lineups
        lineups_url = f"{self.BASE_URL}/event/{event_id}/lineups"
        try:
            lineups_data = await self.fetch_json(lineups_url)
            details["lineups"] = self._parse_lineups(lineups_data)
        except Exception as e:
            logger.debug("fetch_lineups_error", event_id=event_id, error=str(e))
        
        # xG data
        xg_url = f"{self.BASE_URL}/event/{event_id}/graph"
        try:
            xg_data = await self.fetch_json(xg_url)
            details["xg"] = self._parse_xg(xg_data)
        except Exception as e:
            logger.debug("fetch_xg_error", event_id=event_id, error=str(e))
        
        return details
    
    async def scrape_standings(self, season_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape current league standings"""
        url = f"{self.BASE_URL}/unique-tournament/{self.PREMIER_LEAGUE_ID}/season/{season_id or 'current'}/standings/total"
        
        try:
            data = await self.fetch_json(url)
            standings = []
            
            for standing in data.get("standings", []):
                rows = standing.get("rows", [])
                for row in rows:
                    team_data = {
                        "position": row.get("position"),
                        "team_id": row.get("team", {}).get("id"),
                        "team_name": row.get("team", {}).get("name"),
                        "played": row.get("matches"),
                        "won": row.get("wins"),
                        "drawn": row.get("draws"),
                        "lost": row.get("losses"),
                        "goals_for": row.get("scoresFor"),
                        "goals_against": row.get("scoresAgainst"),
                        "goal_difference": row.get("scoresFor", 0) - row.get("scoresAgainst", 0),
                        "points": row.get("points"),
                        "form": self._parse_form(row.get("form", {}))
                    }
                    standings.append(team_data)
            
            logger.info("standings_scraped", count=len(standings))
            return standings
            
        except Exception as e:
            logger.error("fetch_standings_error", error=str(e))
            return []
    
    async def scrape_team_stats(self, team_id: int) -> Dict[str, Any]:
        """Scrape detailed team statistics"""
        url = f"{self.BASE_URL}/team/{team_id}/unique-tournament/{self.PREMIER_LEAGUE_ID}/season/current/statistics"
        
        try:
            data = await self.fetch_json(url)
            return self._parse_team_statistics(data)
        except Exception as e:
            logger.error("fetch_team_stats_error", team_id=team_id, error=str(e))
            return {}
    
    def _parse_event(self, event: Dict) -> Optional[Dict[str, Any]]:
        """Parse a Sofascore event into our format"""
        try:
            home_team = event.get("homeTeam", {})
            away_team = event.get("awayTeam", {})
            
            status_type = event.get("status", {}).get("type", "")
            
            match_data = {
                "external_id": str(event.get("id")),
                "source": self.get_source_name(),
                "home_team": home_team.get("name"),
                "away_team": away_team.get("name"),
                "home_team_id": home_team.get("id"),
                "away_team_id": away_team.get("id"),
                "match_date": self._parse_timestamp(event.get("startTimestamp")),
                "status": self._map_status(status_type),
                "league": "Premier League",
                "country": "England",
                "round": event.get("roundInfo", {}).get("round"),
                "venue": event.get("venue", {}).get("stadium", {}).get("name"),
                "scraped_at": datetime.now().isoformat()
            }
            
            # Add scores if available
            home_score = event.get("homeScore", {})
            away_score = event.get("awayScore", {})
            
            if home_score.get("current") is not None:
                match_data["home_score"] = home_score.get("current")
                match_data["home_score_ht"] = home_score.get("period1")
            
            if away_score.get("current") is not None:
                match_data["away_score"] = away_score.get("current")
                match_data["away_score_ht"] = away_score.get("period1")
            
            # Add minute for live matches
            if status_type == "inprogress":
                match_data["minute"] = event.get("time", {}).get("currentPeriodStartTimestamp")
            
            return match_data
            
        except Exception as e:
            logger.warning("parse_event_error", error=str(e))
            return None
    
    def _parse_statistics(self, data: Dict) -> Dict[str, Any]:
        """Parse match statistics"""
        stats = {"home": {}, "away": {}}
        
        for group in data.get("statistics", []):
            for item in group.get("groups", []):
                for stat in item.get("statisticsItems", []):
                    stat_name = stat.get("name", "").lower().replace(" ", "_")
                    stats["home"][stat_name] = stat.get("home")
                    stats["away"][stat_name] = stat.get("away")
        
        return stats
    
    def _parse_lineups(self, data: Dict) -> Dict[str, Any]:
        """Parse match lineups"""
        lineups = {"home": [], "away": []}
        
        for team in ["home", "away"]:
            players = data.get(team, {}).get("players", [])
            for player in players:
                player_info = player.get("player", {})
                lineups[team].append({
                    "id": player_info.get("id"),
                    "name": player_info.get("name"),
                    "position": player.get("position"),
                    "jersey_number": player.get("jerseyNumber"),
                    "rating": player.get("statistics", {}).get("rating"),
                    "substitute": player.get("substitute", False)
                })
        
        return lineups
    
    def _parse_xg(self, data: Dict) -> Dict[str, float]:
        """Parse expected goals data"""
        xg_data = {}
        
        for point in data.get("graph", []):
            if point.get("type") == "expectedGoals":
                xg_data["home_xg"] = point.get("homeScore")
                xg_data["away_xg"] = point.get("awayScore")
                break
        
        return xg_data
    
    def _parse_form(self, form_data: Dict) -> str:
        """Parse team form data"""
        form_str = ""
        for values in form_data.get("value", []):
            if values == 1:
                form_str += "L"
            elif values == 2:
                form_str += "D"
            elif values == 3:
                form_str += "W"
        return form_str[:5]  # Last 5 results
    
    def _parse_team_statistics(self, data: Dict) -> Dict[str, Any]:
        """Parse team statistics"""
        stats = {}
        
        for group in data.get("statistics", []):
            group_name = group.get("name", "").lower().replace(" ", "_")
            stats[group_name] = {}
            
            for item in group.get("statisticsItems", []):
                stat_name = item.get("name", "").lower().replace(" ", "_")
                stats[group_name][stat_name] = {
                    "value": item.get("value"),
                    "per_match": item.get("valuePerMatch")
                }
        
        return stats
    
    def _parse_timestamp(self, timestamp: Optional[int]) -> Optional[str]:
        """Convert Unix timestamp to ISO format"""
        if timestamp:
            return datetime.fromtimestamp(timestamp).isoformat()
        return None
    
    def _map_status(self, status: str) -> str:
        """Map Sofascore status to our status"""
        mapping = {
            "notstarted": "scheduled",
            "inprogress": "live",
            "finished": "finished",
            "postponed": "postponed",
            "canceled": "cancelled"
        }
        return mapping.get(status.lower(), status)
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate match data"""
        required = ["home_team", "away_team", "external_id"]
        return all(data.get(field) for field in required)
