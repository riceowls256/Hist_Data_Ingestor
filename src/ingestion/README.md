# Ingestion Module

The ingestion module provides a flexible, extensible framework for collecting historical financial data from multiple API providers. It implements the adapter pattern to support different data sources while maintaining a consistent interface for the pipeline orchestrator.

## Architecture

### API Adapter Pattern

The module uses an adapter pattern to abstract different API providers behind a common interface:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Pipeline        │────│ BaseAPIAdapter   │────│ Specific        │
│ Orchestrator    │    │ (Interface)      │    │ Adapters        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                │                ┌───────▼────────┐
                                │                │ DatabentoAdapter│
                                │                └────────────────┘
                                │                ┌────────────────┐
                                └────────────────│ IBAdapter      │
                                                 │ (Future)       │
                                                 └────────────────┘
```

### Core Components

#### Base API Adapter (`BaseAPIAdapter`)

Abstract base class defining the common interface for all API adapters.

**Required Methods:**
- `extract_data()`: Main extraction method
- `validate_symbols()`: Symbol validation and normalization
- `get_available_schemas()`: Return supported data schemas
- `estimate_request_size()`: Estimate data volume for rate limiting

#### Databento Adapter (`api_adapters/databento_adapter.py`)

Production-ready adapter for Databento's historical data API.

**Features:**
- **Multiple Dataset Support**: GLBX.MDP3 (CME futures), XNAS.ITCH (NASDAQ equities)
- **Schema Support**: OHLCV (all timeframes), Trades, TBBO, Statistics, Definitions
- **Rate Limiting**: Intelligent request batching with respect for API limits
- **Error Recovery**: Automatic retry with exponential backoff
- **Symbol Resolution**: Continuous contract mapping and validation

## Usage Examples

### Basic Data Extraction

```python
from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
from datetime import date

# Initialize adapter
adapter = DatabentoAdapter()

# Extract daily OHLCV data
job_config = {
    "dataset": "GLBX.MDP3",
    "schema": "ohlcv-1d", 
    "symbols": ["ES.c.0", "NQ.c.0"],
    "start_date": date(2024, 1, 1),
    "end_date": date(2024, 1, 31),
    "stype_in": "continuous"
}

data_generator = adapter.extract_data(job_config)

# Process data in chunks
for chunk in data_generator:
    print(f"Received {len(chunk)} records")
    # Data is automatically transformed to common format
```

### Advanced Configuration

```python
# Complex job with custom parameters
job_config = {
    "name": "hourly_es_data",
    "dataset": "GLBX.MDP3",
    "schema": "ohlcv-1h",
    "symbols": ["ES.FUT"],  # Native symbol format
    "stype_in": "native",
    "start_date": date(2024, 1, 1),
    "end_date": date(2024, 3, 31),
    "date_chunk_interval_days": 30,  # Process in 30-day chunks
    "batch_size": 1000,              # Records per batch
    "rate_limit_delay": 1.0          # Delay between requests
}

adapter = DatabentoAdapter()
for batch in adapter.extract_data(job_config):
    print(f"Processing batch: {len(batch)} records")
```

## Supported Data Schemas

### OHLCV (Open, High, Low, Close, Volume)

**Available Timeframes:**
- `ohlcv-1s`: 1-second bars
- `ohlcv-1m`: 1-minute bars  
- `ohlcv-5m`: 5-minute bars
- `ohlcv-15m`: 15-minute bars
- `ohlcv-1h`: 1-hour bars
- `ohlcv-1d`: 1-day bars

**Data Fields:**
```python
{
    "ts_event": datetime,      # Event timestamp
    "instrument_id": int,      # Internal instrument ID
    "open_price": Decimal,     # Opening price
    "high_price": Decimal,     # High price
    "low_price": Decimal,      # Low price
    "close_price": Decimal,    # Closing price
    "volume": int,             # Trading volume
    "granularity": str         # Time granularity
}
```

### Trades

Individual trade records with price, size, and direction.

**Data Fields:**
```python
{
    "ts_event": datetime,      # Trade timestamp
    "instrument_id": int,      # Internal instrument ID
    "price": Decimal,          # Trade price
    "size": int,               # Trade size
    "side": str                # Trade side ('B' or 'S')
}
```

### TBBO (Top of Book Bid/Offer)

Best bid and ask quotes for market depth analysis.

**Data Fields:**
```python
{
    "ts_event": datetime,      # Quote timestamp
    "instrument_id": int,      # Internal instrument ID
    "bid_px_00": Decimal,      # Best bid price
    "ask_px_00": Decimal,      # Best ask price
    "bid_sz_00": int,          # Best bid size
    "ask_sz_00": int           # Best ask size
}
```

### Statistics

Market statistics including settlement prices, open interest, and volume summaries.

**Data Fields:**
```python
{
    "ts_event": datetime,      # Statistic timestamp
    "instrument_id": int,      # Internal instrument ID
    "stat_type": str,          # Statistic type
    "stat_value": Decimal,     # Statistic value
    "update_action": str       # Update action
}
```

### Definitions

Instrument definitions and contract specifications.

**Data Fields:**
```python
{
    "ts_event": datetime,      # Definition timestamp
    "instrument_id": int,      # Internal instrument ID
    "raw_symbol": str,         # Original symbol
    "asset": str,              # Underlying asset
    "exchange": str,           # Trading exchange
    "currency": str,           # Contract currency
    "tick_size": Decimal,      # Minimum price increment
    "multiplier": Decimal      # Contract multiplier
}
```

## Configuration

### Databento Configuration

Configuration is loaded from `configs/api_specific/databento_config.yaml`:

```yaml
api:
  key_env_var: "DATABENTO_API_KEY"
  base_url: "https://hist.databento.com"
  timeout: 30

