"""
Odds Scraper - Bahis oranları toplama
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog

from ..base import BaseScraper

logger = structlog.get_logger()


class OddsScraper(BaseScraper):
    """
    Scraper for betting odds from multiple sources.
    Collects: 1X2 odds, Over/Under, BTTS, Asian Handicap
    """
    
    # Odds API endpoints (using example - actual implementation would use real APIs)
    ODDS_API_URL = "https://api.the-odds-api.com/v4"
    
    # Bookmakers to track
    BOOKMAKERS = [
        "bet365",
        "pinnacle",
        "williamhill",
        "unibet",
        "betfair",
        "1xbet",
        "betway"
    ]
    
    # Market types
    MARKETS = ["h2h", "spreads", "totals"]  # 1X2, Asian Handicap, Over/Under
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
    
    def get_source_name(self) -> str:
        return "odds_api"
    
    async def scrape(self, **kwargs) -> List[Dict[str, Any]]:
        """Scrape odds for Premier League matches"""
        await self.init_session()
        
        try:
            return await self.scrape_premier_league_odds()
        finally:
            await self.close_session()
    
    async def scrape_premier_league_odds(self) -> List[Dict[str, Any]]:
        """Scrape odds for all upcoming Premier League matches"""
        all_odds = []
        
        for market in self.MARKETS:
            try:
                url = f"{self.ODDS_API_URL}/sports/soccer_england_epl/odds"
                params = {
                    "apiKey": self.api_key,
                    "regions": "uk,eu",
                    "markets": market,
                    "oddsFormat": "decimal"
                }
                
                data = await self.fetch_json(url, params=params)
                
                for match in data:
                    odds_data = self._parse_match_odds(match, market)
                    if odds_data:
                        all_odds.append(odds_data)
                        
            except Exception as e:
                logger.warning("fetch_odds_error", market=market, error=str(e))
                continue
        
        logger.info("odds_scraped", count=len(all_odds))
        return self._merge_odds(all_odds)
    
    def _parse_match_odds(self, match: Dict, market: str) -> Optional[Dict]:
        """Parse odds for a single match"""
        try:
            match_data = {
                "external_id": match.get("id"),
                "source": self.get_source_name(),
                "home_team": match.get("home_team"),
                "away_team": match.get("away_team"),
                "match_date": match.get("commence_time"),
                "market_type": market,
                "bookmakers": [],
                "scraped_at": datetime.now().isoformat()
            }
            
            for bookmaker in match.get("bookmakers", []):
                bookie_name = bookmaker.get("key")
                if bookie_name not in self.BOOKMAKERS:
                    continue
                
                bookie_odds = {
                    "name": bookie_name,
                    "last_update": bookmaker.get("last_update"),
                    "markets": {}
                }
                
                for market_data in bookmaker.get("markets", []):
                    market_key = market_data.get("key")
                    outcomes = {}
                    
                    for outcome in market_data.get("outcomes", []):
                        name = outcome.get("name")
                        price = outcome.get("price")
                        point = outcome.get("point")
                        
                        if point is not None:
                            outcomes[f"{name}_{point}"] = price
                        else:
                            outcomes[name] = price
                    
                    bookie_odds["markets"][market_key] = outcomes
                
                match_data["bookmakers"].append(bookie_odds)
            
            return match_data if match_data["bookmakers"] else None
            
        except Exception as e:
            logger.warning("parse_odds_error", error=str(e))
            return None
    
    def _merge_odds(self, odds_list: List[Dict]) -> List[Dict]:
        """Merge odds from different markets for the same match"""
        merged = {}
        
        for odds in odds_list:
            match_key = f"{odds['home_team']}_{odds['away_team']}_{odds['match_date']}"
            
            if match_key not in merged:
                merged[match_key] = {
                    "external_id": odds["external_id"],
                    "source": odds["source"],
                    "home_team": odds["home_team"],
                    "away_team": odds["away_team"],
                    "match_date": odds["match_date"],
                    "odds": {},
                    "scraped_at": odds["scraped_at"]
                }
            
            # Merge bookmaker odds
            for bookmaker in odds.get("bookmakers", []):
                bookie_name = bookmaker["name"]
                if bookie_name not in merged[match_key]["odds"]:
                    merged[match_key]["odds"][bookie_name] = {}
                
                for market_key, outcomes in bookmaker.get("markets", {}).items():
                    merged[match_key]["odds"][bookie_name][market_key] = outcomes
        
        return list(merged.values())
    
    def calculate_implied_probability(self, odds: float) -> float:
        """Calculate implied probability from decimal odds"""
        if odds <= 0:
            return 0
        return 1 / odds
    
    def calculate_overround(self, home_odds: float, draw_odds: float, away_odds: float) -> float:
        """Calculate bookmaker overround (margin)"""
        if 0 in [home_odds, draw_odds, away_odds]:
            return 0
        
        implied = (
            self.calculate_implied_probability(home_odds) +
            self.calculate_implied_probability(draw_odds) +
            self.calculate_implied_probability(away_odds)
        )
        return (implied - 1) * 100
    
    def get_best_odds(self, odds_data: Dict) -> Dict[str, Dict]:
        """Get best available odds for each outcome across all bookmakers"""
        best_odds = {
            "h2h": {"home": 0, "draw": 0, "away": 0},
            "over_2.5": 0,
            "under_2.5": 0,
            "btts_yes": 0,
            "btts_no": 0
        }
        
        for bookie_name, markets in odds_data.get("odds", {}).items():
            # 1X2
            h2h = markets.get("h2h", {})
            best_odds["h2h"]["home"] = max(best_odds["h2h"]["home"], h2h.get("Home Team", 0))
            best_odds["h2h"]["draw"] = max(best_odds["h2h"]["draw"], h2h.get("Draw", 0))
            best_odds["h2h"]["away"] = max(best_odds["h2h"]["away"], h2h.get("Away Team", 0))
            
            # Totals
            totals = markets.get("totals", {})
            best_odds["over_2.5"] = max(best_odds["over_2.5"], totals.get("Over_2.5", 0))
            best_odds["under_2.5"] = max(best_odds["under_2.5"], totals.get("Under_2.5", 0))
        
        return best_odds
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate odds data"""
        return bool(data.get("home_team") and data.get("away_team") and data.get("odds"))
