# Transformation Module

The transformation module serves as the critical data bridge between external API formats (like Databento) and the internal standardized data models used for storage. It applies field mappings, data type conversions, validation rules, and business logic to ensure data consistency and quality throughout the ingestion pipeline.

## Overview

The transformation layer implements a **declarative, YAML-driven approach** that enables:
- **Flexible field mapping** between different data provider schemas
- **Configurable validation rules** for data quality assurance
- **Data type conversion and normalization** (timestamps, precision, etc.)
- **Conditional logic** for complex mapping scenarios
- **Batch processing** for high-performance data transformation

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Source   │───▶│  Transformation  │───▶│  Storage Layer  │
│  (Databento)    │    │     Engine       │    │  (TimescaleDB)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │   YAML       │
                       │ Configuration│
                       └──────────────┘
```

## Key Components

### 1. `mapping_configs/` - Declarative Mapping Configurations
Contains YAML files that define how to transform data from specific sources to standardized internal formats.

**Main Configuration:**
- `databento_mappings.yaml` - Complete field mappings for all Databento schemas (OHLCV, Trades, TBBO, Statistics)

**Test Configuration:**
- `test_databento_mappings.yaml` (in `tests/fixtures/`) - Simplified mappings for unit testing

### 2. `rule_engine/` - Transformation Engine Implementation
Core engine that parses YAML configurations and applies transformations to Pydantic model instances.

**Key Files:**
- `engine.py` - Main RuleEngine class with transformation and validation logic
- `__init__.py` - Module exports and factory functions

**Features:**
- YAML configuration parsing and validation
- Schema-specific field mapping application
- Conditional mapping support (e.g., statistics stat_type handling)
- Data type conversion and global transformations
- Comprehensive validation rule evaluation
- Batch processing capabilities
- Detailed error handling and logging

### 3. `validators/` - Post-Transformation Validation
Reserved for future Story 2.4 implementation using Pandera for advanced business rule validation.

## Configuration Structure

### YAML Configuration Format

```yaml
version: "1.0"
description: "Field mappings for [Data Provider] Pydantic models"

schema_mappings:
  [schema_name]:
    source_model: "[SourcePydanticModelName]"
    target_schema: "[target_table_name]"
    description: "Description of this mapping"
    
    field_mappings:
      source_field: "target_field"
      # Direct field mappings
      
    transformations:
      # Validation rules
      rule_name:
        fields: ["field1", "field2"]
        rule: "validation_expression"
      
      # Global rules
      global_rule_name:
        rule: "field1 > 0 and field2 < field3"
        
    defaults:
      field_name: default_value
      # Default values for missing fields

conditional_mappings:
  [schema_name]:
    # Complex conditional logic
    
global_settings:
  timezone_normalization: "UTC"
  price_precision: 8
  skip_validation_errors: false
```

### Field Mapping Examples

```yaml
# OHLCV Mapping Example
ohlcv:
  source_model: "DatabentoOHLCVRecord"
  target_schema: "daily_ohlcv_data"
  
  field_mappings:
    ts_event: "ts_event"           # Direct timestamp mapping
    open: "open_price"             # Field name transformation
    high: "high_price"
    low: "low_price"
    close: "close_price"
    volume: "volume"
    
  transformations:
    price_validation:
      fields: ["open_price", "high_price", "low_price", "close_price"]
      rule: "value > 0"
      
    ohlcv_integrity:
      rule: "high_price >= low_price and high_price >= open_price"
      
  defaults:
    granularity: "1d"
    data_source: "databento"
```

## Usage Patterns

### Basic Transformation

```python
from src.transformation.rule_engine import create_rule_engine

# Initialize engine with configuration
engine = create_rule_engine("src/transformation/mapping_configs/databento_mappings.yaml")

# Transform single record
transformed_data = engine.transform_record(databento_record, "ohlcv")

# Transform batch of records
transformed_batch = engine.transform_batch(record_list, "trades")
```

### Advanced Usage

```python
# Disable validation for performance
transformed_data = engine.transform_record(record, "ohlcv", validate=False)

# Check supported schemas
schemas = engine.get_supported_schemas()  # ["ohlcv", "trades", "tbbo", "statistics"]

# Get target schema for model
target = engine.get_target_schema_for_model("DatabentoOHLCVRecord")  # "ohlcv"
```

### Error Handling

```python
from src.transformation.rule_engine.engine import TransformationError, ValidationRuleError

try:
    result = engine.transform_record(record, "ohlcv")
except ValidationRuleError as e:
    logger.error(f"Validation failed: {e}")
    # Handle validation failure (quarantine record)
except TransformationError as e:
    logger.error(f"Transformation failed: {e}")
    # Handle transformation failure
