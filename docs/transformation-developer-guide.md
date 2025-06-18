# Transformation Module Developer Guide

This guide provides comprehensive instructions for developers working with the transformation module, including how to add new data provider mappings, extend validation rules, and integrate with the pipeline.

## Quick Start

### Prerequisites
- Pydantic models defined in `src/storage/models.py`
- Understanding of target database schema (see `docs/architecture.md`)
- Basic YAML knowledge

### Basic Workflow
1. **Define Pydantic Models** → 2. **Create YAML Mapping** → 3. **Write Unit Tests** → 4. **Test Integration**

## Adding New Data Provider Mappings

### Step 1: Define Pydantic Models

First, ensure your data provider has appropriate Pydantic models in `src/storage/models.py`:

```python
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional

class NewProviderOHLCVRecord(BaseModel):
    """Pydantic model for NewProvider OHLCV data."""
    timestamp: datetime = Field(..., description="Event timestamp")
    symbol: str = Field(..., description="Trading symbol")
    open_price: Decimal = Field(..., description="Opening price")
    high_price: Decimal = Field(..., description="High price")
    low_price: Decimal = Field(..., description="Low price")
    close_price: Decimal = Field(..., description="Closing price")
    volume: Decimal = Field(..., description="Trading volume")
    
    # Provider-specific fields
    exchange: Optional[str] = Field(None, description="Exchange identifier")
    currency: Optional[str] = Field("USD", description="Currency code")
```

### Step 2: Create YAML Mapping Configuration

Create a new mapping file in `src/transformation/mapping_configs/`:

```yaml
# new_provider_mappings.yaml
version: "1.0"
description: "Field mappings for NewProvider Pydantic models to standardized internal schemas"

schema_mappings:
  ohlcv:
    source_model: "NewProviderOHLCVRecord"
    target_schema: "daily_ohlcv_data"
    description: "Maps NewProvider OHLCV data to internal OHLCV format"
    
    field_mappings:
      # Direct field mappings
      timestamp: "ts_event"
      symbol: "symbol"
      open_price: "open_price"
      high_price: "high_price"
      low_price: "low_price"
      close_price: "close_price"
      volume: "volume"
      
      # Optional field mappings
      exchange: "exchange"
      currency: "currency"
      
    transformations:
      # Validation rules
      price_validation:
        fields: ["open_price", "high_price", "low_price", "close_price"]
        rule: "value > 0"
        
      volume_validation:
        fields: ["volume"]
        rule: "value >= 0"
        
      ohlcv_integrity:
        rule: "high_price >= low_price and high_price >= open_price and high_price >= close_price and low_price <= open_price and low_price <= close_price"
        
    defaults:
      # Default values for missing fields
      granularity: "1d"
      data_source: "new_provider"
      currency: "USD"

global_settings:
  timezone_normalization: "UTC"
  price_precision: 8
  skip_validation_errors: false
```

### Step 3: Create Unit Tests

Add comprehensive tests in `tests/unit/transformation/`:

