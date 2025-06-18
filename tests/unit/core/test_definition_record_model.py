"""
Unit tests for DatabentoDefinitionRecord Pydantic model.

This test module validates the DatabentoDefinitionRecord model structure,
field validation, serialization, and business logic for all 67 fields.
"""

import pytest
from datetime import datetime, timezone, date
from decimal import Decimal
from pydantic import ValidationError

from src.storage.models import DatabentoDefinitionRecord


class TestDatabentoDefinitionRecord:
    """
    Unit tests for DatabentoDefinitionRecord Pydantic model.
    
    Tests cover field validation, type conversion, serialization,
    and business logic for the complete 67-field model.
    """
    
    @pytest.fixture
    def minimal_valid_data(self):
        """Minimal valid data for creating a DatabentoDefinitionRecord."""
        return {
            # Header fields (required)
            "ts_event": datetime(2024, 12, 1, 12, 0, 0, tzinfo=timezone.utc),
            "ts_recv": datetime(2024, 12, 1, 12, 0, 1, tzinfo=timezone.utc),
            "rtype": 19,
            "publisher_id": 1,
            "instrument_id": 5002,
            
            # Core definition fields (required)
            "raw_symbol": "ESH5",
            "security_update_action": "A",
            "instrument_class": "FUT",
            "min_price_increment": Decimal("0.25"),
            "display_factor": Decimal("1.0"),
            "expiration": datetime(2025, 3, 21, 13, 30, 0, tzinfo=timezone.utc),
            "activation": datetime(2024, 6, 14, 17, 0, 0, tzinfo=timezone.utc),
            "high_limit_price": Decimal("6000.00"),
            "low_limit_price": Decimal("3000.00"),
            "max_price_variation": Decimal("500.00"),
            "unit_of_measure_qty": Decimal("50.0"),
            "min_price_increment_amount": Decimal("12.50"),
            "price_ratio": Decimal("1.0"),
            "inst_attrib_value": 0,
            
            # Market parameters (required)
            "market_depth_implied": 10,
            "market_depth": 10,
            "market_segment_id": 54,
            "max_trade_vol": 2000,
            "min_lot_size": 1,
            "min_lot_size_block": 1,
            "min_lot_size_round_lot": 1,
            "min_trade_vol": 1,
            "channel_id": 54,
            
            # Currency and classification (required)
            "currency": "USD",
            "group": "ES",
            "exchange": "GLBX",
            "asset": "ES",
            
            # Leg fields (required)
            "leg_count": 0
        }
    
    @pytest.fixture
    def complete_valid_data(self, minimal_valid_data):
        """Complete valid data with all optional fields populated."""
        complete_data = minimal_valid_data.copy()
        complete_data.update({
            # Optional identifiers
            "underlying_id": 1001,
            "raw_instrument_id": 5002,
            
            # Contract details
            "contract_multiplier": 50,
            "decay_quantity": 0,
            "original_contract_size": 50,
            "appl_id": 54,
            "maturity_year": 2025,
            "decay_start_date": date(2025, 3, 1),
            
            # Currency and classification
            "settl_currency": "USD",
            "secsubtype": None,
            "cfi": "FFIXSX",
            "security_type": "FUT",
            "unit_of_measure": "USD",
            "underlying": "SPX",
            
            # Option-specific fields
            "strike_price_currency": None,
            "strike_price": None,
            
            # Trading algorithm and display
            "match_algorithm": "FIFO",
            "main_fraction": 4,
            "price_display_format": 2,
            "sub_fraction": 4,
            "underlying_product": 1,
            
            # Maturity details
            "maturity_month": 3,
            "maturity_day": 21,
            "maturity_week": None,
            
            # Miscellaneous attributes
            "user_defined_instrument": "N",
            "contract_multiplier_unit": 1,
            "flow_schedule_type": None,
            "tick_rule": 0,
            
            # Leg fields for spreads/strategies
            "leg_index": None,
            "leg_instrument_id": None,
            "leg_raw_symbol": None,
            "leg_instrument_class": None,
            "leg_side": None,
            "leg_price": None,
            "leg_delta": None,
            "leg_ratio_price_numerator": None,
            "leg_ratio_price_denominator": None,
            "leg_ratio_qty_numerator": None,
            "leg_ratio_qty_denominator": None,
            "leg_underlying_id": None
        })
        return complete_data

    def test_minimal_valid_record_creation(self, minimal_valid_data):
        """Test creating a record with minimal required fields."""
        record = DatabentoDefinitionRecord(**minimal_valid_data)
        
        assert record.instrument_id == 5002
        assert record.raw_symbol == "ESH5"
        assert record.instrument_class == "FUT"
        assert record.min_price_increment == Decimal("0.25")
        assert record.leg_count == 0

    def test_complete_valid_record_creation(self, complete_valid_data):
        """Test creating a record with all fields populated."""
        record = DatabentoDefinitionRecord(**complete_valid_data)
        
        # Validate all major field categories
        assert record.instrument_id == 5002
        assert record.contract_multiplier == 50
        assert record.maturity_year == 2025
        assert record.cfi == "FFIXSX"
        assert record.match_algorithm == "FIFO"

    def test_required_field_validation(self, minimal_valid_data):
        """Test that required fields are properly validated."""
        # Test missing ts_event
        invalid_data = minimal_valid_data.copy()
        del invalid_data["ts_event"]
        
        with pytest.raises(ValidationError) as exc_info:
            DatabentoDefinitionRecord(**invalid_data)
        assert "ts_event" in str(exc_info.value)
        
        # Test missing instrument_id
        invalid_data = minimal_valid_data.copy()
        del invalid_data["instrument_id"]
        
        with pytest.raises(ValidationError) as exc_info:
            DatabentoDefinitionRecord(**invalid_data)
        assert "instrument_id" in str(exc_info.value)

    def test_datetime_field_validation(self, minimal_valid_data):
        """Test datetime field validation and timezone handling."""
        # Test naive datetime (should be converted to UTC)
        naive_data = minimal_valid_data.copy()
        naive_data["ts_event"] = datetime(2024, 12, 1, 12, 0, 0)  # No timezone
        
        record = DatabentoDefinitionRecord(**naive_data)
        assert record.ts_event.tzinfo == timezone.utc
        
        # Test invalid datetime type
        invalid_data = minimal_valid_data.copy()
        invalid_data["ts_event"] = "not-a-datetime"
        
        with pytest.raises(ValidationError):
            DatabentoDefinitionRecord(**invalid_data)

    def test_decimal_field_validation(self, minimal_valid_data):
        """Test decimal field validation and precision."""
        # Test string to decimal conversion
        string_data = minimal_valid_data.copy()
        string_data["min_price_increment"] = "0.25"
        
        record = DatabentoDefinitionRecord(**string_data)
        assert record.min_price_increment == Decimal("0.25")
        
        # Test float to decimal conversion
        float_data = minimal_valid_data.copy()
        float_data["min_price_increment"] = 0.25
        
        record = DatabentoDefinitionRecord(**float_data)
        assert isinstance(record.min_price_increment, Decimal)
        
        # Test invalid decimal
        invalid_data = minimal_valid_data.copy()
        invalid_data["min_price_increment"] = "not-a-number"
        
        with pytest.raises(ValidationError):
            DatabentoDefinitionRecord(**invalid_data)

    def test_integer_field_validation(self, minimal_valid_data):
        """Test integer field validation."""
        # Test string to integer conversion
        string_data = minimal_valid_data.copy()
        string_data["instrument_id"] = "5002"
        
        record = DatabentoDefinitionRecord(**string_data)
        assert record.instrument_id == 5002
        
        # Test invalid integer
        invalid_data = minimal_valid_data.copy()
        invalid_data["instrument_id"] = "not-an-integer"
        
        with pytest.raises(ValidationError):
            DatabentoDefinitionRecord(**invalid_data)

    def test_string_field_validation(self, minimal_valid_data):
        """Test string field validation."""
        # Test valid string
        record = DatabentoDefinitionRecord(**minimal_valid_data)
        assert record.raw_symbol == "ESH5"
        
        # Test empty string (should be valid)
        empty_data = minimal_valid_data.copy()
        empty_data["raw_symbol"] = ""
        
        record = DatabentoDefinitionRecord(**empty_data)
        assert record.raw_symbol == ""

    def test_optional_field_handling(self, minimal_valid_data):
        """Test that optional fields can be None."""
        record = DatabentoDefinitionRecord(**minimal_valid_data)
        
        # These should be None when not provided
        assert record.underlying_id is None
        assert record.strike_price is None
        assert record.leg_index is None
        assert record.maturity_week is None

    def test_leg_fields_for_outright_instruments(self, minimal_valid_data):
        """Test leg fields for outright instruments (leg_count = 0)."""
        record = DatabentoDefinitionRecord(**minimal_valid_data)
        
        assert record.leg_count == 0
        assert record.leg_index is None
        assert record.leg_instrument_id is None
        assert record.leg_raw_symbol is None

    def test_leg_fields_for_spread_instruments(self, minimal_valid_data):
        """Test leg fields for spread instruments (leg_count > 0)."""
        spread_data = minimal_valid_data.copy()
        spread_data.update({
            "instrument_class": "SPREAD",
            "leg_count": 2,
            "leg_index": 0,
            "leg_instrument_id": 5001,
            "leg_raw_symbol": "ESH5",
            "leg_instrument_class": "FUT",
            "leg_side": "B",
            "leg_price": Decimal("4500.00"),
            "leg_delta": Decimal("1.0"),
            "leg_ratio_price_numerator": 1,
            "leg_ratio_price_denominator": 1,
            "leg_ratio_qty_numerator": 1,
            "leg_ratio_qty_denominator": 1,
            "leg_underlying_id": 1001
        })
        
        record = DatabentoDefinitionRecord(**spread_data)
        
        assert record.leg_count == 2
        assert record.leg_index == 0
        assert record.leg_instrument_id == 5001
        assert record.leg_side == "B"
        assert record.leg_price == Decimal("4500.00")

    def test_option_specific_fields(self, minimal_valid_data):
        """Test option-specific fields."""
        option_data = minimal_valid_data.copy()
        option_data.update({
            "instrument_class": "OPT",
            "strike_price": Decimal("4500.00"),
            "strike_price_currency": "USD"
        })
        
        record = DatabentoDefinitionRecord(**option_data)
        
        assert record.instrument_class == "OPT"
        assert record.strike_price == Decimal("4500.00")
        assert record.strike_price_currency == "USD"

    def test_maturity_fields_validation(self, minimal_valid_data):
        """Test maturity field validation."""
        maturity_data = minimal_valid_data.copy()
        maturity_data.update({
            "maturity_year": 2025,
            "maturity_month": 3,
            "maturity_day": 21,
            "maturity_week": 12
        })
        
        record = DatabentoDefinitionRecord(**maturity_data)
        
        assert record.maturity_year == 2025
        assert record.maturity_month == 3
        assert record.maturity_day == 21
        assert record.maturity_week == 12

    def test_serialization_to_dict(self, complete_valid_data):
        """Test serialization to dictionary."""
        record = DatabentoDefinitionRecord(**complete_valid_data)
        
        # Test model_dump
        data_dict = record.model_dump()
        
        assert isinstance(data_dict, dict)
        assert data_dict["instrument_id"] == 5002
        assert data_dict["raw_symbol"] == "ESH5"
        
        # Datetime fields should be datetime objects
        assert isinstance(data_dict["ts_event"], datetime)
        assert isinstance(data_dict["expiration"], datetime)

    def test_json_serialization(self, complete_valid_data):
        """Test JSON serialization with custom serializers."""
        record = DatabentoDefinitionRecord(**complete_valid_data)
        
        # Test model_dump with mode='json'
        json_dict = record.model_dump(mode='json')
        
        # Datetime fields should be ISO strings
        assert isinstance(json_dict["ts_event"], str)
        assert "T" in json_dict["ts_event"]  # ISO format
        
        # Decimal fields should be strings
        assert isinstance(json_dict["min_price_increment"], str)
        assert json_dict["min_price_increment"] == "0.25"

    def test_model_validation_with_invalid_data(self):
        """Test model validation with various invalid data scenarios."""
        # Test completely empty data
        with pytest.raises(ValidationError):
            DatabentoDefinitionRecord()
        
        # Test with wrong types
        with pytest.raises(ValidationError):
            DatabentoDefinitionRecord(
                ts_event="not-a-datetime",
                instrument_id="not-an-integer",
                min_price_increment="not-a-decimal"
            )

    def test_business_logic_validation(self, minimal_valid_data):
        """Test business logic validation scenarios."""
        # Test activation after expiration (should be allowed by model, validated elsewhere)
        invalid_dates_data = minimal_valid_data.copy()
        invalid_dates_data["activation"] = datetime(2025, 4, 1, tzinfo=timezone.utc)
        invalid_dates_data["expiration"] = datetime(2025, 3, 21, tzinfo=timezone.utc)
        
        # Model should accept this (business logic validation happens elsewhere)
        record = DatabentoDefinitionRecord(**invalid_dates_data)
        assert record.activation > record.expiration

    def test_field_count_completeness(self, complete_valid_data):
        """Test that all 73 expected fields are present in the model."""
        record = DatabentoDefinitionRecord(**complete_valid_data)

        # Count all model fields - access from class, not instance
        field_count = len(DatabentoDefinitionRecord.model_fields)

        # Should have exactly 73 fields as implemented (more than originally documented 67)
        assert field_count == 73, f"Expected 73 fields, found {field_count}. Model has been enhanced beyond original 67-field specification."
        
        # Verify key field categories are present
        header_fields = ['ts_event', 'ts_recv', 'rtype', 'publisher_id', 'instrument_id']
        core_fields = ['raw_symbol', 'instrument_class', 'min_price_increment', 'expiration']
        leg_fields = ['leg_count', 'leg_index', 'leg_instrument_id', 'leg_side']
        
        for field in header_fields + core_fields + leg_fields:
            assert field in DatabentoDefinitionRecord.model_fields, f"Missing expected field: {field}"

    def test_model_copy_and_update(self, minimal_valid_data):
        """Test model copying and updating."""
        original_record = DatabentoDefinitionRecord(**minimal_valid_data)
        
        # Test model copy with updates
        updated_record = original_record.model_copy(update={
            "raw_symbol": "ESM5",
            "maturity_month": 6
        })
        
        assert updated_record.raw_symbol == "ESM5"
        assert updated_record.maturity_month == 6
        assert updated_record.instrument_id == original_record.instrument_id  # Unchanged
        
        # Original should be unchanged
        assert original_record.raw_symbol == "ESH5"

    def test_model_equality(self, minimal_valid_data):
        """Test model equality comparison."""
        record1 = DatabentoDefinitionRecord(**minimal_valid_data)
        record2 = DatabentoDefinitionRecord(**minimal_valid_data)
        
        # Should be equal with same data
        assert record1 == record2
        
        # Should be different with different data
        different_data = minimal_valid_data.copy()
        different_data["instrument_id"] = 9999
        record3 = DatabentoDefinitionRecord(**different_data)
        
        assert record1 != record3

    def test_timezone_aware_datetime_validation(self, minimal_valid_data):
        """Test that datetime fields are properly timezone-aware."""
        record = DatabentoDefinitionRecord(**minimal_valid_data)
        
        # All datetime fields should be timezone-aware
        datetime_fields = ['ts_event', 'ts_recv', 'expiration', 'activation']
        
        for field_name in datetime_fields:
            field_value = getattr(record, field_name)
            if field_value is not None:
                assert field_value.tzinfo is not None, f"Field {field_name} is not timezone-aware"
                # Should be UTC
                assert field_value.tzinfo == timezone.utc, f"Field {field_name} is not in UTC"


# Standalone test functions for pytest discovery
def test_model_import():
    """Test that the model can be imported successfully."""
    from src.storage.models import DatabentoDefinitionRecord
    assert DatabentoDefinitionRecord is not None


def test_model_in_schema_mapping():
    """Test that the model is properly registered in schema mapping."""
    from src.storage.models import DATABENTO_SCHEMA_MODEL_MAPPING
    
    assert "definition" in DATABENTO_SCHEMA_MODEL_MAPPING
    assert DATABENTO_SCHEMA_MODEL_MAPPING["definition"] == DatabentoDefinitionRecord


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v", "-s"])
