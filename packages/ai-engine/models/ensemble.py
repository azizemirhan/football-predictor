"""
Ensemble Model - Çoklu model kombinasyonu
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple
import structlog

from .base import BasePredictor, PredictionResult, normalize_probabilities
from .poisson import PoissonModel
from .elo import EloModel
from .xgboost_model import XGBoostModel

logger = structlog.get_logger()


class EnsembleModel(BasePredictor):
    """
    Ensemble model combining multiple prediction models.
    
    Strategies:
    - Simple average
    - Weighted average (based on recent performance)
    - Stacking (meta-learner)
    """
    
    def __init__(
        self, 
        version: str = "1.0",
        strategy: str = "weighted",
        models: Optional[List[BasePredictor]] = None
    ):
        super().__init__(model_name="ensemble", version=version)
        
        self.strategy = strategy
        self.models = models or []
        self.weights = {}  # model_name -> weight
        
        # Performance tracking
        self.model_performance = {}  # model_name -> {accuracy, log_loss}
    
    def add_model(self, model: BasePredictor, weight: float = 1.0):
        """Add a model to the ensemble"""
        self.models.append(model)
        self.weights[model.model_name] = weight
        logger.info("model_added", model=model.model_name, weight=weight)
    
    def train(self, data, **kwargs) -> Dict[str, float]:
        """
        Train all models in the ensemble.
        
        Args:
            data: Training data
            
        Returns:
            Combined training metrics
        """
        logger.info("training_started", model=self.model_name, n_models=len(self.models))
        
        all_metrics = {}
        
        for model in self.models:
            try:
                metrics = model.train(data, **kwargs)
                all_metrics[model.model_name] = metrics
                
                # Update performance tracking
                self.model_performance[model.model_name] = {
                    "accuracy": metrics.get("accuracy", 0),
                    "log_loss": metrics.get("log_loss", 1)
                }
                
            except Exception as e:
                logger.error("model_train_error", model=model.model_name, error=str(e))
                all_metrics[model.model_name] = {"error": str(e)}
        
        # Update weights based on performance
        if self.strategy == "weighted":
            self._update_weights()
        
        self.is_trained = True
        self.training_metrics = all_metrics
        
        logger.info("training_completed", model=self.model_name, metrics=all_metrics)
        
        return all_metrics
    
    def _update_weights(self):
        """Update model weights based on performance"""
        if not self.model_performance:
            return
        
        # Use accuracy as weight (higher is better)
        accuracies = {
            name: perf.get("accuracy", 0.5)
            for name, perf in self.model_performance.items()
        }
        
        # Normalize to sum to 1
        total = sum(accuracies.values())
        if total > 0:
            self.weights = {
                name: acc / total
                for name, acc in accuracies.items()
            }
        
        logger.info("weights_updated", weights=self.weights)
    
    def predict(self, match_data: Dict) -> Dict[str, Any]:
        """
        Make ensemble prediction.
        
        Args:
            match_data: Match information
            
        Returns:
            Combined prediction
        """
        if not self.models:
            return self._default_prediction(match_data)
        
        predictions = []
        model_predictions = {}
        
        # Get predictions from each model
        for model in self.models:
            try:
                pred = model.predict(match_data)
                if not pred.get("error"):
                    predictions.append(pred)
                    model_predictions[model.model_name] = pred
            except Exception as e:
                logger.warning("model_predict_error", model=model.model_name, error=str(e))
        
        if not predictions:
            return self._default_prediction(match_data)
        
        # Combine predictions
        if self.strategy == "simple":
            combined = self._simple_average(predictions)
        elif self.strategy == "weighted":
            combined = self._weighted_average(predictions)
        else:
            combined = self._simple_average(predictions)
        
        # Calculate confidence based on model agreement
        confidence = self._calculate_ensemble_confidence(predictions)
        
        result = PredictionResult(
            home_win_prob=combined["home_win_prob"],
            draw_prob=combined["draw_prob"],
            away_win_prob=combined["away_win_prob"],
            expected_home_goals=combined.get("expected_home_goals"),
            expected_away_goals=combined.get("expected_away_goals"),
            confidence=confidence,
            model_name=self.model_name,
            factors={"model_predictions": model_predictions}
        )
        
        output = result.to_dict()
        output["home_team"] = match_data.get("home_team")
        output["away_team"] = match_data.get("away_team")
        output["match_id"] = match_data.get("id")
        output["individual_predictions"] = model_predictions
        
        return output
    
    def _simple_average(self, predictions: List[Dict]) -> Dict[str, float]:
        """Simple average of all predictions"""
        n = len(predictions)
        
        home_win = sum(p["home_win_prob"] for p in predictions) / n
        draw = sum(p["draw_prob"] for p in predictions) / n
        away_win = sum(p["away_win_prob"] for p in predictions) / n
        
        probs = normalize_probabilities([home_win, draw, away_win])
        
        # Average expected goals if available
        exp_home = None
        exp_away = None
        
        goals_preds = [p for p in predictions if p.get("expected_home_goals")]
        if goals_preds:
            exp_home = sum(p["expected_home_goals"] for p in goals_preds) / len(goals_preds)
            exp_away = sum(p["expected_away_goals"] for p in goals_preds) / len(goals_preds)
        
        return {
            "home_win_prob": probs[0],
            "draw_prob": probs[1],
            "away_win_prob": probs[2],
            "expected_home_goals": exp_home,
            "expected_away_goals": exp_away
        }
    
    def _weighted_average(self, predictions: List[Dict]) -> Dict[str, float]:
        """Weighted average based on model performance"""
        home_win = 0.0
        draw = 0.0
        away_win = 0.0
        total_weight = 0.0
        
        for pred in predictions:
            model_name = pred.get("model", "unknown")
            weight = self.weights.get(model_name, 1 / len(predictions))
            
            home_win += pred["home_win_prob"] * weight
            draw += pred["draw_prob"] * weight
            away_win += pred["away_win_prob"] * weight
            total_weight += weight
        
        if total_weight > 0:
            home_win /= total_weight
            draw /= total_weight
            away_win /= total_weight
        
        probs = normalize_probabilities([home_win, draw, away_win])
        
        # Weighted average expected goals
        exp_home = None
        exp_away = None
        total_goals_weight = 0.0
        
        for pred in predictions:
            if pred.get("expected_home_goals"):
                model_name = pred.get("model", "unknown")
                weight = self.weights.get(model_name, 1 / len(predictions))
                
                if exp_home is None:
                    exp_home = 0
                    exp_away = 0
                
                exp_home += pred["expected_home_goals"] * weight
                exp_away += pred["expected_away_goals"] * weight
                total_goals_weight += weight
        
        if total_goals_weight > 0:
            exp_home /= total_goals_weight
            exp_away /= total_goals_weight
        
        return {
            "home_win_prob": probs[0],
            "draw_prob": probs[1],
            "away_win_prob": probs[2],
            "expected_home_goals": exp_home,
            "expected_away_goals": exp_away
        }
    
    def _calculate_ensemble_confidence(self, predictions: List[Dict]) -> float:
        """
        Calculate confidence based on model agreement.
        Higher confidence when models agree on outcome.
        """
        if len(predictions) < 2:
            return 0.5
        
        # Get predicted outcomes
        outcomes = []
        for pred in predictions:
            max_prob = max(
                pred["home_win_prob"],
                pred["draw_prob"],
                pred["away_win_prob"]
            )
            if max_prob == pred["home_win_prob"]:
                outcomes.append("H")
            elif max_prob == pred["draw_prob"]:
                outcomes.append("D")
            else:
                outcomes.append("A")
        
        # Calculate agreement
        agreement = max(outcomes.count(o) for o in set(outcomes)) / len(outcomes)
        
        # Adjust based on probability spread
        avg_max_prob = np.mean([
            max(p["home_win_prob"], p["draw_prob"], p["away_win_prob"])
            for p in predictions
        ])
        
        return (agreement + avg_max_prob) / 2
    
    def get_model_weights(self) -> Dict[str, float]:
        """Get current model weights"""
        return self.weights.copy()
    
    def set_model_weights(self, weights: Dict[str, float]):
        """Set model weights manually"""
        self.weights.update(weights)
        logger.info("weights_set", weights=self.weights)


def create_default_ensemble() -> EnsembleModel:
    """Create ensemble with default models"""
    ensemble = EnsembleModel(strategy="weighted")
    
    # Add models
    ensemble.add_model(PoissonModel(), weight=0.30)
    ensemble.add_model(EloModel(), weight=0.25)
    ensemble.add_model(XGBoostModel(), weight=0.45)
    
    return ensemble
