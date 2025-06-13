"""
Data Transformation Rule Engine

This module provides the core transformation engine that applies mapping rules
from YAML configuration files to convert Databento Pydantic models into
standardized internal data formats.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Type
from decimal import Decimal
from datetime import datetime, timezone

from pydantic import BaseModel, ValidationError

# Import Databento models
from src.storage.models import (
    DatabentoOHLCVRecord,
    DatabentoTradeRecord, 
    DatabentoTBBORecord,
    DatabentoStatisticsRecord,
    DATABENTO_SCHEMA_MODEL_MAPPING
)

logger = logging.getLogger(__name__)


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
        if schema_name not in self.schema_mappings:
            available_schemas = list(self.schema_mappings.keys())
            raise KeyError(f"Schema '{schema_name}' not found. Available schemas: {available_schemas}")
            
        return self.schema_mappings[schema_name]
    
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
                self._validate_transformed_data(transformed_data, mapping_config)
            
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
    
    def _validate_transformed_data(self, data: Dict[str, Any], mapping_config: Dict[str, Any]) -> None:
        """Apply validation rules to transformed data."""
        transformations = mapping_config.get('transformations', {})
        
        for rule_name, rule_config in transformations.items():
            try:
                self._apply_validation_rule(data, rule_config, rule_name)
            except ValidationRuleError as e:
                if not self.global_settings.get('skip_validation_errors', False):
                    raise
                else:
                    logger.warning(f"Validation rule '{rule_name}' failed but continuing: {e}")
    
    def _apply_validation_rule(self, data: Dict[str, Any], rule_config: Dict[str, Any], rule_name: str) -> None:
        """Apply a single validation rule to the data."""
        rule = rule_config.get('rule')
        fields = rule_config.get('fields', [])
        
        if fields:
            # Field-specific validation
            for field in fields:
                if field in data:
                    value = data[field]
                    if not self._evaluate_rule(value, rule):
                        raise ValidationRuleError(
                            f"Validation failed for field '{field}' in rule '{rule_name}': {rule}"
                        )
        else:
            # Global rule evaluation
            if not self._evaluate_data_rule(data, rule):
                raise ValidationRuleError(f"Global validation failed for rule '{rule_name}': {rule}")
    
    def _evaluate_rule(self, value: Any, rule: str) -> bool:
        """Evaluate a validation rule against a single value."""
        try:
            # Create evaluation context with value and null alias
            eval_context = {
                'value': value,
                'null': None  # Allow 'null' syntax in rules
            }
            
            # Evaluate the rule with proper context
            return eval(rule, {"__builtins__": {}}, eval_context)
            
        except Exception as e:
            logger.error(f"Error evaluating rule '{rule}' with value {value}: {e}")
            return False
    
    def _evaluate_data_rule(self, data: Dict[str, Any], rule: str) -> bool:
        """Evaluate a validation rule against the entire data dictionary."""
        try:
            # Create a safe evaluation context from the data dictionary.
            # This ensures that keys with 'None' values are available for 'is null' checks.
            eval_context = data.copy()
            eval_context['null'] = None  # Allow 'null' syntax in rules
            
            # Evaluate the rule within the context of the data.
            # The __builtins__ are restricted for security.
            return eval(rule, {"__builtins__": {}}, eval_context)
            
        except Exception as e:
            logger.error(f"Error evaluating data rule '{rule}' with data {data}: {e}")
            return False
    
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
        Transform a batch of records efficiently.
        
        Args:
            records: List of Databento Pydantic model instances
            schema_name: Target schema name for transformation
            validate: Whether to apply validation rules
            
        Returns:
            List of transformed data dictionaries
            
        Raises:
            TransformationError: If any transformation fails
        """
        transformed_records = []
        failed_records = []
        
        for i, record in enumerate(records):
            try:
                transformed_data = self.transform_record(record, schema_name, validate)
                transformed_records.append(transformed_data)
            except (TransformationError, ValidationRuleError) as e:
                logger.error(f"Failed to transform record {i}: {e}")
                failed_records.append((i, record, str(e)))
                
                # Decide whether to continue or fail fast
                if not self.global_settings.get('skip_validation_errors', False):
                    raise TransformationError(f"Batch transformation failed at record {i}: {e}")
        
        if failed_records:
            logger.warning(f"Batch transformation completed with {len(failed_records)} failed records")
        
        return transformed_records
    
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
