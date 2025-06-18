# Transformation Module

The transformation module provides a comprehensive framework for processing, validating, and transforming raw financial data from various sources into a standardized format for storage. It implements a rule-based transformation engine with configurable mapping rules and robust validation mechanisms.

## Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Raw Data        │────│ RuleEngine       │────│ Transformed     │
│ (API Format)    │    │                  │    │ Data            │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Validation       │
                       │ Framework        │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Quarantine       │
                       │ (Invalid Data)   │
                       └──────────────────┘
```

#### Rule Engine (`rule_engine/engine.py`)

Central orchestrator for data transformation workflows.

**Key Features:**
- **Configurable Rules**: YAML-based transformation rule definitions
- **Schema Validation**: Automatic validation against Pydantic schemas
- **Error Handling**: Comprehensive error capture with detailed logging
- **Performance Monitoring**: Transformation timing and throughput metrics
- **Quarantine Management**: Automatic isolation of invalid records

#### Mapping Configurations (`mapping_configs/`)

Declarative mapping rules that define how to transform data from source format to target format.

**Supported Transformations:**
- **Field Mapping**: Direct field-to-field mapping
- **Type Conversion**: Automatic type casting with validation
- **Price Scaling**: Currency and precision adjustments
- **Timestamp Normalization**: UTC conversion and format standardization
- **Symbol Normalization**: Consistent symbol formatting

#### Validation Framework (`validators/`)

Comprehensive validation system with support for multiple validation layers.

**Validation Types:**
- **Schema Validation**: Structure and type validation
- **Business Rule Validation**: Domain-specific validation rules
- **Data Quality Checks**: Range, format, and consistency validation
- **Referential Integrity**: Cross-record validation and relationships

## Usage Examples

### Basic Transformation

```python
from src.transformation.rule_engine.engine import RuleEngine
from datetime import datetime

# Initialize rule engine
engine = RuleEngine()

# Raw data from API
raw_data = [
    {
        "timestamp": "2024-01-01T10:00:00Z",
        "symbol": "ESM4",
        "open": "5000.25",
        "high": "5010.75", 
        "low": "4995.50",
        "close": "5005.00",
        "volume": "125000"
    }
]

# Apply transformation rules
transformed_data = engine.transform(
    data=raw_data,
    source_schema="databento_ohlcv",
    target_schema="standardized_ohlcv",
    mapping_config="databento_mappings.yaml"
)

print(f"Transformed {len(transformed_data)} records")
```

### Advanced Rule Configuration

```python
# Custom transformation with validation
config = {
    "source_schema": "databento_trades",
    "target_schema": "standardized_trades", 
    "mapping_rules": {
        "field_mappings": {
            "ts_event": "timestamp",
            "price": "trade_price",
            "size": "trade_size"
        },
        "transformations": {
            "price": {
                "type": "decimal_conversion",
                "precision": 4,
                "scaling_factor": 1e-9
            },
            "timestamp": {
                "type": "datetime_conversion",
                "source_format": "nanoseconds",
                "target_format": "datetime"
            }
        }
    },
    "validation_rules": {
        "price": {"min": 0, "required": True},
        "size": {"min": 1, "required": True}
    }
}

result = engine.transform_with_config(raw_data, config)
```

## Mapping Configuration Format

### Basic Field Mapping

```yaml
# databento_ohlcv_mappings.yaml
schema_mapping:
  source_schema: "databento_ohlcv_1d"
  target_schema: "standardized_ohlcv"

field_mappings:
  ts_event: timestamp
  instrument_id: instrument_id
  open: open_price
  high: high_price
  low: low_price
  close: close_price
  volume: volume

transformations:
  open_price:
    type: "decimal_conversion"
    precision: 4
    scaling_factor: 1e-9
  
  high_price:
    type: "decimal_conversion"
    precision: 4
    scaling_factor: 1e-9
  
  timestamp:
    type: "datetime_conversion"
    source_format: "nanoseconds_utc"
    target_format: "datetime_utc"

validation:
  required_fields:
    - timestamp
    - instrument_id
    - open_price
    - close_price
  
  field_validation:
    open_price:
      type: "decimal"
      minimum: 0
      maximum: 1000000
    
    volume:
      type: "integer"
      minimum: 0
```

### Complex Transformation Rules

```yaml
# Advanced transformation example
transformations:
  symbol:
    type: "symbol_normalization"
    rules:
      - pattern: "^(.+)M(\\d)$"
        replacement: "${1}.c.${2}"
      - pattern: "^(.+)Z(\\d)$" 
        replacement: "${1}.c.${2}"
  
  price_fields:
    type: "batch_decimal_conversion"
    fields: ["open", "high", "low", "close"]
    precision: 4
    scaling_factor: 1e-9
    
  calculated_fields:
    mid_price:
      formula: "(open_price + close_price) / 2"
      type: "decimal"
      precision: 4
    
    price_range:
      formula: "high_price - low_price"
      type: "decimal"
      precision: 4

conditional_transformations:
  - condition: "schema == 'trades'"
    transformations:
      trade_direction:
        type: "mapping"
        values:
          "B": "buy"
          "S": "sell"
          "": "unknown"
```

## Validation Framework

### Schema Validation

```python
from src.transformation.validators.schema_validator import SchemaValidator

validator = SchemaValidator()

# Load validation schema
schema = validator.load_schema("databento_ohlcv_schema.yaml")

# Validate single record
result = validator.validate_record(record, schema)
if not result.is_valid:
    print(f"Validation errors: {result.errors}")

# Validate batch
batch_result = validator.validate_batch(records, schema)
print(f"Valid records: {len(batch_result.valid_records)}")
print(f"Invalid records: {len(batch_result.invalid_records)}")
```

### Custom Business Rules

```python
from src.transformation.validators.business_rules import BusinessRuleValidator

