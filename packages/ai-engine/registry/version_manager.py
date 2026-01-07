"""
Version Manager - Semantic versioning for models
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class SemanticVersion:
    """
    Semantic version (MAJOR.MINOR.PATCH).

    - MAJOR: Breaking changes (new training algorithm, architecture change)
    - MINOR: New features (additional features, improved preprocessing)
    - PATCH: Bug fixes, minor improvements
    """
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __lt__(self, other: 'SemanticVersion') -> bool:
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: 'SemanticVersion') -> bool:
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __gt__(self, other: 'SemanticVersion') -> bool:
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: 'SemanticVersion') -> bool:
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    def __eq__(self, other: 'SemanticVersion') -> bool:
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)

    @classmethod
    def parse(cls, version_str: str) -> 'SemanticVersion':
        """Parse version string"""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version_str)
        if not match:
            raise ValueError(f"Invalid version string: {version_str}")

        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3))
        )

    def bump_major(self) -> 'SemanticVersion':
        """Bump major version"""
        return SemanticVersion(self.major + 1, 0, 0)

    def bump_minor(self) -> 'SemanticVersion':
        """Bump minor version"""
        return SemanticVersion(self.major, self.minor + 1, 0)

    def bump_patch(self) -> 'SemanticVersion':
        """Bump patch version"""
        return SemanticVersion(self.major, self.minor, self.patch + 1)


class VersionManager:
    """
    Manage model versions using semantic versioning.

    Determines appropriate version bumps based on changes.
    """

    def __init__(self, registry):
        """
        Args:
            registry: ModelRegistry instance
        """
        self.registry = registry

    def get_latest_version(self, model_name: str) -> Optional[SemanticVersion]:
        """Get latest version for a model"""
        models = self.registry.list_models(model_name=model_name)

        if not models:
            return None

        versions = [SemanticVersion.parse(m.version) for m in models]
        return max(versions)

    def suggest_next_version(
        self,
        model_name: str,
        change_type: str = 'patch'  # 'major', 'minor', or 'patch'
    ) -> SemanticVersion:
        """
        Suggest next version number.

        Args:
            model_name: Model name
            change_type: Type of change ('major', 'minor', 'patch')

        Returns:
            Next semantic version
        """
        latest = self.get_latest_version(model_name)

        if latest is None:
            # First version
            return SemanticVersion(1, 0, 0)

        if change_type == 'major':
            return latest.bump_major()
        elif change_type == 'minor':
            return latest.bump_minor()
        else:  # patch
            return latest.bump_patch()

    def auto_version(
        self,
        model_name: str,
        old_metrics: Optional[dict] = None,
        new_metrics: Optional[dict] = None,
        hyperparams_changed: bool = False,
        architecture_changed: bool = False,
        features_changed: bool = False
    ) -> SemanticVersion:
        """
        Automatically determine version based on changes.

        Rules:
        - Major bump: Architecture changed
        - Minor bump: Hyperparameters or features changed
        - Patch bump: Only metrics improved (same config)

        Args:
            model_name: Model name
            old_metrics: Previous metrics
            new_metrics: New metrics
            hyperparams_changed: Whether hyperparameters changed
            architecture_changed: Whether model architecture changed
            features_changed: Whether feature set changed

        Returns:
            Next semantic version
        """
        if architecture_changed:
            change_type = 'major'
            logger.info("version_bump", type='major', reason='architecture_changed')

        elif hyperparams_changed or features_changed:
            change_type = 'minor'
            reason = []
            if hyperparams_changed:
                reason.append('hyperparameters')
            if features_changed:
                reason.append('features')
            logger.info("version_bump", type='minor', reason=','.join(reason))

        else:
            change_type = 'patch'
            logger.info("version_bump", type='patch', reason='metrics_only')

        return self.suggest_next_version(model_name, change_type)

    def is_compatible(
        self,
        version_a: str,
        version_b: str,
        compatibility_level: str = 'minor'  # 'major' or 'minor'
    ) -> bool:
        """
        Check if two versions are compatible.

        Args:
            version_a: First version
            version_b: Second version
            compatibility_level: 'major' (1.x.x == 1.y.z) or 'minor' (1.2.x == 1.2.y)

        Returns:
            True if compatible
        """
        v_a = SemanticVersion.parse(version_a)
        v_b = SemanticVersion.parse(version_b)

        if compatibility_level == 'major':
            return v_a.major == v_b.major
        else:  # minor
            return v_a.major == v_b.major and v_a.minor == v_b.minor

    def get_version_range(
        self,
        model_name: str,
        min_version: Optional[str] = None,
        max_version: Optional[str] = None
    ) -> list:
        """
        Get all versions within a range.

        Args:
            model_name: Model name
            min_version: Minimum version (inclusive)
            max_version: Maximum version (inclusive)

        Returns:
            List of ModelMetadata within range
        """
        models = self.registry.list_models(model_name=model_name)

        filtered = []
        for model in models:
            version = SemanticVersion.parse(model.version)

            if min_version:
                min_v = SemanticVersion.parse(min_version)
                if version < min_v:
                    continue

            if max_version:
                max_v = SemanticVersion.parse(max_version)
                if version > max_v:
                    continue

            filtered.append(model)

        return sorted(filtered, key=lambda x: SemanticVersion.parse(x.version))


def compare_hyperparameters(
    old_params: dict,
    new_params: dict
) -> dict:
    """
    Compare two hyperparameter sets.

    Returns:
        Dictionary with changes
    """
    changes = {
        'added': {},
        'removed': {},
        'modified': {}
    }

    # Find added
    for key in new_params:
        if key not in old_params:
            changes['added'][key] = new_params[key]

    # Find removed
    for key in old_params:
        if key not in new_params:
            changes['removed'][key] = old_params[key]

    # Find modified
    for key in old_params:
        if key in new_params and old_params[key] != new_params[key]:
            changes['modified'][key] = {
                'old': old_params[key],
                'new': new_params[key]
            }

    return changes
