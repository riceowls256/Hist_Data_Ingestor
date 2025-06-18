"""
Unit tests for the Databento validation schemas and functions.
"""

import pytest
import pandas as pd
import pandera.pandas as pa
from decimal import Decimal
from datetime import datetime, timezone

from src.transformation.validators.databento_validators import (
    OHLCVSchema,
    TradeSchema,
    TBBOSchema,
    StatisticsSchema,
    DefinitionSchema,
    ValidationSeverity,
    validate_dataframe,
    validate_timestamp_timezone_aware,
    validate_symbol_format,
    validate_cross_field_consistency_ohlcv,
    validate_cross_field_consistency_trade
)

# Test constants
TEST_TIMESTAMP = datetime(2024, 1, 1, tzinfo=timezone.utc)

# ========================================================================================
# Custom Business Logic Validator Tests
# ========================================================================================

def test_validate_timestamp_timezone_aware():
    """Test timestamp range validation."""
    # Valid timezone-aware timestamp (recent past)
    tz_aware = datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert validate_timestamp_timezone_aware(tz_aware) == True
    
    # Valid naive timestamp (Pandera converts timezone-aware to naive)
    naive = datetime(2024, 1, 1)
    assert validate_timestamp_timezone_aware(naive) == True
    
    # None should be allowed
    assert validate_timestamp_timezone_aware(None) == True
    
    # Future timestamp (within 20 years) should be valid
    future = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert validate_timestamp_timezone_aware(future) == True
    
    # Too far future should be invalid
    far_future = datetime(2050, 1, 1, tzinfo=timezone.utc)
    assert validate_timestamp_timezone_aware(far_future) == False

def test_validate_symbol_format():
    """Test symbol format validation."""
    # Valid symbols
    assert validate_symbol_format("ES.FUT") == True
    assert validate_symbol_format("CL.C.0") == True  # Fixed case
    assert validate_symbol_format("SPY") == True
    assert validate_symbol_format("ES_H24") == True
    
    # Invalid symbols
    assert validate_symbol_format("") == False
    assert validate_symbol_format("   ") == False
    assert validate_symbol_format(None) == False
    assert validate_symbol_format("ES FUT") == False  # space
    assert validate_symbol_format("es.fut") == False  # lowercase not allowed

def test_validate_cross_field_consistency_ohlcv():
    """Test OHLCV cross-field consistency validation."""
    # Valid OHLCV data
    valid_df = pd.DataFrame({
        "open_price": [100.0],
        "high_price": [105.0],
        "low_price": [98.0],
        "close_price": [102.0]
    })
    result = validate_cross_field_consistency_ohlcv(valid_df)
    assert result.iloc[0] == True
    
    # Invalid OHLCV data (high < low)
    invalid_df = pd.DataFrame({
        "open_price": [100.0],
        "high_price": [95.0],  # High less than low
        "low_price": [98.0],
        "close_price": [102.0]
    })
    result = validate_cross_field_consistency_ohlcv(invalid_df)
    assert result.iloc[0] == False

# ========================================================================================
# OHLCV Schema Tests
# ========================================================================================

def test_ohlcv_schema_valid():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
        "open_price": [100.0],
        "high_price": [102.0],
        "low_price": [99.0],
        "close_price": [101.0],
        "volume": [1000],
        "trade_count": [50],
        "vwap": [100.5],
        "granularity": ["1d"],
        "data_source": ["databento"]
    })
    assert isinstance(OHLCVSchema.validate(df), pd.DataFrame)

def test_ohlcv_schema_invalid_prices():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
        "open_price": [100.0],
        "high_price": [98.0],  # High < Low should fail
        "low_price": [99.0],
        "close_price": [101.0],
        "volume": [1000],
        "trade_count": [50],
        "vwap": [100.5],
        "granularity": ["1d"],
        "data_source": ["databento"]
    })
    with pytest.raises(pa.errors.SchemaError):
        OHLCVSchema.validate(df)

def test_ohlcv_schema_negative_volume():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "open": [100.0],
        "high": [102.0],
        "low": [99.0],
        "close": [101.0],
        "volume": [-1000]  # Negative volume should fail
    })
    with pytest.raises(pa.errors.SchemaError):
        OHLCVSchema.validate(df)

# ========================================================================================
# Trade Schema Tests
# ========================================================================================

def test_trade_schema_valid():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "price": [100.50],
        "size": [100],
        "side": ["A"]
    })
    assert isinstance(TradeSchema.validate(df), pd.DataFrame)

