# Transformation Layer Integration Example

This document demonstrates how to integrate the transformation layer with existing pipeline components, specifically showing how to use the RuleEngine with the DatabentoAdapter to create a complete data processing pipeline.

## Overview

The transformation layer sits between the DatabentoAdapter (which produces validated Pydantic models) and the storage layer (which expects standardized data dictionaries). This integration example shows how to connect these components.

## Basic Integration Pattern

### 1. Simple Pipeline Integration

```python
from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
from src.transformation.rule_engine import create_rule_engine
from src.storage.models import DATABENTO_SCHEMA_MODEL_MAPPING

class DataProcessingPipeline:
    """Complete data processing pipeline with transformation."""
    
    def __init__(self, adapter_config, transformation_config_path):
        self.adapter = DatabentoAdapter(adapter_config)
        self.transformer = create_rule_engine(transformation_config_path)
        
    def process_job(self, job_config):
        """Process a complete data ingestion job."""
        # Connect to data source
        self.adapter.connect()
        
        try:
            # Fetch raw data
            raw_records = self.adapter.fetch_historical_data(job_config)
            
            # Transform data
            transformed_records = []
            schema_type = self._get_schema_type(job_config["schema"])
            
            for record in raw_records:
                try:
                    transformed = self.transformer.transform_record(record, schema_type)
                    transformed_records.append(transformed)
                except Exception as e:
                    self._handle_transformation_error(record, e)
            
            return transformed_records
            
        finally:
            self.adapter.disconnect()
    
    def _get_schema_type(self, databento_schema):
        """Map Databento schema to transformation schema type."""
        schema_mapping = {
            "ohlcv-1d": "ohlcv",
            "ohlcv-1m": "ohlcv", 
            "trades": "trades",
            "tbbo": "tbbo",
            "statistics": "statistics"
        }
        return schema_mapping.get(databento_schema, databento_schema)
    
    def _handle_transformation_error(self, record, error):
        """Handle transformation errors."""
        print(f"Transformation failed for record: {error}")
        # In production: log error, quarantine record, etc.
```

### 2. Streaming Pipeline with Error Handling

```python
from typing import Iterator, Tuple, Optional
from src.transformation.rule_engine.engine import ValidationRuleError, TransformationError

class StreamingTransformationPipeline:
    """Streaming pipeline that processes records as they arrive."""
    
    def __init__(self, adapter_config, transformation_config_path):
        self.adapter = DatabentoAdapter(adapter_config)
        self.transformer = create_rule_engine(transformation_config_path)
        self.stats = {
            'processed': 0,
            'transformed': 0,
            'validation_errors': 0,
            'transformation_errors': 0
        }
    
    def stream_transformed_data(
        self, 
        job_config
    ) -> Iterator[Tuple[Optional[dict], Optional[Exception]]]:
        """
        Stream transformed data with error information.
        
        Yields:
            Tuple of (transformed_record, error) where one is None
        """
        self.adapter.connect()
        
        try:
            schema_type = self._get_schema_type(job_config["schema"])
            
            for record in self.adapter.fetch_historical_data(job_config):
                self.stats['processed'] += 1
                
                try:
                    transformed = self.transformer.transform_record(record, schema_type)
                    self.stats['transformed'] += 1
                    yield (transformed, None)
                    
                except ValidationRuleError as e:
                    self.stats['validation_errors'] += 1
                    yield (None, e)
                    
                except TransformationError as e:
                    self.stats['transformation_errors'] += 1
                    yield (None, e)
                    
        finally:
            self.adapter.disconnect()
    
    def get_processing_stats(self):
        """Get processing statistics."""
        return self.stats.copy()
```

## Advanced Integration Patterns

### 3. Batch Processing with Quarantine

