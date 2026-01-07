"""
Hyperparameter Tuning - Optuna ile otomatik model optimizasyonu
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Callable, Tuple
import optuna
from optuna.trial import Trial
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
import structlog

from ..models.base import BasePredictor
from ..evaluation.metrics import PredictionMetrics
from ..evaluation.backtesting import BacktestEngine

logger = structlog.get_logger()


class OptunaCallback:
    """Callback for Optuna optimization progress"""

    def __init__(self):
        self.best_value = float('inf')
        self.trials = []

    def __call__(self, study: optuna.Study, trial: optuna.Trial):
        """Called after each trial"""
        if study.best_value < self.best_value:
            self.best_value = study.best_value
            logger.info(
                "new_best_trial",
                trial=trial.number,
                value=round(trial.value, 4),
                params=trial.params
            )

        self.trials.append({
            'number': trial.number,
            'value': trial.value,
            'params': trial.params,
            'state': trial.state.name
        })


class HyperparameterTuner:
    """
    Hyperparameter tuning using Optuna.

    Features:
    - Bayesian optimization
    - Pruning for early stopping
    - Multi-objective optimization
    - Cross-validation based tuning
    """

    def __init__(
        self,
        n_trials: int = 100,
        timeout: Optional[int] = None,  # seconds
        n_jobs: int = -1,
        cv_folds: int = 3,
        optimization_metric: str = 'log_loss',  # 'log_loss', 'accuracy', 'roi'
        direction: str = 'minimize'  # 'minimize' or 'maximize'
    ):
        self.n_trials = n_trials
        self.timeout = timeout
        self.n_jobs = n_jobs
        self.cv_folds = cv_folds
        self.optimization_metric = optimization_metric
        self.direction = direction

        # Optuna components
        self.sampler = TPESampler(seed=42)
        self.pruner = MedianPruner(n_startup_trials=5, n_warmup_steps=10)
        self.callback = OptunaCallback()

    def tune(
        self,
        model_class: type,
        param_space: Dict[str, Any],
        data: pd.DataFrame,
        fixed_params: Optional[Dict] = None
    ) -> Tuple[Dict[str, Any], optuna.Study]:
        """
        Tune hyperparameters for a model.

        Args:
            model_class: Model class to instantiate
            param_space: Parameter space definition
            data: Training data
            fixed_params: Fixed parameters (not tuned)

        Returns:
            (best_params, study) tuple
        """
        logger.info(
            "tuning_started",
            model=model_class.__name__,
            n_trials=self.n_trials,
            metric=self.optimization_metric
        )

        fixed_params = fixed_params or {}

        def objective(trial: Trial) -> float:
            """Objective function for Optuna"""

            # Sample hyperparameters
            params = self._sample_params(trial, param_space)
            params.update(fixed_params)

            # Create model
            try:
                model = model_class(**params)
            except Exception as e:
                logger.error("model_creation_error", error=str(e), params=params)
                raise optuna.TrialPruned()

            # Evaluate with cross-validation
            try:
                score = self._cross_validate(model, data, trial)
            except Exception as e:
                logger.error("cv_error", error=str(e), trial=trial.number)
                raise optuna.TrialPruned()

            return score

        # Create study
        study = optuna.create_study(
            direction=self.direction,
            sampler=self.sampler,
            pruner=self.pruner
        )

        # Optimize
        study.optimize(
            objective,
            n_trials=self.n_trials,
            timeout=self.timeout,
            n_jobs=self.n_jobs,
            callbacks=[self.callback],
            show_progress_bar=True
        )

        best_params = study.best_params
        best_value = study.best_value

        logger.info(
            "tuning_completed",
            best_value=round(best_value, 4),
            best_params=best_params,
            n_trials=len(study.trials)
        )

        return best_params, study

    def _sample_params(self, trial: Trial, param_space: Dict) -> Dict[str, Any]:
        """Sample parameters from the parameter space"""
        params = {}

        for name, config in param_space.items():
            param_type = config.get('type')

            if param_type == 'int':
                params[name] = trial.suggest_int(
                    name,
                    config['low'],
                    config['high'],
                    step=config.get('step', 1),
                    log=config.get('log', False)
                )

            elif param_type == 'float':
                params[name] = trial.suggest_float(
                    name,
                    config['low'],
                    config['high'],
                    step=config.get('step'),
                    log=config.get('log', False)
                )

            elif param_type == 'categorical':
                params[name] = trial.suggest_categorical(
                    name,
                    config['choices']
                )

            elif param_type == 'uniform':
                params[name] = trial.suggest_uniform(
                    name,
                    config['low'],
                    config['high']
                )

            elif param_type == 'loguniform':
                params[name] = trial.suggest_loguniform(
                    name,
                    config['low'],
                    config['high']
                )

        return params

    def _cross_validate(
        self,
        model: BasePredictor,
        data: pd.DataFrame,
        trial: Optional[Trial] = None
    ) -> float:
        """
        Perform cross-validation and return metric.

        Args:
            model: Model to evaluate
            data: Training data
            trial: Optuna trial (for pruning)

        Returns:
            Metric value
        """
        data = data.sort_values('match_date').copy()

        fold_scores = []

        # Time-series CV
        total_days = (data['match_date'].max() - data['match_date'].min()).days
        fold_size = total_days // self.cv_folds

        for fold in range(self.cv_folds):
            # Split
            split_date = data['match_date'].min() + pd.Timedelta(days=fold_size * (fold + 1))
            test_start = split_date - pd.Timedelta(days=30)

            train_data = data[data['match_date'] < test_start]
            test_data = data[
                (data['match_date'] >= test_start) &
                (data['match_date'] < split_date) &
                (data['home_score'].notna())
            ]

            if len(train_data) < 50 or len(test_data) < 10:
                continue

            # Train
            try:
                model.train(train_data)
            except Exception as e:
                logger.warning("fold_train_error", fold=fold, error=str(e))
                continue

            # Evaluate
            metrics_engine = PredictionMetrics()

            for _, match in test_data.iterrows():
                try:
                    pred = model.predict({
                        'home_team': match['home_team'],
                        'away_team': match['away_team']
                    })

                    # Actual result
                    if match['home_score'] > match['away_score']:
                        actual = 'H'
                    elif match['home_score'] == match['away_score']:
                        actual = 'D'
                    else:
                        actual = 'A'

                    metrics_engine.add_prediction(
                        actual_result=actual,
                        predicted_probs={
                            'H': pred.get('home_win_prob', 0.33),
                            'D': pred.get('draw_prob', 0.33),
                            'A': pred.get('away_win_prob', 0.34)
                        }
                    )

                except Exception as e:
                    logger.warning("prediction_error", error=str(e))
                    continue

            fold_metrics = metrics_engine.calculate_all_metrics()
            score = fold_metrics.get(self.optimization_metric, 0)
            fold_scores.append(score)

            # Pruning
            if trial is not None:
                trial.report(score, fold)
                if trial.should_prune():
                    raise optuna.TrialPruned()

        if not fold_scores:
            raise optuna.TrialPruned()

        return np.mean(fold_scores)

    def get_optimization_history(self) -> pd.DataFrame:
        """Get optimization history as DataFrame"""
        if not self.callback.trials:
            return pd.DataFrame()

        df = pd.DataFrame(self.callback.trials)
        return df

    def plot_optimization_history(self, study: optuna.Study, save_path: Optional[str] = None):
        """Plot optimization history"""
        try:
            from optuna.visualization import (
                plot_optimization_history,
                plot_param_importances,
                plot_parallel_coordinate
            )

            # Optimization history
            fig = plot_optimization_history(study)
            if save_path:
                fig.write_html(f"{save_path}_history.html")

            # Parameter importances
            if len(study.trials) > 10:
                fig = plot_param_importances(study)
                if save_path:
                    fig.write_html(f"{save_path}_importance.html")

            # Parallel coordinates
            fig = plot_parallel_coordinate(study)
            if save_path:
                fig.write_html(f"{save_path}_parallel.html")

            logger.info("plots_saved", path=save_path)

        except ImportError:
            logger.warning("optuna_visualization_not_available")


def create_xgboost_param_space() -> Dict[str, Any]:
    """Create parameter space for XGBoost"""
    return {
        'max_depth': {
            'type': 'int',
            'low': 3,
            'high': 10
        },
        'learning_rate': {
            'type': 'loguniform',
            'low': 0.001,
            'high': 0.3
        },
        'n_estimators': {
            'type': 'int',
            'low': 50,
            'high': 500,
            'step': 50
        },
        'min_child_weight': {
            'type': 'int',
            'low': 1,
            'high': 10
        },
        'subsample': {
            'type': 'uniform',
            'low': 0.5,
            'high': 1.0
        },
        'colsample_bytree': {
            'type': 'uniform',
            'low': 0.5,
            'high': 1.0
        },
        'gamma': {
            'type': 'loguniform',
            'low': 1e-8,
            'high': 1.0
        },
        'reg_alpha': {
            'type': 'loguniform',
            'low': 1e-8,
            'high': 10.0
        },
        'reg_lambda': {
            'type': 'loguniform',
            'low': 1e-8,
            'high': 10.0
        }
    }


def create_lightgbm_param_space() -> Dict[str, Any]:
    """Create parameter space for LightGBM"""
    return {
        'max_depth': {
            'type': 'int',
            'low': 3,
            'high': 12
        },
        'learning_rate': {
            'type': 'loguniform',
            'low': 0.001,
            'high': 0.3
        },
        'n_estimators': {
            'type': 'int',
            'low': 50,
            'high': 500,
            'step': 50
        },
        'num_leaves': {
            'type': 'int',
            'low': 20,
            'high': 200
        },
        'min_child_samples': {
            'type': 'int',
            'low': 5,
            'high': 100
        },
        'subsample': {
            'type': 'uniform',
            'low': 0.5,
            'high': 1.0
        },
        'colsample_bytree': {
            'type': 'uniform',
            'low': 0.5,
            'high': 1.0
        },
        'reg_alpha': {
            'type': 'loguniform',
            'low': 1e-8,
            'high': 10.0
        },
        'reg_lambda': {
            'type': 'loguniform',
            'low': 1e-8,
            'high': 10.0
        }
    }


def create_ensemble_param_space() -> Dict[str, Any]:
    """Create parameter space for Ensemble"""
    return {
        'strategy': {
            'type': 'categorical',
            'choices': ['simple', 'weighted']
        }
    }
