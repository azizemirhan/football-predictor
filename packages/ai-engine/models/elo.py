"""
Elo Rating System - Dinamik takım güç sıralaması
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import structlog

from .base import BasePredictor, PredictionResult, normalize_probabilities

logger = structlog.get_logger()


class EloModel(BasePredictor):
    """
    Elo rating system for football predictions.
    
    Features:
    - Dynamic K-factor based on match importance
    - Home advantage adjustment
    - Goal difference impact
    - Season regression (ratings regress to mean each season)
    """
    
    # Initial Elo ratings
    INITIAL_RATING = 1500
    AVERAGE_RATING = 1500
    
    # K-factor range
    K_BASE = 20
    K_MIN = 10
    K_MAX = 40
    
    # Home advantage in Elo points
    HOME_ADVANTAGE = 65
    
    # Goal difference multiplier
    GOAL_DIFF_MULTIPLIER = 0.5
    
    # Season regression factor
    SEASON_REGRESSION = 0.33
    
    def __init__(self, version: str = "1.0"):
        super().__init__(model_name="elo", version=version)
        
        self.ratings = {}  # team -> current rating
        self.rating_history = {}  # team -> list of (date, rating)
        self.matches_played = {}  # team -> count
    
    def train(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Train Elo model by processing historical matches.
        
        Args:
            data: DataFrame with home_team, away_team, home_score, away_score, match_date
            
        Returns:
            Training metrics
        """
        logger.info("training_started", model=self.model_name, samples=len(data))
        
        # Sort by date
        matches = data[data["home_score"].notna()].copy()
        matches = matches.sort_values("match_date")
        
        # Reset ratings
        self.ratings = {}
        self.rating_history = {}
        self.matches_played = {}
        
        # Process each match
        for _, row in matches.iterrows():
            self._process_match(
                home_team=row["home_team"],
                away_team=row["away_team"],
                home_score=int(row["home_score"]),
                away_score=int(row["away_score"]),
                match_date=row.get("match_date")
            )
        
        # Calculate metrics
        metrics = self._evaluate(matches)
        
        self.is_trained = True
        self.training_metrics = metrics
        
        logger.info(
            "training_completed",
            model=self.model_name,
            teams=len(self.ratings),
            **metrics
        )
        
        return metrics
    
    def _process_match(
        self,
        home_team: str,
        away_team: str,
        home_score: int,
        away_score: int,
        match_date: Optional[datetime] = None
    ):
        """Process a single match and update ratings"""
        
        # Initialize teams if needed
        if home_team not in self.ratings:
            self.ratings[home_team] = self.INITIAL_RATING
            self.rating_history[home_team] = []
            self.matches_played[home_team] = 0
        
        if away_team not in self.ratings:
            self.ratings[away_team] = self.INITIAL_RATING
            self.rating_history[away_team] = []
            self.matches_played[away_team] = 0
        
        # Get current ratings
        home_rating = self.ratings[home_team]
        away_rating = self.ratings[away_team]
        
        # Expected scores
        home_expected = self._expected_score(home_rating + self.HOME_ADVANTAGE, away_rating)
        away_expected = 1 - home_expected
        
        # Actual result (1 = win, 0.5 = draw, 0 = loss)
        if home_score > away_score:
            home_actual = 1.0
        elif home_score == away_score:
            home_actual = 0.5
        else:
            home_actual = 0.0
        away_actual = 1 - home_actual
        
        # Calculate K-factor
        k_home = self._calculate_k_factor(home_team, home_score, away_score)
        k_away = self._calculate_k_factor(away_team, away_score, home_score)
        
        # Update ratings
        home_delta = k_home * (home_actual - home_expected)
        away_delta = k_away * (away_actual - away_expected)
        
        self.ratings[home_team] += home_delta
        self.ratings[away_team] += away_delta
        
        # Update history
        if match_date:
            self.rating_history[home_team].append((match_date, self.ratings[home_team]))
            self.rating_history[away_team].append((match_date, self.ratings[away_team]))
        
        # Increment match count
        self.matches_played[home_team] += 1
        self.matches_played[away_team] += 1
    
    def _expected_score(self, rating_a: float, rating_b: float) -> float:
        """Calculate expected score using Elo formula"""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def _calculate_k_factor(
        self, 
        team: str, 
        goals_for: int, 
        goals_against: int
    ) -> float:
        """Calculate dynamic K-factor"""
        
        # Base K-factor
        k = self.K_BASE
        
        # Adjust for goal difference
        goal_diff = abs(goals_for - goals_against)
        if goal_diff > 1:
            k *= (1 + self.GOAL_DIFF_MULTIPLIER * np.log(goal_diff))
        
        # Adjust for matches played (higher K for new teams)
        matches = self.matches_played.get(team, 0)
        if matches < 10:
            k *= 1.5
        elif matches < 20:
            k *= 1.2
        
        return np.clip(k, self.K_MIN, self.K_MAX)
    
    def _evaluate(self, data: pd.DataFrame) -> Dict[str, float]:
        """Evaluate model predictions"""
        correct = 0
        total = 0
        
        for _, row in data.iterrows():
            pred = self.predict({
                "home_team": row["home_team"],
                "away_team": row["away_team"]
            })
            
            # Actual result
            if row["home_score"] > row["away_score"]:
                actual = "H"
            elif row["home_score"] == row["away_score"]:
                actual = "D"
            else:
                actual = "A"
            
            if pred.get("predicted_result") == actual:
                correct += 1
            total += 1
        
        return {
            "accuracy": round(correct / total, 4) if total > 0 else 0,
            "samples": total
        }
    
    def predict(self, match_data: Dict) -> Dict[str, Any]:
        """
        Predict match outcome using Elo ratings.
        
        Args:
            match_data: Dict with home_team, away_team
            
        Returns:
            Prediction dictionary
        """
        home_team = match_data.get("home_team")
        away_team = match_data.get("away_team")
        
        # Get ratings (use average for unknown teams)
        home_rating = self.ratings.get(home_team, self.AVERAGE_RATING)
        away_rating = self.ratings.get(away_team, self.AVERAGE_RATING)
        
        # Adjust for home advantage
        home_adj = home_rating + self.HOME_ADVANTAGE
        
        # Calculate win probabilities
        home_win_prob = self._expected_score(home_adj, away_rating)
        away_win_prob = self._expected_score(away_rating, home_adj)
        
        # Estimate draw probability based on rating difference
        rating_diff = abs(home_adj - away_rating)
        draw_base = 0.26  # Base draw probability
        draw_adjustment = draw_base * np.exp(-rating_diff / 400)
        draw_prob = draw_adjustment
        
        # Adjust win probabilities
        home_win_prob = home_win_prob * (1 - draw_prob)
        away_win_prob = away_win_prob * (1 - draw_prob)
        
        # Normalize
        probs = normalize_probabilities([home_win_prob, draw_prob, away_win_prob])
        
        result = PredictionResult(
            home_win_prob=probs[0],
            draw_prob=probs[1],
            away_win_prob=probs[2],
            model_name=self.model_name,
            factors={
                "home_rating": round(home_rating, 1),
                "away_rating": round(away_rating, 1),
                "rating_diff": round(home_rating - away_rating, 1),
                "home_advantage": self.HOME_ADVANTAGE
            }
        )
        
        output = result.to_dict()
        output["home_team"] = home_team
        output["away_team"] = away_team
        output["match_id"] = match_data.get("id")
        
        return output
    
    def get_rating(self, team: str) -> float:
        """Get current Elo rating for a team"""
        return self.ratings.get(team, self.AVERAGE_RATING)
    
    def get_rankings(self, top_n: Optional[int] = None) -> List[Tuple[str, float]]:
        """Get team rankings by Elo rating"""
        sorted_teams = sorted(
            self.ratings.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        if top_n:
            sorted_teams = sorted_teams[:top_n]
        
        return [(team, round(rating, 1)) for team, rating in sorted_teams]
    
    def apply_season_regression(self):
        """Apply season regression - ratings move toward average"""
        for team in self.ratings:
            diff = self.ratings[team] - self.AVERAGE_RATING
            self.ratings[team] -= diff * self.SEASON_REGRESSION
        
        logger.info("season_regression_applied", factor=self.SEASON_REGRESSION)
    
    def head_to_head_probability(
        self, 
        team_a: str, 
        team_b: str, 
        neutral: bool = False
    ) -> Dict[str, float]:
        """Calculate head-to-head win probability"""
        rating_a = self.ratings.get(team_a, self.AVERAGE_RATING)
        rating_b = self.ratings.get(team_b, self.AVERAGE_RATING)
        
        if not neutral:
            rating_a += self.HOME_ADVANTAGE
        
        prob_a = self._expected_score(rating_a, rating_b)
        
        return {
            team_a: round(prob_a, 4),
            team_b: round(1 - prob_a, 4)
        }
