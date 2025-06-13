# Transformation Configuration Examples and Usage Patterns

This document provides practical examples and usage patterns for the transformation module, demonstrating real-world scenarios and best practices.

## Configuration Examples

### Basic OHLCV Mapping

```yaml
# Simple OHLCV mapping with validation
version: "1.0"
description: "Basic OHLCV transformation example"

schema_mappings:
  ohlcv:
    source_model: "DatabentoOHLCVRecord"
    target_schema: "daily_ohlcv_data"
    
    field_mappings:
      ts_event: "ts_event"
      symbol: "symbol"
      open: "open_price"
      high: "high_price"
      low: "low_price"
      close: "close_price"
      volume: "volume"
      
    transformations:
      price_validation:
        fields: ["open_price", "high_price", "low_price", "close_price"]
        rule: "value > 0"
        
      ohlcv_integrity:
        rule: "high_price >= low_price"
        
    defaults:
      granularity: "1d"
      data_source: "databento"

global_settings:
  timezone_normalization: "UTC"
  price_precision: 8
```

### Complex Multi-Schema Configuration

```yaml
# Complete multi-schema configuration
version: "1.0"
description: "Comprehensive Databento mappings for all schemas"

schema_mappings:
  ohlcv:
    source_model: "DatabentoOHLCVRecord"
    target_schema: "daily_ohlcv_data"
    description: "OHLCV data transformation"
    
    field_mappings:
      ts_event: "ts_event"
      ts_recv: "ts_recv"
      symbol: "symbol"
      open: "open_price"
      high: "high_price"
      low: "low_price"
      close: "close_price"
      volume: "volume"
      
    transformations:
      price_validation:
        fields: ["open_price", "high_price", "low_price", "close_price"]
        rule: "value > 0"
      volume_validation:
        fields: ["volume"]
        rule: "value >= 0"
      ohlcv_integrity:
        rule: "high_price >= low_price and high_price >= open_price and high_price >= close_price and low_price <= open_price and low_price <= close_price"
        
    defaults:
      granularity: "1d"
      data_source: "databento"

  trades:
    source_model: "DatabentoTradeRecord"
    target_schema: "trades_data"
    description: "Trade data transformation"
    
    field_mappings:
      ts_event: "ts_event"
      ts_recv: "ts_recv"
      symbol: "symbol"
      price: "price"
      size: "size"
      side: "side"
      
    transformations:
      price_validation:
        fields: ["price"]
        rule: "value > 0"
      size_validation:
        fields: ["size"]
        rule: "value > 0"
        
    defaults:
      data_source: "databento"

  tbbo:
    source_model: "DatabentoTBBORecord"
    target_schema: "tbbo_data"
    description: "Top of book data transformation"
    
    field_mappings:
      ts_event: "ts_event"
      ts_recv: "ts_recv"
      symbol: "symbol"
      bid_px: "bid_price"
      ask_px: "ask_price"
      bid_sz: "bid_size"
      ask_sz: "ask_size"
      
    transformations:
      price_validation:
        fields: ["bid_price", "ask_price"]
        rule: "value > 0"
      size_validation:
        fields: ["bid_size", "ask_size"]
        rule: "value > 0"
      bid_ask_spread:
        rule: "ask_price > bid_price"
        
    defaults:
      data_source: "databento"

conditional_mappings:
  statistics:
    - condition: "stat_type == 'volume'"
      field_mappings:
        value: "volume_stat"
        ts_event: "ts_event"
        symbol: "symbol"
    - condition: "stat_type == 'price'"
      field_mappings:
        value: "price_stat"
        ts_event: "ts_event"
        symbol: "symbol"

global_settings:
  timezone_normalization: "UTC"
  price_precision: 8
  skip_validation_errors: false
```

### Advanced Validation Rules

```yaml
# Advanced validation patterns
transformations:
  # Range validation
  price_range_check:
    fields: ["price"]
    rule: "value >= 0.01 and value <= 100000"
    
  # Percentage validation
  percentage_fields:
    fields: ["change_percent"]
    rule: "value >= -100 and value <= 1000"
    
  # Conditional validation
  volume_conditional:
    rule: "volume > 0 if trade_type == 'executed' else volume >= 0"
    
  # Cross-field validation
  timestamp_order:
    rule: "ts_recv >= ts_event"
    
  # Null handling
  required_fields:
    rule: "symbol is not null and price is not null"
    
  # Complex business rules
  market_hours:
    rule: "ts_event.hour >= 9 and ts_event.hour <= 16"
    
  # Statistical validation
  outlier_detection:
    fields: ["price"]
    rule: "value <= (avg_price * 3)"  # Simple outlier check
```

## Usage Patterns

### Basic Usage

