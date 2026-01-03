"""
Poisson Model - Bivariate Poisson dağılımı ile maç skor tahmini
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize
from typing import Any, Dict, List, Optional, Tuple
import structlog

from .base import BasePredictor, PredictionResult, normalize_probabilities

logger = structlog.get_logger()


class PoissonModel(BasePredictor):
    """
    Poisson regression model for predicting football match outcomes.
    
    Uses team attack and defense strengths to estimate expected goals,
    then calculates match outcome probabilities from Poisson distribution.
    """
    
    def __init__(self, version: str = "1.0"):
        super().__init__(model_name="poisson", version=version)
        
        # Model parameters
        self.home_advantage = 0.0
        self.attack_strengths = {}  # team -> attack strength
        self.defense_strengths = {}  # team -> defense strength
        self.league_avg_goals = 1.35  # Default average goals per team
        
        # Hyperparameters
        self.max_goals = 10  # Maximum goals to consider
        self.regularization = 0.001
    
    def train(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Train Poisson model using historical match data.
        
        Args:
            data: DataFrame with columns: home_team, away_team, home_score, away_score
            
        Returns:
            Training metrics
        """
        logger.info("training_started", model=self.model_name, samples=len(data))
        
        # Filter completed matches
        matches = data[data["home_score"].notna()].copy()
        
        if len(matches) < 50:
            logger.warning("insufficient_data", count=len(matches))
            return {"error": "Insufficient training data"}
        
        # Get unique teams
        teams = list(set(matches["home_team"].unique()) | set(matches["away_team"].unique()))
        n_teams = len(teams)
        team_idx = {team: i for i, team in enumerate(teams)}
        
        # Initial parameters: [home_adv, attack1..n, defense1..n]
        n_params = 1 + 2 * n_teams
        x0 = np.zeros(n_params)
        x0[0] = 0.25  # Initial home advantage
        
        # Prepare match data
        home_idx = matches["home_team"].map(team_idx).values
        away_idx = matches["away_team"].map(team_idx).values
        home_goals = matches["home_score"].values.astype(float)
        away_goals = matches["away_score"].values.astype(float)
        
        # Calculate league average
        self.league_avg_goals = (home_goals.mean() + away_goals.mean()) / 2
        
        # Optimize parameters
        def neg_log_likelihood(params):
            home_adv = params[0]
            attack = params[1:n_teams+1]
            defense = params[n_teams+1:]
            
            # Expected goals
            lambda_home = np.exp(home_adv + attack[home_idx] - defense[away_idx])
            lambda_away = np.exp(attack[away_idx] - defense[home_idx])
            
            # Log likelihood
            ll = (stats.poisson.logpmf(home_goals, lambda_home).sum() +
                  stats.poisson.logpmf(away_goals, lambda_away).sum())
            
            # Regularization
            reg = self.regularization * (np.sum(attack**2) + np.sum(defense**2))
            
            return -ll + reg
        
        # Constraint: sum of attack/defense = 0
        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x[1:n_teams+1])},
            {"type": "eq", "fun": lambda x: np.sum(x[n_teams+1:])}
        ]
        
        result = minimize(
            neg_log_likelihood,
            x0,
            method="SLSQP",
            constraints=constraints,
            options={"maxiter": 1000}
        )
        
        if not result.success:
            logger.warning("optimization_warning", message=result.message)
        
        # Store parameters
        self.home_advantage = result.x[0]
        for i, team in enumerate(teams):
            self.attack_strengths[team] = result.x[1 + i]
            self.defense_strengths[team] = result.x[n_teams + 1 + i]
        
        # Calculate training metrics
        metrics = self._evaluate(matches)
        
        self.is_trained = True
        self.training_metrics = metrics
        
        logger.info(
            "training_completed",
            model=self.model_name,
            teams=n_teams,
            home_advantage=round(self.home_advantage, 3),
            **metrics
        )
        
        return metrics
    
    def _evaluate(self, data: pd.DataFrame) -> Dict[str, float]:
        """Evaluate model on data"""
        correct = 0
        total = 0
        log_loss_sum = 0
        
        for _, row in data.iterrows():
            pred = self.predict({
                "home_team": row["home_team"],
                "away_team": row["away_team"]
            })
            
            if pred.get("error"):
                continue
            
            # Actual result
            if row["home_score"] > row["away_score"]:
                actual = "H"
                actual_probs = [1, 0, 0]
            elif row["home_score"] == row["away_score"]:
                actual = "D"
                actual_probs = [0, 1, 0]
            else:
                actual = "A"
                actual_probs = [0, 0, 1]
            
            # Predicted result
            probs = [pred["home_win_prob"], pred["draw_prob"], pred["away_win_prob"]]
            predicted = ["H", "D", "A"][np.argmax(probs)]
            
            if predicted == actual:
                correct += 1
            total += 1
            
            # Log loss
            eps = 1e-15
            probs = np.clip(probs, eps, 1 - eps)
            log_loss_sum -= np.sum(np.array(actual_probs) * np.log(probs))
        
        return {
            "accuracy": round(correct / total, 4) if total > 0 else 0,
            "log_loss": round(log_loss_sum / total, 4) if total > 0 else 0,
            "samples": total
        }
    
    def predict(self, match_data: Dict) -> Dict[str, Any]:
        """
        Predict match outcome.
        
        Args:
            match_data: Dict with home_team, away_team
            
        Returns:
            Prediction dictionary
        """
        home_team = match_data.get("home_team")
        away_team = match_data.get("away_team")
        
        # Get team strengths (use 0 for unknown teams)
        home_attack = self.attack_strengths.get(home_team, 0)
        home_defense = self.defense_strengths.get(home_team, 0)
        away_attack = self.attack_strengths.get(away_team, 0)
        away_defense = self.defense_strengths.get(away_team, 0)
        
        # Calculate expected goals
        exp_home_goals = np.exp(self.home_advantage + home_attack - away_defense)
        exp_away_goals = np.exp(away_attack - home_defense)
        
        # Scale by league average
        exp_home_goals *= self.league_avg_goals
        exp_away_goals *= self.league_avg_goals
        
        # Calculate score probabilities
        home_win_prob = 0.0
        draw_prob = 0.0
        away_win_prob = 0.0
        
        for home_goals in range(self.max_goals):
            for away_goals in range(self.max_goals):
                prob = (stats.poisson.pmf(home_goals, exp_home_goals) *
                       stats.poisson.pmf(away_goals, exp_away_goals))
                
                if home_goals > away_goals:
                    home_win_prob += prob
                elif home_goals == away_goals:
                    draw_prob += prob
                else:
                    away_win_prob += prob
        
        # Normalize
        probs = normalize_probabilities([home_win_prob, draw_prob, away_win_prob])
        
        result = PredictionResult(
            home_win_prob=probs[0],
            draw_prob=probs[1],
            away_win_prob=probs[2],
            expected_home_goals=exp_home_goals,
            expected_away_goals=exp_away_goals,
            model_name=self.model_name,
            factors={
                "home_attack": round(home_attack, 3),
                "home_defense": round(home_defense, 3),
                "away_attack": round(away_attack, 3),
                "away_defense": round(away_defense, 3),
                "home_advantage": round(self.home_advantage, 3)
            }
        )
        
        output = result.to_dict()
        output["home_team"] = home_team
        output["away_team"] = away_team
        output["match_id"] = match_data.get("id")
        
        return output
    
    def predict_score_matrix(
        self, 
        home_team: str, 
        away_team: str, 
        max_goals: int = 6
    ) -> np.ndarray:
        """
        Calculate probability matrix for each possible score.
        
        Returns:
            2D array where [i,j] = P(home=i, away=j)
        """
        # Get expected goals
        home_attack = self.attack_strengths.get(home_team, 0)
        away_attack = self.attack_strengths.get(away_team, 0)
        away_defense = self.defense_strengths.get(away_team, 0)
        home_defense = self.defense_strengths.get(home_team, 0)
        
        exp_home = np.exp(self.home_advantage + home_attack - away_defense) * self.league_avg_goals
        exp_away = np.exp(away_attack - home_defense) * self.league_avg_goals
        
        # Build probability matrix
        matrix = np.zeros((max_goals, max_goals))
        
        for i in range(max_goals):
            for j in range(max_goals):
                matrix[i, j] = (stats.poisson.pmf(i, exp_home) * 
                               stats.poisson.pmf(j, exp_away))
        
        return matrix
    
    def get_most_likely_scores(
        self, 
        home_team: str, 
        away_team: str, 
        top_n: int = 5
    ) -> List[Tuple[str, float]]:
        """Get most likely exact scores"""
        matrix = self.predict_score_matrix(home_team, away_team)
        
        # Flatten and get indices
        flat = matrix.flatten()
        top_indices = np.argsort(flat)[::-1][:top_n]
        
        results = []
        for idx in top_indices:
            i, j = divmod(idx, matrix.shape[1])
            results.append((f"{i}-{j}", float(flat[idx])))
        
        return results
