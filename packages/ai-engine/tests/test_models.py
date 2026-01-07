"""
Comprehensive Model Tests
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from ..models.base import BasePredictor, PredictionResult, MatchResult
from ..models.poisson import PoissonModel
from ..models.elo import EloModel
from ..models.xgboost_model import XGBoostModel
from ..models.ensemble import EnsembleModel, create_default_ensemble


# Fixtures
@pytest.fixture
def sample_match_data():
    """Create sample match data"""
    dates = pd.date_range(start='2023-01-01', periods=200, freq='D')

    data = {
        'match_date': dates,
        'home_team': ['Team A', 'Team B'] * 100,
        'away_team': ['Team C', 'Team D'] * 100,
        'home_score': np.random.randint(0, 4, 200),
        'away_score': np.random.randint(0, 4, 200),
        'home_odds': np.random.uniform(1.5, 3.5, 200),
        'draw_odds': np.random.uniform(2.5, 4.5, 200),
        'away_odds': np.random.uniform(1.5, 3.5, 200)
    }

    return pd.DataFrame(data)


@pytest.fixture
def trained_poisson_model(sample_match_data):
    """Create trained Poisson model"""
    model = PoissonModel()
    model.train(sample_match_data)
    return model


@pytest.fixture
def trained_elo_model(sample_match_data):
    """Create trained Elo model"""
    model = EloModel()
    model.train(sample_match_data)
    return model


# Base Model Tests
class TestBaseModel:
    """Test base model functionality"""

    def test_prediction_result_creation(self):
        """Test PredictionResult creation"""
        result = PredictionResult(
            home_win_prob=0.5,
            draw_prob=0.3,
            away_win_prob=0.2,
            expected_home_goals=1.8,
            expected_away_goals=1.2,
            model_name='test'
        )

        assert result.home_win_prob == 0.5
        assert result.predicted_result == 'H'
        assert result.confidence > 0

    def test_prediction_result_to_dict(self):
        """Test conversion to dictionary"""
        result = PredictionResult(
            home_win_prob=0.5,
            draw_prob=0.3,
            away_win_prob=0.2
        )

        result_dict = result.to_dict()

        assert 'home_win_prob' in result_dict
        assert 'predicted_result' in result_dict
        assert 'confidence' in result_dict

    def test_match_result_from_score(self):
        """Test MatchResult.from_score"""
        assert MatchResult.from_score(2, 1) == 'H'
        assert MatchResult.from_score(1, 1) == 'D'
        assert MatchResult.from_score(1, 2) == 'A'


# Poisson Model Tests
class TestPoissonModel:
    """Test Poisson model"""

    def test_model_creation(self):
        """Test model instantiation"""
        model = PoissonModel(version="1.0")
        assert model.model_name == "poisson"
        assert model.version == "1.0"
        assert not model.is_trained

    def test_model_training(self, sample_match_data):
        """Test model training"""
        model = PoissonModel()
        metrics = model.train(sample_match_data)

        assert model.is_trained
        assert 'accuracy' in metrics
        assert 'log_loss' in metrics
        assert len(model.attack_strengths) > 0
        assert len(model.defense_strengths) > 0

    def test_prediction(self, trained_poisson_model):
        """Test making predictions"""
        pred = trained_poisson_model.predict({
            'home_team': 'Team A',
            'away_team': 'Team B'
        })

        assert 'home_win_prob' in pred
        assert 'draw_prob' in pred
        assert 'away_win_prob' in pred
        assert 'expected_home_goals' in pred

        # Check probabilities sum to ~1
        total = pred['home_win_prob'] + pred['draw_prob'] + pred['away_win_prob']
        assert abs(total - 1.0) < 0.01

    def test_score_matrix(self, trained_poisson_model):
        """Test score probability matrix"""
        matrix = trained_poisson_model.predict_score_matrix('Team A', 'Team B')

        assert matrix.shape[0] > 0
        assert matrix.shape[1] > 0
        assert matrix.sum() > 0  # Some probability

    def test_most_likely_scores(self, trained_poisson_model):
        """Test most likely scores"""
        scores = trained_poisson_model.get_most_likely_scores('Team A', 'Team B')

        assert len(scores) > 0
        assert all(isinstance(s, tuple) for s in scores)

    def test_model_save_load(self, trained_poisson_model, tmp_path):
        """Test model persistence"""
        model_path = tmp_path / "poisson.joblib"

        # Save
        trained_poisson_model.save(str(model_path))
        assert model_path.exists()

        # Load
        loaded_model = PoissonModel.load(str(model_path))
        assert loaded_model.is_trained
        assert loaded_model.model_name == "poisson"


# Elo Model Tests
class TestEloModel:
    """Test Elo model"""

    def test_model_creation(self):
        """Test model instantiation"""
        model = EloModel()
        assert model.model_name == "elo"
        assert model.INITIAL_RATING == 1500

    def test_model_training(self, sample_match_data):
        """Test training"""
        model = EloModel()
        metrics = model.train(sample_match_data)

        assert model.is_trained
        assert 'accuracy' in metrics
        assert len(model.ratings) > 0

    def test_prediction(self, trained_elo_model):
        """Test predictions"""
        pred = trained_elo_model.predict({
            'home_team': 'Team A',
            'away_team': 'Team B'
        })

        assert 'home_win_prob' in pred
        assert 'factors' in pred
        assert 'home_rating' in pred['factors']

    def test_get_rating(self, trained_elo_model):
        """Test getting team rating"""
        rating = trained_elo_model.get_rating('Team A')
        assert isinstance(rating, float)
        assert rating > 0

    def test_get_rankings(self, trained_elo_model):
        """Test team rankings"""
        rankings = trained_elo_model.get_rankings(top_n=5)

        assert len(rankings) <= 5
        assert all(isinstance(r, tuple) for r in rankings)

    def test_season_regression(self, trained_elo_model):
        """Test season regression"""
        initial_rating = trained_elo_model.get_rating('Team A')

        trained_elo_model.apply_season_regression()

        new_rating = trained_elo_model.get_rating('Team A')

        # Rating should move toward average
        assert new_rating != initial_rating


# XGBoost Model Tests
class TestXGBoostModel:
    """Test XGBoost model"""

    def test_model_creation(self):
        """Test instantiation"""
        model = XGBoostModel()
        assert model.model_name == "xgboost"
        assert model.model is None

    def test_custom_params(self):
        """Test custom parameters"""
        model = XGBoostModel(max_depth=10, learning_rate=0.05)
        assert model.params['max_depth'] == 10
        assert model.params['learning_rate'] == 0.05

    def test_training(self, sample_match_data):
        """Test training"""
        model = XGBoostModel()
        metrics = model.train(sample_match_data)

        assert model.is_trained
        assert model.model is not None
        assert 'train_accuracy' in metrics
        assert 'val_accuracy' in metrics

    def test_feature_importance(self, sample_match_data):
        """Test feature importance"""
        model = XGBoostModel()
        model.train(sample_match_data)

        importance = model.get_feature_importance()

        assert isinstance(importance, dict)
        assert len(importance) > 0


# Ensemble Model Tests
class TestEnsembleModel:
    """Test ensemble model"""

    def test_ensemble_creation(self):
        """Test creating ensemble"""
        ensemble = EnsembleModel(strategy='weighted')
        assert ensemble.model_name == 'ensemble'
        assert ensemble.strategy == 'weighted'

    def test_add_model(self):
        """Test adding models to ensemble"""
        ensemble = EnsembleModel()
        model = PoissonModel()

        ensemble.add_model(model, weight=0.5)

        assert len(ensemble.models) == 1
        assert ensemble.weights['poisson'] == 0.5

    def test_ensemble_prediction(self, sample_match_data):
        """Test ensemble predictions"""
        ensemble = EnsembleModel(strategy='simple')

        # Add trained models
        poisson = PoissonModel()
        poisson.train(sample_match_data[:100])

        elo = EloModel()
        elo.train(sample_match_data[:100])

        ensemble.add_model(poisson)
        ensemble.add_model(elo)

        # Predict
        pred = ensemble.predict({
            'home_team': 'Team A',
            'away_team': 'Team B'
        })

        assert 'home_win_prob' in pred
        assert 'individual_predictions' in pred

    def test_default_ensemble(self):
        """Test default ensemble creation"""
        ensemble = create_default_ensemble()

        assert len(ensemble.models) == 3
        assert 'poisson' in ensemble.weights
        assert 'elo' in ensemble.weights
        assert 'xgboost' in ensemble.weights


# Batch Prediction Tests
class TestBatchPredictions:
    """Test batch prediction functionality"""

    def test_batch_predictions(self, trained_poisson_model):
        """Test predicting multiple matches"""
        matches = [
            {'home_team': 'Team A', 'away_team': 'Team B'},
            {'home_team': 'Team C', 'away_team': 'Team D'}
        ]

        predictions = trained_poisson_model.predict_batch(matches)

        assert len(predictions) == 2
        assert all('home_win_prob' in p for p in predictions)


# Error Handling Tests
class TestErrorHandling:
    """Test error handling"""

    def test_insufficient_training_data(self):
        """Test training with insufficient data"""
        model = PoissonModel()

        # Create very small dataset
        small_data = pd.DataFrame({
            'match_date': pd.date_range(start='2023-01-01', periods=10),
            'home_team': ['A'] * 10,
            'away_team': ['B'] * 10,
            'home_score': [1] * 10,
            'away_score': [0] * 10
        })

        metrics = model.train(small_data)

        assert 'error' in metrics or model.is_trained

    def test_prediction_before_training(self):
        """Test predicting before training"""
        model = PoissonModel()

        pred = model.predict({
            'home_team': 'Team A',
            'away_team': 'Team B'
        })

        # Should return default prediction
        assert 'home_win_prob' in pred
        assert pred.get('error') is True or pred['home_win_prob'] == 0.33


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