```python
from src.transformation.rule_engine import create_rule_engine

# Initialize engine
engine = create_rule_engine("src/transformation/mapping_configs/databento_mappings.yaml")

# Transform single record
ohlcv_record = DatabentoOHLCVRecord(...)
result = engine.transform_record(ohlcv_record, "ohlcv")

# Result is ready for database insertion
print(result)
# {
#   'ts_event': datetime(...),
#   'symbol': 'AAPL',
#   'open_price': Decimal('150.00'),
#   'high_price': Decimal('155.00'),
#   ...
# }
```

### Batch Processing

```python
# Process multiple records efficiently
records = [record1, record2, record3, ...]
results = engine.transform_batch(records, "ohlcv")

# Process in chunks for large datasets
def process_large_dataset(records, chunk_size=1000):
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        transformed_chunk = engine.transform_batch(chunk, "ohlcv")
        yield transformed_chunk
```

### Error Handling Patterns

```python
from src.transformation.rule_engine.engine import TransformationError, ValidationRuleError

def safe_transform(engine, record, schema_type):
    """Transform with comprehensive error handling."""
    try:
        return engine.transform_record(record, schema_type)
    except ValidationRuleError as e:
        logger.warning(f"Validation failed: {e}")
        # Quarantine record for review
        quarantine_record(record, "validation_failure", str(e))
        return None
    except TransformationError as e:
        logger.error(f"Transformation failed: {e}")
        # Quarantine record for investigation
        quarantine_record(record, "transformation_failure", str(e))
        return None
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        raise
```

### Pipeline Integration

```python
class DataTransformationPipeline:
    """Complete data transformation pipeline."""
    
    def __init__(self, config_path):
        self.engine = create_rule_engine(config_path)
        self.quarantine = QuarantineHandler()
        
    def process_records(self, records, schema_type):
        """Process records with error handling and quarantine."""
        successful_transforms = []
        failed_transforms = []
        
        for record in records:
            try:
                transformed = self.engine.transform_record(record, schema_type)
                successful_transforms.append(transformed)
            except (ValidationRuleError, TransformationError) as e:
                self.quarantine.quarantine_record(record, type(e).__name__, str(e))
                failed_transforms.append((record, e))
                
        return successful_transforms, failed_transforms
    
    def get_schema_for_record(self, record):
        """Automatically determine schema type from record."""
        model_name = type(record).__name__
        return self.engine.get_target_schema_for_model(model_name)
```

### Performance Optimization

```python
# High-performance transformation for trusted data
def fast_transform(engine, records, schema_type):
    """Fast transformation with validation disabled."""
    return engine.transform_batch(
        records, 
        schema_type, 
        validate=False  # Skip validation for performance
    )

# Memory-efficient processing
def memory_efficient_transform(engine, record_iterator, schema_type, batch_size=1000):
    """Process large datasets without loading all into memory."""
    batch = []
    for record in record_iterator:
        batch.append(record)
        if len(batch) >= batch_size:
            yield engine.transform_batch(batch, schema_type)
            batch = []
    
    # Process remaining records
    if batch:
        yield engine.transform_batch(batch, schema_type)
```

## Real-World Scenarios

### Scenario 1: Multi-Provider Data Ingestion

```python
class MultiProviderPipeline:
    """Handle data from multiple providers with different schemas."""
    
    def __init__(self):
        self.engines = {
            'databento': create_rule_engine('databento_mappings.yaml'),
            'alpha_vantage': create_rule_engine('alpha_vantage_mappings.yaml'),
            'yahoo': create_rule_engine('yahoo_mappings.yaml')
        }
    
    def transform_record(self, record, provider):
        """Transform record based on provider."""
        engine = self.engines[provider]
        schema_type = self.detect_schema_type(record)
        return engine.transform_record(record, schema_type)
    
    def detect_schema_type(self, record):
        """Auto-detect schema type from record."""
        model_name = type(record).__name__
        if 'OHLCV' in model_name:
            return 'ohlcv'
        elif 'Trade' in model_name:
            return 'trades'
        elif 'TBBO' in model_name:
            return 'tbbo'
        else:
            raise ValueError(f"Unknown record type: {model_name}")
```

### Scenario 2: Data Quality Monitoring

```python
class DataQualityMonitor:
    """Monitor transformation quality and generate reports."""
    
    def __init__(self, engine):
        self.engine = engine
        self.stats = {
            'total_records': 0,
            'successful_transforms': 0,
            'validation_failures': 0,
            'transformation_errors': 0
        }
    
    def transform_with_monitoring(self, record, schema_type):
        """Transform with quality monitoring."""
        self.stats['total_records'] += 1
        
        try:
            result = self.engine.transform_record(record, schema_type)
            self.stats['successful_transforms'] += 1
            return result
        except ValidationRuleError:
            self.stats['validation_failures'] += 1
            raise
        except TransformationError:
            self.stats['transformation_errors'] += 1
            raise
    
    def get_quality_report(self):
        """Generate data quality report."""
        total = self.stats['total_records']
        if total == 0:
            return "No records processed"
        
        success_rate = (self.stats['successful_transforms'] / total) * 100
        validation_failure_rate = (self.stats['validation_failures'] / total) * 100
        
        return f"""
        Data Quality Report:
        - Total Records: {total}
        - Success Rate: {success_rate:.2f}%
        - Validation Failures: {validation_failure_rate:.2f}%
        - Transformation Errors: {self.stats['transformation_errors']}
        """
```