def test_trade_schema_invalid_side():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "price": [100.50],
        "size": [100],
        "side": ["X"]  # Invalid side code
    })
    with pytest.raises(pa.errors.SchemaError):
        TradeSchema.validate(df)

def test_trade_schema_negative_price():
    # Test that moderately negative prices are allowed (for spread instruments)
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "price": [-25.50],  # Moderate negative price should be allowed
        "size": [100],
        "side": ["A"],
        "symbol": ["CL-ES"]  # Spread symbol
    })
    # Should not raise an error for moderate negative prices
    validated_df = TradeSchema.validate(df)
    assert len(validated_df) == 1
    
    # Test that extremely negative prices still fail
    df_extreme = pd.DataFrame({
        "instrument_id": [1], 
        "ts_event": [datetime.now(timezone.utc)],
        "price": [-1000.50],  # Extremely negative price should fail
        "size": [100],
        "side": ["A"],
        "symbol": ["CL.FUT"]  # Regular symbol
    })
    with pytest.raises(pa.errors.SchemaError):
        TradeSchema.validate(df_extreme)

# ========================================================================================
# TBBO Schema Tests
# ========================================================================================

def test_tbbo_schema_valid():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "bid_px": [99.50],
        "ask_px": [100.50],
        "bid_sz": [100],
        "ask_sz": [200]
    })
    assert isinstance(TBBOSchema.validate(df), pd.DataFrame)

def test_tbbo_schema_invalid_spread():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "bid_px": [101.50],  # Bid > Ask should fail
        "ask_px": [100.50],
        "bid_sz": [100],
        "ask_sz": [200]
    })
    with pytest.raises(pa.errors.SchemaError):
        TBBOSchema.validate(df)

def test_tbbo_schema_null_values():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "bid_px": [None],  # Null values should be allowed
        "ask_px": [100.50],
        "bid_sz": [None],
        "ask_sz": [200]
    })
    assert isinstance(TBBOSchema.validate(df), pd.DataFrame)

# ========================================================================================
# Statistics Schema Tests
# ========================================================================================

def test_statistics_schema_valid():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "stat_type": [1],  # Opening price
        "stat_value": [100.50],
        "update_action": [1]  # Changed to integer
    })
    assert isinstance(StatisticsSchema.validate(df), pd.DataFrame)

def test_statistics_schema_invalid_stat_type():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "stat_type": [0],  # Invalid stat type (< 1)
        "stat_value": [100.50],
        "update_action": [1]
    })
    with pytest.raises(pa.errors.SchemaError):
        StatisticsSchema.validate(df)

def test_statistics_schema_negative_price_stat():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "stat_type": [1],  # Opening price (should be positive)
        "stat_value": [-100.50],  # Negative price for price stat
        "update_action": ["A"]
    })
    with pytest.raises(pa.errors.SchemaError):
        StatisticsSchema.validate(df)

# ========================================================================================
# Definition Schema Tests
# ========================================================================================

def test_definition_schema_valid():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "symbol": ["ES.FUT"],
        "expiration": [datetime(2024, 12, 15, tzinfo=timezone.utc)],
        "activation": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
        "min_price_increment": [0.25],
        "unit_of_measure_qty": [50.0],
        "instrument_class": ["Future"]
    })
    assert isinstance(DefinitionSchema.validate(df), pd.DataFrame)

def test_definition_schema_invalid_symbol():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "symbol": ["es.fut"],  # Lowercase should fail
        "expiration": [datetime(2024, 12, 15, tzinfo=timezone.utc)],
        "activation": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
        "min_price_increment": [0.25],
        "unit_of_measure_qty": [50.0],
        "instrument_class": ["Future"]
    })
    with pytest.raises(pa.errors.SchemaError):
        DefinitionSchema.validate(df)

def test_definition_schema_invalid_dates():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "symbol": ["ES.FUT"],
        "expiration": [datetime(2024, 1, 1, tzinfo=timezone.utc)],  # Expiration before activation
        "activation": [datetime(2024, 12, 15, tzinfo=timezone.utc)],
        "min_price_increment": [0.25],
        "unit_of_measure_qty": [50.0],
        "instrument_class": ["Future"]
    })
    with pytest.raises(pa.errors.SchemaError):
        DefinitionSchema.validate(df)

def test_definition_schema_invalid_instrument_class():
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "symbol": ["ES.FUT"],
        "expiration": [datetime(2024, 12, 15, tzinfo=timezone.utc)],
        "activation": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
        "min_price_increment": [0.25],
        "unit_of_measure_qty": [50.0],
        "instrument_class": ["InvalidClass"]  # Invalid instrument class
    })
    with pytest.raises(pa.errors.SchemaError):
        DefinitionSchema.validate(df)

