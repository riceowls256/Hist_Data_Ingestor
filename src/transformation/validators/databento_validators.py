"""
Custom validation functions and Pandera schemas for Databento data.

This module provides business logic validation for Databento data after it has
been transformed into the standardized internal model. It complements the initial
Pydantic validation by enforcing domain-specific rules.
"""

import pandera.pandas as pa
from pandera.typing import DataFrame, Series
from decimal import Decimal
from datetime import datetime, timezone
import pandas as pd
from enum import Enum
from typing import Optional, Union
import re

# ========================================================================================
# Validation Severity Levels
# ========================================================================================

class ValidationSeverity(Enum):
    """Validation severity levels for different types of validation failures."""
    ERROR = "ERROR"      # Critical failures that prevent data storage
    WARNING = "WARNING"  # Data quality issues that should be flagged
    INFO = "INFO"        # Informational notices about data characteristics

# ========================================================================================
# Custom Business Logic Validators
# ========================================================================================

def validate_timestamp_timezone_aware(timestamp: datetime) -> bool:
    """Validate that timestamp is timezone-aware and within reasonable range."""
    if timestamp is None:
        return True  # Allow None values
    
    # Check if timezone-aware
    if timestamp.tzinfo is None:
        return False
    
    # Check reasonable range (not too far in past/future)
    now = datetime.now(timezone.utc)
    min_date = datetime(1970, 1, 1, tzinfo=timezone.utc)  # Unix epoch
    max_date = now.replace(year=now.year + 20)  # 20 years in future (more lenient)
    
    return min_date <= timestamp <= max_date

def validate_symbol_format(symbol: str) -> bool:
    """Validate symbol format patterns (non-empty, expected format)."""
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Remove whitespace
    symbol = symbol.strip()
    if not symbol:
        return False
    
    # More lenient symbol format validation (alphanumeric, dots, underscores, hyphens allowed)
    pattern = r'^[A-Za-z0-9._-]+$'  # Allow lowercase too
    return bool(re.match(pattern, symbol))

def validate_cross_field_consistency_ohlcv(df: pd.DataFrame) -> pd.Series:
    """Cross-field consistency validation for OHLCV data."""
    conditions = []
    
    # High should be >= all other prices
    if 'high' in df.columns and 'open' in df.columns:
        conditions.append(df['high'] >= df['open'])
    if 'high' in df.columns and 'close' in df.columns:
        conditions.append(df['high'] >= df['close'])
    if 'high' in df.columns and 'low' in df.columns:
        conditions.append(df['high'] >= df['low'])
    
    # Low should be <= all other prices
    if 'low' in df.columns and 'open' in df.columns:
        conditions.append(df['low'] <= df['open'])
    if 'low' in df.columns and 'close' in df.columns:
        conditions.append(df['low'] <= df['close'])
    
    # Combine all conditions
    if conditions:
        return pd.concat(conditions, axis=1).all(axis=1)
    else:
        return pd.Series([True] * len(df), index=df.index)

def validate_cross_field_consistency_trade(df: pd.DataFrame) -> pd.Series:
    """Cross-field consistency validation for Trade data."""
    conditions = []
    
    # ts_event should be <= ts_recv if both present
    if 'ts_event' in df.columns and 'ts_recv' in df.columns:
        # Handle None values gracefully
        mask = df['ts_event'].notna() & df['ts_recv'].notna()
        condition = pd.Series([True] * len(df), index=df.index)
        condition[mask] = df.loc[mask, 'ts_event'] <= df.loc[mask, 'ts_recv']
        conditions.append(condition)
    
    # Combine all conditions
    if conditions:
        return pd.concat(conditions, axis=1).all(axis=1)
    else:
        return pd.Series([True] * len(df), index=df.index)

# ========================================================================================
# Base Schema with common checks
# ========================================================================================

class BaseDatabentoSchema(pa.DataFrameModel):
    """Base schema with common checks for all Databento records."""
    instrument_id: Series[int] = pa.Field(gt=0, coerce=True)
    ts_event: Series[datetime] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = True

# ========================================================================================
# OHLCV Validation Schema
# ========================================================================================

