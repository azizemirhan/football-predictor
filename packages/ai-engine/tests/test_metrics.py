"""
Tests for Evaluation Metrics
"""

import pytest
import numpy as np

from ..evaluation.metrics import (
    PredictionMetrics,
    calculate_value_bet_metrics,
    compare_models
)


class TestPredictionMetrics:
    """Test PredictionMetrics class"""

    @pytest.fixture
    def metrics_engine(self):
        """Create metrics engine"""
        return PredictionMetrics()

    def test_add_prediction(self, metrics_engine):
        """Test adding predictions"""
        metrics_engine.add_prediction(
            actual_result='H',
            predicted_probs={'H': 0.6, 'D': 0.3, 'A': 0.1}
        )

        assert len(metrics_engine.predictions) == 1

    def test_classification_metrics(self, metrics_engine):
        """Test classification metrics"""
        # Add predictions
        predictions = [
            ('H', {'H': 0.6, 'D': 0.3, 'A': 0.1}),  # Correct
            ('H', {'H': 0.4, 'D': 0.3, 'A': 0.3}),  # Correct
            ('D', {'H': 0.3, 'D': 0.5, 'A': 0.2}),  # Correct
            ('A', {'H': 0.6, 'D': 0.3, 'A': 0.1}),  # Wrong
        ]

        for actual, probs in predictions:
            metrics_engine.add_prediction(actual, probs)

        metrics = metrics_engine.calculate_all_metrics()

        assert 'accuracy' in metrics
        assert 'total_predictions' in metrics
        assert metrics['total_predictions'] == 4
        assert metrics['accuracy'] == 0.75  # 3/4 correct

    def test_probabilistic_metrics(self, metrics_engine):
        """Test probabilistic metrics"""
        metrics_engine.add_prediction(
            'H',
            {'H': 0.7, 'D': 0.2, 'A': 0.1}
        )

        metrics = metrics_engine.calculate_all_metrics()

        assert 'log_loss' in metrics
        assert 'brier_score' in metrics
        assert 'rps' in metrics
        assert metrics['log_loss'] > 0

    def test_betting_metrics(self, metrics_engine):
        """Test betting metrics"""
        # Add predictions with odds
        metrics_engine.add_prediction(
            actual_result='H',
            predicted_probs={'H': 0.6, 'D': 0.3, 'A': 0.1},
            odds={'H': 2.0, 'D': 3.5, 'A': 4.0},
            stake=10
        )

        metrics_engine.add_prediction(
            actual_result='D',
            predicted_probs={'H': 0.3, 'D': 0.5, 'A': 0.2},
            odds={'H': 2.5, 'D': 3.0, 'A': 3.5},
            stake=10
        )

        metrics = metrics_engine.calculate_all_metrics()

        assert 'total_bets' in metrics
        assert 'roi_pct' in metrics
        assert 'sharpe_ratio' in metrics

    def test_calibration_metrics(self, metrics_engine):
        """Test calibration metrics"""
        for _ in range(20):
            metrics_engine.add_prediction(
                'H',
                {'H': 0.5, 'D': 0.3, 'A': 0.2}
            )

        metrics = metrics_engine.calculate_all_metrics()

        assert 'expected_calibration_error' in metrics

    def test_confusion_matrix(self, metrics_engine):
        """Test confusion matrix"""
        predictions = [
            ('H', {'H': 0.6, 'D': 0.3, 'A': 0.1}),
            ('D', {'H': 0.3, 'D': 0.5, 'A': 0.2}),
            ('A', {'H': 0.2, 'D': 0.3, 'A': 0.5}),
        ]

        for actual, probs in predictions:
            metrics_engine.add_prediction(actual, probs)

        cm = metrics_engine.get_confusion_matrix()

        assert cm.shape == (3, 3)


class TestValueBetMetrics:
    """Test value betting metrics"""

    def test_value_bet_calculation(self):
        """Test value bet metrics"""
        predictions = [
            {
                'predicted_probs': {'H': 0.6, 'D': 0.3, 'A': 0.1},
                'odds': {'H': 2.5, 'D': 3.0, 'A': 4.0},  # H is value bet
                'actual_result': 'H'
            },
            {
                'predicted_probs': {'H': 0.4, 'D': 0.4, 'A': 0.2},
                'odds': {'H': 2.0, 'D': 3.0, 'A': 5.0},  # No value
                'actual_result': 'D'
            }
        ]

        metrics = calculate_value_bet_metrics(predictions, threshold=0.05)

        assert 'value_bets_found' in metrics
        assert metrics['value_bets_found'] >= 0


class TestModelComparison:
    """Test model comparison"""

    def test_compare_two_models(self):
        """Test comparing two models"""
        model_a_preds = [
            {
                'actual_result': 'H',
                'predicted_probs': {'H': 0.6, 'D': 0.3, 'A': 0.1}
            },
            {
                'actual_result': 'D',
                'predicted_probs': {'H': 0.3, 'D': 0.5, 'A': 0.2}
            }
        ]

        model_b_preds = [
            {
                'actual_result': 'H',
                'predicted_probs': {'H': 0.5, 'D': 0.3, 'A': 0.2}
            },
            {
                'actual_result': 'D',
                'predicted_probs': {'H': 0.4, 'D': 0.4, 'A': 0.2}
            }
        ]

        comparison = compare_models(
            model_a_preds,
            model_b_preds,
            model_a_name="XGBoost",
            model_b_name="Poisson"
        )

        assert 'model_a_metrics' in comparison
        assert 'model_b_metrics' in comparison
        assert 'differences' in comparison
        assert 'winners' in comparison


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
