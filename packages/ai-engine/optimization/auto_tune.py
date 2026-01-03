"""
Auto-tuning utilities - Kolay hyperparameter tuning fonksiyonları
"""

import pandas as pd
from typing import Any, Dict, Optional, Tuple
import structlog

from ..models.xgboost_model import XGBoostModel
from ..models.lightgbm_model import LightGBMModel
from .hyperparameter_tuner import (
    HyperparameterTuner,
    create_xgboost_param_space,
    create_lightgbm_param_space
)

logger = structlog.get_logger()


def auto_tune_model(
    model_class: type,
    param_space: Dict[str, Any],
    data: pd.DataFrame,
    n_trials: int = 100,
    optimization_metric: str = 'log_loss',
    cv_folds: int = 3,
    save_study: bool = True,
    study_path: Optional[str] = None
) -> Tuple[Any, Dict[str, Any]]:
    """
    Auto-tune any model with default settings.

    Args:
        model_class: Model class to tune
        param_space: Parameter space
        data: Training data
        n_trials: Number of optimization trials
        optimization_metric: Metric to optimize
        cv_folds: Number of CV folds
        save_study: Whether to save study results
        study_path: Path to save study

    Returns:
        (tuned_model, best_params) tuple
    """
    logger.info(
        "auto_tune_started",
        model=model_class.__name__,
        n_trials=n_trials,
        metric=optimization_metric
    )

    # Create tuner
    direction = 'minimize' if optimization_metric in ['log_loss', 'brier_score', 'rps'] else 'maximize'

    tuner = HyperparameterTuner(
        n_trials=n_trials,
        cv_folds=cv_folds,
        optimization_metric=optimization_metric,
        direction=direction
    )

    # Tune
    best_params, study = tuner.tune(
        model_class=model_class,
        param_space=param_space,
        data=data
    )

    # Create best model
    tuned_model = model_class(**best_params)

    # Train on full data
    logger.info("training_best_model", params=best_params)
    tuned_model.train(data)

    # Save study
    if save_study and study_path:
        tuner.plot_optimization_history(study, save_path=study_path)

    logger.info(
        "auto_tune_completed",
        best_value=round(study.best_value, 4),
        trials_completed=len(study.trials)
    )

    return tuned_model, best_params


def tune_xgboost(
    data: pd.DataFrame,
    n_trials: int = 100,
    optimization_metric: str = 'log_loss',
    custom_param_space: Optional[Dict] = None
) -> Tuple[XGBoostModel, Dict[str, Any]]:
    """
    Tune XGBoost model with sensible defaults.

    Args:
        data: Training data
        n_trials: Number of trials
        optimization_metric: Metric to optimize
        custom_param_space: Custom parameter space (overrides default)

    Returns:
        (tuned_model, best_params)
    """
    param_space = custom_param_space or create_xgboost_param_space()

    logger.info("tuning_xgboost", n_trials=n_trials, metric=optimization_metric)

    model, params = auto_tune_model(
        model_class=XGBoostModel,
        param_space=param_space,
        data=data,
        n_trials=n_trials,
        optimization_metric=optimization_metric,
        study_path='outputs/xgboost_tuning'
    )

    return model, params


def tune_lightgbm(
    data: pd.DataFrame,
    n_trials: int = 100,
    optimization_metric: str = 'log_loss',
    custom_param_space: Optional[Dict] = None
) -> Tuple[LightGBMModel, Dict[str, Any]]:
    """
    Tune LightGBM model with sensible defaults.

    Args:
        data: Training data
        n_trials: Number of trials
        optimization_metric: Metric to optimize
        custom_param_space: Custom parameter space (overrides default)

    Returns:
        (tuned_model, best_params)
    """
    param_space = custom_param_space or create_lightgbm_param_space()

    logger.info("tuning_lightgbm", n_trials=n_trials, metric=optimization_metric)

    model, params = auto_tune_model(
        model_class=LightGBMModel,
        param_space=param_space,
        data=data,
        n_trials=n_trials,
        optimization_metric=optimization_metric,
        study_path='outputs/lightgbm_tuning'
    )

    return model, params


def grid_search_simple(
    model_class: type,
    param_grid: Dict[str, list],
    data: pd.DataFrame,
    metric: str = 'accuracy'
) -> Tuple[Any, Dict]:
    """
    Simple grid search (for small parameter spaces).

    Args:
        model_class: Model class
        param_grid: Parameter grid {param_name: [values]}
        data: Training data
        metric: Evaluation metric

    Returns:
        (best_model, best_params)
    """
    from itertools import product

    logger.info("grid_search_started", params=list(param_grid.keys()))

    # Generate all combinations
    keys = param_grid.keys()
    values = param_grid.values()
    combinations = [dict(zip(keys, v)) for v in product(*values)]

    logger.info("grid_combinations", total=len(combinations))

    best_score = float('-inf') if metric in ['accuracy', 'roi'] else float('inf')
    best_params = None
    best_model = None

    for i, params in enumerate(combinations):
        logger.info(f"testing_combination_{i+1}/{len(combinations)}", params=params)

        try:
            model = model_class(**params)
            model.train(data)

            # Simple train accuracy
            train_metrics = model.training_metrics
            score = train_metrics.get(metric, 0)

            # Check if better
            is_better = (
                score > best_score if metric in ['accuracy', 'roi']
                else score < best_score
            )

            if is_better:
                best_score = score
                best_params = params
                best_model = model
                logger.info("new_best", score=round(score, 4), params=params)

        except Exception as e:
            logger.error("combination_error", error=str(e), params=params)
            continue

    logger.info(
        "grid_search_completed",
        best_score=round(best_score, 4),
        best_params=best_params
    )

    return best_model, best_params


def quick_tune(
    model_class: type,
    data: pd.DataFrame,
    n_trials: int = 20
) -> Any:
    """
    Quick tune with minimal trials (for rapid iteration).

    Args:
        model_class: Model class
        data: Training data
        n_trials: Number of trials (default: 20)

    Returns:
        Tuned model
    """
    logger.info("quick_tune", model=model_class.__name__, n_trials=n_trials)

    # Use default param space based on model
    if model_class.__name__ == 'XGBoostModel':
        param_space = create_xgboost_param_space()
    elif model_class.__name__ == 'LightGBMModel':
        param_space = create_lightgbm_param_space()
    else:
        raise ValueError(f"No default param space for {model_class.__name__}")

    model, params = auto_tune_model(
        model_class=model_class,
        param_space=param_space,
        data=data,
        n_trials=n_trials,
        cv_folds=2,  # Faster CV
        save_study=False
    )

    return model