```

## Integration with Pipeline Components

### 1. DatabentoAdapter Integration
The transformation engine is designed to work seamlessly with the DatabentoAdapter output:

```python
# In pipeline orchestration
adapter = DatabentoAdapter(config)
engine = create_rule_engine()

# Fetch and transform
records = adapter.fetch_historical_data(job_config)
for record in records:
    transformed = engine.transform_record(record, schema_name)
    # Pass to storage layer
```

### 2. Storage Layer Integration
Transformed data is ready for direct insertion into TimescaleDB:

```python
# Transformation output matches database schema exactly
transformed_data = engine.transform_record(databento_record, "ohlcv")
# transformed_data keys match database column names:
# {'ts_event': datetime, 'open_price': Decimal, 'high_price': Decimal, ...}

# Ready for storage
storage_layer.insert_ohlcv_data(transformed_data)
```

### 3. Validation Layer Integration (Future - Story 2.4)
The transformation layer prepares data for post-transformation validation:

```python
# Current (Story 2.3)
transformed_data = engine.transform_record(record, "ohlcv", validate=True)

# Future (Story 2.4) - Additional Pandera validation
validated_data = pandera_validator.validate(transformed_data, "ohlcv")
```

## Developer Guide: Adding New Mapping Configurations

### Step 1: Define Pydantic Models
Ensure your data source has appropriate Pydantic models in `src/storage/models.py`:

```python
class NewProviderRecord(BaseModel):
    """Pydantic model for new data provider."""
    timestamp: datetime
    price: Decimal
    # ... other fields
```

### Step 2: Create Mapping Configuration
Add new provider mapping to `src/transformation/mapping_configs/`:

```yaml
# new_provider_mappings.yaml
version: "1.0"
description: "Field mappings for NewProvider"

schema_mappings:
  new_schema:
    source_model: "NewProviderRecord"
    target_schema: "target_table_name"
    
    field_mappings:
      timestamp: "ts_event"
      price: "price"
      
    transformations:
      price_validation:
        fields: ["price"]
        rule: "value > 0"
        
    defaults:
      data_source: "new_provider"
```

### Step 3: Create Unit Tests
Add comprehensive tests in `tests/unit/transformation/`:

```python
# test_new_provider_mappings.py
def test_new_provider_transformation():
    engine = RuleEngine("path/to/new_provider_mappings.yaml")
    record = NewProviderRecord(timestamp=datetime.now(), price=Decimal("100.0"))
    result = engine.transform_record(record, "new_schema")
    assert result["ts_event"] == record.timestamp
    assert result["price"] == Decimal("100.0")
```

### Step 4: Update Documentation
- Add new provider to this documentation
- Update architecture diagrams if needed
- Document any provider-specific transformation logic

## Performance Considerations

### Batch Processing
- Use `transform_batch()` for processing multiple records efficiently
- Configure `batch_size` in global settings for optimal memory usage

### Validation Performance
- Set `validate=False` for high-throughput scenarios where data quality is pre-assured
- Use `skip_validation_errors=true` to continue processing despite validation failures

### Memory Management
- Process large datasets in chunks using the batch processing capabilities
- Monitor memory usage during transformation of large record sets

## Error Handling and Logging

### Validation Failures
- **Field-level validation:** Logs specific field and rule that failed
- **Global validation:** Logs the entire rule and data context
- **Quarantine support:** Failed records can be logged and quarantined for review

### Transformation Errors
- **Configuration errors:** YAML parsing failures, missing mappings
- **Model mismatches:** Source model doesn't match expected type
- **Data type errors:** Type conversion failures

### Logging Strategy
```python
# Detailed logging for debugging
global_settings:
  log_transformation_details: true

# Error logs include:
# - Full record data for context
# - Specific rule that failed
# - Validation expression and values
```

## Security Considerations

### Safe Rule Evaluation
- Uses restricted `eval()` with `{"__builtins__": {}}` to prevent code injection
- Validation rules are limited to mathematical and logical expressions
- No access to dangerous Python built-ins

### Configuration Validation
- YAML configurations are parsed and validated before use
- Malformed configurations cause startup failures, not runtime errors

## Future Enhancements

### Planned for Story 2.4
- **Pandera Integration:** Advanced statistical validation rules
- **Cross-record validation:** Validate relationships between multiple records
- **Statistical outlier detection:** Identify and handle anomalous data points

### Potential Future Features
- **Dynamic rule compilation:** Compile frequently-used rules for better performance
- **Rule versioning:** Support multiple versions of mapping configurations
- **Visual configuration tools:** Web-based YAML configuration editor
- **Performance monitoring:** Track transformation performance metrics 