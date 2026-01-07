"""
Backtesting Framework - Model performans testi ve validasyon
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import structlog

from ..models.base import BasePredictor
from .metrics import PredictionMetrics, calculate_value_bet_metrics

logger = structlog.get_logger()


@dataclass
class BacktestResult:
    """Backtest sonuçlar1n1 tutar"""
    model_name: str
    start_date: datetime
    end_date: datetime
    total_matches: int
    metrics: Dict[str, float]
    predictions: List[Dict]
    equity_curve: List[float]
    monthly_performance: Dict[str, Dict]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            **asdict(self),
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None
        }

    def save(self, filepath: str):
        """Save results to JSON"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class BacktestEngine:
    """
    Backtesting engine for football prediction models.

    Features:
    - Walk-forward validation
    - Time-series cross-validation
    - Out-of-sample testing
    - Betting simulation
    - Performance tracking
    """

    def __init__(
        self,
        initial_bankroll: float = 1000.0,
        stake_size: float = 10.0,
        min_edge: float = 0.03,  # Minimum 3% edge for value bets
        max_stake_pct: float = 0.05  # Max 5% of bankroll per bet
    ):
        self.initial_bankroll = initial_bankroll
        self.stake_size = stake_size
        self.min_edge = min_edge
        self.max_stake_pct = max_stake_pct

    def walk_forward_validation(
        self,
        model: BasePredictor,
        data: pd.DataFrame,
        train_window: int = 365,  # Days
        test_window: int = 30,    # Days
        step_size: int = 30,      # Days
        retrain: bool = True
    ) -> BacktestResult:
        """
        Walk-forward validation.

        Trains on rolling window, tests on next period.
        Simulates realistic deployment scenario.

        Args:
            model: Prediction model
            data: Historical match data
            train_window: Training window size in days
            test_window: Test window size in days
            step_size: Step size between iterations
            retrain: Whether to retrain model at each step

        Returns:
            BacktestResult with comprehensive metrics
        """
        logger.info(
            "walk_forward_started",
            model=model.model_name,
            train_window=train_window,
            test_window=test_window
        )

        # Ensure data is sorted by date
        data = data.sort_values('match_date').copy()
        data['match_date'] = pd.to_datetime(data['match_date'])

        all_predictions = []
        equity_curve = [self.initial_bankroll]
        current_bankroll = self.initial_bankroll

        start_date = data['match_date'].min() + timedelta(days=train_window)
        end_date = data['match_date'].max()

        current_date = start_date

        iteration = 0
        while current_date + timedelta(days=test_window) <= end_date:
            iteration += 1

            # Training window
            train_start = current_date - timedelta(days=train_window)
            train_end = current_date
            train_data = data[
                (data['match_date'] >= train_start) &
                (data['match_date'] < train_end)
            ]

            # Test window
            test_start = current_date
            test_end = current_date + timedelta(days=test_window)
            test_data = data[
                (data['match_date'] >= test_start) &
                (data['match_date'] < test_end) &
                (data['home_score'].notna())
            ]

            logger.info(
                "walk_forward_iteration",
                iteration=iteration,
                train_samples=len(train_data),
                test_samples=len(test_data),
                train_period=f"{train_start.date()} to {train_end.date()}",
                test_period=f"{test_start.date()} to {test_end.date()}"
            )

            # Train model
            if retrain and len(train_data) >= 50:
                try:
                    model.train(train_data)
                except Exception as e:
                    logger.error("training_error", error=str(e), iteration=iteration)

            # Make predictions
            for _, match in test_data.iterrows():
                pred = self._make_prediction(model, match)
                if pred:
                    # Simulate betting
                    bet_result = self._simulate_bet(
                        prediction=pred,
                        bankroll=current_bankroll
                    )

                    if bet_result:
                        current_bankroll = bet_result['new_bankroll']
                        equity_curve.append(current_bankroll)

                        pred.update(bet_result)

                    all_predictions.append(pred)

            # Move to next window
            current_date += timedelta(days=step_size)

        # Calculate metrics
        metrics_engine = PredictionMetrics()
        for pred in all_predictions:
            metrics_engine.add_prediction(
                actual_result=pred['actual_result'],
                predicted_probs=pred['predicted_probs'],
                odds=pred.get('odds'),
                stake=pred.get('stake', 0)
            )

        metrics = metrics_engine.calculate_all_metrics()

        # Add custom metrics
        metrics['final_bankroll'] = round(current_bankroll, 2)
        metrics['total_return_pct'] = round(
            ((current_bankroll - self.initial_bankroll) / self.initial_bankroll) * 100, 2
        )

        # Monthly performance
        monthly_perf = self._calculate_monthly_performance(all_predictions)

        result = BacktestResult(
            model_name=model.model_name,
            start_date=start_date,
            end_date=end_date,
            total_matches=len(all_predictions),
            metrics=metrics,
            predictions=all_predictions,
            equity_curve=equity_curve,
            monthly_performance=monthly_perf
        )

        logger.info(
            "walk_forward_completed",
            model=model.model_name,
            accuracy=metrics.get('accuracy'),
            roi=metrics.get('roi_pct'),
            final_bankroll=current_bankroll
        )

        return result

    def time_series_cv(
        self,
        model: BasePredictor,
        data: pd.DataFrame,
        n_splits: int = 5,
        test_size: int = 60  # Days
    ) -> Dict[str, Any]:
        """
        Time-series cross-validation.

        Splits data into sequential train/test folds.
        Ensures no data leakage.

        Args:
            model: Prediction model
            data: Historical data
            n_splits: Number of CV splits
            test_size: Test set size in days

        Returns:
            CV results with metrics per fold
        """
        logger.info("time_series_cv_started", model=model.model_name, n_splits=n_splits)

        data = data.sort_values('match_date').copy()
        data['match_date'] = pd.to_datetime(data['match_date'])

        fold_results = []

        # Calculate split points
        total_days = (data['match_date'].max() - data['match_date'].min()).days
        fold_size = total_days // n_splits

        for fold in range(n_splits):
            # Split point
            split_date = data['match_date'].min() + timedelta(days=fold_size * (fold + 1))
            test_start = split_date - timedelta(days=test_size)

            train_data = data[data['match_date'] < test_start]
            test_data = data[
                (data['match_date'] >= test_start) &
                (data['match_date'] < split_date) &
                (data['home_score'].notna())
            ]

            if len(train_data) < 50 or len(test_data) < 10:
                continue

            logger.info(
                "cv_fold",
                fold=fold + 1,
                train_samples=len(train_data),
                test_samples=len(test_data)
            )

            # Train
            try:
                model.train(train_data)
            except Exception as e:
                logger.error("cv_train_error", fold=fold, error=str(e))
                continue

            # Test
            predictions = []
            for _, match in test_data.iterrows():
                pred = self._make_prediction(model, match)
                if pred:
                    predictions.append(pred)

            # Calculate metrics
            metrics_engine = PredictionMetrics()
            for pred in predictions:
                metrics_engine.add_prediction(
                    actual_result=pred['actual_result'],
                    predicted_probs=pred['predicted_probs'],
                    odds=pred.get('odds')
                )

            fold_metrics = metrics_engine.calculate_all_metrics()
            fold_metrics['fold'] = fold + 1
            fold_metrics['train_size'] = len(train_data)
            fold_metrics['test_size'] = len(test_data)

            fold_results.append(fold_metrics)

        # Aggregate results
        avg_metrics = self._aggregate_cv_results(fold_results)

        logger.info("time_series_cv_completed", **avg_metrics)

        return {
            'avg_metrics': avg_metrics,
            'fold_results': fold_results
        }

    def out_of_sample_test(
        self,
        model: BasePredictor,
        train_data: pd.DataFrame,
        test_data: pd.DataFrame,
        retrain: bool = True
    ) -> BacktestResult:
        """
        Out-of-sample testing.

        Train on one dataset, test on completely separate dataset.

        Args:
            model: Prediction model
            train_data: Training data
            test_data: Test data
            retrain: Whether to retrain model

        Returns:
            BacktestResult
        """
        logger.info(
            "oos_test_started",
            model=model.model_name,
            train_size=len(train_data),
            test_size=len(test_data)
        )

        # Train
        if retrain:
            model.train(train_data)

        # Test
        predictions = []
        equity_curve = [self.initial_bankroll]
        current_bankroll = self.initial_bankroll

        test_data = test_data[test_data['home_score'].notna()].copy()

        for _, match in test_data.iterrows():
            pred = self._make_prediction(model, match)
            if pred:
                # Simulate betting
                bet_result = self._simulate_bet(pred, current_bankroll)
                if bet_result:
                    current_bankroll = bet_result['new_bankroll']
                    equity_curve.append(current_bankroll)
                    pred.update(bet_result)

                predictions.append(pred)

        # Calculate metrics
        metrics_engine = PredictionMetrics()
        for pred in predictions:
            metrics_engine.add_prediction(
                actual_result=pred['actual_result'],
                predicted_probs=pred['predicted_probs'],
                odds=pred.get('odds'),
                stake=pred.get('stake', 0)
            )

        metrics = metrics_engine.calculate_all_metrics()
        metrics['final_bankroll'] = round(current_bankroll, 2)

        monthly_perf = self._calculate_monthly_performance(predictions)

        result = BacktestResult(
            model_name=model.model_name,
            start_date=test_data['match_date'].min(),
            end_date=test_data['match_date'].max(),
            total_matches=len(predictions),
            metrics=metrics,
            predictions=predictions,
            equity_curve=equity_curve,
            monthly_performance=monthly_perf
        )

        logger.info("oos_test_completed", **metrics)

        return result

    def _make_prediction(self, model: BasePredictor, match: pd.Series) -> Optional[Dict]:
        """Make prediction for a single match"""
        try:
            match_data = {
                'id': match.get('id'),
                'home_team': match['home_team'],
                'away_team': match['away_team'],
                'match_date': match.get('match_date')
            }

            # Add available features
            for col in match.index:
                if col not in match_data:
                    match_data[col] = match[col]

            pred = model.predict(match_data)

            # Get actual result
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
                'match_id': match_data.get('id'),
                'home_team': match['home_team'],
                'away_team': match['away_team'],
                'match_date': match.get('match_date'),
                'actual_result': actual,
                'actual_score': f"{home_score}-{away_score}",
                'predicted_probs': {
                    'H': pred.get('home_win_prob', 0.33),
                    'D': pred.get('draw_prob', 0.33),
                    'A': pred.get('away_win_prob', 0.34)
                },
                'odds': odds if odds else None,
                'confidence': pred.get('confidence', 0)
            }

        except Exception as e:
            logger.warning("prediction_error", error=str(e), match_id=match.get('id'))
            return None

    def _simulate_bet(
        self,
        prediction: Dict,
        bankroll: float
    ) -> Optional[Dict]:
        """
        Simulate betting based on value bet strategy.

        Only bets when edge > min_edge.
        """
        if not prediction.get('odds'):
            return None

        probs = prediction['predicted_probs']
        odds = prediction['odds']
        actual = prediction['actual_result']

        # Find best value bet
        best_ev = -1
        best_outcome = None

        for outcome in ['H', 'D', 'A']:
            if outcome not in odds:
                continue

            model_prob = probs.get(outcome, 0.33)
            implied_prob = 1 / odds[outcome]
            edge = model_prob - implied_prob
            ev = (model_prob * odds[outcome]) - 1

            if edge >= self.min_edge and ev > best_ev:
                best_ev = ev
                best_outcome = outcome

        if best_outcome is None:
            return None

        # Calculate stake (Kelly criterion or fixed)
        stake = min(
            self.stake_size,
            bankroll * self.max_stake_pct
        )

        # Place bet
        won = best_outcome == actual
        if won:
            payout = stake * odds[best_outcome]
            profit = payout - stake
        else:
            payout = 0
            profit = -stake

        new_bankroll = bankroll + profit

        return {
            'bet_placed': True,
            'bet_outcome': best_outcome,
            'stake': round(stake, 2),
            'odds_taken': odds[best_outcome],
            'won': won,
            'profit': round(profit, 2),
            'payout': round(payout, 2),
            'new_bankroll': round(new_bankroll, 2)
        }

    def _calculate_monthly_performance(
        self,
        predictions: List[Dict]
    ) -> Dict[str, Dict]:
        """Calculate performance by month"""
        monthly = {}

        for pred in predictions:
            if not pred.get('match_date'):
                continue

            date = pd.to_datetime(pred['match_date'])
            month_key = date.strftime('%Y-%m')

            if month_key not in monthly:
                monthly[month_key] = {
                    'total_bets': 0,
                    'won_bets': 0,
                    'profit': 0,
                    'predictions': []
                }

            monthly[month_key]['predictions'].append(pred)

            if pred.get('bet_placed'):
                monthly[month_key]['total_bets'] += 1
                if pred.get('won'):
                    monthly[month_key]['won_bets'] += 1
                monthly[month_key]['profit'] += pred.get('profit', 0)

        # Calculate metrics
        for month in monthly:
            total = monthly[month]['total_bets']
            if total > 0:
                monthly[month]['win_rate'] = round(
                    monthly[month]['won_bets'] / total, 4
                )
            else:
                monthly[month]['win_rate'] = 0

            monthly[month]['profit'] = round(monthly[month]['profit'], 2)
            # Remove predictions from output (too large)
            del monthly[month]['predictions']

        return monthly

    def _aggregate_cv_results(self, fold_results: List[Dict]) -> Dict[str, float]:
        """Aggregate cross-validation results"""
        if not fold_results:
            return {}

        metrics = {}

        # Average metrics across folds
        for key in fold_results[0].keys():
            if key in ['fold', 'train_size', 'test_size']:
                continue

            values = [f[key] for f in fold_results if key in f and isinstance(f[key], (int, float))]
            if values:
                metrics[f'mean_{key}'] = round(np.mean(values), 4)
                metrics[f'std_{key}'] = round(np.std(values), 4)

        return metrics