class OHLCVSchema(BaseDatabentoSchema):
    """Validation schema for OHLCV data with business logic checks."""
    open: Series[float] = pa.Field(gt=0, coerce=True)
    high: Series[float] = pa.Field(gt=0, coerce=True)
    low: Series[float] = pa.Field(gt=0, coerce=True)
    close: Series[float] = pa.Field(gt=0, coerce=True)
    volume: Series[int] = pa.Field(ge=0, coerce=True)

    @pa.dataframe_check
    def check_ohlc_logic(cls, df: pd.DataFrame) -> pd.Series:
        """Validate OHLC price relationships."""
        return validate_cross_field_consistency_ohlcv(df)

    @pa.dataframe_check
    def check_timestamps(cls, df: pd.DataFrame) -> pd.Series:
        """Validate timestamp timezone awareness."""
        return df['ts_event'].apply(validate_timestamp_timezone_aware)

# ========================================================================================
# Trade Validation Schema
# ========================================================================================

class TradeSchema(BaseDatabentoSchema):
    """Validation schema for Trade data with business logic checks."""
    price: Series[float] = pa.Field(gt=0, coerce=True)
    size: Series[int] = pa.Field(gt=0, coerce=True)
    side: Series[str] = pa.Field(nullable=True)  # Can be None

    @pa.dataframe_check
    def check_side_values(cls, df: pd.DataFrame) -> pd.Series:
        """Validate side codes are valid."""
        valid_sides = {'A', 'B', 'N', None}
        return df['side'].isin(valid_sides) | df['side'].isna()

    @pa.dataframe_check
    def check_cross_field_consistency(cls, df: pd.DataFrame) -> pd.Series:
        """Validate cross-field consistency for trades."""
        return validate_cross_field_consistency_trade(df)

    @pa.dataframe_check
    def check_timestamps(cls, df: pd.DataFrame) -> pd.Series:
        """Validate timestamp timezone awareness."""
        return df['ts_event'].apply(validate_timestamp_timezone_aware)

# ========================================================================================
# TBBO Validation Schema
# ========================================================================================

class TBBOSchema(BaseDatabentoSchema):
    """Validation schema for TBBO (Top of Book) data."""
    bid_px: Series[float] = pa.Field(gt=0, nullable=True, coerce=True)
    ask_px: Series[float] = pa.Field(gt=0, nullable=True, coerce=True)
    bid_sz: Series[float] = pa.Field(ge=0, nullable=True, coerce=True)  # Use float for nullable
    ask_sz: Series[float] = pa.Field(ge=0, nullable=True, coerce=True)  # Use float for nullable

    @pa.dataframe_check
    def check_bid_ask_spread(cls, df: pd.DataFrame) -> pd.Series:
        """Validate bid <= ask when both are present."""
        # Only check when both bid and ask are not null
        mask = df['bid_px'].notna() & df['ask_px'].notna()
        condition = pd.Series([True] * len(df), index=df.index)
        condition[mask] = df.loc[mask, 'bid_px'] <= df.loc[mask, 'ask_px']
        return condition

    @pa.dataframe_check
    def check_timestamps(cls, df: pd.DataFrame) -> pd.Series:
        """Validate timestamp timezone awareness."""
        return df['ts_event'].apply(validate_timestamp_timezone_aware)

# ========================================================================================
# Statistics Validation Schema
# ========================================================================================

class StatisticsSchema(BaseDatabentoSchema):
    """Validation schema for Statistics data."""
    stat_type: Series[int] = pa.Field(ge=1, le=255, coerce=True)  # Valid stat type codes
    stat_value: Series[float] = pa.Field(nullable=True, coerce=True)
    update_action: Series[str] = pa.Field(nullable=True)

    @pa.dataframe_check
    def check_stat_type_codes(cls, df: pd.DataFrame) -> pd.Series:
        """Validate stat_type codes are within expected range."""
        # Common CME stat types: 1-10 are standard, but allow broader range
        return (df['stat_type'] >= 1) & (df['stat_type'] <= 255)

    @pa.dataframe_check
    def check_stat_value_consistency(cls, df: pd.DataFrame) -> pd.Series:
        """Validate stat_value consistency based on stat_type."""
        # For price-related stats (1-5), values should be positive
        price_stat_types = {1, 2, 4, 5, 8, 9, 10}  # Opening, Settlement, High, Low, etc.
        mask = df['stat_type'].isin(price_stat_types) & df['stat_value'].notna()
        condition = pd.Series([True] * len(df), index=df.index)
        condition[mask] = df.loc[mask, 'stat_value'] > 0
        return condition

    @pa.dataframe_check
    def check_timestamps(cls, df: pd.DataFrame) -> pd.Series:
        """Validate timestamp timezone awareness."""
        return df['ts_event'].apply(validate_timestamp_timezone_aware)

