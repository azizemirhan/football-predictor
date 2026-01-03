"""
Data Processor - Verileri temizleme ve dönüştürme
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog
import pandas as pd

logger = structlog.get_logger()


class DataProcessor:
    """
    Process and clean scraped data before saving to database.
    """
    
    # Team name normalization mapping
    TEAM_NAME_MAPPING = {
        # Premier League variations
        "manchester united": "Manchester United",
        "man utd": "Manchester United",
        "man united": "Manchester United",
        "manchester city": "Manchester City",
        "man city": "Manchester City",
        "tottenham hotspur": "Tottenham Hotspur",
        "tottenham": "Tottenham Hotspur",
        "spurs": "Tottenham Hotspur",
        "wolverhampton wanderers": "Wolverhampton",
        "wolverhampton": "Wolverhampton",
        "wolves": "Wolverhampton",
        "west ham united": "West Ham United",
        "west ham": "West Ham United",
        "newcastle united": "Newcastle United",
        "newcastle": "Newcastle United",
        "nottingham forest": "Nottingham Forest",
        "nott'm forest": "Nottingham Forest",
        "brighton & hove albion": "Brighton",
        "brighton and hove albion": "Brighton",
        "brighton hove albion": "Brighton",
        "crystal palace": "Crystal Palace",
        "leicester city": "Leicester City",
        "leicester": "Leicester City",
        "aston villa": "Aston Villa",
        "ipswich town": "Ipswich Town",
        "ipswich": "Ipswich Town",
    }
    
    def __init__(self):
        self._team_cache = {}
    
    def process_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Process and deduplicate match data.
        
        Args:
            matches: Raw match data from scrapers
            
        Returns:
            Processed and deduplicated match list
        """
        processed = []
        seen = set()
        
        for match in matches:
            try:
                # Normalize team names
                match["home_team"] = self.normalize_team_name(match.get("home_team", ""))
                match["away_team"] = self.normalize_team_name(match.get("away_team", ""))
                
                # Skip invalid matches
                if not match["home_team"] or not match["away_team"]:
                    continue
                
                # Create unique key for deduplication
                match_key = self._create_match_key(match)
                
                if match_key in seen:
                    continue
                seen.add(match_key)
                
                # Clean and validate data
                cleaned = self._clean_match_data(match)
                if cleaned:
                    processed.append(cleaned)
                    
            except Exception as e:
                logger.warning("process_match_error", error=str(e))
                continue
        
        logger.info("matches_processed", raw=len(matches), processed=len(processed))
        return processed
    
    def process_odds(self, odds_list: List[Dict]) -> List[Dict]:
        """
        Process odds data.
        
        Args:
            odds_list: Raw odds data from scrapers
            
        Returns:
            Processed odds list
        """
        processed = []
        
        for odds in odds_list:
            try:
                # Normalize team names
                odds["home_team"] = self.normalize_team_name(odds.get("home_team", ""))
                odds["away_team"] = self.normalize_team_name(odds.get("away_team", ""))
                
                if not odds["home_team"] or not odds["away_team"]:
                    continue
                
                # Extract best odds
                odds["best_odds"] = self._extract_best_odds(odds.get("odds", {}))
                
                # Calculate implied probabilities
                if odds["best_odds"].get("home"):
                    odds["implied_probs"] = self._calculate_implied_probs(odds["best_odds"])
                
                processed.append(odds)
                
            except Exception as e:
                logger.warning("process_odds_error", error=str(e))
                continue
        
        logger.info("odds_processed", raw=len(odds_list), processed=len(processed))
        return processed
    
    def process_stats(self, stats_list: List[Dict]) -> List[Dict]:
        """
        Process match statistics data.
        
        Args:
            stats_list: Raw statistics data
            
        Returns:
            Processed statistics list
        """
        processed = []
        
        for stats in stats_list:
            try:
                cleaned = {
                    "match_id": stats.get("match_id"),
                    "source": stats.get("source"),
                    "home_stats": self._normalize_stats(stats.get("home_stats", {})),
                    "away_stats": self._normalize_stats(stats.get("away_stats", {})),
                    "processed_at": datetime.now().isoformat()
                }
                processed.append(cleaned)
                
            except Exception as e:
                logger.warning("process_stats_error", error=str(e))
                continue
        
        return processed
    
    def normalize_team_name(self, name: str) -> str:
        """Normalize team name to standard format"""
        if not name:
            return ""
        
        # Check cache
        if name in self._team_cache:
            return self._team_cache[name]
        
        # Clean and normalize
        cleaned = name.strip().lower()
        
        # Check mapping
        if cleaned in self.TEAM_NAME_MAPPING:
            result = self.TEAM_NAME_MAPPING[cleaned]
        else:
            # Title case with proper handling
            result = self._title_case(name)
        
        self._team_cache[name] = result
        return result
    
    def _title_case(self, name: str) -> str:
        """Proper title case for team names"""
        # Handle special cases
        name = name.strip()
        
        # Common abbreviations to preserve
        preserve = {"FC", "AFC", "CF", "SC", "AC"}
        
        words = name.split()
        result = []
        
        for word in words:
            upper = word.upper()
            if upper in preserve:
                result.append(upper)
            else:
                result.append(word.capitalize())
        
        return " ".join(result)
    
    def _create_match_key(self, match: Dict) -> str:
        """Create unique key for match deduplication"""
        home = match.get("home_team", "").lower()
        away = match.get("away_team", "").lower()
        
        # Parse date to just date portion
        date_str = match.get("match_date", "")
        if isinstance(date_str, str) and date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_str = dt.strftime("%Y-%m-%d")
            except:
                pass
        
        return f"{home}|{away}|{date_str}"
    
    def _clean_match_data(self, match: Dict) -> Optional[Dict]:
        """Clean and validate match data"""
        cleaned = {
            "home_team": match["home_team"],
            "away_team": match["away_team"],
            "match_date": self._parse_date(match.get("match_date")),
            "status": match.get("status", "scheduled"),
            "league": match.get("league", "Premier League"),
            "country": match.get("country", "England"),
            "external_ids": {
                match.get("source", "unknown"): match.get("external_id")
            },
            "scraped_at": datetime.now().isoformat()
        }
        
        # Add optional fields
        for field in ["home_score", "away_score", "home_score_ht", "away_score_ht",
                      "venue", "referee", "matchday", "round", "minute"]:
            if match.get(field) is not None:
                cleaned[field] = match[field]
        
        return cleaned
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse and normalize date string"""
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str.isoformat()
        
        # Try various formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M",
            "%d.%m.%Y %H:%M",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.split("+")[0].split("Z")[0], fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        return date_str
    
    def _extract_best_odds(self, odds_data: Dict) -> Dict:
        """Extract best odds from multiple bookmakers"""
        best = {
            "home": 0,
            "draw": 0,
            "away": 0,
            "over_2.5": 0,
            "under_2.5": 0
        }
        
        for bookie, markets in odds_data.items():
            # 1X2
            h2h = markets.get("h2h", {})
            if h2h.get("Home Team", 0) > best["home"]:
                best["home"] = h2h["Home Team"]
                best["home_bookie"] = bookie
            if h2h.get("Draw", 0) > best["draw"]:
                best["draw"] = h2h["Draw"]
                best["draw_bookie"] = bookie
            if h2h.get("Away Team", 0) > best["away"]:
                best["away"] = h2h["Away Team"]
                best["away_bookie"] = bookie
            
            # Totals
            totals = markets.get("totals", {})
            if totals.get("Over_2.5", 0) > best["over_2.5"]:
                best["over_2.5"] = totals["Over_2.5"]
            if totals.get("Under_2.5", 0) > best["under_2.5"]:
                best["under_2.5"] = totals["Under_2.5"]
        
        return best
    
    def _calculate_implied_probs(self, odds: Dict) -> Dict:
        """Calculate implied probabilities from odds"""
        probs = {}
        
        for outcome in ["home", "draw", "away"]:
            if odds.get(outcome, 0) > 0:
                probs[f"{outcome}_prob"] = 1 / odds[outcome]
        
        # Normalize to sum to 1
        total = sum(probs.values())
        if total > 0:
            probs = {k: v / total for k, v in probs.items()}
        
        return probs
    
    def _normalize_stats(self, stats: Dict) -> Dict:
        """Normalize statistics field names"""
        mapping = {
            "Ball Possession": "possession",
            "Total Shots": "shots",
            "Shots on Target": "shots_on_target",
            "Corner Kicks": "corners",
            "Fouls": "fouls",
            "Yellow Cards": "yellow_cards",
            "Red Cards": "red_cards",
            "Passes": "passes",
            "Pass Accuracy": "pass_accuracy",
            "Expected Goals": "xg",
            "Expected Goals Against": "xg_against",
        }
        
        normalized = {}
        for key, value in stats.items():
            normalized_key = mapping.get(key, key.lower().replace(" ", "_"))
            normalized[normalized_key] = value
        
        return normalized


class DataValidator:
    """Validate data integrity and quality"""
    
    @staticmethod
    def validate_match(match: Dict) -> List[str]:
        """Validate match data, return list of errors"""
        errors = []
        
        # Required fields
        if not match.get("home_team"):
            errors.append("Missing home_team")
        if not match.get("away_team"):
            errors.append("Missing away_team")
        if not match.get("match_date"):
            errors.append("Missing match_date")
        
        # Same team check
        if match.get("home_team") == match.get("away_team"):
            errors.append("Home and away teams are the same")
        
        # Score validation for finished matches
        if match.get("status") == "finished":
            if match.get("home_score") is None:
                errors.append("Missing home_score for finished match")
            if match.get("away_score") is None:
                errors.append("Missing away_score for finished match")
        
        return errors
    
    @staticmethod
    def validate_odds(odds: Dict) -> List[str]:
        """Validate odds data, return list of errors"""
        errors = []
        
        if not odds.get("home_team"):
            errors.append("Missing home_team")
        if not odds.get("away_team"):
            errors.append("Missing away_team")
        
        # Check odds values are positive
        for outcome in ["home", "draw", "away"]:
            value = odds.get("best_odds", {}).get(outcome, 0)
            if value < 1:
                errors.append(f"Invalid {outcome} odds: {value}")
        
        return errors