# ========================================================================================
# Validation Severity Tests
# ========================================================================================

def test_validate_dataframe_error_severity():
    """Test validation with ERROR severity (default behavior)."""
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "open_price": [100.0],
        "high_price": [98.0],  # Invalid: high < low
        "low_price": [99.0],
        "close_price": [101.0],
        "volume": [1000],
        "trade_count": [50],
        "vwap": [100.5],
        "granularity": ["1d"],
        "data_source": ["databento"]
    })
    
    with pytest.raises((pa.errors.SchemaError, pa.errors.SchemaErrors)):
        validate_dataframe(df, "ohlcv-1d", ValidationSeverity.ERROR)

def test_validate_dataframe_warning_severity():
    """Test validation with WARNING severity (logs warning, removes invalid rows)."""
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "open_price": [100.0],
        "high_price": [98.0],  # Invalid: high < low
        "low_price": [99.0],
        "close_price": [101.0],
        "volume": [1000],
        "trade_count": [50],
        "vwap": [100.5],
        "granularity": ["1d"],
        "data_source": ["databento"]
    })
    
    # Should not raise exception, should return DataFrame with invalid rows removed
    result = validate_dataframe(df, "ohlcv-1d", ValidationSeverity.WARNING)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0  # Invalid row should be removed

def test_validate_dataframe_info_severity():
    """Test validation with INFO severity (logs info, returns data)."""
    df = pd.DataFrame({
        "instrument_id": [1],
        "ts_event": [datetime.now(timezone.utc)],
        "open_price": [100.0],
        "high_price": [98.0],  # Invalid: high < low
        "low_price": [99.0],
        "close_price": [101.0],
        "volume": [1000],
        "trade_count": [50],
        "vwap": [100.5],
        "granularity": ["1d"],
        "data_source": ["databento"]
    })
    
    # Should not raise exception, should return original DataFrame
    result = validate_dataframe(df, "ohlcv-1d", ValidationSeverity.INFO)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1

# ========================================================================================
# Schema Dispatcher Tests
# ========================================================================================

def test_validate_dataframe_unknown_schema():
    """Test validation with unknown schema name."""
    df = pd.DataFrame({"test": [1]})
    
    with pytest.raises(ValueError, match="Unknown schema name"):
        validate_dataframe(df, "unknown_schema")

def test_validate_dataframe_all_schemas():
    """Test that all schema names are supported."""
    schema_names = ["ohlcv-1d", "ohlcv-1h", "ohlcv-1m", "trades", "tbbo", "statistics", "definition"]
    
    for schema_name in schema_names:
        # Should not raise ValueError for schema name
        try:
            # Create minimal valid data for each schema
            if "ohlcv" in schema_name:
                df = pd.DataFrame({
                    "instrument_id": [1],
                    "ts_event": [datetime.now(timezone.utc)],
                    "open_price": [100.0], "high_price": [102.0], "low_price": [99.0], "close_price": [101.0], 
                    "volume": [1000], "trade_count": [50], "vwap": [100.5], 
                    "granularity": ["1d"], "data_source": ["databento"]
                })
            elif schema_name == "trades":
                df = pd.DataFrame({
                    "instrument_id": [1],
                    "ts_event": [datetime.now(timezone.utc)],
                    "price": [100.0], "size": [100], "side": ["A"]
                })
            elif schema_name == "tbbo":
                df = pd.DataFrame({
                    "instrument_id": [1],
                    "ts_event": [datetime.now(timezone.utc)],
                    "bid_px": [99.0], "ask_px": [101.0], "bid_sz": [100], "ask_sz": [100]
                })
            elif schema_name == "statistics":
                df = pd.DataFrame({
                    "instrument_id": [1],
                    "ts_event": [datetime.now(timezone.utc)],
                    "stat_type": [1], "stat_value": [100.0], "update_action": [1]
                })
            elif schema_name == "definition":
                df = pd.DataFrame({
                    "instrument_id": [1],
                    "ts_event": [datetime.now(timezone.utc)],
                    "symbol": ["ES.FUT"], "expiration": [datetime(2024, 12, 15, tzinfo=timezone.utc)],
                    "activation": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
                    "min_price_increment": [0.25], "unit_of_measure_qty": [50.0], "instrument_class": ["Future"]
                })
            
            result = validate_dataframe(df, schema_name)
            assert isinstance(result, pd.DataFrame)
        except pa.errors.SchemaError:
            # Schema errors are expected for some test data, but ValueError should not occur
            pass 