class OHLCVBusinessRules(BusinessRuleValidator):
    def validate_price_consistency(self, record):
        """Validate OHLCV price relationships"""
        high = record.get('high_price', 0)
        low = record.get('low_price', 0)
        open_price = record.get('open_price', 0)
        close = record.get('close_price', 0)
        
        errors = []
        
        if high < low:
            errors.append("High price cannot be less than low price")
        
        if not (low <= open_price <= high):
            errors.append("Open price must be between low and high")
            
        if not (low <= close <= high):
            errors.append("Close price must be between low and high")
            
        return errors
    
    def validate_volume_consistency(self, record):
        """Validate volume data"""
        volume = record.get('volume', 0)
        
        if volume < 0:
            return ["Volume cannot be negative"]
        
        # Additional volume validation rules
        return []

# Use custom validator
validator = OHLCVBusinessRules()
errors = validator.validate_record(record)
```

### Validation Schema Format

```yaml
# ohlcv_validation_schema.yaml
type: object
properties:
  timestamp:
    type: string
    format: date-time
    description: "Event timestamp in UTC"
  
  instrument_id:
    type: integer
    minimum: 1
    description: "Internal instrument identifier"
  
  open_price:
    type: number
    multipleOf: 0.0001
    minimum: 0
    maximum: 1000000
    description: "Opening price"
  
  high_price:
    type: number
    multipleOf: 0.0001
    minimum: 0
    maximum: 1000000
    description: "High price"
  
  low_price:
    type: number
    multipleOf: 0.0001
    minimum: 0
    maximum: 1000000
    description: "Low price"
  
  close_price:
    type: number
    multipleOf: 0.0001
    minimum: 0
    maximum: 1000000
    description: "Closing price"
  
  volume:
    type: integer
    minimum: 0
    description: "Trading volume"

required:
  - timestamp
  - instrument_id
  - open_price
  - high_price
  - low_price
  - close_price

additionalProperties: false

# Custom validation rules
custom_validations:
  price_consistency:
    rule: "high_price >= low_price"
    error_message: "High price must be greater than or equal to low price"
  
  ohlc_range:
    rule: "low_price <= open_price <= high_price AND low_price <= close_price <= high_price"
    error_message: "Open and close prices must be within high/low range"
```

## Error Handling and Quarantine

### Quarantine Management

```python
from src.transformation.quarantine.manager import QuarantineManager

quarantine = QuarantineManager()

# Process batch with automatic quarantine
result = engine.transform_with_quarantine(
    data=raw_data,
    mapping_config="databento_mappings.yaml"
)

print(f"Successfully transformed: {len(result.valid_records)}")
print(f"Quarantined records: {len(result.quarantined_records)}")

# Analyze quarantined records
for record in result.quarantined_records:
    print(f"Record ID: {record.id}")
    print(f"Errors: {record.errors}")
    print(f"Original data: {record.original_data}")
```

### Error Analysis

```python
# Generate error report
error_report = quarantine.generate_error_report(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)

print(f"Total quarantined records: {error_report.total_records}")
print(f"Most common errors: {error_report.error_frequency}")

# Export quarantined data for analysis
quarantine.export_quarantined_data(
    output_file="quarantine_analysis.csv",
    include_errors=True,
    include_original_data=True
)
```

## Performance Optimization

### Batch Processing

```python
# Optimize for large datasets
config = {
    "batch_size": 10000,           # Process in larger batches
    "parallel_workers": 4,         # Use multiple workers
    "memory_limit_mb": 512,        # Memory usage limit
    "enable_caching": True,        # Cache transformation rules
    "validation_level": "basic"    # Reduce validation overhead
}

engine = RuleEngine(config)
result = engine.transform_large_dataset(data_iterator, mapping_config)
```

### Rule Optimization

```python
# Pre-compile transformation rules
engine.precompile_rules("databento_mappings.yaml")

# Use optimized field mapping
optimized_mapping = engine.optimize_field_mapping(
    source_fields=["ts_event", "open", "high", "low", "close"],
    target_fields=["timestamp", "open_price", "high_price", "low_price", "close_price"]
)
```

## Configuration Management

### Environment-Specific Configurations

```yaml
# transformation_config.yaml
default:
  validation_level: "strict"
  enable_quarantine: true
  max_error_threshold: 0.05  # 5% error threshold

development:
  validation_level: "basic"
  enable_quarantine: false
  max_error_threshold: 0.10

production:
  validation_level: "strict"
  enable_quarantine: true
  max_error_threshold: 0.01  # 1% error threshold
  enable_monitoring: true
```

### Dynamic Rule Loading

```python
# Load rules at runtime
engine.load_mapping_config("databento_mappings.yaml")
engine.reload_validation_schemas()

# Hot-reload configuration changes
engine.watch_config_changes(
    config_directory="mapping_configs/",
    auto_reload=True
)
```

## Best Practices

### Rule Design
- Keep transformation rules simple and testable
- Use declarative configurations over imperative code
- Document all transformation logic with examples
- Version control mapping configurations

### Validation Strategy
- Implement multiple validation layers (schema, business rules, data quality)
- Use appropriate validation levels for different environments
- Monitor validation error rates and patterns
- Quarantine invalid data for analysis rather than dropping

### Performance
- Batch process data for efficiency
- Use appropriate worker counts for CPU-bound transformations
- Monitor memory usage during large dataset processing
- Cache compiled rules and schemas

### Error Handling
- Provide detailed error messages with context
- Log transformation failures with original data
- Implement retry logic for transient failures
- Generate regular reports on data quality issues

### Testing
- Write unit tests for all transformation rules
- Test with representative data samples
- Validate performance with large datasets
- Test error conditions and edge cases 