```python
# test_new_provider_mappings.py
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from src.transformation.rule_engine.engine import RuleEngine
from src.storage.models import NewProviderOHLCVRecord

class TestNewProviderMappings:
    
    @pytest.fixture
    def engine(self):
        """Create RuleEngine with NewProvider mappings."""
        return RuleEngine("src/transformation/mapping_configs/new_provider_mappings.yaml")
    
    @pytest.fixture
    def sample_ohlcv_record(self):
        """Create sample NewProvider OHLCV record."""
        return NewProviderOHLCVRecord(
            timestamp=datetime(2024, 1, 15, 9, 30, 0, tzinfo=timezone.utc),
            symbol="AAPL",
            open_price=Decimal("150.00"),
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.50"),
            volume=Decimal("1000000"),
            exchange="NASDAQ",
            currency="USD"
        )
    
    def test_ohlcv_transformation_success(self, engine, sample_ohlcv_record):
        """Test successful OHLCV record transformation."""
        result = engine.transform_record(sample_ohlcv_record, "ohlcv")
        
        # Verify field mappings
        assert result["ts_event"] == sample_ohlcv_record.timestamp
        assert result["symbol"] == "AAPL"
        assert result["open_price"] == Decimal("150.00")
        assert result["high_price"] == Decimal("155.00")
        assert result["low_price"] == Decimal("149.00")
        assert result["close_price"] == Decimal("154.50")
        assert result["volume"] == Decimal("1000000")
        assert result["exchange"] == "NASDAQ"
        assert result["currency"] == "USD"
        
        # Verify defaults
        assert result["granularity"] == "1d"
        assert result["data_source"] == "new_provider"
    
    def test_validation_rules(self, engine):
        """Test validation rules catch invalid data."""
        # Test negative price
        invalid_record = NewProviderOHLCVRecord(
            timestamp=datetime.now(timezone.utc),
            symbol="TEST",
            open_price=Decimal("-10.00"),  # Invalid negative price
            high_price=Decimal("155.00"),
            low_price=Decimal("149.00"),
            close_price=Decimal("154.50"),
            volume=Decimal("1000000")
        )
        
        with pytest.raises(Exception):  # Should raise ValidationRuleError
            engine.transform_record(invalid_record, "ohlcv")
    
    def test_ohlcv_integrity_validation(self, engine):
        """Test OHLCV integrity validation."""
        # Test high < low (invalid)
        invalid_record = NewProviderOHLCVRecord(
            timestamp=datetime.now(timezone.utc),
            symbol="TEST",
            open_price=Decimal("150.00"),
            high_price=Decimal("140.00"),  # High < Low (invalid)
            low_price=Decimal("149.00"),
            close_price=Decimal("154.50"),
            volume=Decimal("1000000")
        )
        
        with pytest.raises(Exception):  # Should raise ValidationRuleError
            engine.transform_record(invalid_record, "ohlcv")
```

### Step 4: Test Integration

Test the integration with the RuleEngine:

```python
# Integration test example
def test_new_provider_integration():
    from src.transformation.rule_engine import create_rule_engine
    
    # Initialize engine
    engine = create_rule_engine("src/transformation/mapping_configs/new_provider_mappings.yaml")
    
    # Verify supported schemas
    schemas = engine.get_supported_schemas()
    assert "ohlcv" in schemas
    
    # Verify model mapping
    target = engine.get_target_schema_for_model("NewProviderOHLCVRecord")
    assert target == "ohlcv"
    
    # Test batch processing
    records = [sample_record_1, sample_record_2, sample_record_3]
    results = engine.transform_batch(records, "ohlcv")
    assert len(results) == 3
```

## Advanced Configuration Patterns

### Conditional Mappings

For complex scenarios where field mappings depend on record content:

```yaml
conditional_mappings:
  statistics:
    # Map different stat_type values to different target fields
    - condition: "stat_type == 'volume'"
      field_mappings:
        value: "volume_stat"
        
    - condition: "stat_type == 'price'"
      field_mappings:
        value: "price_stat"
        
    - condition: "stat_type in ['bid', 'ask']"
      field_mappings:
        value: "quote_stat"
        side: "quote_side"
```

### Complex Validation Rules

```yaml
transformations:
  # Cross-field validation
  bid_ask_spread:
    rule: "ask_price > bid_price"
    
  # Conditional validation
  volume_check:
    rule: "volume > 0 if trade_type == 'executed' else True"
    
  # Range validation
  price_range:
    fields: ["price"]
    rule: "value >= 0.01 and value <= 100000"
    
  # Null handling
  optional_field_check:
    rule: "exchange is not null or venue is not null"
```

### Global Transformations

```yaml
global_settings:
  # Timezone normalization
  timezone_normalization: "UTC"
  
  # Precision settings
  price_precision: 8
  volume_precision: 2
  
  # Error handling
  skip_validation_errors: false
  log_transformation_details: true
  
  # Performance settings
  batch_size: 1000
```

## Testing Best Practices

### Test Structure

```python
class TestProviderMappings:
    """Comprehensive test suite for provider mappings."""
    
    @pytest.fixture
    def engine(self):
        """RuleEngine fixture."""
        return RuleEngine("path/to/mappings.yaml")
    
    @pytest.fixture
    def valid_record(self):
        """Valid record fixture."""
        return ProviderRecord(...)
    
    @pytest.fixture
    def invalid_record(self):
        """Invalid record fixture for testing validation."""
        return ProviderRecord(...)
    
    def test_successful_transformation(self, engine, valid_record):
        """Test successful transformation."""
        pass
    
    def test_validation_failures(self, engine, invalid_record):
        """Test validation rule failures."""
        pass
    
    def test_edge_cases(self, engine):
        """Test edge cases and boundary conditions."""
        pass
    
    def test_batch_processing(self, engine):
        """Test batch transformation."""
        pass
```

