"""
Tests for Backtesting Framework
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from ..evaluation.backtesting import BacktestEngine, BacktestResult
from ..models.poisson import PoissonModel
from ..models.elo import EloModel


@pytest.fixture
def sample_historical_data():
    """Create sample historical data for backtesting"""
    dates = pd.date_range(start='2023-01-01', periods=365, freq='D')

    data = {
        'match_date': dates,
        'home_team': np.random.choice(['Team A', 'Team B', 'Team C', 'Team D'], 365),
        'away_team': np.random.choice(['Team A', 'Team B', 'Team C', 'Team D'], 365),
        'home_score': np.random.randint(0, 4, 365),
        'away_score': np.random.randint(0, 4, 365),
        'home_odds': np.random.uniform(1.5, 3.5, 365),
        'draw_odds': np.random.uniform(2.5, 4.5, 365),
        'away_odds': np.random.uniform(1.5, 3.5, 365)
    }

    return pd.DataFrame(data)


class TestBacktestEngine:
    """Test BacktestEngine"""

    def test_engine_creation(self):
        """Test creating backtest engine"""
        engine = BacktestEngine(
            initial_bankroll=1000,
            stake_size=10,
            min_edge=0.05
        )

        assert engine.initial_bankroll == 1000
        assert engine.stake_size == 10
        assert engine.min_edge == 0.05

    def test_walk_forward_validation(self, sample_historical_data):
        """Test walk-forward validation"""
        engine = BacktestEngine()
        model = PoissonModel()

        result = engine.walk_forward_validation(
            model=model,
            data=sample_historical_data,
            train_window=90,
            test_window=30,
            step_size=30,
            retrain=True
        )

        assert isinstance(result, BacktestResult)
        assert result.total_matches > 0
        assert 'accuracy' in result.metrics
        assert len(result.equity_curve) > 0

    def test_time_series_cv(self, sample_historical_data):
        """Test time-series cross-validation"""
        engine = BacktestEngine()
        model = EloModel()

        results = engine.time_series_cv(
            model=model,
            data=sample_historical_data,
            n_splits=3,
            test_size=30
        )

        assert 'avg_metrics' in results
        assert 'fold_results' in results
        assert len(results['fold_results']) > 0

    def test_out_of_sample(self, sample_historical_data):
        """Test out-of-sample testing"""
        engine = BacktestEngine()
        model = PoissonModel()

        split_idx = int(len(sample_historical_data) * 0.8)
        train_data = sample_historical_data[:split_idx]
        test_data = sample_historical_data[split_idx:]

        result = engine.out_of_sample_test(
            model=model,
            train_data=train_data,
            test_data=test_data
        )

        assert isinstance(result, BacktestResult)
        assert result.total_matches > 0


class TestBacktestResult:
    """Test BacktestResult"""

    def test_result_to_dict(self):
        """Test converting result to dictionary"""
        result = BacktestResult(
            model_name='test',
            start_date=datetime.now(),
            end_date=datetime.now(),
            total_matches=100,
            metrics={'accuracy': 0.55},
            predictions=[],
            equity_curve=[1000, 1050, 1100],
            monthly_performance={}
        )

        result_dict = result.to_dict()

        assert 'model_name' in result_dict
        assert 'total_matches' in result_dict
        assert 'metrics' in result_dict

    def test_result_save(self, tmp_path):
        """Test saving result to file"""
        result = BacktestResult(
            model_name='test',
            start_date=datetime.now(),
            end_date=datetime.now(),
            total_matches=100,
            metrics={'accuracy': 0.55},
            predictions=[],
            equity_curve=[1000],
            monthly_performance={}
        )

        filepath = tmp_path / "backtest_result.json"
        result.save(str(filepath))

        assert filepath.exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
