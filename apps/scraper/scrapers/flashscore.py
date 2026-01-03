"""
Flashscore Scraper - Premier League maç verileri
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import structlog

from .base import PlaywrightScraper

logger = structlog.get_logger()


class FlashscoreScraper(PlaywrightScraper):
    """
    Scraper for Flashscore.com
    Collects: matches, live scores, match statistics
    """
    
    BASE_URL = "https://www.flashscore.com"
    PREMIER_LEAGUE_URL = f"{BASE_URL}/football/england/premier-league"
    
    def get_source_name(self) -> str:
        return "flashscore"
    
    async def scrape(self, scrape_type: str = "fixtures") -> List[Dict[str, Any]]:
        """
        Main scrape method.
        
        Args:
            scrape_type: One of 'fixtures', 'results', 'live'
            
        Returns:
            List of match data dictionaries
        """
        await self.init_browser()
        
        try:
            if scrape_type == "fixtures":
                return await self.scrape_fixtures()
            elif scrape_type == "results":
                return await self.scrape_results()
            elif scrape_type == "live":
                return await self.scrape_live_matches()
            else:
                raise ValueError(f"Unknown scrape_type: {scrape_type}")
        finally:
            await self.close_browser()
    
    async def scrape_fixtures(self) -> List[Dict[str, Any]]:
        """Scrape upcoming fixtures"""
        url = f"{self.PREMIER_LEAGUE_URL}/fixtures/"
        await self.navigate(url, wait_selector=".event__match")
        
        # Wait for matches to load
        await self.page.wait_for_timeout(2000)
        
        html = await self.get_content()
        soup = self.parse_html(html)
        
        matches = []
        
        # Find all match elements
        match_elements = soup.select(".event__match")
        current_date = None
        
        for match_el in match_elements:
            try:
                # Check for date header
                date_header = match_el.find_previous_sibling(class_="event__header")
                if date_header:
                    date_text = date_header.get_text(strip=True)
                    current_date = self._parse_date_header(date_text)
                
                match_data = self._parse_match_element(match_el, current_date)
                if match_data and self.validate_data(match_data):
                    matches.append(match_data)
                    
            except Exception as e:
                logger.warning("parse_match_error", error=str(e))
                continue
        
        logger.info("fixtures_scraped", count=len(matches))
        return matches
    
    async def scrape_results(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Scrape recent results"""
        url = f"{self.PREMIER_LEAGUE_URL}/results/"
        await self.navigate(url, wait_selector=".event__match")
        
        # Scroll to load more results
        await self.scroll_to_bottom()
        await self.page.wait_for_timeout(2000)
        
        html = await self.get_content()
        soup = self.parse_html(html)
        
        matches = []
        match_elements = soup.select(".event__match")
        current_date = None
        
        for match_el in match_elements:
            try:
                date_header = match_el.find_previous_sibling(class_="event__header")
                if date_header:
                    date_text = date_header.get_text(strip=True)
                    current_date = self._parse_date_header(date_text)
                
                match_data = self._parse_result_element(match_el, current_date)
                if match_data and self.validate_data(match_data):
                    matches.append(match_data)
                    
            except Exception as e:
                logger.warning("parse_result_error", error=str(e))
                continue
        
        logger.info("results_scraped", count=len(matches))
        return matches
    
    async def scrape_live_matches(self) -> List[Dict[str, Any]]:
        """Scrape currently live matches"""
        url = self.PREMIER_LEAGUE_URL
        await self.navigate(url, wait_selector="body")
        
        html = await self.get_content()
        soup = self.parse_html(html)
        
        live_matches = []
        
        # Find live match elements
        live_elements = soup.select(".event__match--live")
        
        for match_el in live_elements:
            try:
                match_data = self._parse_live_match(match_el)
                if match_data:
                    live_matches.append(match_data)
            except Exception as e:
                logger.warning("parse_live_error", error=str(e))
                continue
        
        logger.info("live_matches_scraped", count=len(live_matches))
        return live_matches
    
    async def scrape_match_stats(self, match_id: str) -> Dict[str, Any]:
        """Scrape detailed statistics for a specific match"""
        url = f"{self.BASE_URL}/match/{match_id}/#/match-summary/match-statistics/0"
        await self.navigate(url)
        await self.page.wait_for_timeout(2000)
        
        html = await self.get_content()
        soup = self.parse_html(html)
        
        stats = {
            "match_id": match_id,
            "home_stats": {},
            "away_stats": {}
        }
        
        # Parse statistics rows
        stat_rows = soup.select(".stat__row")
        
        for row in stat_rows:
            try:
                stat_name = row.select_one(".stat__categoryName")
                home_value = row.select_one(".stat__homeValue")
                away_value = row.select_one(".stat__awayValue")
                
                if stat_name and home_value and away_value:
                    name = self.clean_text(stat_name.get_text())
                    stats["home_stats"][name] = self._parse_stat_value(home_value.get_text())
                    stats["away_stats"][name] = self._parse_stat_value(away_value.get_text())
                    
            except Exception as e:
                logger.warning("parse_stat_error", error=str(e))
                continue
        
        return stats
    
    def _parse_match_element(self, element, current_date: Optional[datetime]) -> Optional[Dict]:
        """Parse a single match element for fixtures"""
        try:
            # Match ID from data attribute or link
            match_id = element.get("id", "").replace("g_1_", "")
            
            # Time
            time_el = element.select_one(".event__time")
            time_str = self.clean_text(time_el.get_text()) if time_el else ""
            
            # Teams
            home_el = element.select_one(".event__participant--home")
            away_el = element.select_one(".event__participant--away")
            
            home_team = self.clean_text(home_el.get_text()) if home_el else ""
            away_team = self.clean_text(away_el.get_text()) if away_el else ""
            
            if not home_team or not away_team:
                return None
            
            # Combine date and time
            match_datetime = None
            if current_date and time_str:
                try:
                    hours, minutes = map(int, time_str.split(":"))
                    match_datetime = current_date.replace(hour=hours, minute=minutes)
                except ValueError:
                    match_datetime = current_date
            
            return {
                "external_id": match_id,
                "source": self.get_source_name(),
                "home_team": home_team,
                "away_team": away_team,
                "match_date": match_datetime.isoformat() if match_datetime else None,
                "status": "scheduled",
                "league": "Premier League",
                "country": "England",
                "scraped_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("parse_element_error", error=str(e))
            return None
    
    def _parse_result_element(self, element, current_date: Optional[datetime]) -> Optional[Dict]:
        """Parse a single match element for results"""
        match_data = self._parse_match_element(element, current_date)
        
        if not match_data:
            return None
        
        try:
            # Scores
            home_score_el = element.select_one(".event__score--home")
            away_score_el = element.select_one(".event__score--away")
            
            home_score = int(self.clean_text(home_score_el.get_text())) if home_score_el else None
            away_score = int(self.clean_text(away_score_el.get_text())) if away_score_el else None
            
            match_data["home_score"] = home_score
            match_data["away_score"] = away_score
            match_data["status"] = "finished"
            
            return match_data
            
        except Exception as e:
            logger.warning("parse_score_error", error=str(e))
            return match_data
    
    def _parse_live_match(self, element) -> Optional[Dict]:
        """Parse a live match element"""
        match_data = self._parse_match_element(element, datetime.now())
        
        if not match_data:
            return None
        
        try:
            # Current scores
            home_score_el = element.select_one(".event__score--home")
            away_score_el = element.select_one(".event__score--away")
            
            match_data["home_score"] = int(self.clean_text(home_score_el.get_text())) if home_score_el else 0
            match_data["away_score"] = int(self.clean_text(away_score_el.get_text())) if away_score_el else 0
            match_data["status"] = "live"
            
            # Match minute
            stage_el = element.select_one(".event__stage--block")
            if stage_el:
                minute_text = self.clean_text(stage_el.get_text())
                minute_match = re.search(r"(\d+)", minute_text)
                match_data["minute"] = int(minute_match.group(1)) if minute_match else None
            
            return match_data
            
        except Exception as e:
            logger.warning("parse_live_error", error=str(e))
            return match_data
    
    def _parse_date_header(self, date_text: str) -> Optional[datetime]:
        """Parse date from header text"""
        try:
            # Handle "Today", "Tomorrow", etc.
            date_text = date_text.lower().strip()
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            if "today" in date_text:
                return today
            elif "tomorrow" in date_text:
                return today + timedelta(days=1)
            elif "yesterday" in date_text:
                return today - timedelta(days=1)
            
            # Try parsing date format like "13.01.2024"
            date_match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", date_text)
            if date_match:
                day, month, year = map(int, date_match.groups())
                return datetime(year, month, day)
            
            # Try format like "Saturday, 13 January 2024"
            for fmt in ["%A, %d %B %Y", "%d %B %Y", "%d.%m.%Y", "%d/%m/%Y"]:
                try:
                    return datetime.strptime(date_text, fmt)
                except ValueError:
                    continue
            
            return None
            
        except Exception:
            return None
    
    def _parse_stat_value(self, value: str) -> Any:
        """Parse statistic value (percentage, number, etc.)"""
        value = self.clean_text(value)
        
        # Percentage
        if "%" in value:
            return float(value.replace("%", ""))
        
        # Number
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate match data"""
        required_fields = ["home_team", "away_team"]
        return all(data.get(field) for field in required_fields)
