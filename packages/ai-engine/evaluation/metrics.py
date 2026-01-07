"""
Evaluation Metrics - Model performans metrikleri
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    log_loss, roc_auc_score, confusion_matrix
)
import structlog

logger = structlog.get_logger()


class PredictionMetrics:
    """
    Calculate comprehensive metrics for match predictions.

    Metrics include:
    - Classification metrics (accuracy, precision, recall, F1)
    - Probabilistic metrics (log loss, Brier score, RPS)
    - Betting metrics (ROI, yield, Sharpe ratio)
    - Calibration metrics
    """

    def __init__(self):
        self.predictions = []
        self.actuals = []

    def add_prediction(
        self,
        actual_result: str,  # 'H', 'D', 'A'
        predicted_probs: Dict[str, float],  # {'H': 0.5, 'D': 0.3, 'A': 0.2}
        actual_score: Optional[Tuple[int, int]] = None,
        odds: Optional[Dict[str, float]] = None,
        stake: float = 1.0
    ):
        """Add a single prediction to the evaluation set"""
        self.predictions.append({
            'actual_result': actual_result,
            'predicted_probs': predicted_probs,
            'actual_score': actual_score,
            'odds': odds,
            'stake': stake
        })

    def calculate_all_metrics(self) -> Dict[str, float]:
        """Calculate all available metrics"""
        if not self.predictions:
            return {}

        metrics = {}

        # Classification metrics
        metrics.update(self._classification_metrics())

        # Probabilistic metrics
        metrics.update(self._probabilistic_metrics())

        # Betting metrics (if odds available)
        if any(p.get('odds') for p in self.predictions):
            metrics.update(self._betting_metrics())

        # Calibration
        metrics.update(self._calibration_metrics())

        return metrics

    def _classification_metrics(self) -> Dict[str, float]:
        """Calculate classification metrics"""
        y_true = []
        y_pred = []

        for pred in self.predictions:
            actual = pred['actual_result']
            probs = pred['predicted_probs']

            # Get predicted outcome
            predicted = max(probs, key=probs.get)

            y_true.append(actual)
            y_pred.append(predicted)

        # Convert to numeric for sklearn
        label_map = {'H': 0, 'D': 1, 'A': 2}
        y_true_numeric = [label_map[y] for y in y_true]
        y_pred_numeric = [label_map[y] for y in y_pred]

        accuracy = accuracy_score(y_true_numeric, y_pred_numeric)

        # Confusion matrix
        cm = confusion_matrix(y_true_numeric, y_pred_numeric, labels=[0, 1, 2])

        return {
            'accuracy': round(accuracy, 4),
            'total_predictions': len(y_true),
            'home_wins_predicted': y_pred.count('H'),
            'draws_predicted': y_pred.count('D'),
            'away_wins_predicted': y_pred.count('A'),
            'home_wins_actual': y_true.count('H'),
            'draws_actual': y_true.count('D'),
            'away_wins_actual': y_true.count('A')
        }

    def _probabilistic_metrics(self) -> Dict[str, float]:
        """Calculate probabilistic metrics"""
        y_true = []
        y_pred_probs = []

        label_map = {'H': 0, 'D': 1, 'A': 2}

        for pred in self.predictions:
            actual = pred['actual_result']
            probs = pred['predicted_probs']

            # One-hot encode actual
            y_true_vec = [0, 0, 0]
            y_true_vec[label_map[actual]] = 1
            y_true.append(y_true_vec)

            # Probability vector
            prob_vec = [
                probs.get('H', 0.33),
                probs.get('D', 0.33),
                probs.get('A', 0.34)
            ]
            y_pred_probs.append(prob_vec)

        y_true = np.array(y_true)
        y_pred_probs = np.array(y_pred_probs)

        # Log Loss
        logloss = self._calculate_log_loss(y_true, y_pred_probs)

        # Brier Score
        brier = self._calculate_brier_score(y_true, y_pred_probs)

        # Ranked Probability Score (RPS)
        rps = self._calculate_rps(y_true, y_pred_probs)

        return {
            'log_loss': round(logloss, 4),
            'brier_score': round(brier, 4),
            'rps': round(rps, 4)
        }

    def _calculate_log_loss(self, y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-15) -> float:
        """Calculate log loss (cross-entropy)"""
        y_pred = np.clip(y_pred, eps, 1 - eps)
        return -np.mean(np.sum(y_true * np.log(y_pred), axis=1))

    def _calculate_brier_score(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Calculate Brier score"""
        return np.mean(np.sum((y_true - y_pred) ** 2, axis=1))

    def _calculate_rps(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculate Ranked Probability Score.
        Lower is better. Measures accuracy of ordered outcomes.
        """
        # Cumulative probabilities
        cum_true = np.cumsum(y_true, axis=1)
        cum_pred = np.cumsum(y_pred, axis=1)

        # RPS
        rps = np.mean(np.sum((cum_pred - cum_true) ** 2, axis=1) / (y_true.shape[1] - 1))
        return rps

    def _betting_metrics(self) -> Dict[str, float]:
        """Calculate betting performance metrics"""
        total_staked = 0.0
        total_returned = 0.0
        profits = []

        wins = 0
        losses = 0

        for pred in self.predictions:
            if not pred.get('odds'):
                continue

            actual = pred['actual_result']
            probs = pred['predicted_probs']
            odds = pred['odds']
            stake = pred.get('stake', 1.0)

            # Find best bet (highest expected value)
            best_outcome = max(probs, key=probs.get)

            # Place bet
            total_staked += stake

            if best_outcome == actual and best_outcome in odds:
                # Win
                payout = stake * odds[best_outcome]
                total_returned += payout
                profits.append(payout - stake)
                wins += 1
            else:
                # Loss
                profits.append(-stake)
                losses += 1

        if total_staked == 0:
            return {}

        net_profit = total_returned - total_staked
        roi = (net_profit / total_staked) * 100
        yield_pct = roi  # Same as ROI in this context

        # Sharpe Ratio (risk-adjusted returns)
        if len(profits) > 1:
            sharpe = (np.mean(profits) / np.std(profits)) * np.sqrt(len(profits)) if np.std(profits) > 0 else 0
        else:
            sharpe = 0

        # Maximum drawdown
        cumulative = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0

        return {
            'total_bets': wins + losses,
            'winning_bets': wins,
            'losing_bets': losses,
            'win_rate': round(wins / (wins + losses), 4) if (wins + losses) > 0 else 0,
            'total_staked': round(total_staked, 2),
            'total_returned': round(total_returned, 2),
            'net_profit': round(net_profit, 2),
            'roi_pct': round(roi, 2),
            'yield_pct': round(yield_pct, 2),
            'sharpe_ratio': round(sharpe, 4),
            'max_drawdown': round(max_drawdown, 2),
            'avg_profit_per_bet': round(np.mean(profits), 2) if profits else 0
        }

    def _calibration_metrics(self) -> Dict[str, float]:
        """
        Calculate calibration metrics.
        Measures how well predicted probabilities match actual frequencies.
        """
        # Group predictions by probability bins
        bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        calibration_data = []

        for outcome in ['H', 'D', 'A']:
            predicted_probs = []
            actual_outcomes = []

            for pred in self.predictions:
                prob = pred['predicted_probs'].get(outcome, 0.33)
                actual = 1 if pred['actual_result'] == outcome else 0

                predicted_probs.append(prob)
                actual_outcomes.append(actual)

            # Calculate calibration for this outcome
            predicted_probs = np.array(predicted_probs)
            actual_outcomes = np.array(actual_outcomes)

            # Expected Calibration Error (ECE)
            ece = 0
            for i in range(len(bins) - 1):
                mask = (predicted_probs >= bins[i]) & (predicted_probs < bins[i+1])
                if mask.sum() > 0:
                    avg_pred = predicted_probs[mask].mean()
                    avg_actual = actual_outcomes[mask].mean()
                    ece += mask.sum() / len(predicted_probs) * abs(avg_pred - avg_actual)

            calibration_data.append({
                'outcome': outcome,
                'ece': ece
            })

        # Average ECE across outcomes
        avg_ece = np.mean([d['ece'] for d in calibration_data])

        return {
            'expected_calibration_error': round(avg_ece, 4)
        }

    def get_confusion_matrix(self) -> np.ndarray:
        """Get confusion matrix"""
        y_true = []
        y_pred = []

        label_map = {'H': 0, 'D': 1, 'A': 2}

        for pred in self.predictions:
            actual = pred['actual_result']
            probs = pred['predicted_probs']
            predicted = max(probs, key=probs.get)

            y_true.append(label_map[actual])
            y_pred.append(label_map[predicted])

        return confusion_matrix(y_true, y_pred, labels=[0, 1, 2])

    def reset(self):
        """Reset all predictions"""
        self.predictions = []


def calculate_value_bet_metrics(
    predictions: List[Dict],
    threshold: float = 0.05  # Minimum edge (5%)
) -> Dict[str, float]:
    """
    Calculate metrics specifically for value betting strategy.

    Args:
        predictions: List of predictions with odds and probabilities
        threshold: Minimum expected value threshold

    Returns:
        Value betting metrics
    """
    value_bets = []

    for pred in predictions:
        probs = pred.get('predicted_probs', {})
        odds = pred.get('odds', {})
        actual = pred.get('actual_result')

        for outcome in ['H', 'D', 'A']:
            if outcome in odds and outcome in probs:
                implied_prob = 1 / odds[outcome]
                model_prob = probs[outcome]

                # Expected value
                ev = (model_prob * odds[outcome]) - 1

                # Edge
                edge = model_prob - implied_prob

                if edge >= threshold:
                    value_bets.append({
                        'outcome': outcome,
                        'model_prob': model_prob,
                        'implied_prob': implied_prob,
                        'odds': odds[outcome],
                        'edge': edge,
                        'ev': ev,
                        'won': outcome == actual
                    })

    if not value_bets:
        return {'value_bets_found': 0}

    wins = sum(1 for bet in value_bets if bet['won'])
    total = len(value_bets)

    # Calculate returns
    total_ev = sum(bet['ev'] for bet in value_bets)
    avg_ev = total_ev / total
    avg_edge = np.mean([bet['edge'] for bet in value_bets])
    avg_odds = np.mean([bet['odds'] for bet in value_bets])

    return {
        'value_bets_found': total,
        'value_bets_won': wins,
        'value_bet_win_rate': round(wins / total, 4),
        'avg_edge': round(avg_edge, 4),
        'avg_expected_value': round(avg_ev, 4),
        'avg_odds': round(avg_odds, 2)
    }


def compare_models(
    model_a_predictions: List[Dict],
    model_b_predictions: List[Dict],
    model_a_name: str = "Model A",
    model_b_name: str = "Model B"
) -> Dict[str, Any]:
    """
    Compare two models' predictions.

    Returns:
        Comparison metrics and statistical test results
    """
    metrics_a = PredictionMetrics()
    metrics_b = PredictionMetrics()

    for pred in model_a_predictions:
        metrics_a.add_prediction(
            actual_result=pred['actual_result'],
            predicted_probs=pred['predicted_probs'],
            odds=pred.get('odds')
        )

    for pred in model_b_predictions:
        metrics_b.add_prediction(
            actual_result=pred['actual_result'],
            predicted_probs=pred['predicted_probs'],
            odds=pred.get('odds')
        )

    results_a = metrics_a.calculate_all_metrics()
    results_b = metrics_b.calculate_all_metrics()

    # Calculate differences
    comparison = {
        'model_a_name': model_a_name,
        'model_b_name': model_b_name,
        'model_a_metrics': results_a,
        'model_b_metrics': results_b,
        'differences': {
            'accuracy_diff': results_a.get('accuracy', 0) - results_b.get('accuracy', 0),
            'log_loss_diff': results_a.get('log_loss', 1) - results_b.get('log_loss', 1),
            'brier_diff': results_a.get('brier_score', 1) - results_b.get('brier_score', 1),
            'roi_diff': results_a.get('roi_pct', 0) - results_b.get('roi_pct', 0)
        }
    }

    # Determine winner
    winners = {
        'accuracy': model_a_name if results_a.get('accuracy', 0) > results_b.get('accuracy', 0) else model_b_name,
        'log_loss': model_a_name if results_a.get('log_loss', 1) < results_b.get('log_loss', 1) else model_b_name,
        'brier_score': model_a_name if results_a.get('brier_score', 1) < results_b.get('brier_score', 1) else model_b_name,
        'roi': model_a_name if results_a.get('roi_pct', 0) > results_b.get('roi_pct', 0) else model_b_name
    }

    comparison['winners'] = winners

    return comparison
