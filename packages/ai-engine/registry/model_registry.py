"""
Model Registry - Centralized model storage and versioning
"""

import os
import json
import joblib
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import structlog

from ..models.base import BasePredictor

logger = structlog.get_logger()


class ModelStage(Enum):
    """Model deployment stages"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


@dataclass
class ModelMetadata:
    """Metadata for a registered model"""
    model_id: str
    model_name: str
    version: str
    stage: ModelStage
    created_at: datetime
    updated_at: datetime
    author: str
    description: str

    # Training metadata
    training_metrics: Dict[str, float]
    training_data_hash: str
    training_date: datetime
    training_duration: float  # seconds

    # Model info
    model_class: str
    hyperparameters: Dict[str, Any]
    feature_names: List[str]

    # Performance
    validation_metrics: Dict[str, float]
    test_metrics: Optional[Dict[str, float]]

    # Deployment
    deployed_at: Optional[datetime]
    deployment_target: Optional[str]

    # Files
    model_path: str
    artifact_paths: Dict[str, str]

    # Tags
    tags: Dict[str, str]

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['stage'] = self.stage.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['training_date'] = self.training_date.isoformat()
        if self.deployed_at:
            data['deployed_at'] = self.deployed_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelMetadata':
        """Create from dictionary"""
        data = data.copy()
        data['stage'] = ModelStage(data['stage'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['training_date'] = datetime.fromisoformat(data['training_date'])
        if data.get('deployed_at'):
            data['deployed_at'] = datetime.fromisoformat(data['deployed_at'])
        return cls(**data)


class ModelRegistry:
    """
    Centralized model registry for versioning and lifecycle management.

    Features:
    - Model versioning (semantic versioning)
    - Stage management (dev -> staging -> production)
    - Metadata tracking
    - Model comparison
    - Rollback capability
    """

    def __init__(self, registry_path: str = "models/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)

        self.models_dir = self.registry_path / "models"
        self.models_dir.mkdir(exist_ok=True)

        self.metadata_file = self.registry_path / "registry.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, List[Dict]]:
        """Load registry metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """Save registry metadata"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2, default=str)

    def register_model(
        self,
        model: BasePredictor,
        model_name: str,
        version: str,
        training_metrics: Dict[str, float],
        validation_metrics: Dict[str, float],
        training_data_hash: str,
        training_duration: float,
        author: str = "system",
        description: str = "",
        stage: ModelStage = ModelStage.DEVELOPMENT,
        hyperparameters: Optional[Dict] = None,
        test_metrics: Optional[Dict] = None,
        tags: Optional[Dict] = None
    ) -> str:
        """
        Register a new model version.

        Args:
            model: Trained model instance
            model_name: Name of the model (e.g., 'xgboost', 'ensemble')
            version: Semantic version (e.g., '1.0.0', '2.1.3')
            training_metrics: Metrics from training
            validation_metrics: Metrics from validation
            training_data_hash: Hash of training data
            training_duration: Training duration in seconds
            author: Author name
            description: Model description
            stage: Deployment stage
            hyperparameters: Model hyperparameters
            test_metrics: Test set metrics (optional)
            tags: Custom tags

        Returns:
            model_id: Unique identifier for this model version
        """
        model_id = self._generate_model_id(model_name, version)

        logger.info(
            "registering_model",
            model_id=model_id,
            model_name=model_name,
            version=version,
            stage=stage.value
        )

        # Create model directory
        model_dir = self.models_dir / model_id
        model_dir.mkdir(exist_ok=True)

        # Save model
        model_path = model_dir / "model.joblib"
        joblib.dump(model, model_path)

        # Get feature names
        feature_names = getattr(model, 'feature_names', [])

        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            model_name=model_name,
            version=version,
            stage=stage,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            author=author,
            description=description,
            training_metrics=training_metrics,
            training_data_hash=training_data_hash,
            training_date=datetime.now(),
            training_duration=training_duration,
            model_class=model.__class__.__name__,
            hyperparameters=hyperparameters or {},
            feature_names=feature_names,
            validation_metrics=validation_metrics,
            test_metrics=test_metrics,
            deployed_at=None,
            deployment_target=None,
            model_path=str(model_path),
            artifact_paths={},
            tags=tags or {}
        )

        # Save metadata
        metadata_path = model_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2, default=str)

        # Update registry
        if model_name not in self.metadata:
            self.metadata[model_name] = []

        self.metadata[model_name].append(metadata.to_dict())
        self._save_metadata()

        logger.info(
            "model_registered",
            model_id=model_id,
            path=str(model_path)
        )

        return model_id

    def load_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        stage: Optional[ModelStage] = None
    ) -> Tuple[BasePredictor, ModelMetadata]:
        """
        Load a model from registry.

        Args:
            model_name: Name of the model
            version: Specific version (if None, loads latest)
            stage: Load from specific stage (if None, uses version)

        Returns:
            (model, metadata) tuple
        """
        if model_name not in self.metadata:
            raise ValueError(f"Model {model_name} not found in registry")

        versions = self.metadata[model_name]

        # Filter by stage
        if stage:
            versions = [v for v in versions if v['stage'] == stage.value]
            if not versions:
                raise ValueError(f"No {stage.value} model found for {model_name}")

        # Filter by version
        if version:
            versions = [v for v in versions if v['version'] == version]
            if not versions:
                raise ValueError(f"Version {version} not found for {model_name}")

        # Get latest
        metadata_dict = max(versions, key=lambda x: x['updated_at'])
        metadata = ModelMetadata.from_dict(metadata_dict)

        # Load model
        model = joblib.load(metadata.model_path)

        logger.info(
            "model_loaded",
            model_id=metadata.model_id,
            version=metadata.version,
            stage=metadata.stage.value
        )

        return model, metadata

    def promote_model(
        self,
        model_name: str,
        version: str,
        target_stage: ModelStage
    ):
        """
        Promote a model to a different stage.

        Args:
            model_name: Model name
            version: Version to promote
            target_stage: Target deployment stage
        """
        logger.info(
            "promoting_model",
            model_name=model_name,
            version=version,
            target_stage=target_stage.value
        )

        # Find model
        if model_name not in self.metadata:
            raise ValueError(f"Model {model_name} not found")

        for i, meta in enumerate(self.metadata[model_name]):
            if meta['version'] == version:
                # Update stage
                self.metadata[model_name][i]['stage'] = target_stage.value
                self.metadata[model_name][i]['updated_at'] = datetime.now().isoformat()

                if target_stage == ModelStage.PRODUCTION:
                    self.metadata[model_name][i]['deployed_at'] = datetime.now().isoformat()

                # Update metadata file
                model_id = meta['model_id']
                model_dir = self.models_dir / model_id
                metadata_path = model_dir / "metadata.json"

                with open(metadata_path, 'w') as f:
                    json.dump(self.metadata[model_name][i], f, indent=2, default=str)

                self._save_metadata()

                logger.info(
                    "model_promoted",
                    model_id=model_id,
                    new_stage=target_stage.value
                )
                return

        raise ValueError(f"Version {version} not found for {model_name}")

    def list_models(
        self,
        model_name: Optional[str] = None,
        stage: Optional[ModelStage] = None
    ) -> List[ModelMetadata]:
        """
        List registered models.

        Args:
            model_name: Filter by model name
            stage: Filter by stage

        Returns:
            List of ModelMetadata
        """
        models = []

        model_names = [model_name] if model_name else self.metadata.keys()

        for name in model_names:
            if name not in self.metadata:
                continue

            for meta_dict in self.metadata[name]:
                if stage and meta_dict['stage'] != stage.value:
                    continue

                meta = ModelMetadata.from_dict(meta_dict)
                models.append(meta)

        return sorted(models, key=lambda x: x.updated_at, reverse=True)

    def compare_models(
        self,
        model_name: str,
        versions: List[str],
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple versions of a model.

        Args:
            model_name: Model name
            versions: List of versions to compare
            metrics: Metrics to compare (if None, uses all)

        Returns:
            Comparison dictionary
        """
        if model_name not in self.metadata:
            raise ValueError(f"Model {model_name} not found")

        comparison = {
            'model_name': model_name,
            'versions': {},
            'best': {}
        }

        # Collect metrics for each version
        for version in versions:
            meta_list = [m for m in self.metadata[model_name] if m['version'] == version]

            if not meta_list:
                logger.warning("version_not_found", version=version)
                continue

            meta = meta_list[0]
            val_metrics = meta.get('validation_metrics', {})

            comparison['versions'][version] = {
                'validation_metrics': val_metrics,
                'stage': meta['stage'],
                'created_at': meta['created_at']
            }

        # Find best for each metric
        if metrics is None:
            # Get all available metrics
            all_metrics = set()
            for v in comparison['versions'].values():
                all_metrics.update(v['validation_metrics'].keys())
            metrics = list(all_metrics)

        for metric in metrics:
            values = {}
            for version, data in comparison['versions'].items():
                if metric in data['validation_metrics']:
                    values[version] = data['validation_metrics'][metric]

            if values:
                # Determine best (lower is better for loss metrics)
                if metric in ['log_loss', 'brier_score', 'rps']:
                    best_version = min(values, key=values.get)
                else:
                    best_version = max(values, key=values.get)

                comparison['best'][metric] = {
                    'version': best_version,
                    'value': values[best_version]
                }

        return comparison

    def delete_model(
        self,
        model_name: str,
        version: str
    ):
        """
        Delete a model version.

        Args:
            model_name: Model name
            version: Version to delete
        """
        logger.warning(
            "deleting_model",
            model_name=model_name,
            version=version
        )

        if model_name not in self.metadata:
            raise ValueError(f"Model {model_name} not found")

        # Find and remove
        for i, meta in enumerate(self.metadata[model_name]):
            if meta['version'] == version:
                model_id = meta['model_id']

                # Delete files
                model_dir = self.models_dir / model_id
                if model_dir.exists():
                    import shutil
                    shutil.rmtree(model_dir)

                # Remove from metadata
                del self.metadata[model_name][i]

                # Clean up empty model entries
                if not self.metadata[model_name]:
                    del self.metadata[model_name]

                self._save_metadata()

                logger.info("model_deleted", model_id=model_id)
                return

        raise ValueError(f"Version {version} not found for {model_name}")

    def get_production_model(
        self,
        model_name: str
    ) -> Tuple[BasePredictor, ModelMetadata]:
        """
        Get current production model.

        Args:
            model_name: Model name

        Returns:
            (model, metadata) tuple
        """
        return self.load_model(model_name, stage=ModelStage.PRODUCTION)

    def _generate_model_id(self, model_name: str, version: str) -> str:
        """Generate unique model ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{model_name}_v{version}_{timestamp}"

    def _calculate_data_hash(self, data: Any) -> str:
        """Calculate hash of training data"""
        # Simple hash based on data shape and sample
        if hasattr(data, 'shape'):
            content = f"{data.shape}_{data.head().to_string() if hasattr(data, 'head') else ''}"
        else:
            content = str(data)[:1000]

        return hashlib.md5(content.encode()).hexdigest()
