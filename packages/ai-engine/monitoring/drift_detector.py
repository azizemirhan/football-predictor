"""
Drift Detection - Data and concept drift monitoring
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from scipy import stats
from collections import deque
import structlog

logger = structlog.get_logger()


@dataclass
class DataDrift:
    """Data drift detection result"""
    feature_name: str
    drift_detected: bool
    drift_score: float
    p_value: float
    reference_mean: float
    current_mean: float
    reference_std: float
    current_std: float
    test_method: str
    timestamp: datetime


@dataclass
class ConceptDrift:
    """Concept drift detection result"""
    drift_detected: bool
    drift_score: float
    accuracy_drop: float
    error_rate_increase: float
    timestamp: datetime


class DriftDetector:
    """
    Detect data drift and concept drift.

    Data drift: Changes in input feature distributions
    Concept drift: Changes in the relationship between features and target
    """

    def __init__(
        self,
        reference_data: Optional[pd.DataFrame] = None,
        window_size: int = 500,
        drift_threshold: float = 0.05  # p-value threshold
    ):
        """
        Args:
            reference_data: Reference dataset (training data)
            window_size: Rolling window size for current data
            drift_threshold: Statistical significance threshold
        """
        self.reference_data = reference_data
        self.window_size = window_size
        self.drift_threshold = drift_threshold

        # Reference statistics
        self.reference_stats = {}
        if reference_data is not None:
            self._calculate_reference_stats()

        # Current data buffer
        self.current_buffer = deque(maxlen=window_size)

        # Drift history
        self.data_drift_history = []
        self.concept_drift_history = []

    def _calculate_reference_stats(self):
        """Calculate statistics from reference data"""
        for col in self.reference_data.select_dtypes(include=[np.number]).columns:
            self.reference_stats[col] = {
                'mean': float(self.reference_data[col].mean()),
                'std': float(self.reference_data[col].std()),
                'min': float(self.reference_data[col].min()),
                'max': float(self.reference_data[col].max()),
                'quantiles': {
                    '25': float(self.reference_data[col].quantile(0.25)),
                    '50': float(self.reference_data[col].quantile(0.50)),
                    '75': float(self.reference_data[col].quantile(0.75))
                }
            }

    def add_sample(self, features: Dict[str, float], prediction: Dict, actual_result: Optional[str] = None):
        """
        Add a sample to the current buffer.

        Args:
            features: Feature dictionary
            prediction: Model prediction
            actual_result: Actual outcome (if available)
        """
        self.current_buffer.append({
            'features': features,
            'prediction': prediction,
            'actual_result': actual_result,
            'timestamp': datetime.now()
        })

    def detect_data_drift(
        self,
        feature_name: Optional[str] = None,
        method: str = 'ks'  # 'ks' (Kolmogorov-Smirnov) or 't-test'
    ) -> List[DataDrift]:
        """
        Detect data drift in features.

        Args:
            feature_name: Specific feature to check (None = check all)
            method: Statistical test method

        Returns:
            List of DataDrift results
        """
        if len(self.current_buffer) < 30:
            logger.warning("insufficient_samples", count=len(self.current_buffer))
            return []

        results = []

        # Convert buffer to DataFrame
        current_features = pd.DataFrame([s['features'] for s in self.current_buffer])

        features_to_check = [feature_name] if feature_name else current_features.columns

        for feature in features_to_check:
            if feature not in current_features.columns:
                continue

            if feature not in self.reference_stats:
                continue

            current_values = current_features[feature].dropna()

            if len(current_values) < 10:
                continue

            # Get reference distribution
            if self.reference_data is not None:
                reference_values = self.reference_data[feature].dropna()
            else:
                # Use reference stats to generate approximate distribution
                ref_stats = self.reference_stats[feature]
                reference_values = np.random.normal(
                    ref_stats['mean'],
                    ref_stats['std'],
                    size=1000
                )

            # Perform statistical test
            if method == 'ks':
                # Kolmogorov-Smirnov test
                statistic, p_value = stats.ks_2samp(reference_values, current_values)
                drift_score = statistic
            else:  # t-test
                statistic, p_value = stats.ttest_ind(reference_values, current_values)
                drift_score = abs(statistic)

            drift_detected = p_value < self.drift_threshold

            drift = DataDrift(
                feature_name=feature,
                drift_detected=drift_detected,
                drift_score=float(drift_score),
                p_value=float(p_value),
                reference_mean=float(self.reference_stats[feature]['mean']),
                current_mean=float(current_values.mean()),
                reference_std=float(self.reference_stats[feature]['std']),
                current_std=float(current_values.std()),
                test_method=method,
                timestamp=datetime.now()
            )

            results.append(drift)

            if drift_detected:
                logger.warning(
                    "data_drift_detected",
                    feature=feature,
                    drift_score=drift_score,
                    p_value=p_value
                )

                self.data_drift_history.append(drift)

        return results

    def detect_concept_drift(
        self,
        accuracy_threshold: float = 0.10  # 10% drop
    ) -> Optional[ConceptDrift]:
        """
        Detect concept drift (change in prediction accuracy).

        Args:
            accuracy_threshold: Minimum accuracy drop to trigger drift

        Returns:
            ConceptDrift result
        """
        # Filter samples with actual results
        samples_with_results = [
            s for s in self.current_buffer
            if s['actual_result'] is not None
        ]

        if len(samples_with_results) < 30:
            return None

        # Calculate current accuracy
        correct = 0
        total = 0

        for sample in samples_with_results:
            pred = sample['prediction']
            actual = sample['actual_result']

            # Get predicted outcome
            probs = {
                'H': pred.get('home_win_prob', 0.33),
                'D': pred.get('draw_prob', 0.33),
                'A': pred.get('away_win_prob', 0.34)
            }
            predicted = max(probs, key=probs.get)

            if predicted == actual:
                correct += 1
            total += 1

        current_accuracy = correct / total if total > 0 else 0

        # Calculate error rate
        current_error_rate = 1 - current_accuracy

        # Compare with reference (if available)
        # For now, use a simple threshold-based approach
        # In production, you'd compare with historical baseline

        # Estimate reference accuracy (placeholder)
        reference_accuracy = 0.55  # Should come from baseline metrics

        accuracy_drop = reference_accuracy - current_accuracy
        error_rate_increase = current_error_rate - (1 - reference_accuracy)

        drift_detected = accuracy_drop >= accuracy_threshold

        drift = ConceptDrift(
            drift_detected=drift_detected,
            drift_score=float(accuracy_drop),
            accuracy_drop=float(accuracy_drop),
            error_rate_increase=float(error_rate_increase),
            timestamp=datetime.now()
        )

        if drift_detected:
            logger.warning(
                "concept_drift_detected",
                accuracy_drop=accuracy_drop,
                current_accuracy=current_accuracy
            )

            self.concept_drift_history.append(drift)

        return drift

    def detect_prediction_drift(self) -> Dict[str, float]:
        """
        Detect drift in prediction distributions.

        Checks if model predictions are shifting over time.

        Returns:
            Dictionary with drift metrics
        """
        if len(self.current_buffer) < 30:
            return {}

        # Split buffer into two halves
        mid = len(self.current_buffer) // 2
        first_half = list(self.current_buffer)[:mid]
        second_half = list(self.current_buffer)[mid:]

        # Calculate average predictions for each half
        def avg_predictions(samples):
            home_probs = []
            draw_probs = []
            away_probs = []

            for s in samples:
                pred = s['prediction']
                home_probs.append(pred.get('home_win_prob', 0.33))
                draw_probs.append(pred.get('draw_prob', 0.33))
                away_probs.append(pred.get('away_win_prob', 0.34))

            return {
                'home_avg': np.mean(home_probs),
                'draw_avg': np.mean(draw_probs),
                'away_avg': np.mean(away_probs)
            }

        first_avg = avg_predictions(first_half)
        second_avg = avg_predictions(second_half)

        # Calculate drift
        home_drift = abs(first_avg['home_avg'] - second_avg['home_avg'])
        draw_drift = abs(first_avg['draw_avg'] - second_avg['draw_avg'])
        away_drift = abs(first_avg['away_avg'] - second_avg['away_avg'])

        total_drift = home_drift + draw_drift + away_drift

        return {
            'home_drift': float(home_drift),
            'draw_drift': float(draw_drift),
            'away_drift': float(away_drift),
            'total_drift': float(total_drift),
            'drift_detected': total_drift > 0.15  # 15% threshold
        }

    def get_drift_summary(self) -> Dict[str, Any]:
        """Get summary of drift detection"""
        # Recent data drift
        recent_data_drift = [
            d for d in self.data_drift_history[-10:]
        ]

        # Recent concept drift
        recent_concept_drift = [
            d for d in self.concept_drift_history[-5:]
        ]

        return {
            'buffer_size': len(self.current_buffer),
            'data_drift_count': len(self.data_drift_history),
            'concept_drift_count': len(self.concept_drift_history),
            'recent_data_drift': [
                {
                    'feature': d.feature_name,
                    'drift_score': d.drift_score,
                    'p_value': d.p_value,
                    'timestamp': d.timestamp.isoformat()
                }
                for d in recent_data_drift
            ],
            'recent_concept_drift': [
                {
                    'accuracy_drop': d.accuracy_drop,
                    'timestamp': d.timestamp.isoformat()
                }
                for d in recent_concept_drift
            ],
            'prediction_drift': self.detect_prediction_drift()
        }

    def reset_reference(self, new_reference_data: pd.DataFrame):
        """Update reference data"""
        self.reference_data = new_reference_data
        self._calculate_reference_stats()
        logger.info("reference_data_updated", samples=len(new_reference_data))


class AdaptiveDriftDetector:
    """
    Adaptive drift detector using Page-Hinkley test.

    Detects abrupt changes in data streams.
    """

    def __init__(
        self,
        delta: float = 0.005,  # Magnitude of change to detect
        lambda_: float = 50,    # Detection threshold
        alpha: float = 0.9999   # Forgetting factor
    ):
        self.delta = delta
        self.lambda_ = lambda_
        self.alpha = alpha

        self.sum = 0
        self.min_sum = 0
        self.n = 0
        self.drift_detected_flag = False

    def add_value(self, value: float) -> bool:
        """
        Add a value and check for drift.

        Args:
            value: Metric value (e.g., prediction error)

        Returns:
            True if drift detected
        """
        self.n += 1

        # Update sum
        self.sum = self.alpha * self.sum + (value - self.delta)

        # Update minimum
        if self.sum < self.min_sum:
            self.min_sum = self.sum

        # Check for drift
        if self.sum - self.min_sum > self.lambda_:
            self.drift_detected_flag = True
            logger.warning(
                "adaptive_drift_detected",
                n=self.n,
                sum=self.sum,
                min_sum=self.min_sum,
                diff=self.sum - self.min_sum
            )
            self.reset()
            return True

        return False

    def reset(self):
        """Reset detector"""
        self.sum = 0
        self.min_sum = 0
        self.drift_detected_flag = False
