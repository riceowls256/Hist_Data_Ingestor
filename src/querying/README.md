# Querying Module

The querying module provides a comprehensive interface for retrieving historical financial data from TimescaleDB. It features automatic symbol resolution, support for all Databento schemas, and optimized queries for time-series data.

## Features

- **Automatic Symbol Resolution**: Query by symbol (e.g., "ES.c.0") instead of instrument_id
- **Multi-Schema Support**: OHLCV, Trades, TBBO, Statistics, and Definitions data
- **TimescaleDB Optimization**: Index-aware queries leveraging hypertable partitioning
- **Flexible Output**: List of dictionaries or Pandas DataFrame formats
- **Comprehensive Error Handling**: Graceful degradation and detailed error messages
- **Connection Pooling**: Efficient database connection management

## Quick Start

```python
from src.querying import QueryBuilder
from datetime import datetime, date

# Initialize the query builder
with QueryBuilder() as qb:
    # Query daily OHLCV data
    results = qb.query_daily_ohlcv(
        symbols=["ES.c.0"],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31)
    )
    
    # Convert to DataFrame for analysis
    df = qb.to_dataframe(results)
    print(f"Retrieved {len(df)} OHLCV records")
```

## Available Query Methods

### 1. Daily OHLCV Data

Query daily Open, High, Low, Close, Volume data with optional granularity filtering.

```python
results = qb.query_daily_ohlcv(
    symbols=["ES.c.0", "NQ.c.0"],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
    granularity="1d",  # Optional: filter by specific granularity
    limit=1000         # Optional: limit number of results
)
```

**Returns:** List of dictionaries with fields:
- `ts_event`: Event timestamp
- `instrument_id`: Internal instrument identifier
- `symbol`: Resolved symbol name
- `open_price`, `high_price`, `low_price`, `close_price`: OHLC prices (Decimal)
- `volume`: Trading volume
- `granularity`: Time granularity (e.g., "1d", "1h")

### 2. Trades Data

Query individual trade records with optional filtering by trade side and volume.

```python
results = qb.query_trades(
    symbols=["ES.c.0"],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 1),  # Single day for high-volume data
    side="B",           # Optional: "B" for buy, "S" for sell
    min_volume=100,     # Optional: minimum trade volume
    limit=10000         # Recommended for large datasets
)
```

**Returns:** List of dictionaries with fields:
- `ts_event`: Trade timestamp
- `instrument_id`: Internal instrument identifier
- `symbol`: Resolved symbol name
- `price`: Trade price (Decimal)
- `size`: Trade size/volume
- `side`: Trade side ("B" or "S")

### 3. Top of Book (TBBO) Data

Query best bid/offer data for market depth analysis.

```python
results = qb.query_tbbo(
    symbols=["ES.c.0"],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 1),
    limit=10000  # Recommended for high-frequency data
)
```

**Returns:** List of dictionaries with fields:
- `ts_event`: Quote timestamp
- `instrument_id`: Internal instrument identifier
- `symbol`: Resolved symbol name
- `bid_px_00`: Best bid price (Decimal)
- `ask_px_00`: Best ask price (Decimal)
- `bid_sz_00`: Best bid size
- `ask_sz_00`: Best ask size

### 4. Statistics Data

Query market statistics like settlement prices, open interest, and volume.

```python
results = qb.query_statistics(
    symbols=["ES.c.0"],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
    stat_type="SettlementPrice",  # Optional: filter by statistic type
    limit=1000
)
```

**Returns:** List of dictionaries with fields:
- `ts_event`: Statistic timestamp
- `instrument_id`: Internal instrument identifier
- `symbol`: Resolved symbol name
- `stat_type`: Type of statistic
- `stat_value`: Statistic value (Decimal)
- `update_action`: Update action type

### 5. Definitions Data

Query instrument definitions and contract specifications.

```python
results = qb.query_definitions(
    symbols=["ES.c.0"],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
    asset="ES",         # Optional: filter by underlying asset
    exchange="XCME",    # Optional: filter by exchange
    limit=100
)
```

**Returns:** List of dictionaries with fields:
- `ts_event`: Definition timestamp
- `instrument_id`: Internal instrument identifier
- `symbol`: Resolved symbol name
- `raw_symbol`: Original symbol from data source
- `asset`: Underlying asset
- `exchange`: Trading exchange
- `currency`: Contract currency
- `tick_size`: Minimum price increment (Decimal)
- `multiplier`: Contract multiplier (Decimal)

## Symbol Discovery

Find available symbols in the database:

