"""
Schema Validation - Validate scraped data against schemas
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import re
import structlog

logger = structlog.get_logger()


class FieldType(Enum):
    """Field data types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    EMAIL = "email"
    URL = "url"
    LIST = "list"
    DICT = "dict"


@dataclass
class FieldSchema:
    """Schema for a single field"""
    name: str
    type: FieldType
    required: bool = False
    nullable: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    choices: Optional[List[Any]] = None
    default: Optional[Any] = None


@dataclass
class ValidationError:
    """Validation error details"""
    field: str
    error_type: str
    message: str
    value: Any = None


@dataclass
class ValidationResult:
    """Result of validation"""
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[str]
    validated_data: Optional[Dict] = None

    def add_error(self, field: str, error_type: str, message: str, value: Any = None):
        """Add validation error"""
        self.errors.append(ValidationError(field, error_type, message, value))
        self.is_valid = False

    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)


class SchemaValidator:
    """
    Validate data against defined schemas.

    Usage:
        schema = SchemaValidator({
            'match_id': FieldSchema('match_id', FieldType.STRING, required=True),
            'home_score': FieldSchema('home_score', FieldType.INTEGER, min_value=0),
        })
        result = schema.validate(data)
    """

    def __init__(self, schema: Dict[str, FieldSchema]):
        self.schema = schema

    def validate(self, data: Dict[str, Any], strict: bool = False) -> ValidationResult:
        """
        Validate data against schema.

        Args:
            data: Data to validate
            strict: If True, reject extra fields not in schema

        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[], validated_data={})

        # Check required fields
        for field_name, field_schema in self.schema.items():
            if field_schema.required and field_name not in data:
                result.add_error(
                    field_name,
                    'required',
                    f'Required field "{field_name}" is missing'
                )
                continue

            # Get value
            value = data.get(field_name, field_schema.default)

            # Check nullable
            if value is None:
                if not field_schema.nullable:
                    result.add_error(
                        field_name,
                        'nullable',
                        f'Field "{field_name}" cannot be null',
                        value
                    )
                continue

            # Validate field
            validated_value = self._validate_field(field_name, value, field_schema, result)
            if validated_value is not None or value is None:
                result.validated_data[field_name] = validated_value

        # Check for extra fields in strict mode
        if strict:
            for field_name in data:
                if field_name not in self.schema:
                    result.add_warning(f'Extra field "{field_name}" not in schema')

        return result

    def _validate_field(
        self,
        field_name: str,
        value: Any,
        schema: FieldSchema,
        result: ValidationResult
    ) -> Any:
        """Validate single field"""

        # Type validation
        if schema.type == FieldType.STRING:
            if not isinstance(value, str):
                result.add_error(field_name, 'type', f'Expected string, got {type(value).__name__}', value)
                return None

            # Length validation
            if schema.min_length and len(value) < schema.min_length:
                result.add_error(
                    field_name,
                    'min_length',
                    f'String length {len(value)} < minimum {schema.min_length}',
                    value
                )

            if schema.max_length and len(value) > schema.max_length:
                result.add_error(
                    field_name,
                    'max_length',
                    f'String length {len(value)} > maximum {schema.max_length}',
                    value
                )

            # Pattern validation
            if schema.pattern and not re.match(schema.pattern, value):
                result.add_error(
                    field_name,
                    'pattern',
                    f'Value does not match pattern {schema.pattern}',
                    value
                )

        elif schema.type in (FieldType.INTEGER, FieldType.FLOAT):
            try:
                if schema.type == FieldType.INTEGER:
                    value = int(value)
                else:
                    value = float(value)
            except (ValueError, TypeError):
                result.add_error(
                    field_name,
                    'type',
                    f'Cannot convert to {schema.type.value}',
                    value
                )
                return None

            # Range validation
            if schema.min_value is not None and value < schema.min_value:
                result.add_error(
                    field_name,
                    'min_value',
                    f'Value {value} < minimum {schema.min_value}',
                    value
                )

            if schema.max_value is not None and value > schema.max_value:
                result.add_error(
                    field_name,
                    'max_value',
                    f'Value {value} > maximum {schema.max_value}',
                    value
                )

        elif schema.type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                if value in ('true', 'True', '1', 1):
                    value = True
                elif value in ('false', 'False', '0', 0):
                    value = False
                else:
                    result.add_error(
                        field_name,
                        'type',
                        'Cannot convert to boolean',
                        value
                    )
                    return None

        elif schema.type == FieldType.EMAIL:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, str(value)):
                result.add_error(
                    field_name,
                    'email',
                    'Invalid email format',
                    value
                )

        elif schema.type == FieldType.URL:
            url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
            if not re.match(url_pattern, str(value)):
                result.add_error(
                    field_name,
                    'url',
                    'Invalid URL format',
                    value
                )

        # Choices validation
        if schema.choices and value not in schema.choices:
            result.add_error(
                field_name,
                'choices',
                f'Value must be one of {schema.choices}',
                value
            )

        return value


# Predefined schemas for common data types
MATCH_SCHEMA = SchemaValidator({
    'external_id': FieldSchema('external_id', FieldType.STRING, required=True),
    'source': FieldSchema('source', FieldType.STRING, required=True),
    'home_team': FieldSchema('home_team', FieldType.STRING, required=True, min_length=1),
    'away_team': FieldSchema('away_team', FieldType.STRING, required=True, min_length=1),
    'home_score': FieldSchema('home_score', FieldType.INTEGER, nullable=True, min_value=0),
    'away_score': FieldSchema('away_score', FieldType.INTEGER, nullable=True, min_value=0),
    'match_date': FieldSchema('match_date', FieldType.STRING, nullable=True),
    'status': FieldSchema('status', FieldType.STRING, choices=['scheduled', 'live', 'finished', 'postponed', 'cancelled']),
    'league': FieldSchema('league', FieldType.STRING),
    'country': FieldSchema('country', FieldType.STRING),
})

ODDS_SCHEMA = SchemaValidator({
    'match_id': FieldSchema('match_id', FieldType.STRING, required=True),
    'bookmaker': FieldSchema('bookmaker', FieldType.STRING, required=True),
    'home_odds': FieldSchema('home_odds', FieldType.FLOAT, required=True, min_value=1.0),
    'draw_odds': FieldSchema('draw_odds', FieldType.FLOAT, required=True, min_value=1.0),
    'away_odds': FieldSchema('away_odds', FieldType.FLOAT, required=True, min_value=1.0),
    'timestamp': FieldSchema('timestamp', FieldType.STRING, required=True),
})
