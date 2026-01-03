"""
XGBoost Model - Gradient boosting ile maç sonucu tahmini
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
import xgboost as xgb
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
import structlog

from .base import BasePredictor, PredictionResult, normalize_probabilities

logger = structlog.get_logger()


class XGBoostModel(BasePredictor):
    """
    XGBoost classifier for match outcome prediction.
    
    Uses engineered features from team statistics to predict
    match outcomes (Home Win, Draw, Away Win).
    """
    
    def __init__(self, version: str = "1.0", **xgb_params):
        super().__init__(model_name="xgboost", version=version)
        
        # Default XGBoost parameters
        self.params = {
            "objective": "multi:softprob",
            "num_class": 3,
            "max_depth": 6,
            "learning_rate": 0.1,
            "n_estimators": 200,
            "min_child_weight": 3,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "gamma": 0.1,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "random_state": 42,
            "n_jobs": -1,
            "eval_metric": "mlogloss"
        }
        self.params.update(xgb_params)
        
        self.model = None
        self.feature_names = []
        self.label_encoder = LabelEncoder()
        self.scaler = None
    
    def train(self, data: pd.DataFrame, features: Optional[pd.DataFrame] = None) -> Dict[str, float]:
        """
        Train XGBoost model.
        
        Args:
            data: Match data with home_score, away_score
            features: Pre-computed features (optional)
            
        Returns:
            Training metrics
        """
        logger.info("training_started", model=self.model_name, samples=len(data))
        
        # Filter completed matches
        matches = data[data["home_score"].notna()].copy()
        
        # Generate or use provided features
        if features is not None:
            X = features
        else:
            X = self._generate_features(matches)
        
        self.feature_names = list(X.columns)
        
        # Create target variable
        y = matches.apply(self._get_result, axis=1)
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Train-test split
        X_train, X_val, y_train, y_val = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42
        )
        
        # Create model
        self.model = xgb.XGBClassifier(**self.params)
        
        # Train with early stopping
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_val = self.model.predict(X_val)
        
        train_acc = np.mean(y_pred_train == y_train)
        val_acc = np.mean(y_pred_val == y_val)
        
        # Cross-validation
        cv_scores = cross_val_score(self.model, X, y_encoded, cv=5, scoring="accuracy")
        
        metrics = {
            "train_accuracy": round(train_acc, 4),
            "val_accuracy": round(val_acc, 4),
            "cv_accuracy": round(cv_scores.mean(), 4),
            "cv_std": round(cv_scores.std(), 4),
            "samples": len(X)
        }
        
        self.is_trained = True
        self.training_metrics = metrics
        
        logger.info("training_completed", model=self.model_name, **metrics)
        
        return metrics
    
    def _get_result(self, row) -> str:
        """Get match result from scores"""
        if row["home_score"] > row["away_score"]:
            return "H"
        elif row["home_score"] == row["away_score"]:
            return "D"
        else:
            return "A"
    
    def _generate_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate features from match data.
        Uses available columns or creates placeholders.
        """
        features = pd.DataFrame()
        
        # Form features (if available)
        if "home_form_points" in data.columns:
            features["home_form_points"] = data["home_form_points"]
            features["away_form_points"] = data["away_form_points"]
        else:
            features["home_form_points"] = 0
            features["away_form_points"] = 0
        
        # Goals features
        if "home_goals_scored_avg" in data.columns:
            features["home_goals_scored_avg"] = data["home_goals_scored_avg"]
            features["home_goals_conceded_avg"] = data["home_goals_conceded_avg"]
            features["away_goals_scored_avg"] = data["away_goals_scored_avg"]
            features["away_goals_conceded_avg"] = data["away_goals_conceded_avg"]
        else:
            features["home_goals_scored_avg"] = 1.5
            features["home_goals_conceded_avg"] = 1.0
            features["away_goals_scored_avg"] = 1.2
            features["away_goals_conceded_avg"] = 1.2
        
        # Rating features
        if "home_elo" in data.columns:
            features["home_elo"] = data["home_elo"]
            features["away_elo"] = data["away_elo"]
            features["elo_diff"] = features["home_elo"] - features["away_elo"]
        else:
            features["home_elo"] = 1500
            features["away_elo"] = 1500
            features["elo_diff"] = 0
        
        # xG features
        if "home_xg_avg" in data.columns:
            features["home_xg_avg"] = data["home_xg_avg"]
            features["away_xg_avg"] = data["away_xg_avg"]
        
        # H2H features
        if "h2h_home_wins" in data.columns:
            features["h2h_home_wins"] = data["h2h_home_wins"]
            features["h2h_away_wins"] = data["h2h_away_wins"]
            features["h2h_draws"] = data["h2h_draws"]
        
        # Position features
        if "home_position" in data.columns:
            features["home_position"] = data["home_position"]
            features["away_position"] = data["away_position"]
            features["position_diff"] = data["away_position"] - data["home_position"]
        
        return features.fillna(0)
    
    def predict(self, match_data: Dict) -> Dict[str, Any]:
        """
        Predict match outcome.
        
        Args:
            match_data: Dict with features or raw data
            
        Returns:
            Prediction dictionary
        """
        if not self.is_trained or self.model is None:
            return self._default_prediction(match_data)
        
        # Prepare features
        if "features" in match_data:
            features = match_data["features"]
        else:
            features = self._extract_features(match_data)
        
        # Convert to array
        X = np.array([features[f] for f in self.feature_names]).reshape(1, -1)
        
        # Predict probabilities
        probs = self.model.predict_proba(X)[0]
        
        # Map to H, D, A
        classes = self.label_encoder.classes_
        prob_dict = {c: p for c, p in zip(classes, probs)}
        
        home_win_prob = prob_dict.get("H", 0.33)
        draw_prob = prob_dict.get("D", 0.33)
        away_win_prob = prob_dict.get("A", 0.34)
        
        result = PredictionResult(
            home_win_prob=home_win_prob,
            draw_prob=draw_prob,
            away_win_prob=away_win_prob,
            model_name=self.model_name,
            factors=self._get_feature_importance(match_data)
        )
        
        output = result.to_dict()
        output["home_team"] = match_data.get("home_team")
        output["away_team"] = match_data.get("away_team")
        output["match_id"] = match_data.get("id")
        
        return output
    
    def _extract_features(self, match_data: Dict) -> Dict[str, float]:
        """Extract features from match data dict"""
        features = {}
        
        for name in self.feature_names:
            features[name] = match_data.get(name, 0)
        
        return features
    
    def _get_feature_importance(self, match_data: Dict) -> Dict[str, float]:
        """Get top feature importances for this prediction"""
        if self.model is None:
            return {}
        
        importance = self.model.feature_importances_
        top_indices = np.argsort(importance)[::-1][:5]
        
        return {
            self.feature_names[i]: round(float(importance[i]), 4)
            for i in top_indices
        }
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get all feature importances"""
        if self.model is None:
            return {}
        
        importance = self.model.feature_importances_
        
        return {
            name: round(float(imp), 4)
            for name, imp in sorted(
                zip(self.feature_names, importance),
                key=lambda x: x[1],
                reverse=True
            )
        }
