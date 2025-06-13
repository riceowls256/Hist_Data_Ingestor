# Ingestion Module

The ingestion module is responsible for fetching, normalizing, and integrating data from external APIs. It implements a robust adapter pattern that provides a consistent interface across different data providers while handling provider-specific nuances, error conditions, and data formats.

## Overview

The ingestion layer serves as the entry point for all external data into the system. It abstracts away the complexities of different API providers and delivers validated, normalized data to the transformation layer.

### Key Features

- **Unified Adapter Interface**: Consistent API across all data providers
- **Robust Error Handling**: Comprehensive retry logic and error recovery
- **Configuration-Driven**: Flexible configuration for different providers and environments
- **Data Validation**: Automatic conversion to validated Pydantic models
- **Performance Optimization**: Date chunking, batch processing, and connection pooling
- **Comprehensive Logging**: Structured logging for monitoring and debugging

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   External      │    │    Ingestion     │    │ Transformation  │
│   APIs          │───▶│    Module        │───▶│    Layer        │
│ (Databento, IB)│    │  (API Adapters)  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ Configuration│
                       │   & Retry    │
                       │   Policies   │
                       └──────────────┘
```

## Key Components

### 1. `api_adapters/` - API Adapter Implementations

Contains adapter classes for specific data providers, all implementing the `BaseAdapter` interface.

#### `base_adapter.py` - Abstract Base Class

Defines the common interface that all API adapters must implement:

```python
class BaseAdapter(ABC):
    """Abstract base class for all API data adapters."""
    
    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the API."""
        
    @abstractmethod
    def fetch_historical_data(self, job_config: Dict[str, Any]) -> Iterator[BaseModel]:
        """Fetch historical data based on job configuration."""
        
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the adapter configuration."""
        
    def disconnect(self) -> None:
        """Close connection to the API."""
```

**Features:**
- Context manager support (`__enter__`/`__exit__`)
- Consistent error handling patterns
- Configuration validation interface
- Connection lifecycle management

#### `databento_adapter.py` - Databento API Implementation

Production-ready adapter for the Databento market data API.

**Key Features:**
- **Official Client Integration**: Uses `databento-python` client library
- **Comprehensive Retry Logic**: Tenacity-based retries with exponential backoff
- **Date Chunking**: Automatic chunking for large date ranges
- **Multi-Schema Support**: OHLCV, Trades, TBBO, Statistics schemas
- **Pydantic Conversion**: Automatic conversion to validated models
- **Structured Logging**: Detailed logging for monitoring and debugging

**Configuration Structure:**
```yaml
api:
  key_env_var: "DATABENTO_API_KEY"
retry_policy:
  max_retries: 3
  base_delay: 1.0
  max_delay: 60.0
  backoff_multiplier: 2.0
```

**Supported Schemas:**
- `ohlcv-1d`, `ohlcv-1m` → `DatabentoOHLCVRecord`
- `trades` → `DatabentoTradeRecord`
- `tbbo` → `DatabentoTBBORecord`
- `statistics` → `DatabentoStatisticsRecord`

#### `interactive_brokers_adapter.py` - Interactive Brokers (Placeholder)

Reserved for future Interactive Brokers API integration.

### 2. `data_fetcher.py` - High-Level Data Fetching (Future)

Reserved for orchestration logic that coordinates multiple adapters and data sources.

## Usage Patterns

### Basic Usage

```python
from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter

# Initialize adapter
config = {
    "api": {"key_env_var": "DATABENTO_API_KEY"},
    "retry_policy": {"max_retries": 3, "base_delay": 1.0}
}
adapter = DatabentoAdapter(config)

# Connect and fetch data
adapter.connect()
try:
    job_config = {
        "dataset": "GLBX.MDP3",
        "schema": "ohlcv-1d",
        "symbols": ["AAPL", "MSFT"],
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-01-31T23:59:59Z",
        "stype_in": "continuous"
    }
    
    for record in adapter.fetch_historical_data(job_config):
        print(f"Fetched: {record.symbol} at {record.ts_event}")
        
finally:
    adapter.disconnect()
```

### Context Manager Usage

```python
# Automatic connection management
with DatabentoAdapter(config) as adapter:
    for record in adapter.fetch_historical_data(job_config):
        process_record(record)