### Test Coverage Requirements

1. **Happy Path:** Valid records transform correctly
2. **Validation Rules:** All validation rules catch invalid data
3. **Edge Cases:** Null values, missing fields, boundary conditions
4. **Error Handling:** Malformed data, type mismatches
5. **Performance:** Batch processing, large datasets

## Integration Patterns

### Pipeline Integration

```python
# Example pipeline integration
class DataPipeline:
    def __init__(self, provider_config):
        self.adapter = ProviderAdapter(provider_config)
        self.transformer = create_rule_engine(provider_config.mapping_file)
        self.storage = StorageLayer()
    
    def process_data(self, job_config):
        # Fetch data
        records = self.adapter.fetch_data(job_config)
        
        # Transform data
        transformed_records = []
        for record in records:
            try:
                transformed = self.transformer.transform_record(
                    record, 
                    job_config.schema_type
                )
                transformed_records.append(transformed)
            except ValidationRuleError as e:
                self.handle_validation_error(record, e)
            except TransformationError as e:
                self.handle_transformation_error(record, e)
        
        # Store data
        self.storage.bulk_insert(transformed_records, job_config.target_table)
```

### Error Handling Integration

```python
def handle_transformation_errors(record, error, quarantine_handler):
    """Comprehensive error handling for transformation failures."""
    
    if isinstance(error, ValidationRuleError):
        # Log validation failure
        logger.warning(f"Validation failed for record {record.id}: {error}")
        
        # Quarantine record for review
        quarantine_handler.quarantine_record(record, "validation_failure", str(error))
        
    elif isinstance(error, TransformationError):
        # Log transformation failure
        logger.error(f"Transformation failed for record {record.id}: {error}")
        
        # Quarantine record for investigation
        quarantine_handler.quarantine_record(record, "transformation_failure", str(error))
        
    else:
        # Unexpected error
        logger.critical(f"Unexpected error transforming record {record.id}: {error}")
        raise error
```

## Performance Optimization

### Batch Processing

```python
# Optimize for large datasets
def process_large_dataset(records, transformer, batch_size=1000):
    """Process large datasets efficiently."""
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        # Transform batch
        transformed_batch = transformer.transform_batch(batch, "ohlcv")
        
        # Process transformed batch
        yield transformed_batch
```

### Validation Performance

```python
# Skip validation for trusted sources
transformed_data = engine.transform_record(
    record, 
    "ohlcv", 
    validate=False  # Skip validation for performance
)

# Or configure globally
global_settings:
  skip_validation_errors: true  # Continue processing despite validation failures
```

## Troubleshooting

### Common Issues

1. **YAML Parsing Errors**
   - Check YAML syntax and indentation
   - Validate field names and structure
   - Ensure proper quoting of special characters

2. **Validation Rule Failures**
   - Check rule syntax and field references
   - Verify data types match expectations
   - Test rules with sample data

3. **Model Mismatches**
   - Ensure source_model matches actual Pydantic model name
   - Verify model is imported and available
   - Check field names match model attributes

4. **Performance Issues**
   - Use batch processing for large datasets
   - Consider disabling validation for trusted sources
   - Monitor memory usage during transformation

### Debugging Tips

```python
# Enable detailed logging
import logging
logging.getLogger('transformation').setLevel(logging.DEBUG)

# Test individual rules
engine._evaluate_rule("price > 0", {"price": 100})  # Should return True

# Inspect configuration
print(engine.config)  # View loaded configuration
print(engine.get_supported_schemas())  # View available schemas
```

## Migration Guide

### Updating Existing Mappings

When updating existing mapping configurations:

1. **Version Control:** Always version your mapping files
2. **Backward Compatibility:** Test with existing data
3. **Gradual Rollout:** Deploy changes incrementally
4. **Rollback Plan:** Keep previous version available

```yaml
# Version your mappings
version: "1.1"  # Increment version
description: "Updated mappings with new validation rules"

# Document changes
changelog:
  - version: "1.1"
    date: "2024-01-15"
    changes:
      - "Added new validation rule for price ranges"
      - "Updated field mapping for exchange field"
```

### Schema Evolution

When database schemas change:

1. **Update target_schema references**
2. **Modify field mappings as needed**
3. **Update validation rules**
4. **Test with existing and new data**
5. **Update documentation**

This guide provides the foundation for working with the transformation module. For specific questions or advanced use cases, refer to the main transformation module documentation or consult with the development team. 