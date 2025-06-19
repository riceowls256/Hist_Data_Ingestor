"""
Data Transformation Rule Engine

This module provides the core transformation engine that applies mapping rules
from YAML configuration files to convert Databento Pydantic models into
standardized internal data formats.
"""

import structlog
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Type
from decimal import Decimal
from datetime import datetime, timezone

from pydantic import BaseModel, ValidationError
import pandas as pd
import pandera.pandas as pa

from transformation.validators.databento_validators import get_validation_schema

# Import Databento models
from storage.models import (
    DatabentoOHLCVRecord,
    DatabentoTradeRecord,
    DatabentoTBBORecord,
    DatabentoStatisticsRecord,
    DATABENTO_SCHEMA_MODEL_MAPPING
)

logger = structlog.get_logger(__name__)


class TransformationError(Exception):
    """Raised when data transformation fails."""
    pass


class ValidationRuleError(Exception):
    """Raised when validation rules fail."""
    pass


class RuleEngine:
    """
    Core rule engine for transforming Databento Pydantic models using YAML configuration.

    Handles field mapping, data type conversions, validation rules, and conditional
    transformations based on declarative configuration.
    """

    def __init__(self, mapping_config_path: str):
        """
        Initialize the RuleEngine with a mapping configuration file.

        Args:
            mapping_config_path: Path to the YAML mapping configuration file

        Raises:
            FileNotFoundError: If the mapping configuration file doesn't exist
            yaml.YAMLError: If the YAML file is malformed
        """
        self.mapping_config_path = Path(mapping_config_path)
        self.config = self._load_mapping_config()
        self.schema_mappings = self.config.get('schema_mappings', {})
        self.conditional_mappings = self.config.get('conditional_mappings', {})
        self.global_settings = self.config.get('global_settings', {})

        logger.info(f"RuleEngine initialized with config: {mapping_config_path}")

    def _load_mapping_config(self) -> Dict[str, Any]:
        """Load and parse the YAML mapping configuration file."""
        try:
            with open(self.mapping_config_path, 'r') as file:
                config = yaml.safe_load(file)

            logger.info(f"Loaded mapping configuration version: {config.get('version', 'unknown')}")
            return config

        except FileNotFoundError:
            logger.error(f"Mapping configuration file not found: {self.mapping_config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise

    def _normalize_schema_name(self, schema_name: str) -> str:
        """
        Normalize user-friendly or CLI schema aliases to their canonical schema names.
        Uses the same comprehensive alias mapping as the databento adapter.
        
        Args:
            schema_name: Schema name or alias
            
        Returns:
            Canonical schema name
        """
        aliases = {
            # Definitions
            "definitions": "definition",

            # OHLCV Aliases
            "ohlcv-daily": "ohlcv-1d",
            "ohlcv-eod": "ohlcv-1d",
            "ohlcv-d": "ohlcv-1d",
            "ohlcv-h": "ohlcv-1h",
            "ohlcv-m": "ohlcv-1m",
            "ohlcv-s": "ohlcv-1s",

            # Market Depth
            "top-of-book": "tbbo",
            "quotes": "tbbo",

            # Statistics shorthand
            "stats": "statistics",

            # Other common shorthands
            "order-book": "mbp-1",
            "book": "mbp-1",
            "best-book": "mbp-1",
            "trd": "trades",
            "bbo": "tbbo",
        }
        
        input_schema = schema_name.lower()
        canonical_schema = aliases.get(input_schema, input_schema)
        
        return canonical_schema

    def get_schema_mapping(self, schema_name: str) -> Dict[str, Any]:
        """
        Get the mapping configuration for a specific schema.

        Args:
            schema_name: Name of the schema (e.g., 'ohlcv', 'trades', 'tbbo', 'statistics')

        Returns:
            Dictionary containing the schema mapping configuration

        Raises:
            KeyError: If the schema is not found in the configuration
        """
        # Normalize schema name to handle aliases
        normalized_schema = self._normalize_schema_name(schema_name)
        
        if normalized_schema not in self.schema_mappings:
            available_schemas = list(self.schema_mappings.keys())
            available_aliases = list({"definitions": "definition", "stats": "statistics", "ohlcv": "ohlcv-1d"}.keys())
            raise KeyError(f"Schema '{schema_name}' not found. Available schemas: {available_schemas}. Available aliases: {available_aliases}")

        return self.schema_mappings[normalized_schema]

    def transform_record(self,
                         record: BaseModel,
                         schema_name: str,
                         validate: bool = True) -> Dict[str, Any]:
        """
        Transform a Databento Pydantic record using the configured mapping rules.

        Args:
            record: Databento Pydantic model instance to transform
            schema_name: Target schema name for transformation
            validate: Whether to apply validation rules

        Returns:
            Dictionary containing the transformed data ready for storage

        Raises:
            TransformationError: If transformation fails
            ValidationRuleError: If validation rules fail
            KeyError: If schema mapping is not found

        Example:
            >>> from storage.models import DatabentoOHLCVRecord
            >>> from datetime import datetime, timezone
            >>> from decimal import Decimal
            >>>
            >>> engine = RuleEngine('configs/mapping_configs/databento_mappings.yaml')
            >>>
            >>> # Create a sample OHLCV record
            >>> record = DatabentoOHLCVRecord(
            ...     ts_event=datetime(2024, 1, 15, 9, 30, tzinfo=timezone.utc),
            ...     instrument_id=123456,
            ...     symbol='ES.c.0',
            ...     open=Decimal('4800.50'),
            ...     high=Decimal('4805.25'),
            ...     low=Decimal('4798.75'),
            ...     close=Decimal('4802.00'),
            ...     volume=1000
            ... )
            >>>
            >>> # Transform for TimescaleDB storage
            >>> transformed = engine.transform_record(record, 'ohlcv')
            >>> print(f"Transformed fields: {list(transformed.keys())}")
            >>> print(f"Close price: {transformed['close']}")
        """
        try:
            mapping_config = self.get_schema_mapping(schema_name)

            # Verify source model matches expected type
            expected_model = mapping_config.get('source_model')
            actual_model = record.__class__.__name__

            if actual_model != expected_model:
                raise TransformationError(
                    f"Model mismatch: expected {expected_model}, got {actual_model}"
                )

            # Apply field mappings
            transformed_data = self._apply_field_mappings(record, mapping_config)

            # Apply conditional mappings (for complex scenarios like statistics)
            if schema_name in self.conditional_mappings:
                transformed_data = self._apply_conditional_mappings(
                    transformed_data, schema_name, record
                )

            # Apply default values for missing fields
            transformed_data = self._apply_defaults(transformed_data, mapping_config)

            # Apply validation rules if enabled
            if validate:
                self._validate_transformed_data(transformed_data, mapping_config, schema_name)

            # Apply global transformations
            transformed_data = self._apply_global_transformations(transformed_data)

            logger.debug(f"Successfully transformed {actual_model} record for schema {schema_name}")
            return transformed_data

        except Exception as e:
            logger.error(f"Transformation failed for {schema_name}: {str(e)}")
            raise TransformationError(f"Failed to transform record: {str(e)}") from e

    def _apply_field_mappings(self, record: BaseModel, mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply direct field mappings from source to target schema."""
        field_mappings = mapping_config.get('field_mappings', {})
        transformed_data = {}

        for source_field, target_field in field_mappings.items():
            # Get value from source record
            if hasattr(record, source_field):
                value = getattr(record, source_field)

                # Handle None values
                if value is not None:
                    # Apply type-specific transformations
                    transformed_value = self._transform_field_value(value, source_field)
                    transformed_data[target_field] = transformed_value
                else:
                    transformed_data[target_field] = None
            else:
                logger.warning(f"Source field '{source_field}' not found in record")
                transformed_data[target_field] = None

        return transformed_data

    def _apply_conditional_mappings(self,
                                    transformed_data: Dict[str, Any],
                                    schema_name: str,
                                    original_record: BaseModel) -> Dict[str, Any]:
        """Apply conditional field mappings based on record attributes."""
        conditional_config = self.conditional_mappings.get(schema_name, {})

        # Handle statistics conditional mappings based on stat_type
        if schema_name == 'statistics' and 'stat_type_mappings' in conditional_config:
            stat_type = getattr(original_record, 'stat_type', None)
            stat_mappings = conditional_config['stat_type_mappings']

            # Get the appropriate mapping for this stat_type
            mapping = stat_mappings.get(stat_type, stat_mappings.get('default', {}))

            if mapping:
                primary_field = mapping.get('primary_field')
                target_field = mapping.get('target_field')

                if primary_field and target_field and hasattr(original_record, primary_field):
                    value = getattr(original_record, primary_field)
                    if value is not None:
                        transformed_data[target_field] = self._transform_field_value(value, primary_field)

        return transformed_data

    def _apply_defaults(self, transformed_data: Dict[str, Any], mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply default values for missing or null fields."""
        defaults = mapping_config.get('defaults', {})

        for field, default_value in defaults.items():
            if field not in transformed_data or transformed_data[field] is None:
                transformed_data[field] = default_value

        return transformed_data

    def _validate_transformed_data(self, data: Dict[str, Any], mapping_config: Dict[str, Any], schema_name: str) -> None:
        """
        Validate transformed data using Pandera schemas.
        This replaces the old rule-based validation.
        
        Args:
            data: The transformed data to validate
            mapping_config: The mapping configuration
            schema_name: The schema name for validation
        """

        validation_schema = get_validation_schema(schema_name)
        if not validation_schema:
            logger.warning(f"No Pandera validation schema found for '{schema_name}', skipping.")
            return

        # Bind schema context to logger for all validation-related logs
        validation_logger = logger.bind(schema_name=schema_name, validation_type="pandera")

        try:
            # Pandera expects a DataFrame
            df = pd.DataFrame([data])
            validation_schema.validate(df, lazy=True)
        except pa.errors.SchemaErrors as err:
            validation_logger.error(
                "Pandera validation failed",
                errors=err.failure_cases.to_dict(orient="records"),
                data=data
            )
            # We can decide to quarantine here or let the caller handle it.
            # For now, we raise a specific error.
            raise ValidationRuleError(f"Pandera validation failed: {err.failure_cases}")
        except Exception as e:
            validation_logger.error(
                "An unexpected error occurred during Pandera validation",
                error=str(e)
            )
            raise TransformationError(f"Unexpected validation error: {e}")


    def _transform_field_value(self, value: Any, field_name: str) -> Any:
        """Apply field-specific transformations."""
        # Handle Decimal precision for price fields
        if isinstance(value, Decimal):
            precision = self.global_settings.get('price_precision', 8)
            return round(value, precision)

        # Handle datetime timezone normalization
        if isinstance(value, datetime):
            # Ensure timezone-aware datetime in UTC
            if value.tzinfo is None:
                # Naive datetime - assume it's UTC and make it timezone-aware
                logger.warning(f"Converting naive datetime to UTC: {value}")
                return value.replace(tzinfo=timezone.utc)
            else:
                # Already timezone-aware - convert to UTC if needed
                return value.astimezone(timezone.utc)
            return value

        # Return value as-is for other types
        return value

    def _apply_global_transformations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply global transformations to the entire data dictionary."""
        # Apply timezone normalization if configured
        target_timezone = self.global_settings.get('timezone_normalization')
        if target_timezone == 'UTC':
            for key, value in data.items():
                if isinstance(value, datetime):
                    # Ensure all timestamps are timezone-aware UTC
                    if value.tzinfo is None:
                        logger.warning(f"Converting naive datetime to UTC in field '{key}': {value}")
                        data[key] = value.replace(tzinfo=timezone.utc)
                    else:
                        # Convert to UTC if needed
                        data[key] = value.astimezone(timezone.utc)

        return data

    def transform_batch(self,
                        records: List[BaseModel],
                        schema_name: str,
                        validate: bool = True) -> List[Dict[str, Any]]:
        """
        Transform a batch of Databento Pydantic records using the configured mapping rules.

        Args:
            records: List of Databento Pydantic model instances to transform
            schema_name: Target schema name for transformation
            validate: Whether to apply validation rules

        Returns:
            List of dictionaries containing the transformed data
        """
        # Bind schema context for all batch operations
        batch_logger = logger.bind(schema_name=schema_name, operation="batch_transform", batch_size=len(records))

        transformed_batch = []

        for record in records:
            try:
                transformed_record = self.transform_record(
                    record, schema_name, validate=False  # Validation will be done on the batch
                )
                transformed_batch.append(transformed_record)
            except TransformationError as e:
                batch_logger.error("Failed to transform record in batch", error=str(e))
                # Decide on error handling: skip record, add to error list, etc.
                continue

        if validate and transformed_batch:
            # Convert list of dicts to DataFrame for batch validation
            df = pd.DataFrame(transformed_batch)
            
            # Fix nullable integer columns that pandas infers as float64
            # This prevents Pandera coercion errors when validating nullable int columns
            if 'trade_count' in df.columns:
                df['trade_count'] = df['trade_count'].astype('Int64')

            validation_schema = get_validation_schema(schema_name)
            if validation_schema:
                try:
                    validation_schema.validate(df, lazy=True)
                except pa.errors.SchemaErrors as err:
                    batch_logger.error(
                        "Pandera batch validation failed",
                        num_failures=len(err.failure_cases),
                        failure_details=err.failure_cases.to_dict(orient="records")
                    )
                    # For now, we raise an error. In a real pipeline, you might
                    # filter out the bad records and quarantine them.
                    raise ValidationRuleError(f"Batch validation failed for {len(err.failure_cases)} records.")
            else:
                batch_logger.warning("No Pandera validation schema found, skipping batch validation.")

        return transformed_batch

    def get_supported_schemas(self) -> List[str]:
        """Get list of supported schema names."""
        return list(self.schema_mappings.keys())

    def get_target_schema_for_model(self, model_class_name: str) -> Optional[str]:
        """
        Get the target schema name for a given Databento model class.

        Args:
            model_class_name: Name of the Databento model class

        Returns:
            Target schema name or None if not found
        """
        for schema_name, config in self.schema_mappings.items():
            if config.get('source_model') == model_class_name:
                return schema_name
        return None


def create_rule_engine(mapping_config_path: Optional[str] = None) -> RuleEngine:
    """
    Factory function to create a RuleEngine instance.

    Args:
        mapping_config_path: Path to mapping config file.
                           Defaults to databento_mappings.yaml in mapping_configs/

    Returns:
        Configured RuleEngine instance
    """
    if mapping_config_path is None:
        # Default to databento mappings
        base_path = Path(__file__).parent.parent / "mapping_configs"
        mapping_config_path = base_path / "databento_mappings.yaml"

    return RuleEngine(str(mapping_config_path))


# Export main classes and functions
__all__ = [
    'RuleEngine',
    'TransformationError',
    'ValidationRuleError',
    'create_rule_engine'
]