```python
symbols = qb.get_available_symbols(
    asset="ES",         # Optional: filter by asset
    exchange="XCME",    # Optional: filter by exchange
    limit=100
)
print(f"Found {len(symbols)} symbols")
for symbol in symbols[:5]:
    print(f"- {symbol}")
```

## Data Format Conversion

### Convert to Pandas DataFrame

```python
# Query data
results = qb.query_daily_ohlcv(symbols=["ES.c.0"], ...)

# Convert to DataFrame
df = qb.to_dataframe(results)

# DataFrame operations
print(df.head())
print(df.describe())
df.to_csv("ohlcv_data.csv", index=False)
```

### Working with Decimal Types

Financial data uses `Decimal` types for precision. Convert as needed:

```python
import pandas as pd

# Convert Decimal columns to float for numerical operations
df['open_price'] = df['open_price'].astype(float)
df['close_price'] = df['close_price'].astype(float)

# Calculate returns
df['return'] = (df['close_price'] - df['open_price']) / df['open_price']
```

## Error Handling

The module provides comprehensive error handling:

```python
from src.querying.exceptions import (
    QueryingError, 
    SymbolResolutionError, 
    QueryExecutionError
)

try:
    with QueryBuilder() as qb:
        results = qb.query_daily_ohlcv(
            symbols=["INVALID_SYMBOL"],
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )
except SymbolResolutionError as e:
    print(f"Symbol not found: {e}")
except QueryExecutionError as e:
    print(f"Database error: {e}")
except QueryingError as e:
    print(f"General querying error: {e}")
```

## Performance Optimization

### Best Practices

1. **Use Date Ranges**: Always specify reasonable date ranges to limit result sets
2. **Apply Limits**: Use the `limit` parameter for high-volume data (trades, tbbo)
3. **Batch Symbol Queries**: Query multiple symbols in one call rather than individual calls
4. **Filter Early**: Use schema-specific filters (side, stat_type, etc.) to reduce data transfer

### Example: Efficient Large Data Query

```python
# Good: Reasonable date range with limit
results = qb.query_trades(
    symbols=["ES.c.0"],
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 1),  # Single day
    limit=50000
)

# Process in chunks if needed
chunk_size = 10000
for i in range(0, len(results), chunk_size):
    chunk = results[i:i + chunk_size]
    # Process chunk
    df_chunk = qb.to_dataframe(chunk)
    # ... analysis ...
```

## Configuration

The QueryBuilder uses the same database configuration as the storage layer:

```bash
# Environment variables
export TIMESCALE_HOST=localhost
export TIMESCALE_PORT=5432
export TIMESCALE_DB=hist_data
export TIMESCALE_USER=postgres
export TIMESCALE_PASSWORD=your_password
```

## Integration with Other Modules

### With CLI

```python
# Example CLI integration
from src.querying import QueryBuilder

def cli_query_command(symbol: str, start: str, end: str):
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    
    with QueryBuilder() as qb:
        results = qb.query_daily_ohlcv(
            symbols=[symbol],
            start_date=start_date,
            end_date=end_date
        )
        
        df = qb.to_dataframe(results)
        print(df.to_string())
```

### With Analysis Tools

```python
import matplotlib.pyplot as plt

# Query and visualize data
with QueryBuilder() as qb:
    results = qb.query_daily_ohlcv(
        symbols=["ES.c.0"],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31)
    )
    
    df = qb.to_dataframe(results)
    df['close_price'] = df['close_price'].astype(float)
    
    plt.figure(figsize=(12, 6))
    plt.plot(df['ts_event'], df['close_price'])
    plt.title('ES Futures Price Chart')
    plt.xlabel('Date')
    plt.ylabel('Close Price')
    plt.show()
```

## Testing

Run the comprehensive test suite:

```bash
# Unit tests
python -m pytest tests/unit/querying/ -v

# Integration tests
python -m pytest tests/integration/test_querying_integration.py -v

# All querying tests
python -m pytest tests/ -k "querying" -v
```

## Troubleshooting

### Common Issues

1. **Symbol Not Found**: Verify symbol exists using `get_available_symbols()`
2. **No Data Returned**: Check date ranges and ensure data exists for the period
3. **Connection Errors**: Verify database configuration and connectivity
4. **Performance Issues**: Use appropriate limits and date ranges for large datasets

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.getLogger('src.querying').setLevel(logging.DEBUG)

# Now QueryBuilder will log detailed query information
with QueryBuilder() as qb:
    results = qb.query_daily_ohlcv(...)
```

## API Reference

For complete API documentation, see the docstrings in:
- `query_builder.py`: Main QueryBuilder class and methods
- `table_definitions.py`: SQLAlchemy table definitions
- `exceptions.py`: Custom exception classes 