retry_policy:
  max_retries: 3
  base_delay: 1.0
  max_delay: 60.0
  backoff_multiplier: 2.0
  respect_retry_after: true

jobs:
  - name: "daily_ohlcv"
    dataset: "GLBX.MDP3"
    schema: "ohlcv-1d"
    symbols: ["ES.FUT", "NQ.FUT"]
    stype_in: "continuous"
    start_date: "2024-01-01"
    end_date: "2024-12-31"
    date_chunk_interval_days: 90
```

### Rate Limiting

The Databento adapter implements intelligent rate limiting:

- **Request Batching**: Groups small requests to optimize API usage
- **Exponential Backoff**: Automatic retry with increasing delays
- **Rate Limit Respect**: Honors API rate limit headers
- **Request Size Estimation**: Calculates optimal chunk sizes

## Error Handling

### Common Error Scenarios

**API Authentication Errors:**
```python
from src.ingestion.exceptions import APIAuthenticationError

try:
    adapter = DatabentoAdapter()
    data = adapter.extract_data(job_config)
except APIAuthenticationError as e:
    print(f"Authentication failed: {e}")
    print("Check your DATABENTO_API_KEY environment variable")
```

**Symbol Validation Errors:**
```python
from src.ingestion.exceptions import SymbolValidationError

try:
    data = adapter.extract_data(job_config)
except SymbolValidationError as e:
    print(f"Invalid symbols: {e.invalid_symbols}")
    print(f"Suggestions: {e.suggested_symbols}")
```

**Rate Limit Handling:**
```python
from src.ingestion.exceptions import RateLimitExceededError

try:
    data = adapter.extract_data(job_config)
except RateLimitExceededError as e:
    print(f"Rate limit exceeded. Retry after: {e.retry_after} seconds")
    # Adapter automatically handles retries
```

## Adding New API Adapters

### 1. Create Adapter Class

```python
from src.ingestion.api_adapters.base_adapter import BaseAPIAdapter

class NewAPIAdapter(BaseAPIAdapter):
    def __init__(self):
        super().__init__()
        self.api_name = "new_api"
    
    def extract_data(self, job_config):
        """Extract data from new API"""
        # Implementation here
        pass
    
    def validate_symbols(self, symbols, dataset):
        """Validate symbols for new API"""
        # Implementation here
        pass
    
    def get_available_schemas(self):
        """Return supported schemas"""
        return ["ohlcv-1d", "trades"]
```

### 2. Create Configuration

Create `configs/api_specific/new_api_config.yaml`:

```yaml
api:
  key_env_var: "NEW_API_KEY"
  base_url: "https://api.newprovider.com"
  timeout: 30

retry_policy:
  max_retries: 3
  base_delay: 1.0
```

### 3. Register Adapter

Update `src/ingestion/adapter_factory.py`:

```python
from .api_adapters.new_api_adapter import NewAPIAdapter

ADAPTER_REGISTRY = {
    "databento": DatabentoAdapter,
    "new_api": NewAPIAdapter,  # Add new adapter
}
```

### 4. Add Validation Schema

Create validation schema in `configs/validation_schemas/new_api_ohlcv_schema.yaml`:

```yaml
type: object
properties:
  ts_event:
    type: string
    format: date-time
  price:
    type: number
    minimum: 0
required:
  - ts_event
  - price
```

## Performance Optimization

### Chunking Strategy

Different data types require different chunking strategies:

```python
# High-frequency data (trades, TBBO)
job_config["date_chunk_interval_days"] = 1  # 1-day chunks

# Medium-frequency data (minute OHLCV)
job_config["date_chunk_interval_days"] = 30  # 30-day chunks

# Low-frequency data (daily OHLCV)
job_config["date_chunk_interval_days"] = 365  # 1-year chunks
```

### Memory Management

```python
# Use generator pattern for large datasets
def process_large_dataset():
    adapter = DatabentoAdapter()
    
    for chunk in adapter.extract_data(job_config):
        # Process chunk immediately
        yield chunk
        # Memory is freed after each chunk
```

### Batch Processing

```python
# Optimize for batch processing
job_config.update({
    "batch_size": 5000,           # Larger batches for efficiency
    "parallel_requests": 3,       # Multiple concurrent requests
    "compression": "gzip"         # Enable compression
})
```

## Best Practices

### API Usage
- Always validate symbols before making requests
- Use appropriate chunk sizes for data volume
- Implement proper error handling and retries
- Respect API rate limits and usage guidelines

### Configuration
- Store API keys in environment variables
- Use configuration files for job parameters
- Validate all configuration before execution
- Document configuration changes

### Data Quality
- Implement data validation at extraction point
- Handle missing or invalid data gracefully
- Log data quality issues for monitoring
- Use quarantine mechanism for invalid records

### Performance
- Monitor API response times and adjust timeouts
- Use appropriate chunking strategies for data volume
- Implement caching for frequently accessed metadata
- Profile memory usage for large datasets 