```python
import json
from pathlib import Path
from datetime import datetime

class BatchTransformationPipeline:
    """Batch processing pipeline with quarantine and monitoring."""
    
    def __init__(self, adapter_config, transformation_config_path, quarantine_dir="./quarantine"):
        self.adapter = DatabentoAdapter(adapter_config)
        self.transformer = create_rule_engine(transformation_config_path)
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(exist_ok=True)
        
    def process_batch(self, job_config, batch_size=1000):
        """Process data in batches with quarantine support."""
        self.adapter.connect()
        
        try:
            schema_type = self._get_schema_type(job_config["schema"])
            batch = []
            batch_number = 0
            
            for record in self.adapter.fetch_historical_data(job_config):
                batch.append(record)
                
                if len(batch) >= batch_size:
                    self._process_batch_chunk(batch, schema_type, batch_number)
                    batch = []
                    batch_number += 1
            
            # Process remaining records
            if batch:
                self._process_batch_chunk(batch, schema_type, batch_number)
                
        finally:
            self.adapter.disconnect()
    
    def _process_batch_chunk(self, batch, schema_type, batch_number):
        """Process a single batch chunk."""
        successful_transforms = []
        
        for i, record in enumerate(batch):
            try:
                transformed = self.transformer.transform_record(record, schema_type)
                successful_transforms.append(transformed)
                
            except (ValidationRuleError, TransformationError) as e:
                self._quarantine_record(record, e, batch_number, i)
        
        # Process successful transforms (e.g., save to database)
        if successful_transforms:
            self._save_transformed_batch(successful_transforms, batch_number)
    
    def _quarantine_record(self, record, error, batch_number, record_index):
        """Quarantine failed record with metadata."""
        quarantine_data = {
            'timestamp': datetime.now().isoformat(),
            'batch_number': batch_number,
            'record_index': record_index,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'record_data': record.model_dump() if hasattr(record, 'model_dump') else str(record)
        }
        
        filename = f"quarantine_batch_{batch_number}_record_{record_index}.json"
        quarantine_file = self.quarantine_dir / filename
        
        with open(quarantine_file, 'w') as f:
            json.dump(quarantine_data, f, indent=2, default=str)
    
    def _save_transformed_batch(self, transformed_records, batch_number):
        """Save transformed batch (placeholder for actual storage logic)."""
        print(f"Saving batch {batch_number} with {len(transformed_records)} records")
        # In production: save to database, file, etc.
```

### 4. Multi-Schema Pipeline

```python
class MultiSchemaTransformationPipeline:
    """Pipeline that handles multiple schemas in a single job."""
    
    def __init__(self, adapter_config, transformation_config_path):
        self.adapter = DatabentoAdapter(adapter_config)
        self.transformer = create_rule_engine(transformation_config_path)
        
    def process_multi_schema_job(self, base_job_config, schemas):
        """Process multiple schemas for the same symbols and date range."""
        self.adapter.connect()
        
        try:
            results = {}
            
            for schema in schemas:
                job_config = base_job_config.copy()
                job_config["schema"] = schema
                
                schema_type = self._get_schema_type(schema)
                transformed_records = []
                
                print(f"Processing schema: {schema}")
                
                for record in self.adapter.fetch_historical_data(job_config):
                    try:
                        transformed = self.transformer.transform_record(record, schema_type)
                        transformed_records.append(transformed)
                    except Exception as e:
                        print(f"Error transforming {schema} record: {e}")
                
                results[schema] = transformed_records
                print(f"Completed {schema}: {len(transformed_records)} records")
            
            return results
            
        finally:
            self.adapter.disconnect()
```

## Configuration Examples

### Pipeline Configuration

```python
# Example configuration for the complete pipeline
pipeline_config = {
    "adapter": {
        "api": {
            "key_env_var": "DATABENTO_API_KEY"
        },
        "retry_policy": {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 60.0,
            "backoff_multiplier": 2.0
        }
    },
    "transformation": {
        "config_path": "src/transformation/mapping_configs/databento_mappings.yaml",
        "validation_enabled": True,
        "quarantine_enabled": True
    },
    "storage": {
        "batch_size": 1000,
        "connection_string": "postgresql://user:pass@localhost/db"
    }
}
```

### Job Configuration

```python
# Example job configuration
job_config = {
    "name": "AAPL_OHLCV_Historical",
    "dataset": "GLBX.MDP3",
    "schema": "ohlcv-1d",
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "stype_in": "continuous",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "date_chunk_interval_days": 7
}
```

## Usage Examples

### Basic Usage

