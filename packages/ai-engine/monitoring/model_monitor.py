"""
Model Performance Monitoring - Real-time performance tracking
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import structlog

from ..evaluation.metrics import PredictionMetrics

logger = structlog.get_logger()


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceAlert:
    """Performance alert"""
    timestamp: datetime
    severity: AlertSeverity
    metric_name: str
    current_value: float
    expected_value: float
    threshold: float
    message: str

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value
        }


class ModelMonitor:
    """
    Real-time model performance monitoring.

    Features:
    - Rolling window metrics
    - Performance degradation detection
    - Alert system
    - Trend analysis
    - Automatic reporting
    """

    def __init__(
        self,
        model_name: str,
        window_size: int = 100,  # Number of predictions
        baseline_metrics: Optional[Dict[str, float]] = None,
        alert_thresholds: Optional[Dict[str, Dict]] = None
    ):
        """
        Args:
            model_name: Model name
            window_size: Rolling window size
            baseline_metrics: Expected baseline metrics
            alert_thresholds: Alert threshold configuration
        """
        self.model_name = model_name
        self.window_size = window_size
        self.baseline_metrics = baseline_metrics or {}

        # Default alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'accuracy': {
                'warning_drop': 0.05,  # 5% drop
                'critical_drop': 0.10  # 10% drop
            },
            'log_loss': {
                'warning_increase': 0.10,  # 10% increase
                'critical_increase': 0.20  # 20% increase
            },
            'roi_pct': {
                'warning_drop': 5.0,  # 5% drop
                'critical_drop': 10.0  # 10% drop
            }
        }

        # Rolling data
        self.predictions_buffer = deque(maxlen=window_size)
        self.metrics_history = []  # [(timestamp, metrics)]
        self.alerts = []

        # Statistics
        self.total_predictions = 0
        self.start_time = datetime.now()

    def add_prediction(
        self,
        actual_result: str,
        predicted_probs: Dict[str, float],
        odds: Optional[Dict[str, float]] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Add a prediction to the monitoring buffer.

        Args:
            actual_result: Actual match result
            predicted_probs: Predicted probabilities
            odds: Betting odds (optional)
            timestamp: Prediction timestamp
        """
        timestamp = timestamp or datetime.now()

        self.predictions_buffer.append({
            'actual_result': actual_result,
            'predicted_probs': predicted_probs,
            'odds': odds,
            'timestamp': timestamp
        })

        self.total_predictions += 1

        # Calculate metrics every N predictions
        if len(self.predictions_buffer) >= self.window_size:
            metrics = self._calculate_current_metrics()
            self.metrics_history.append((timestamp, metrics))

            # Check for alerts
            self._check_alerts(metrics, timestamp)

    def _calculate_current_metrics(self) -> Dict[str, float]:
        """Calculate metrics from current buffer"""
        metrics_engine = PredictionMetrics()

        for pred in self.predictions_buffer:
            metrics_engine.add_prediction(
                actual_result=pred['actual_result'],
                predicted_probs=pred['predicted_probs'],
                odds=pred.get('odds')
            )

        return metrics_engine.calculate_all_metrics()

    def _check_alerts(self, current_metrics: Dict[str, float], timestamp: datetime):
        """Check for performance alerts"""
        for metric_name, thresholds in self.alert_thresholds.items():
            if metric_name not in current_metrics:
                continue

            current_value = current_metrics[metric_name]
            baseline_value = self.baseline_metrics.get(metric_name)

            if baseline_value is None:
                continue

            # Check for drops (accuracy, ROI, etc.)
            if 'warning_drop' in thresholds:
                drop = baseline_value - current_value
                drop_pct = drop / baseline_value if baseline_value > 0 else 0

                if drop_pct >= thresholds['critical_drop']:
                    self._create_alert(
                        timestamp=timestamp,
                        severity=AlertSeverity.CRITICAL,
                        metric_name=metric_name,
                        current_value=current_value,
                        expected_value=baseline_value,
                        threshold=thresholds['critical_drop'],
                        message=f"CRITICAL: {metric_name} dropped {drop_pct:.2%} (from {baseline_value:.4f} to {current_value:.4f})"
                    )
                elif drop_pct >= thresholds['warning_drop']:
                    self._create_alert(
                        timestamp=timestamp,
                        severity=AlertSeverity.WARNING,
                        metric_name=metric_name,
                        current_value=current_value,
                        expected_value=baseline_value,
                        threshold=thresholds['warning_drop'],
                        message=f"WARNING: {metric_name} dropped {drop_pct:.2%} (from {baseline_value:.4f} to {current_value:.4f})"
                    )

            # Check for increases (log_loss, etc.)
            if 'warning_increase' in thresholds:
                increase = current_value - baseline_value
                increase_pct = increase / baseline_value if baseline_value > 0 else 0

                if increase_pct >= thresholds['critical_increase']:
                    self._create_alert(
                        timestamp=timestamp,
                        severity=AlertSeverity.CRITICAL,
                        metric_name=metric_name,
                        current_value=current_value,
                        expected_value=baseline_value,
                        threshold=thresholds['critical_increase'],
                        message=f"CRITICAL: {metric_name} increased {increase_pct:.2%} (from {baseline_value:.4f} to {current_value:.4f})"
                    )
                elif increase_pct >= thresholds['warning_increase']:
                    self._create_alert(
                        timestamp=timestamp,
                        severity=AlertSeverity.WARNING,
                        metric_name=metric_name,
                        current_value=current_value,
                        expected_value=baseline_value,
                        threshold=thresholds['warning_increase'],
                        message=f"WARNING: {metric_name} increased {increase_pct:.2%} (from {baseline_value:.4f} to {current_value:.4f})"
                    )

    def _create_alert(
        self,
        timestamp: datetime,
        severity: AlertSeverity,
        metric_name: str,
        current_value: float,
        expected_value: float,
        threshold: float,
        message: str
    ):
        """Create and log alert"""
        alert = PerformanceAlert(
            timestamp=timestamp,
            severity=severity,
            metric_name=metric_name,
            current_value=current_value,
            expected_value=expected_value,
            threshold=threshold,
            message=message
        )

        self.alerts.append(alert)

        logger_func = logger.critical if severity == AlertSeverity.CRITICAL else logger.warning
        logger_func(
            "performance_alert",
            model=self.model_name,
            severity=severity.value,
            **alert.to_dict()
        )

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current rolling window metrics"""
        if len(self.predictions_buffer) < 10:
            return {}

        return self._calculate_current_metrics()

    def get_metrics_trend(
        self,
        metric_name: str,
        lookback_hours: int = 24
    ) -> List[Tuple[datetime, float]]:
        """Get metric trend over time"""
        cutoff = datetime.now() - timedelta(hours=lookback_hours)

        trend = [
            (ts, metrics.get(metric_name))
            for ts, metrics in self.metrics_history
            if ts >= cutoff and metric_name in metrics
        ]

        return trend

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        since: Optional[datetime] = None
    ) -> List[PerformanceAlert]:
        """Get alerts"""
        filtered = self.alerts

        if severity:
            filtered = [a for a in filtered if a.severity == severity]

        if since:
            filtered = [a for a in filtered if a.timestamp >= since]

        return filtered

    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        current_metrics = self.get_current_metrics()
        uptime = (datetime.now() - self.start_time).total_seconds() / 3600  # hours

        recent_alerts = self.get_alerts(since=datetime.now() - timedelta(hours=24))

        return {
            'model_name': self.model_name,
            'total_predictions': self.total_predictions,
            'uptime_hours': round(uptime, 2),
            'window_size': self.window_size,
            'buffer_size': len(self.predictions_buffer),
            'current_metrics': current_metrics,
            'baseline_metrics': self.baseline_metrics,
            'recent_alerts_24h': len(recent_alerts),
            'critical_alerts': len([a for a in recent_alerts if a.severity == AlertSeverity.CRITICAL]),
            'warning_alerts': len([a for a in recent_alerts if a.severity == AlertSeverity.WARNING])
        }

    def reset_baseline(self, new_baseline: Dict[str, float]):
        """Update baseline metrics"""
        self.baseline_metrics = new_baseline
        logger.info("baseline_updated", model=self.model_name, baseline=new_baseline)

    def clear_buffer(self):
        """Clear prediction buffer"""
        self.predictions_buffer.clear()
        logger.info("buffer_cleared", model=self.model_name)

    def should_retrain(self) -> bool:
        """
        Determine if model should be retrained.

        Returns True if:
        - Critical alerts in last 24h
        - Performance significantly degraded
        """
        recent_critical = self.get_alerts(
            severity=AlertSeverity.CRITICAL,
            since=datetime.now() - timedelta(hours=24)
        )

        if recent_critical:
            logger.warning(
                "retrain_recommended",
                model=self.model_name,
                reason=f"{len(recent_critical)} critical alerts in last 24h"
            )
            return True

        return False


class MonitoringDashboard:
    """Dashboard for monitoring multiple models"""

    def __init__(self):
        self.monitors: Dict[str, ModelMonitor] = {}

    def add_monitor(self, model_name: str, monitor: ModelMonitor):
        """Add model monitor"""
        self.monitors[model_name] = monitor
        logger.info("monitor_added", model=model_name)

    def get_all_alerts(
        self,
        severity: Optional[AlertSeverity] = None
    ) -> Dict[str, List[PerformanceAlert]]:
        """Get alerts from all monitors"""
        all_alerts = {}

        for model_name, monitor in self.monitors.items():
            alerts = monitor.get_alerts(severity=severity)
            if alerts:
                all_alerts[model_name] = alerts

        return all_alerts

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary of all models"""
        summaries = {}

        for model_name, monitor in self.monitors.items():
            summaries[model_name] = monitor.get_summary()

        # Overall stats
        total_predictions = sum(s['total_predictions'] for s in summaries.values())
        total_critical = sum(s['critical_alerts'] for s in summaries.values())
        total_warnings = sum(s['warning_alerts'] for s in summaries.values())

        return {
            'total_models': len(self.monitors),
            'total_predictions': total_predictions,
            'total_critical_alerts': total_critical,
            'total_warning_alerts': total_warnings,
            'models': summaries
        }