# ========================================================================================
# Definition Validation Schema
# ========================================================================================

class DefinitionSchema(BaseDatabentoSchema):
    """Validation schema for Definition data."""
    symbol: Series[str] = pa.Field(nullable=False)
    expiration: Series[datetime] = pa.Field(nullable=True)
    activation: Series[datetime] = pa.Field(nullable=True)
    min_price_increment: Series[float] = pa.Field(gt=0, nullable=True, coerce=True)
    unit_of_measure_qty: Series[float] = pa.Field(gt=0, nullable=True, coerce=True)
    instrument_class: Series[str] = pa.Field(nullable=True)

    @pa.dataframe_check
    def check_symbol_format(cls, df: pd.DataFrame) -> pd.Series:
        """Validate symbol format."""
        return df['symbol'].apply(validate_symbol_format)

    @pa.dataframe_check
    def check_expiration_activation(cls, df: pd.DataFrame) -> pd.Series:
        """Validate expiration > activation when both are present."""
        mask = df['expiration'].notna() & df['activation'].notna()
        condition = pd.Series([True] * len(df), index=df.index)
        condition[mask] = df.loc[mask, 'expiration'] > df.loc[mask, 'activation']
        return condition

    @pa.dataframe_check
    def check_instrument_class_values(cls, df: pd.DataFrame) -> pd.Series:
        """Validate instrument_class values."""
        valid_classes = {'Future', 'Option', 'Spread', 'Stock', 'Index', 'FX'}
        return df['instrument_class'].isin(valid_classes) | df['instrument_class'].isna()

    @pa.dataframe_check
    def check_timestamps(cls, df: pd.DataFrame) -> pd.Series:
        """Validate timestamp timezone awareness."""
        return df['ts_event'].apply(validate_timestamp_timezone_aware)

# ========================================================================================
# Schema Dispatcher
# ========================================================================================

def get_validation_schema(schema_name: str) -> pa.DataFrameModel:
    """
    Get the appropriate validation schema based on schema name.
    
    Args:
        schema_name: The schema name from mapping configuration
        
    Returns:
        The corresponding Pandera DataFrameModel schema
        
    Raises:
        ValueError: If schema_name is not recognized
    """
    schema_mapping = {
        "ohlcv-1d": OHLCVSchema,
        "ohlcv-1h": OHLCVSchema,
        "ohlcv-1m": OHLCVSchema,
        "trades": TradeSchema,
        "tbbo": TBBOSchema,
        "statistics": StatisticsSchema,
        "definition": DefinitionSchema,
    }
    
    if schema_name not in schema_mapping:
        raise ValueError(f"Unknown schema name: {schema_name}. Available schemas: {list(schema_mapping.keys())}")
    
    return schema_mapping[schema_name]

def validate_dataframe(df: pd.DataFrame, schema_name: str, severity: ValidationSeverity = ValidationSeverity.ERROR) -> pd.DataFrame:
    """
    Validate a DataFrame using the appropriate schema.
    
    Args:
        df: DataFrame to validate
        schema_name: Schema name to use for validation
        severity: Validation severity level
        
    Returns:
        Validated DataFrame
        
    Raises:
        pa.errors.SchemaError: If validation fails and severity is ERROR
    """
    schema = get_validation_schema(schema_name)
    
    try:
        validated_df = schema.validate(df, lazy=True)
        return validated_df
    except (pa.errors.SchemaError, pa.errors.SchemaErrors) as e:
        if severity == ValidationSeverity.ERROR:
            raise
        elif severity == ValidationSeverity.WARNING:
            # Log warning but return original DataFrame
            import structlog
            logger = structlog.get_logger(__name__)
            logger.warning("Validation warning", schema=schema_name, error=str(e))
            return df
        else:  # INFO
            # Log info but return original DataFrame
            import structlog
            logger = structlog.get_logger(__name__)
            logger.info("Validation info", schema=schema_name, error=str(e))
            return df 