```

### Date Chunking for Large Ranges

```python
job_config = {
    "dataset": "GLBX.MDP3",
    "schema": "trades",
    "symbols": ["AAPL"],
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z",
    "date_chunk_interval_days": 7,  # Process in weekly chunks
    "stype_in": "continuous"
}

with DatabentoAdapter(config) as adapter:
    for record in adapter.fetch_historical_data(job_config):
        # Records are automatically chunked and processed
        yield record
```

## Configuration Management

### Environment-Based Configuration

```python
# Production configuration
production_config = {
    "api": {
        "key_env_var": "DATABENTO_API_KEY_PROD"
    },
    "retry_policy": {
        "max_retries": 5,
        "base_delay": 2.0,
        "max_delay": 120.0,
        "backoff_multiplier": 2.0
    }
}

# Development configuration
development_config = {
    "api": {
        "key_env_var": "DATABENTO_API_KEY_DEV"
    },
    "retry_policy": {
        "max_retries": 2,
        "base_delay": 0.5,
        "max_delay": 30.0,
        "backoff_multiplier": 1.5
    }
}
```

### Job Configuration Examples

```python
# OHLCV Daily Data
ohlcv_job = {
    "name": "AAPL_Daily_OHLCV",
    "dataset": "GLBX.MDP3",
    "schema": "ohlcv-1d",
    "symbols": ["AAPL"],
    "stype_in": "continuous",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z"
}

# Trade Data with Chunking
trades_job = {
    "name": "Multi_Symbol_Trades",
    "dataset": "GLBX.MDP3",
    "schema": "trades",
    "symbols": ["AAPL", "MSFT", "GOOGL"],
    "stype_in": "continuous",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-07T23:59:59Z",
    "date_chunk_interval_days": 1  # Daily chunks
}

# Top of Book Data
tbbo_job = {
    "name": "AAPL_TBBO",
    "dataset": "GLBX.MDP3",
    "schema": "tbbo",
    "symbols": ["AAPL"],
    "stype_in": "continuous",
    "start_date": "2024-01-01T09:30:00Z",
    "end_date": "2024-01-01T16:00:00Z"
}
```

## Error Handling and Resilience

### Retry Logic

The DatabentoAdapter implements sophisticated retry logic using the Tenacity library:

```python
# Automatic retry configuration
@retry(
    stop=stop_after_attempt(max_retries),
    wait=wait_exponential(multiplier=backoff_multiplier, min=base_delay, max=max_delay),
    retry=retry_if_exception_type((databento.BentoError, ConnectionError, TimeoutError))
)
def _make_api_call():
    return self._client.timeseries.get_range(...)
```

**Retry Scenarios:**
- **API Rate Limits**: Automatic backoff with exponential delay
- **Network Timeouts**: Retry with increasing delays
- **Temporary API Errors**: Configurable retry attempts
- **Connection Issues**: Automatic reconnection attempts

### Error Types and Handling

```python
try:
    with DatabentoAdapter(config) as adapter:
        for record in adapter.fetch_historical_data(job_config):
            process_record(record)
            
except ValueError as e:
    # Configuration or job parameter errors
    logger.error(f"Invalid configuration: {e}")
    
except ConnectionError as e:
    # API connection failures
    logger.error(f"Connection failed: {e}")
    
except RuntimeError as e:
    # Data fetching failures after retries
    logger.error(f"Data fetch failed: {e}")
    
except ValidationError as e:
    # Pydantic model validation failures
    logger.warning(f"Data validation failed: {e}")
```

## Performance Considerations

### Date Chunking Strategy

```python
# Optimize chunk size based on data volume
chunk_strategies = {
    "ohlcv-1d": 30,      # 30 days per chunk (low volume)
    "ohlcv-1m": 7,       # 7 days per chunk (medium volume)
    "trades": 1,         # 1 day per chunk (high volume)
    "tbbo": 1            # 1 day per chunk (very high volume)
}

job_config["date_chunk_interval_days"] = chunk_strategies[schema]
```

### Memory Management

```python
# Stream processing for large datasets
def process_large_dataset(adapter, job_config):
    """Process large datasets without loading all into memory."""
    for record in adapter.fetch_historical_data(job_config):
        # Process record immediately
        transformed_record = transform(record)
        save_to_database(transformed_record)
        # Record is garbage collected after processing
