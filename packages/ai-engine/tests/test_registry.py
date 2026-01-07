"""
Tests for Model Registry
"""

import pytest
from datetime import datetime

from ..registry.model_registry import ModelRegistry, ModelStage, ModelMetadata
from ..registry.version_manager import VersionManager, SemanticVersion
from ..models.poisson import PoissonModel
import pandas as pd


@pytest.fixture
def sample_data():
    """Create sample training data"""
    return pd.DataFrame({
        'match_date': pd.date_range('2023-01-01', periods=100),
        'home_team': ['A'] * 100,
        'away_team': ['B'] * 100,
        'home_score': [1] * 100,
        'away_score': [0] * 100
    })


@pytest.fixture
def registry(tmp_path):
    """Create test registry"""
    return ModelRegistry(registry_path=str(tmp_path / "registry"))


@pytest.fixture
def trained_model(sample_data):
    """Create trained model"""
    model = PoissonModel()
    model.train(sample_data)
    return model


class TestModelRegistry:
    """Test ModelRegistry"""

    def test_registry_creation(self, tmp_path):
        """Test creating registry"""
        registry = ModelRegistry(registry_path=str(tmp_path / "test_registry"))

        assert registry.registry_path.exists()
        assert registry.models_dir.exists()

    def test_register_model(self, registry, trained_model):
        """Test registering a model"""
        model_id = registry.register_model(
            model=trained_model,
            model_name='poisson',
            version='1.0.0',
            training_metrics={'accuracy': 0.55},
            validation_metrics={'accuracy': 0.52},
            training_data_hash='abc123',
            training_duration=10.5,
            author='test',
            description='Test model'
        )

        assert model_id is not None
        assert 'poisson' in model_id

    def test_load_model(self, registry, trained_model):
        """Test loading a model"""
        # Register first
        registry.register_model(
            model=trained_model,
            model_name='poisson',
            version='1.0.0',
            training_metrics={'accuracy': 0.55},
            validation_metrics={'accuracy': 0.52},
            training_data_hash='abc123',
            training_duration=10.5
        )

        # Load
        loaded_model, metadata = registry.load_model('poisson', version='1.0.0')

        assert loaded_model is not None
        assert metadata.version == '1.0.0'

    def test_promote_model(self, registry, trained_model):
        """Test promoting model to different stage"""
        # Register as development
        registry.register_model(
            model=trained_model,
            model_name='poisson',
            version='1.0.0',
            training_metrics={'accuracy': 0.55},
            validation_metrics={'accuracy': 0.52},
            training_data_hash='abc123',
            training_duration=10.5,
            stage=ModelStage.DEVELOPMENT
        )

        # Promote to production
        registry.promote_model('poisson', '1.0.0', ModelStage.PRODUCTION)

        # Load production model
        model, metadata = registry.load_model('poisson', stage=ModelStage.PRODUCTION)

        assert metadata.stage == ModelStage.PRODUCTION

    def test_list_models(self, registry, trained_model):
        """Test listing models"""
        # Register multiple versions
        for i in range(3):
            registry.register_model(
                model=trained_model,
                model_name='poisson',
                version=f'1.{i}.0',
                training_metrics={'accuracy': 0.55},
                validation_metrics={'accuracy': 0.52},
                training_data_hash='abc123',
                training_duration=10.5
            )

        models = registry.list_models(model_name='poisson')

        assert len(models) == 3

    def test_compare_models(self, registry, trained_model):
        """Test comparing model versions"""
        # Register two versions
        registry.register_model(
            model=trained_model,
            model_name='poisson',
            version='1.0.0',
            training_metrics={'accuracy': 0.55},
            validation_metrics={'accuracy': 0.52},
            training_data_hash='abc123',
            training_duration=10.5
        )

        registry.register_model(
            model=trained_model,
            model_name='poisson',
            version='1.1.0',
            training_metrics={'accuracy': 0.57},
            validation_metrics={'accuracy': 0.54},
            training_data_hash='def456',
            training_duration=12.0
        )

        comparison = registry.compare_models(
            'poisson',
            ['1.0.0', '1.1.0']
        )

        assert 'versions' in comparison
        assert 'best' in comparison


class TestSemanticVersion:
    """Test SemanticVersion"""

    def test_version_creation(self):
        """Test creating version"""
        v = SemanticVersion(1, 2, 3)

        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
        assert str(v) == '1.2.3'

    def test_version_parsing(self):
        """Test parsing version string"""
        v = SemanticVersion.parse('2.1.5')

        assert v.major == 2
        assert v.minor == 1
        assert v.patch == 5

    def test_version_comparison(self):
        """Test version comparison"""
        v1 = SemanticVersion(1, 0, 0)
        v2 = SemanticVersion(2, 0, 0)
        v3 = SemanticVersion(1, 1, 0)

        assert v1 < v2
        assert v1 < v3
        assert v2 > v1

    def test_version_bump(self):
        """Test version bumping"""
        v = SemanticVersion(1, 2, 3)

        major = v.bump_major()
        assert str(major) == '2.0.0'

        minor = v.bump_minor()
        assert str(minor) == '1.3.0'

        patch = v.bump_patch()
        assert str(patch) == '1.2.4'


class TestVersionManager:
    """Test VersionManager"""

    def test_suggest_next_version(self, registry):
        """Test suggesting next version"""
        vm = VersionManager(registry)

        # First version
        v = vm.suggest_next_version('new_model', 'major')
        assert str(v) == '1.0.0'

    def test_auto_version(self, registry):
        """Test automatic versioning"""
        vm = VersionManager(registry)

        # Architecture changed -> major bump
        v = vm.auto_version(
            'test_model',
            architecture_changed=True
        )

        assert str(v) == '1.0.0'  # First version


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
