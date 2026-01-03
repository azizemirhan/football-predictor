"""
A/B Testing Framework - Statistical model comparison
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import structlog

from ..models.base import BasePredictor
from ..evaluation.metrics import PredictionMetrics
from .statistical_tests import (
    t_test_independent,
    chi_square_test,
    mann_whitney_test
)

logger = structlog.get_logger()


class TestStatus(Enum):
    """A/B test status"""
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"


@dataclass
class TestVariant:
    """A/B test variant (model)"""
    name: str
    model: BasePredictor
    traffic_allocation: float  # 0.0 to 1.0
    predictions: List[Dict]
    metrics: Dict[str, float]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'model_name': self.model.model_name,
            'traffic_allocation': self.traffic_allocation,
            'predictions_count': len(self.predictions),
            'metrics': self.metrics
        }


@dataclass
class ABTestResult:
    """A/B test results"""
    test_id: str
    test_name: str
    start_date: datetime
    end_date: Optional[datetime]
    status: TestStatus
    variants: List[TestVariant]
    winner: Optional[str]
    statistical_significance: Dict[str, Any]
    sample_sizes: Dict[str, int]
    confidence_level: float

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status.value,
            'variants': [v.to_dict() for v in self.variants],
            'winner': self.winner,
            'statistical_significance': self.statistical_significance,
            'sample_sizes': self.sample_sizes,
            'confidence_level': self.confidence_level
        }


class ABTest:
    """
    A/B Testing framework for comparing models.

    Features:
    - Multi-variant testing (A/B/C/...)
    - Traffic splitting
    - Statistical significance testing
    - Early stopping
    - Winner declaration
    """

    def __init__(
        self,
        test_name: str,
        variants: Dict[str, BasePredictor],
        traffic_allocation: Optional[Dict[str, float]] = None,
        confidence_level: float = 0.95,
        min_sample_size: int = 100,
        primary_metric: str = 'accuracy'
    ):
        """
        Args:
            test_name: Name of the test
            variants: Dictionary of {variant_name: model}
            traffic_allocation: Traffic % for each variant (must sum to 1.0)
            confidence_level: Statistical confidence level (0.95 = 95%)
            min_sample_size: Minimum samples per variant
            primary_metric: Primary metric for winner determination
        """
        self.test_id = f"ab_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_name = test_name
        self.confidence_level = confidence_level
        self.min_sample_size = min_sample_size
        self.primary_metric = primary_metric

        self.start_date = datetime.now()
        self.end_date = None
        self.status = TestStatus.RUNNING

        # Set up variants
        n_variants = len(variants)
        if traffic_allocation is None:
            # Equal split
            traffic_allocation = {name: 1.0 / n_variants for name in variants}

        # Validate traffic allocation
        if abs(sum(traffic_allocation.values()) - 1.0) > 0.01:
            raise ValueError("Traffic allocation must sum to 1.0")

        self.variants = {
            name: TestVariant(
                name=name,
                model=model,
                traffic_allocation=traffic_allocation[name],
                predictions=[],
                metrics={}
            )
            for name, model in variants.items()
        }

        logger.info(
            "ab_test_created",
            test_id=self.test_id,
            test_name=test_name,
            variants=list(variants.keys()),
            traffic=traffic_allocation
        )

    def assign_variant(self, match_id: Optional[str] = None) -> str:
        """
        Assign a variant based on traffic allocation.

        Args:
            match_id: Optional match ID for deterministic assignment

        Returns:
            Variant name
        """
        if match_id:
            # Deterministic assignment based on hash
            import hashlib
            hash_val = int(hashlib.md5(str(match_id).encode()).hexdigest(), 16)
            rand = (hash_val % 1000) / 1000.0
        else:
            # Random assignment
            rand = np.random.random()

        # Assign based on traffic allocation
        cumsum = 0
        for name, variant in self.variants.items():
            cumsum += variant.traffic_allocation
            if rand <= cumsum:
                return name

        # Fallback to first variant
        return list(self.variants.keys())[0]

    def run_test(
        self,
        data: pd.DataFrame,
        deterministic: bool = True
    ) -> ABTestResult:
        """
        Run A/B test on dataset.

        Args:
            data: Test data
            deterministic: Use deterministic variant assignment

        Returns:
            ABTestResult
        """
        logger.info(
            "ab_test_started",
            test_id=self.test_id,
            samples=len(data)
        )

        # Process each match
        for _, match in data.iterrows():
            match_id = match.get('id') if deterministic else None
            variant_name = self.assign_variant(match_id)

            # Make prediction with assigned variant
            variant = self.variants[variant_name]
            try:
                pred = self._make_prediction(variant.model, match)
                if pred:
                    variant.predictions.append(pred)
            except Exception as e:
                logger.warning(
                    "prediction_error",
                    variant=variant_name,
                    error=str(e)
                )

        # Calculate metrics for each variant
        for variant in self.variants.values():
            variant.metrics = self._calculate_variant_metrics(variant)

        # Determine winner
        winner = self._determine_winner()

        # Statistical significance
        significance = self._calculate_significance()

        # Create result
        self.end_date = datetime.now()
        self.status = TestStatus.COMPLETED

        result = ABTestResult(
            test_id=self.test_id,
            test_name=self.test_name,
            start_date=self.start_date,
            end_date=self.end_date,
            status=self.status,
            variants=list(self.variants.values()),
            winner=winner,
            statistical_significance=significance,
            sample_sizes={
                name: len(v.predictions)
                for name, v in self.variants.items()
            },
            confidence_level=self.confidence_level
        )

        logger.info(
            "ab_test_completed",
            test_id=self.test_id,
            winner=winner,
            sample_sizes=result.sample_sizes
        )

        return result

    def _make_prediction(
        self,
        model: BasePredictor,
        match: pd.Series
    ) -> Optional[Dict]:
        """Make prediction for a match"""
        match_data = {
            'id': match.get('id'),
            'home_team': match['home_team'],
            'away_team': match['away_team']
        }

        pred = model.predict(match_data)

        # Get actual result
        if pd.notna(match['home_score']):
            home_score = int(match['home_score'])
            away_score = int(match['away_score'])

            if home_score > away_score:
                actual = 'H'
            elif home_score == away_score:
                actual = 'D'
            else:
                actual = 'A'

            # Get odds if available
            odds = {}
            if 'home_odds' in match and match['home_odds'] > 0:
                odds['H'] = float(match['home_odds'])
            if 'draw_odds' in match and match['draw_odds'] > 0:
                odds['D'] = float(match['draw_odds'])
            if 'away_odds' in match and match['away_odds'] > 0:
                odds['A'] = float(match['away_odds'])

            return {
                'match_id': match_data['id'],
                'actual_result': actual,
                'predicted_probs': {
                    'H': pred.get('home_win_prob', 0.33),
                    'D': pred.get('draw_prob', 0.33),
                    'A': pred.get('away_win_prob', 0.34)
                },
                'odds': odds if odds else None
            }

        return None

    def _calculate_variant_metrics(self, variant: TestVariant) -> Dict[str, float]:
        """Calculate metrics for a variant"""
        if not variant.predictions:
            return {}

        metrics_engine = PredictionMetrics()

        for pred in variant.predictions:
            metrics_engine.add_prediction(
                actual_result=pred['actual_result'],
                predicted_probs=pred['predicted_probs'],
                odds=pred.get('odds')
            )

        return metrics_engine.calculate_all_metrics()

    def _determine_winner(self) -> Optional[str]:
        """Determine winner based on primary metric"""
        if not all(len(v.predictions) >= self.min_sample_size for v in self.variants.values()):
            logger.warning(
                "insufficient_samples",
                min_required=self.min_sample_size
            )
            return None

        # Get metric values
        values = {}
        for name, variant in self.variants.items():
            if self.primary_metric in variant.metrics:
                values[name] = variant.metrics[self.primary_metric]

        if not values:
            return None

        # Determine best
        if self.primary_metric in ['log_loss', 'brier_score', 'rps']:
            # Lower is better
            winner = min(values, key=values.get)
        else:
            # Higher is better
            winner = max(values, key=values.get)

        return winner

    def _calculate_significance(self) -> Dict[str, Any]:
        """Calculate statistical significance between variants"""
        significance = {}

        variant_names = list(self.variants.keys())

        # Compare all pairs
        for i, name_a in enumerate(variant_names):
            for name_b in variant_names[i+1:]:
                variant_a = self.variants[name_a]
                variant_b = self.variants[name_b]

                # Get metric values for both variants
                metric_a = variant_a.metrics.get(self.primary_metric)
                metric_b = variant_b.metrics.get(self.primary_metric)

                if metric_a is None or metric_b is None:
                    continue

                # Extract individual prediction outcomes
                outcomes_a = [
                    1 if p['predicted_probs'][p['actual_result']] == max(p['predicted_probs'].values()) else 0
                    for p in variant_a.predictions
                ]
                outcomes_b = [
                    1 if p['predicted_probs'][p['actual_result']] == max(p['predicted_probs'].values()) else 0
                    for p in variant_b.predictions
                ]

                # T-test
                t_result = t_test_independent(outcomes_a, outcomes_b)

                # Mann-Whitney U test (non-parametric)
                mw_result = mann_whitney_test(outcomes_a, outcomes_b)

                pair_key = f"{name_a}_vs_{name_b}"
                significance[pair_key] = {
                    'metric_a': metric_a,
                    'metric_b': metric_b,
                    'difference': metric_a - metric_b,
                    't_test': t_result,
                    'mann_whitney': mw_result,
                    'is_significant': (
                        t_result['p_value'] < (1 - self.confidence_level) and
                        mw_result['p_value'] < (1 - self.confidence_level)
                    )
                }

        return significance

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'status': self.status.value,
            'variants': {
                name: {
                    'traffic': v.traffic_allocation,
                    'samples': len(v.predictions),
                    'metrics': v.metrics
                }
                for name, v in self.variants.items()
            },
            'winner': self._determine_winner(),
            'duration': (
                (self.end_date - self.start_date).total_seconds()
                if self.end_date else None
            )
        }


def run_quick_ab_test(
    model_a: BasePredictor,
    model_b: BasePredictor,
    data: pd.DataFrame,
    model_a_name: str = "Model A",
    model_b_name: str = "Model B",
    primary_metric: str = 'accuracy'
) -> ABTestResult:
    """
    Quick A/B test between two models.

    Args:
        model_a: First model
        model_b: Second model
        data: Test data
        model_a_name: Name for model A
        model_b_name: Name for model B
        primary_metric: Primary metric

    Returns:
        ABTestResult
    """
    test = ABTest(
        test_name=f"{model_a_name}_vs_{model_b_name}",
        variants={
            model_a_name: model_a,
            model_b_name: model_b
        },
        primary_metric=primary_metric
    )

    return test.run_test(data)
