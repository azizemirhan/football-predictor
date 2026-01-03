"""
Feature Engineering - Maç özellikleri çıkarımı
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class FeatureEngineer:
    """
    Generate features for match prediction models.
    
    Feature categories:
    - Form features (recent results)
    - Goals features (scoring/conceding patterns)
    - Rating features (Elo, etc.)
    - H2H features (head-to-head)
    - Home/Away splits
    - xG features
    - Position/standings features
    """
    
    def __init__(self, form_window: int = 5, h2h_window: int = 10):
        self.form_window = form_window
        self.h2h_window = h2h_window
    
    def generate_features(
        self,
        match: Dict,
        historical_data: pd.DataFrame,
        team_ratings: Optional[Dict] = None,
        standings: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Generate all features for a match.
        
        Args:
            match: Match data with home_team, away_team
            historical_data: Historical match data
            team_ratings: Team rating dictionary
            standings: Current standings data
            
        Returns:
            Feature dictionary
        """
        home_team = match.get("home_team")
        away_team = match.get("away_team")
        match_date = match.get("match_date")
        
        features = {}
        
        # Form features
        features.update(self._form_features(home_team, away_team, historical_data, match_date))
        
        # Goals features
        features.update(self._goals_features(home_team, away_team, historical_data, match_date))
        
        # Rating features
        if team_ratings:
            features.update(self._rating_features(home_team, away_team, team_ratings))
        
        # H2H features
        features.update(self._h2h_features(home_team, away_team, historical_data, match_date))
        
        # Home/Away split features
        features.update(self._venue_features(home_team, away_team, historical_data, match_date))
        
        # Standings features
        if standings:
            features.update(self._standings_features(home_team, away_team, standings))
        
        # Derived features
        features.update(self._derived_features(features))
        
        return features
    
    def _form_features(
        self,
        home_team: str,
        away_team: str,
        data: pd.DataFrame,
        match_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate form-based features"""
        features = {}
        
        home_form = self._get_team_form(home_team, data, match_date)
        away_form = self._get_team_form(away_team, data, match_date)
        
        features["home_form_points"] = home_form.get("points", 0)
        features["away_form_points"] = away_form.get("points", 0)
        features["home_form_wins"] = home_form.get("wins", 0)
        features["away_form_wins"] = away_form.get("wins", 0)
        features["home_form_losses"] = home_form.get("losses", 0)
        features["away_form_losses"] = away_form.get("losses", 0)
        features["form_diff"] = features["home_form_points"] - features["away_form_points"]
        
        # Momentum (recent results weighted more)
        features["home_momentum"] = home_form.get("momentum", 0)
        features["away_momentum"] = away_form.get("momentum", 0)
        
        return features
    
    def _get_team_form(
        self,
        team: str,
        data: pd.DataFrame,
        before_date: Optional[datetime]
    ) -> Dict:
        """Get team's recent form"""
        # Filter matches
        team_matches = data[
            (data["home_team"] == team) | (data["away_team"] == team)
        ]
        
        if before_date:
            team_matches = team_matches[
                pd.to_datetime(team_matches["match_date"]) < pd.to_datetime(before_date)
            ]
        
        # Get last N matches
        team_matches = team_matches.nlargest(self.form_window, "match_date")
        
        if len(team_matches) == 0:
            return {"points": 0, "wins": 0, "draws": 0, "losses": 0, "momentum": 0}
        
        wins = 0
        draws = 0
        losses = 0
        momentum = 0
        
        for i, (_, match) in enumerate(team_matches.iterrows()):
            is_home = match["home_team"] == team
            
            if match["home_score"] is None:
                continue
            
            home_score = int(match["home_score"])
            away_score = int(match["away_score"])
            
            if is_home:
                if home_score > away_score:
                    wins += 1
                    momentum += (self.form_window - i) * 3  # Weight recent results
                elif home_score == away_score:
                    draws += 1
                    momentum += (self.form_window - i) * 1
                else:
                    losses += 1
            else:
                if away_score > home_score:
                    wins += 1
                    momentum += (self.form_window - i) * 3
                elif home_score == away_score:
                    draws += 1
                    momentum += (self.form_window - i) * 1
                else:
                    losses += 1
        
        points = wins * 3 + draws
        
        return {
            "points": points,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "momentum": momentum / (self.form_window * 3)  # Normalize
        }
    
    def _goals_features(
        self,
        home_team: str,
        away_team: str,
        data: pd.DataFrame,
        match_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate goals-based features"""
        features = {}
        
        home_goals = self._get_team_goals(home_team, data, match_date)
        away_goals = self._get_team_goals(away_team, data, match_date)
        
        features["home_goals_scored_avg"] = home_goals.get("scored_avg", 1.5)
        features["home_goals_conceded_avg"] = home_goals.get("conceded_avg", 1.2)
        features["away_goals_scored_avg"] = away_goals.get("scored_avg", 1.2)
        features["away_goals_conceded_avg"] = away_goals.get("conceded_avg", 1.3)
        
        # Clean sheets
        features["home_clean_sheets"] = home_goals.get("clean_sheets", 0)
        features["away_clean_sheets"] = away_goals.get("clean_sheets", 0)
        
        # BTTS tendency
        features["home_btts_rate"] = home_goals.get("btts_rate", 0.5)
        features["away_btts_rate"] = away_goals.get("btts_rate", 0.5)
        
        # Over 2.5 tendency
        features["home_over25_rate"] = home_goals.get("over25_rate", 0.5)
        features["away_over25_rate"] = away_goals.get("over25_rate", 0.5)
        
        return features
    
    def _get_team_goals(
        self,
        team: str,
        data: pd.DataFrame,
        before_date: Optional[datetime]
    ) -> Dict:
        """Get team's goal statistics"""
        team_matches = data[
            (data["home_team"] == team) | (data["away_team"] == team)
        ]
        
        if before_date:
            team_matches = team_matches[
                pd.to_datetime(team_matches["match_date"]) < pd.to_datetime(before_date)
            ]
        
        team_matches = team_matches[team_matches["home_score"].notna()]
        team_matches = team_matches.nlargest(self.form_window * 2, "match_date")
        
        if len(team_matches) == 0:
            return {
                "scored_avg": 1.5, "conceded_avg": 1.2,
                "clean_sheets": 0, "btts_rate": 0.5, "over25_rate": 0.5
            }
        
        scored = []
        conceded = []
        clean_sheets = 0
        btts = 0
        over25 = 0
        
        for _, match in team_matches.iterrows():
            is_home = match["home_team"] == team
            home_score = int(match["home_score"])
            away_score = int(match["away_score"])
            total = home_score + away_score
            
            if is_home:
                scored.append(home_score)
                conceded.append(away_score)
                if away_score == 0:
                    clean_sheets += 1
            else:
                scored.append(away_score)
                conceded.append(home_score)
                if home_score == 0:
                    clean_sheets += 1
            
            if home_score > 0 and away_score > 0:
                btts += 1
            if total > 2.5:
                over25 += 1
        
        n = len(team_matches)
        
        return {
            "scored_avg": np.mean(scored),
            "conceded_avg": np.mean(conceded),
            "clean_sheets": clean_sheets,
            "btts_rate": btts / n,
            "over25_rate": over25 / n
        }
    
    def _rating_features(
        self,
        home_team: str,
        away_team: str,
        ratings: Dict
    ) -> Dict[str, float]:
        """Calculate rating-based features"""
        home_elo = ratings.get(home_team, {}).get("elo", 1500)
        away_elo = ratings.get(away_team, {}).get("elo", 1500)
        
        return {
            "home_elo": home_elo,
            "away_elo": away_elo,
            "elo_diff": home_elo - away_elo,
            "elo_ratio": home_elo / away_elo if away_elo > 0 else 1
        }
    
    def _h2h_features(
        self,
        home_team: str,
        away_team: str,
        data: pd.DataFrame,
        match_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate head-to-head features"""
        h2h = data[
            ((data["home_team"] == home_team) & (data["away_team"] == away_team)) |
            ((data["home_team"] == away_team) & (data["away_team"] == home_team))
        ]
        
        if match_date:
            h2h = h2h[pd.to_datetime(h2h["match_date"]) < pd.to_datetime(match_date)]
        
        h2h = h2h[h2h["home_score"].notna()]
        h2h = h2h.nlargest(self.h2h_window, "match_date")
        
        if len(h2h) == 0:
            return {
                "h2h_home_wins": 0, "h2h_away_wins": 0, "h2h_draws": 0,
                "h2h_home_goals_avg": 1.5, "h2h_away_goals_avg": 1.2
            }
        
        home_wins = 0
        away_wins = 0
        draws = 0
        home_goals = []
        away_goals = []
        
        for _, match in h2h.iterrows():
            home_score = int(match["home_score"])
            away_score = int(match["away_score"])
            
            if match["home_team"] == home_team:
                home_goals.append(home_score)
                away_goals.append(away_score)
                if home_score > away_score:
                    home_wins += 1
                elif home_score == away_score:
                    draws += 1
                else:
                    away_wins += 1
            else:
                home_goals.append(away_score)
                away_goals.append(home_score)
                if away_score > home_score:
                    home_wins += 1
                elif home_score == away_score:
                    draws += 1
                else:
                    away_wins += 1
        
        return {
            "h2h_home_wins": home_wins,
            "h2h_away_wins": away_wins,
            "h2h_draws": draws,
            "h2h_home_goals_avg": np.mean(home_goals) if home_goals else 1.5,
            "h2h_away_goals_avg": np.mean(away_goals) if away_goals else 1.2
        }
    
    def _venue_features(
        self,
        home_team: str,
        away_team: str,
        data: pd.DataFrame,
        match_date: Optional[datetime]
    ) -> Dict[str, float]:
        """Calculate home/away specific features"""
        features = {}
        
        # Home team at home
        home_at_home = data[data["home_team"] == home_team]
        if match_date:
            home_at_home = home_at_home[
                pd.to_datetime(home_at_home["match_date"]) < pd.to_datetime(match_date)
            ]
        home_at_home = home_at_home[home_at_home["home_score"].notna()]
        
        if len(home_at_home) > 0:
            home_wins = (home_at_home["home_score"] > home_at_home["away_score"]).sum()
            features["home_home_win_rate"] = home_wins / len(home_at_home)
            features["home_home_goals_avg"] = home_at_home["home_score"].mean()
        else:
            features["home_home_win_rate"] = 0.5
            features["home_home_goals_avg"] = 1.5
        
        # Away team away
        away_at_away = data[data["away_team"] == away_team]
        if match_date:
            away_at_away = away_at_away[
                pd.to_datetime(away_at_away["match_date"]) < pd.to_datetime(match_date)
            ]
        away_at_away = away_at_away[away_at_away["home_score"].notna()]
        
        if len(away_at_away) > 0:
            away_wins = (away_at_away["away_score"] > away_at_away["home_score"]).sum()
            features["away_away_win_rate"] = away_wins / len(away_at_away)
            features["away_away_goals_avg"] = away_at_away["away_score"].mean()
        else:
            features["away_away_win_rate"] = 0.3
            features["away_away_goals_avg"] = 1.2
        
        return features
    
    def _standings_features(
        self,
        home_team: str,
        away_team: str,
        standings: Dict
    ) -> Dict[str, float]:
        """Calculate standings-based features"""
        home_standing = standings.get(home_team, {})
        away_standing = standings.get(away_team, {})
        
        return {
            "home_position": home_standing.get("position", 10),
            "away_position": away_standing.get("position", 10),
            "position_diff": away_standing.get("position", 10) - home_standing.get("position", 10),
            "home_points": home_standing.get("points", 0),
            "away_points": away_standing.get("points", 0),
            "points_diff": home_standing.get("points", 0) - away_standing.get("points", 0)
        }
    
    def _derived_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """Calculate derived/interaction features"""
        derived = {}
        
        # Attack vs Defense
        home_attack = features.get("home_goals_scored_avg", 1.5)
        away_defense = features.get("away_goals_conceded_avg", 1.2)
        away_attack = features.get("away_goals_scored_avg", 1.2)
        home_defense = features.get("home_goals_conceded_avg", 1.2)
        
        derived["home_attack_vs_defense"] = home_attack - away_defense
        derived["away_attack_vs_defense"] = away_attack - home_defense
        
        # Expected goals
        derived["expected_home_goals"] = (home_attack + away_defense) / 2
        derived["expected_away_goals"] = (away_attack + home_defense) / 2
        derived["expected_total_goals"] = derived["expected_home_goals"] + derived["expected_away_goals"]
        
        # Form momentum interaction
        home_momentum = features.get("home_momentum", 0)
        away_momentum = features.get("away_momentum", 0)
        derived["momentum_diff"] = home_momentum - away_momentum
        
        return derived