def compare_models_backtest(
    models: List[BasePredictor],
    data: pd.DataFrame,
    method: str = 'walk_forward',
    **kwargs
) -> Dict[str, Any]:
    """
    Compare multiple models using backtesting.

    Args:
        models: List of models to compare
        data: Historical data
        method: 'walk_forward', 'time_series_cv', or 'oos'
        **kwargs: Additional arguments for backtesting method

    Returns:
        Comparison results
    """
    engine = BacktestEngine()
    results = {}

    for model in models:
        logger.info("backtesting_model", model=model.model_name, method=method)

        if method == 'walk_forward':
            result = engine.walk_forward_validation(model, data, **kwargs)
        elif method == 'time_series_cv':
            result = engine.time_series_cv(model, data, **kwargs)
        elif method == 'oos':
            train_data = kwargs.get('train_data', data[:int(len(data)*0.8)])
            test_data = kwargs.get('test_data', data[int(len(data)*0.8):])
            result = engine.out_of_sample_test(model, train_data, test_data)
        else:
            raise ValueError(f"Unknown method: {method}")

        results[model.model_name] = result

    # Compare
    comparison = _create_comparison_table(results)

    return {
        'individual_results': results,
        'comparison': comparison
    }


def _create_comparison_table(results: Dict[str, BacktestResult]) -> pd.DataFrame:
    """Create comparison table from backtest results"""
    rows = []

    for model_name, result in results.items():
        if isinstance(result, BacktestResult):
            metrics = result.metrics
        else:
            metrics = result.get('avg_metrics', {})

        rows.append({
            'model': model_name,
            'accuracy': metrics.get('accuracy', 0),
            'log_loss': metrics.get('log_loss', 0),
            'brier_score': metrics.get('brier_score', 0),
            'roi_pct': metrics.get('roi_pct', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'win_rate': metrics.get('win_rate', 0),
            'total_bets': metrics.get('total_bets', 0)
        })

    df = pd.DataFrame(rows)
    df = df.sort_values('roi_pct', ascending=False)

    return df
