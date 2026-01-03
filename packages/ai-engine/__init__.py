"""
Football Predictor AI Engine
"""

from .models import (
    BasePredictor,
    PoissonModel,
    EloModel,
    XGBoostModel,
    EnsembleModel,
    create_default_ensemble
)
from .betting import ValueBetCalculator, BankrollManager
from .features import FeatureEngineer

__version__ = "1.0.0"

__all__ = [
    "BasePredictor",
    "PoissonModel",
    "EloModel",
    "XGBoostModel",
    "EnsembleModel",
    "create_default_ensemble",
    "ValueBetCalculator",
    "BankrollManager",
    "FeatureEngineer"
]