```

### Connection Pooling (Future Enhancement)

```python
# Future: Connection pool for multiple concurrent jobs
class AdapterPool:
    def __init__(self, config, pool_size=5):
        self.pool = [DatabentoAdapter(config) for _ in range(pool_size)]
    
    def get_adapter(self):
        return self.pool.pop() if self.pool else DatabentoAdapter(config)
    
    def return_adapter(self, adapter):
        self.pool.append(adapter)
```

## Monitoring and Observability

### Structured Logging

The ingestion module uses structured logging for comprehensive observability:

```python
# Example log output
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "logger": "DatabentoAdapter",
    "message": "Fetching data chunk from Databento API",
    "dataset": "GLBX.MDP3",
    "schema": "ohlcv-1d",
    "symbols": ["AAPL", "MSFT"],
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-07T23:59:59Z",
    "chunk_number": 1,
    "total_chunks": 4
}
```

### Metrics and Monitoring

```python
# Key metrics to monitor
metrics = {
    "records_fetched": 0,
    "api_calls_made": 0,
    "retry_attempts": 0,
    "validation_errors": 0,
    "processing_time_ms": 0,
    "data_volume_mb": 0
}
```

## Testing Patterns

### Unit Testing with Mocks

```python
import pytest
from unittest.mock import Mock, patch
from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter

class TestDatabentoAdapter:
    
    @pytest.fixture
    def adapter(self):
        config = {"api": {"key_env_var": "TEST_API_KEY"}}
        return DatabentoAdapter(config)
    
    @patch('databento.Historical')
    def test_fetch_historical_data(self, mock_client, adapter):
        # Mock API response
        mock_store = Mock()
        mock_store.__iter__ = Mock(return_value=iter([mock_record]))
        mock_client.return_value.timeseries.get_range.return_value = mock_store
        
        # Test data fetching
        records = list(adapter.fetch_historical_data(job_config))
        assert len(records) == 1
        assert isinstance(records[0], DatabentoOHLCVRecord)
```

### Integration Testing

```python
# Integration test with real API (requires API key)
@pytest.mark.integration
def test_real_api_integration():
    if not os.getenv("DATABENTO_API_KEY"):
        pytest.skip("API key not available")
    
    config = {"api": {"key_env_var": "DATABENTO_API_KEY"}}
    adapter = DatabentoAdapter(config)
    
    job_config = {
        "dataset": "GLBX.MDP3",
        "schema": "ohlcv-1d",
        "symbols": ["AAPL"],
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-01-02T00:00:00Z"
    }
    
    with adapter:
        records = list(adapter.fetch_historical_data(job_config))
        assert len(records) > 0
```

## Future Enhancements

### Planned Features

1. **Multi-Provider Support**: Unified interface for multiple data providers
2. **Caching Layer**: Redis-based caching for frequently accessed data
3. **Real-Time Streaming**: WebSocket support for live data feeds
4. **Data Quality Monitoring**: Automatic data quality checks and alerts
5. **Rate Limit Management**: Intelligent rate limiting across multiple jobs

### Extension Points

```python
# Future: Plugin architecture for new adapters
class AdapterRegistry:
    adapters = {
        "databento": DatabentoAdapter,
        "interactive_brokers": InteractiveBrokersAdapter,
        "alpha_vantage": AlphaVantageAdapter
    }
    
    @classmethod
    def get_adapter(cls, provider: str, config: dict):
        adapter_class = cls.adapters.get(provider)
        if not adapter_class:
            raise ValueError(f"Unknown provider: {provider}")
        return adapter_class(config)
```

## Best Practices

### Configuration Management

1. **Environment Variables**: Store API keys in environment variables
2. **Configuration Validation**: Validate all configuration before use
3. **Retry Policies**: Configure appropriate retry policies for each environment
4. **Logging Levels**: Use appropriate logging levels for different environments

### Error Handling

1. **Graceful Degradation**: Continue processing when individual records fail
2. **Comprehensive Logging**: Log all errors with sufficient context
3. **Retry Logic**: Implement exponential backoff for transient failures
4. **Circuit Breakers**: Implement circuit breakers for persistent failures

### Performance

1. **Date Chunking**: Use appropriate chunk sizes for different data types
2. **Memory Management**: Process data in streams for large datasets
3. **Connection Reuse**: Reuse connections when possible
4. **Batch Processing**: Process multiple symbols in single API calls when supported

This comprehensive ingestion module provides a robust foundation for fetching data from external APIs while maintaining high reliability, performance, and observability standards. 