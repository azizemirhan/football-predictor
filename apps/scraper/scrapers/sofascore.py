"""
Sofascore Scraper - Detaylı maç istatistikleri ve xG verileri
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
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
    
    async def scrape(self, scrape_type: str = "fixtures", **kwargs) -> Any:
        """
        Main scrape method.

        Args:
            scrape_type: One of:
                - 'fixtures': Upcoming fixtures
                - 'results': Recent results
                - 'live': Live matches
                - 'standings': League standings
                - 'team_complete': Complete team data (requires team_id)
                - 'team_details': Team basic details (requires team_id)
                - 'team_squad': Team squad (requires team_id)
                - 'team_matches': Team matches (requires team_id, match_type)
                - 'team_transfers': Team transfers (requires team_id)
                - 'team_stats': Team statistics (requires team_id)
                - 'player_stats': Player statistics (requires player_id)
            **kwargs: Additional parameters (e.g., team_id, player_id, season_id, match_type)
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
            elif scrape_type == "team_complete":
                team_id = kwargs.get("team_id")
                if not team_id:
                    raise ValueError("team_id is required for team_complete scrape_type")
                return await self.scrape_complete_team_data(team_id, kwargs.get("include_player_stats", False))
            elif scrape_type == "team_details":
                team_id = kwargs.get("team_id")
                if not team_id:
                    raise ValueError("team_id is required for team_details scrape_type")
                return await self.scrape_team_details(team_id)
            elif scrape_type == "team_squad":
                team_id = kwargs.get("team_id")
                if not team_id:
                    raise ValueError("team_id is required for team_squad scrape_type")
                return await self.scrape_team_squad(team_id, kwargs.get("season_id"))
            elif scrape_type == "team_matches":
                team_id = kwargs.get("team_id")
                if not team_id:
                    raise ValueError("team_id is required for team_matches scrape_type")
                return await self.scrape_team_matches(
                    team_id,
                    kwargs.get("match_type", "last"),
                    kwargs.get("count", 20)
                )
            elif scrape_type == "team_transfers":
                team_id = kwargs.get("team_id")
                if not team_id:
                    raise ValueError("team_id is required for team_transfers scrape_type")
                return await self.scrape_team_transfers(team_id)
            elif scrape_type == "team_stats":
                team_id = kwargs.get("team_id")
                if not team_id:
                    raise ValueError("team_id is required for team_stats scrape_type")
                return await self.scrape_team_stats(team_id, kwargs.get("season_id"))
            elif scrape_type == "player_stats":
                player_id = kwargs.get("player_id")
                if not player_id:
                    raise ValueError("player_id is required for player_stats scrape_type")
                return await self.scrape_player_statistics(player_id, kwargs.get("season_id"))
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
    
    async def scrape_team_stats(self, team_id: int, season_id: Optional[str] = None) -> Dict[str, Any]:
        """Scrape detailed team statistics"""
        season = season_id or "current"
        url = f"{self.BASE_URL}/team/{team_id}/unique-tournament/{self.PREMIER_LEAGUE_ID}/season/{season}/statistics"

        try:
            data = await self.fetch_json(url)
            return self._parse_team_statistics(data)
        except Exception as e:
            logger.error("fetch_team_stats_error", team_id=team_id, error=str(e))
            return {}

    async def scrape_team_details(self, team_id: int) -> Dict[str, Any]:
        """Scrape complete team details including basic info, venue, and manager"""
        url = f"{self.BASE_URL}/team/{team_id}"

        try:
            data = await self.fetch_json(url)
            team_data = data.get("team", {})

            details = {
                "team_id": team_id,
                "name": team_data.get("name"),
                "short_name": team_data.get("shortName"),
                "name_code": team_data.get("nameCode"),
                "slug": team_data.get("slug"),
                "country": team_data.get("country", {}).get("name"),
                "country_code": team_data.get("country", {}).get("alpha2"),
                "founded": team_data.get("foundationDateTimestamp"),
                "venue": {
                    "name": team_data.get("venue", {}).get("stadium", {}).get("name"),
                    "city": team_data.get("venue", {}).get("city", {}).get("name"),
                    "capacity": team_data.get("venue", {}).get("stadium", {}).get("capacity")
                },
                "manager": {
                    "name": team_data.get("manager", {}).get("name"),
                    "id": team_data.get("manager", {}).get("id"),
                    "country": team_data.get("manager", {}).get("country", {}).get("name")
                },
                "colors": {
                    "primary": team_data.get("teamColors", {}).get("primary"),
                    "secondary": team_data.get("teamColors", {}).get("secondary"),
                    "text": team_data.get("teamColors", {}).get("text")
                },
                "source": self.get_source_name(),
                "scraped_at": datetime.now().isoformat()
            }

            logger.info("team_details_scraped", team_id=team_id)
            return details

        except Exception as e:
            logger.error("fetch_team_details_error", team_id=team_id, error=str(e))
            return {}

    async def scrape_team_squad(self, team_id: int, season_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scrape team squad/players for a specific season"""
        season = season_id or "current"
        url = f"{self.BASE_URL}/team/{team_id}/unique-tournament/{self.PREMIER_LEAGUE_ID}/season/{season}/top-players/overall"

        try:
            data = await self.fetch_json(url)
            squad = []

            # Top players by category
            for category in data.get("topPlayers", {}).values():
                for player_data in category:
                    player = player_data.get("player", {})
                    stats = player_data.get("statistics", {})

                    player_info = {
                        "player_id": player.get("id"),
                        "name": player.get("name"),
                        "slug": player.get("slug"),
                        "position": player.get("position"),
                        "jersey_number": player.get("jerseyNumber"),
                        "country": player.get("country", {}).get("name"),
                        "date_of_birth": self._parse_timestamp(player.get("dateOfBirthTimestamp")),
                        "height": player.get("height"),
                        "preferred_foot": player.get("preferredFoot"),
                        "statistics": {
                            "rating": stats.get("rating"),
                            "goals": stats.get("goals"),
                            "assists": stats.get("assists"),
                            "appearances": stats.get("appearances"),
                            "minutes_played": stats.get("minutesPlayed")
                        },
                        "team_id": team_id,
                        "source": self.get_source_name(),
                        "scraped_at": datetime.now().isoformat()
                    }

                    # Avoid duplicates
                    if not any(p["player_id"] == player_info["player_id"] for p in squad):
                        squad.append(player_info)

            # Also get full squad from players endpoint
            players_url = f"{self.BASE_URL}/team/{team_id}/players"
            try:
                players_data = await self.fetch_json(players_url)
                for player in players_data.get("players", []):
                    player_info = {
                        "player_id": player.get("player", {}).get("id"),
                        "name": player.get("player", {}).get("name"),
                        "slug": player.get("player", {}).get("slug"),
                        "position": player.get("player", {}).get("position"),
                        "jersey_number": player.get("player", {}).get("jerseyNumber"),
                        "country": player.get("player", {}).get("country", {}).get("name"),
                        "date_of_birth": self._parse_timestamp(player.get("player", {}).get("dateOfBirthTimestamp")),
                        "height": player.get("player", {}).get("height"),
                        "preferred_foot": player.get("player", {}).get("preferredFoot"),
                        "team_id": team_id,
                        "source": self.get_source_name(),
                        "scraped_at": datetime.now().isoformat()
                    }

                    # Add if not already in squad
                    if not any(p["player_id"] == player_info["player_id"] for p in squad):
                        squad.append(player_info)

            except Exception as e:
                logger.debug("fetch_players_list_error", team_id=team_id, error=str(e))

            logger.info("team_squad_scraped", team_id=team_id, count=len(squad))
            return squad

        except Exception as e:
            logger.error("fetch_team_squad_error", team_id=team_id, error=str(e))
            return []

    async def scrape_team_matches(self, team_id: int, match_type: str = "last", count: int = 20) -> List[Dict[str, Any]]:
        """
        Scrape team matches (last or next)

        Args:
            team_id: Team ID
            match_type: 'last' for previous matches, 'next' for upcoming matches
            count: Number of matches to fetch (0 = all available)
        """
        url = f"{self.BASE_URL}/team/{team_id}/events/{match_type}/{count}"

        try:
            data = await self.fetch_json(url)
            matches = []

            for event in data.get("events", []):
                match_data = self._parse_event(event)
                if match_data:
                    matches.append(match_data)

            logger.info("team_matches_scraped", team_id=team_id, type=match_type, count=len(matches))
            return matches

        except Exception as e:
            logger.error("fetch_team_matches_error", team_id=team_id, type=match_type, error=str(e))
            return []

    async def scrape_team_transfers(self, team_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape team transfer history"""
        url = f"{self.BASE_URL}/team/{team_id}/transfers"

        try:
            data = await self.fetch_json(url)
            transfers = {
                "transfers_in": [],
                "transfers_out": []
            }

            # Incoming transfers
            for transfer in data.get("transfersIn", []):
                player = transfer.get("player", {})
                from_team = transfer.get("fromTeam", {})

                transfer_data = {
                    "player_id": player.get("id"),
                    "player_name": player.get("name"),
                    "position": player.get("position"),
                    "from_team": from_team.get("name"),
                    "from_team_id": from_team.get("id"),
                    "transfer_date": self._parse_timestamp(transfer.get("transferDateTimestamp")),
                    "transfer_fee": transfer.get("transferFee"),
                    "transfer_fee_description": transfer.get("transferFeeDescription"),
                    "type": transfer.get("type"),
                    "source": self.get_source_name(),
                    "scraped_at": datetime.now().isoformat()
                }
                transfers["transfers_in"].append(transfer_data)

            # Outgoing transfers
            for transfer in data.get("transfersOut", []):
                player = transfer.get("player", {})
                to_team = transfer.get("toTeam", {})

                transfer_data = {
                    "player_id": player.get("id"),
                    "player_name": player.get("name"),
                    "position": player.get("position"),
                    "to_team": to_team.get("name"),
                    "to_team_id": to_team.get("id"),
                    "transfer_date": self._parse_timestamp(transfer.get("transferDateTimestamp")),
                    "transfer_fee": transfer.get("transferFee"),
                    "transfer_fee_description": transfer.get("transferFeeDescription"),
                    "type": transfer.get("type"),
                    "source": self.get_source_name(),
                    "scraped_at": datetime.now().isoformat()
                }
                transfers["transfers_out"].append(transfer_data)

            logger.info("team_transfers_scraped",
                       team_id=team_id,
                       transfers_in=len(transfers["transfers_in"]),
                       transfers_out=len(transfers["transfers_out"]))
            return transfers

        except Exception as e:
            logger.error("fetch_team_transfers_error", team_id=team_id, error=str(e))
            return {"transfers_in": [], "transfers_out": []}

    async def scrape_player_statistics(self, player_id: int, season_id: Optional[str] = None) -> Dict[str, Any]:
        """Scrape detailed player statistics for a season"""
        season = season_id or "current"
        url = f"{self.BASE_URL}/player/{player_id}/unique-tournament/{self.PREMIER_LEAGUE_ID}/season/{season}/statistics/overall"

        try:
            data = await self.fetch_json(url)
            stats = data.get("statistics", {})

            player_stats = {
                "player_id": player_id,
                "season": season,
                "rating": stats.get("rating"),
                "appearances": stats.get("appearances"),
                "minutes_played": stats.get("minutesPlayed"),
                "goals": stats.get("goals"),
                "assists": stats.get("assists"),
                "total_shots": stats.get("totalShots"),
                "shots_on_target": stats.get("shotsOnTarget"),
                "big_chances_created": stats.get("bigChancesCreated"),
                "big_chances_missed": stats.get("bigChancesMissed"),
                "expected_goals": stats.get("expectedGoals"),
                "expected_assists": stats.get("expectedAssists"),
                "accurate_passes": stats.get("accuratePasses"),
                "total_passes": stats.get("totalPasses"),
                "key_passes": stats.get("keyPasses"),
                "accurate_crosses": stats.get("accurateCrosses"),
                "total_crosses": stats.get("totalCrosses"),
                "dribbles_attempted": stats.get("dribbleAttempts"),
                "dribbles_successful": stats.get("successfulDribbles"),
                "tackles": stats.get("tackles"),
                "interceptions": stats.get("interceptions"),
                "clearances": stats.get("clearances"),
                "duels_won": stats.get("duelsWon"),
                "duels_total": stats.get("totalDuels"),
                "aerial_duels_won": stats.get("aerialDuelsWon"),
                "aerial_duels_total": stats.get("aerialDuels"),
                "yellow_cards": stats.get("yellowCards"),
                "red_cards": stats.get("redCards"),
                "fouls_committed": stats.get("foulsCommitted"),
                "was_fouled": stats.get("wasFouled"),
                "offsides": stats.get("offsides"),
                "saves": stats.get("saves"),  # For goalkeepers
                "goals_conceded": stats.get("goalsConceded"),  # For goalkeepers
                "clean_sheets": stats.get("cleanSheets"),  # For goalkeepers
                "source": self.get_source_name(),
                "scraped_at": datetime.now().isoformat()
            }

            logger.info("player_statistics_scraped", player_id=player_id)
            return player_stats

        except Exception as e:
            logger.error("fetch_player_statistics_error", player_id=player_id, error=str(e))
            return {}

    async def scrape_team_trophies(self, team_id: int) -> List[Dict[str, Any]]:
        """Scrape team trophy cabinet / achievements"""
        url = f"{self.BASE_URL}/team/{team_id}/trophies"

        try:
            data = await self.fetch_json(url)
            trophies = []

            for trophy in data.get("trophies", []):
                trophy_data = {
                    "tournament_name": trophy.get("tournament", {}).get("name"),
                    "tournament_id": trophy.get("tournament", {}).get("id"),
                    "season": trophy.get("seasonYear"),
                    "title": trophy.get("title"),
                    "team_id": team_id,
                    "source": self.get_source_name(),
                    "scraped_at": datetime.now().isoformat()
                }
                trophies.append(trophy_data)

            logger.info("team_trophies_scraped", team_id=team_id, count=len(trophies))
            return trophies

        except Exception as e:
            logger.error("fetch_team_trophies_error", team_id=team_id, error=str(e))
            return []

    async def scrape_complete_team_data(self, team_id: int, include_player_stats: bool = False) -> Dict[str, Any]:
        """
        Scrape ALL available data for a team from their detail page

        Args:
            team_id: SofaScore team ID
            include_player_stats: If True, fetch detailed statistics for each player (slower)

        Returns:
            Complete team data including:
            - Basic team details
            - Squad/players
            - Recent and upcoming matches
            - Transfer history
            - Team statistics
            - Trophies
            - Player statistics (optional)
        """
        logger.info("scraping_complete_team_data", team_id=team_id)

        complete_data = {
            "team_id": team_id,
            "source": self.get_source_name(),
            "scraped_at": datetime.now().isoformat()
        }

        # 1. Team basic details
        complete_data["team_details"] = await self.scrape_team_details(team_id)

        # 2. Squad
        complete_data["squad"] = await self.scrape_team_squad(team_id)

        # 3. Team statistics
        complete_data["team_statistics"] = await self.scrape_team_stats(team_id)

        # 4. Recent matches (last 20)
        complete_data["recent_matches"] = await self.scrape_team_matches(team_id, "last", 20)

        # 5. Upcoming matches (next 20)
        complete_data["upcoming_matches"] = await self.scrape_team_matches(team_id, "next", 20)

        # 6. Transfers
        complete_data["transfers"] = await self.scrape_team_transfers(team_id)

        # 7. Trophies
        complete_data["trophies"] = await self.scrape_team_trophies(team_id)

        # 8. Player detailed statistics (optional, can be slow)
        if include_player_stats:
            complete_data["player_statistics"] = []
            for player in complete_data["squad"]:
                player_id = player.get("player_id")
                if player_id:
                    player_stats = await self.scrape_player_statistics(player_id)
                    if player_stats:
                        complete_data["player_statistics"].append(player_stats)

        logger.info("complete_team_data_scraped",
                   team_id=team_id,
                   squad_size=len(complete_data["squad"]),
                   recent_matches=len(complete_data["recent_matches"]),
                   upcoming_matches=len(complete_data["upcoming_matches"]),
                   transfers_in=len(complete_data["transfers"]["transfers_in"]),
                   transfers_out=len(complete_data["transfers"]["transfers_out"]),
                   trophies=len(complete_data["trophies"]))

        return complete_data
    
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
