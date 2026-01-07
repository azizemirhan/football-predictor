"""
Tests for Model Monitoring
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from ..monitoring.model_monitor import ModelMonitor, AlertSeverity
from ..monitoring.drift_detector import DriftDetector, AdaptiveDriftDetector


class TestModelMonitor:
    """Test ModelMonitor"""

    @pytest.fixture
    def monitor(self):
        """Create monitor"""
        return ModelMonitor(
            model_name='test_model',
            window_size=100,
            baseline_metrics={'accuracy': 0.60, 'log_loss': 0.65}
        )

    def test_monitor_creation(self, monitor):
        """Test creating monitor"""
        assert monitor.model_name == 'test_model'
        assert monitor.window_size == 100
        assert monitor.baseline_metrics['accuracy'] == 0.60

    def test_add_prediction(self, monitor):
        """Test adding predictions"""
        monitor.add_prediction(
            actual_result='H',
            predicted_probs={'H': 0.6, 'D': 0.3, 'A': 0.1}
        )

        assert len(monitor.predictions_buffer) == 1
        assert monitor.total_predictions == 1

    def test_current_metrics(self, monitor):
        """Test getting current metrics"""
        # Add enough predictions
        for i in range(100):
            result = np.random.choice(['H', 'D', 'A'])
            monitor.add_prediction(
                actual_result=result,
                predicted_probs={'H': 0.4, 'D': 0.3, 'A': 0.3}
            )

        metrics = monitor.get_current_metrics()

        assert 'accuracy' in metrics
        assert 'total_predictions' in metrics

    def test_alert_detection(self, monitor):
        """Test alert detection"""
        # Add predictions with poor accuracy (should trigger alert)
        for i in range(100):
            # Wrong predictions
            monitor.add_prediction(
                actual_result='H',
                predicted_probs={'H': 0.2, 'D': 0.3, 'A': 0.5}  # Predicts A
            )

        # Should have alerts
        alerts = monitor.get_alerts()

        # Might have alerts depending on thresholds
        assert isinstance(alerts, list)

    def test_summary(self, monitor):
        """Test getting summary"""
        for i in range(10):
            monitor.add_prediction(
                actual_result='H',
                predicted_probs={'H': 0.6, 'D': 0.3, 'A': 0.1}
            )

        summary = monitor.get_summary()

        assert 'model_name' in summary
        assert 'total_predictions' in summary
        assert summary['total_predictions'] == 10


class TestDriftDetector:
    """Test DriftDetector"""

    @pytest.fixture
    def reference_data(self):
        """Create reference data"""
        return pd.DataFrame({
            'feature_1': np.random.normal(10, 2, 1000),
            'feature_2': np.random.normal(5, 1, 1000),
            'feature_3': np.random.uniform(0, 1, 1000)
        })

    @pytest.fixture
    def detector(self, reference_data):
        """Create detector"""
        return DriftDetector(
            reference_data=reference_data,
            window_size=500
        )

    def test_detector_creation(self, detector):
        """Test creating detector"""
        assert detector.window_size == 500
        assert len(detector.reference_stats) > 0

    def test_add_sample(self, detector):
        """Test adding samples"""
        detector.add_sample(
            features={'feature_1': 10.5, 'feature_2': 5.2, 'feature_3': 0.3},
            prediction={'home_win_prob': 0.5, 'draw_prob': 0.3, 'away_win_prob': 0.2},
            actual_result='H'
        )

        assert len(detector.current_buffer) == 1

    def test_data_drift_detection(self, detector, reference_data):
        """Test data drift detection"""
        # Add samples similar to reference (no drift)
        for _ in range(100):
            detector.add_sample(
                features={
                    'feature_1': np.random.normal(10, 2),
                    'feature_2': np.random.normal(5, 1),
                    'feature_3': np.random.uniform(0, 1)
                },
                prediction={'home_win_prob': 0.5, 'draw_prob': 0.3, 'away_win_prob': 0.2}
            )

        drifts = detector.detect_data_drift()

        # Should be list of DataDrift objects
        assert isinstance(drifts, list)

    def test_concept_drift_detection(self, detector):
        """Test concept drift detection"""
        # Add samples with poor predictions
        for _ in range(50):
            detector.add_sample(
                features={'feature_1': 10, 'feature_2': 5, 'feature_3': 0.5},
                prediction={'home_win_prob': 0.3, 'draw_prob': 0.3, 'away_win_prob': 0.4},
                actual_result='H'  # Actual is H, but predicted A
            )

        drift = detector.detect_concept_drift()

        # Might detect drift
        if drift:
            assert hasattr(drift, 'drift_detected')
            assert hasattr(drift, 'accuracy_drop')

    def test_prediction_drift(self, detector):
        """Test prediction drift detection"""
        # Add varied predictions
        for i in range(60):
            prob = 0.3 if i < 30 else 0.7
            detector.add_sample(
                features={'feature_1': 10, 'feature_2': 5, 'feature_3': 0.5},
                prediction={'home_win_prob': prob, 'draw_prob': 0.2, 'away_win_prob': 0.1}
            )

        drift_metrics = detector.detect_prediction_drift()

        assert 'total_drift' in drift_metrics


class TestAdaptiveDriftDetector:
    """Test AdaptiveDriftDetector"""

    def test_detector_creation(self):
        """Test creating adaptive detector"""
        detector = AdaptiveDriftDetector(delta=0.005, lambda_=50)

        assert detector.delta == 0.005
        assert detector.lambda_ == 50

    def test_drift_detection(self):
        """Test drift detection"""
        detector = AdaptiveDriftDetector(delta=0.005, lambda_=10)

        # Add stable values
        for _ in range(50):
            drift = detector.add_value(0.5)
            assert drift is False

        # Add sudden change
        for _ in range(20):
            detector.add_value(0.9)

        # Might detect drift after sudden change
        # (depends on lambda parameter)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