### Scenario 3: Dynamic Configuration Updates

```python
class DynamicTransformationEngine:
    """Engine that supports runtime configuration updates."""
    
    def __init__(self, initial_config_path):
        self.config_path = initial_config_path
        self.engine = create_rule_engine(initial_config_path)
        self.last_modified = os.path.getmtime(initial_config_path)
    
    def transform_record(self, record, schema_type):
        """Transform with automatic config reload."""
        self._check_config_update()
        return self.engine.transform_record(record, schema_type)
    
    def _check_config_update(self):
        """Check if configuration file has been updated."""
        current_modified = os.path.getmtime(self.config_path)
        if current_modified > self.last_modified:
            logger.info("Configuration updated, reloading...")
            self.engine = create_rule_engine(self.config_path)
            self.last_modified = current_modified
```

## Testing Patterns

### Unit Test Examples

```python
class TestTransformationPatterns:
    """Comprehensive test patterns for transformation."""
    
    @pytest.fixture
    def engine(self):
        return create_rule_engine("test_mappings.yaml")
    
    def test_successful_transformation(self, engine):
        """Test successful record transformation."""
        record = DatabentoOHLCVRecord(
            ts_event=datetime.now(timezone.utc),
            symbol="AAPL",
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.50"),
            volume=Decimal("1000000")
        )
        
        result = engine.transform_record(record, "ohlcv")
        
        assert result["symbol"] == "AAPL"
        assert result["open_price"] == Decimal("150.00")
        assert "data_source" in result
    
    def test_validation_failure(self, engine):
        """Test validation rule failures."""
        invalid_record = DatabentoOHLCVRecord(
            ts_event=datetime.now(timezone.utc),
            symbol="AAPL",
            open=Decimal("-10.00"),  # Invalid negative price
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.50"),
            volume=Decimal("1000000")
        )
        
        with pytest.raises(ValidationRuleError):
            engine.transform_record(invalid_record, "ohlcv")
    
    def test_batch_processing(self, engine):
        """Test batch transformation."""
        records = [create_test_record() for _ in range(10)]
        results = engine.transform_batch(records, "ohlcv")
        
        assert len(results) == 10
        assert all("symbol" in result for result in results)
    
    @pytest.mark.parametrize("schema_type", ["ohlcv", "trades", "tbbo"])
    def test_multiple_schemas(self, engine, schema_type):
        """Test transformation across different schemas."""
        record = create_test_record_for_schema(schema_type)
        result = engine.transform_record(record, schema_type)
        
        assert result is not None
        assert "data_source" in result
```

### Integration Test Examples

```python
def test_end_to_end_pipeline():
    """Test complete pipeline integration."""
    # Setup
    adapter = DatabentoAdapter(test_config)
    engine = create_rule_engine("databento_mappings.yaml")
    storage = MockStorageLayer()
    
    # Execute
    records = adapter.fetch_test_data()
    transformed_records = []
    
    for record in records:
        schema_type = detect_schema_type(record)
        transformed = engine.transform_record(record, schema_type)
        transformed_records.append(transformed)
    
    # Store
    storage.bulk_insert(transformed_records)
    
    # Verify
    assert len(transformed_records) == len(records)
    assert storage.insert_count == len(records)
```

## Configuration Management

### Environment-Specific Configurations

```yaml
# development.yaml
global_settings:
  skip_validation_errors: true  # Allow processing to continue
  log_transformation_details: true
  price_precision: 8

# production.yaml  
global_settings:
  skip_validation_errors: false  # Strict validation
  log_transformation_details: false
  price_precision: 8
```

### Configuration Versioning

```yaml
# Version tracking in configuration
version: "2.1"
description: "Updated Databento mappings with enhanced validation"

changelog:
  - version: "2.1"
    date: "2024-01-15"
    changes:
      - "Added outlier detection for price fields"
      - "Enhanced OHLCV integrity validation"
      - "Added support for new statistics fields"
  - version: "2.0"
    date: "2024-01-01"
    changes:
      - "Major refactor of validation rules"
      - "Added conditional mappings for statistics"
```

This comprehensive guide provides practical examples and patterns for using the transformation module effectively in various scenarios. Use these patterns as starting points for your specific use cases. 