"""
Base Model - Tüm tahmin modelleri için temel sınıf
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import joblib
import structlog

logger = structlog.get_logger()


class BasePredictor(ABC):
    """
    Abstract base class for all prediction models.
    """
    
    def __init__(self, model_name: str, version: str = "1.0"):
        self.model_name = model_name
        self.version = version
        self.is_trained = False
        self.last_trained = None
        self.training_metrics = {}
    
    @abstractmethod
    def train(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Train the model.
        
        Args:
            data: Training data
            
        Returns:
            Training metrics (accuracy, loss, etc.)
        """
        pass
    
    @abstractmethod
    def predict(self, match_data: Dict) -> Dict[str, Any]:
        """
        Make prediction for a single match.
        
        Args:
            match_data: Match information (teams, stats, etc.)
            
        Returns:
            Prediction with probabilities
        """
        pass
    
    def predict_batch(self, matches: List[Dict]) -> List[Dict]:
        """
        Make predictions for multiple matches.
        
        Args:
            matches: List of match data
            
        Returns:
            List of predictions
        """
        predictions = []
        for match in matches:
            try:
                pred = self.predict(match)
                predictions.append(pred)
            except Exception as e:
                logger.warning(
                    "prediction_error",
                    model=self.model_name,
                    error=str(e)
                )
                predictions.append(self._default_prediction(match))
        
        return predictions
    
    def _default_prediction(self, match: Dict) -> Dict:
        """Return default prediction when model fails"""
        return {
            "match_id": match.get("id"),
            "home_team": match.get("home_team"),
            "away_team": match.get("away_team"),
            "home_win_prob": 0.33,
            "draw_prob": 0.33,
            "away_win_prob": 0.34,
            "confidence": 0.0,
            "model": self.model_name,
            "error": True
        }
    
    def save(self, path: str):
        """Save model to disk"""
        joblib.dump(self, path)
        logger.info("model_saved", model=self.model_name, path=path)
    
    @classmethod
    def load(cls, path: str) -> "BasePredictor":
        """Load model from disk"""
        model = joblib.load(path)
        logger.info("model_loaded", model=model.model_name, path=path)
        return model
    
    def get_model_info(self) -> Dict:
        """Get model metadata"""
        return {
            "name": self.model_name,
            "version": self.version,
            "is_trained": self.is_trained,
            "last_trained": self.last_trained,
            "training_metrics": self.training_metrics
        }


class MatchResult:
    """Enum-like class for match results"""
    HOME_WIN = "H"
    DRAW = "D"
    AWAY_WIN = "A"
    
    @classmethod
    def from_score(cls, home_score: int, away_score: int) -> str:
        if home_score > away_score:
            return cls.HOME_WIN
        elif home_score == away_score:
            return cls.DRAW
        else:
            return cls.AWAY_WIN


class PredictionResult:
    """Container for prediction results"""
    
    def __init__(
        self,
        home_win_prob: float,
        draw_prob: float,
        away_win_prob: float,
        expected_home_goals: Optional[float] = None,
        expected_away_goals: Optional[float] = None,
        confidence: Optional[float] = None,
        model_name: Optional[str] = None,
        factors: Optional[Dict] = None
    ):
        self.home_win_prob = home_win_prob
        self.draw_prob = draw_prob
        self.away_win_prob = away_win_prob
        self.expected_home_goals = expected_home_goals
        self.expected_away_goals = expected_away_goals
        self.confidence = confidence or self._calculate_confidence()
        self.model_name = model_name
        self.factors = factors or {}
    
    def _calculate_confidence(self) -> float:
        """Calculate confidence based on probability distribution"""
        probs = [self.home_win_prob, self.draw_prob, self.away_win_prob]
        max_prob = max(probs)
        # Higher confidence when one outcome is clearly more likely
        return (max_prob - 0.33) / 0.67  # Normalize to 0-1 range
    
    @property
    def predicted_result(self) -> str:
        """Get most likely result"""
        probs = {
            MatchResult.HOME_WIN: self.home_win_prob,
            MatchResult.DRAW: self.draw_prob,
            MatchResult.AWAY_WIN: self.away_win_prob
        }
        return max(probs, key=probs.get)
    
    @property
    def most_likely_score(self) -> Optional[str]:
        """Get most likely score"""
        if self.expected_home_goals is None or self.expected_away_goals is None:
            return None
        return f"{round(self.expected_home_goals)}-{round(self.expected_away_goals)}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "home_win_prob": round(self.home_win_prob, 4),
            "draw_prob": round(self.draw_prob, 4),
            "away_win_prob": round(self.away_win_prob, 4),
            "expected_home_goals": round(self.expected_home_goals, 2) if self.expected_home_goals else None,
            "expected_away_goals": round(self.expected_away_goals, 2) if self.expected_away_goals else None,
            "most_likely_score": self.most_likely_score,
            "predicted_result": self.predicted_result,
            "confidence": round(self.confidence, 4),
            "model": self.model_name,
            "factors": self.factors
        }
    
    def __repr__(self):
        return f"PredictionResult(H={self.home_win_prob:.2%}, D={self.draw_prob:.2%}, A={self.away_win_prob:.2%})"


def normalize_probabilities(probs: List[float]) -> List[float]:
    """Normalize probabilities to sum to 1"""
    total = sum(probs)
    if total == 0:
        return [1/len(probs)] * len(probs)
    return [p / total for p in probs]


def calculate_log_loss(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-15) -> float:
    """Calculate log loss (cross-entropy)"""
    y_pred = np.clip(y_pred, eps, 1 - eps)
    return -np.mean(np.sum(y_true * np.log(y_pred), axis=1))


def calculate_brier_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Brier score"""
    return np.mean(np.sum((y_true - y_pred) ** 2, axis=1))


def calculate_rps(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Ranked Probability Score"""
    # Cumulative sums
    cum_true = np.cumsum(y_true, axis=1)
    cum_pred = np.cumsum(y_pred, axis=1)
    
    # RPS for each prediction
    rps = np.mean(np.sum((cum_pred - cum_true) ** 2, axis=1) / (y_true.shape[1] - 1))
    return rps