```python
# Initialize pipeline
pipeline = DataProcessingPipeline(
    adapter_config=pipeline_config["adapter"],
    transformation_config_path=pipeline_config["transformation"]["config_path"]
)

# Process job
transformed_data = pipeline.process_job(job_config)
print(f"Processed {len(transformed_data)} records")
```

### Streaming Usage

```python
# Initialize streaming pipeline
streaming_pipeline = StreamingTransformationPipeline(
    adapter_config=pipeline_config["adapter"],
    transformation_config_path=pipeline_config["transformation"]["config_path"]
)

# Process streaming data
for transformed_record, error in streaming_pipeline.stream_transformed_data(job_config):
    if error:
        print(f"Error: {error}")
    else:
        # Process successful transformation
        print(f"Transformed: {transformed_record['symbol']} at {transformed_record['ts_event']}")

# Get statistics
stats = streaming_pipeline.get_processing_stats()
print(f"Processing stats: {stats}")
```

### Batch Processing Usage

```python
# Initialize batch pipeline
batch_pipeline = BatchTransformationPipeline(
    adapter_config=pipeline_config["adapter"],
    transformation_config_path=pipeline_config["transformation"]["config_path"],
    quarantine_dir="./data_quarantine"
)

# Process in batches
batch_pipeline.process_batch(job_config, batch_size=500)
```

### Multi-Schema Usage

```python
# Initialize multi-schema pipeline
multi_pipeline = MultiSchemaTransformationPipeline(
    adapter_config=pipeline_config["adapter"],
    transformation_config_path=pipeline_config["transformation"]["config_path"]
)

# Process multiple schemas
base_config = {
    "dataset": "GLBX.MDP3",
    "symbols": ["AAPL"],
    "stype_in": "continuous",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-02T00:00:00Z"
}

schemas = ["ohlcv-1d", "trades", "tbbo"]
results = multi_pipeline.process_multi_schema_job(base_config, schemas)

for schema, records in results.items():
    print(f"{schema}: {len(records)} records")
```

## Error Handling and Monitoring

### Comprehensive Error Handling

```python
class RobustTransformationPipeline:
    """Pipeline with comprehensive error handling and monitoring."""
    
    def __init__(self, adapter_config, transformation_config_path):
        self.adapter = DatabentoAdapter(adapter_config)
        self.transformer = create_rule_engine(transformation_config_path)
        self.error_counts = {}
        
    def process_with_monitoring(self, job_config):
        """Process with detailed error monitoring."""
        self.adapter.connect()
        
        try:
            schema_type = self._get_schema_type(job_config["schema"])
            successful_records = []
            
            for record in self.adapter.fetch_historical_data(job_config):
                try:
                    transformed = self.transformer.transform_record(record, schema_type)
                    successful_records.append(transformed)
                    
                except ValidationRuleError as e:
                    self._track_error("validation", str(e))
                    
                except TransformationError as e:
                    self._track_error("transformation", str(e))
                    
                except Exception as e:
                    self._track_error("unexpected", str(e))
            
            return successful_records, self.error_counts
            
        finally:
            self.adapter.disconnect()
    
    def _track_error(self, error_type, error_message):
        """Track error occurrences."""
        if error_type not in self.error_counts:
            self.error_counts[error_type] = {}
        
        if error_message not in self.error_counts[error_type]:
            self.error_counts[error_type][error_message] = 0
            
        self.error_counts[error_type][error_message] += 1
```

## Performance Considerations

### Memory-Efficient Processing

```python
def memory_efficient_pipeline(adapter_config, transformation_config_path, job_config):
    """Memory-efficient pipeline for large datasets."""
    adapter = DatabentoAdapter(adapter_config)
    transformer = create_rule_engine(transformation_config_path)
    
    adapter.connect()
    
    try:
        schema_type = _get_schema_type(job_config["schema"])
        
        # Process records one at a time to minimize memory usage
        for record in adapter.fetch_historical_data(job_config):
            try:
                transformed = transformer.transform_record(record, schema_type)
                
                # Immediately process/save the transformed record
                yield transformed
                
            except Exception as e:
                # Log error and continue
                print(f"Error processing record: {e}")
                continue
                
    finally:
        adapter.disconnect()
```

This integration example demonstrates how to effectively combine the transformation layer with existing pipeline components to create robust, scalable data processing workflows. 