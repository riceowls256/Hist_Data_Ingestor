# Querying Module

Provides comprehensive querying capabilities for accessing stored historical financial data from TimescaleDB with automatic symbol resolution and performance optimization.

## Overview

The querying module serves as the primary interface for data retrieval in the hist_data_ingestor system. It abstracts the complexity of TimescaleDB queries and provides user-friendly methods for accessing all supported Databento schemas.

## Key Features

- **Automatic Symbol Resolution**: Converts user-friendly symbols (e.g., "ES.c.0") to internal instrument_ids
- **Multi-Schema Support**: Comprehensive coverage of all 5 Databento schemas (OHLCV, Trades, TBBO, Statistics, Definitions)
- **TimescaleDB Optimization**: Index-aware queries leveraging hypertable partitioning for optimal performance
- **Flexible Output Formats**: Returns data as list of dictionaries or Pandas DataFrames
- **Connection Pooling**: Efficient database connection management with SQLAlchemy 2.0
- **Comprehensive Error Handling**: Graceful degradation with detailed error messages

## Key Components

### `query_builder.py`
The main QueryBuilder class that provides all querying functionality:

- **QueryBuilder**: Main class with context manager support for connection management
- **Schema-Specific Methods**: 
  - `query_daily_ohlcv()`: Daily OHLCV data with granularity filtering
  - `query_trades()`: Individual trade records with side and volume filtering
  - `query_tbbo()`: Top-of-book bid/offer data
  - `query_statistics()`: Market statistics (settlement, open interest, etc.)
  - `query_definitions()`: Instrument definitions and contract specifications
- **Utility Methods**:
  - `get_available_symbols()`: Symbol discovery functionality
  - `to_dataframe()`: Convert results to Pandas DataFrame
  - `_resolve_symbols()`: Internal symbol-to-instrument_id resolution

### `table_definitions.py`
SQLAlchemy table definitions for all database schemas:

- **daily_ohlcv_data**: Daily OHLCV hypertable definition
- **trades_data**: Individual trades hypertable definition  
- **tbbo_data**: Top-of-book quotes hypertable definition
- **statistics_data**: Market statistics hypertable definition
- **definitions_data**: Instrument definitions hypertable definition

### `exceptions.py`
Custom exception hierarchy for comprehensive error handling:

- **QueryingError**: Base exception for all querying operations
- **QueryExecutionError**: Database query execution failures
- **SymbolResolutionError**: Symbol-to-instrument_id mapping failures
- **ConnectionError**: Database connectivity issues
- **ValidationError**: Query parameter validation errors

## Architecture Integration

The querying module integrates seamlessly with the existing system architecture:

- **Storage Layer Compatibility**: Uses same connection configuration as TimescaleLoader
- **Logging Integration**: Leverages existing structlog framework for consistent logging
- **Error Handling**: Follows established error handling patterns
- **Configuration**: Uses same environment variables as storage layer

## Performance Characteristics

- **Index Utilization**: All queries are designed to leverage TimescaleDB indexes
- **Memory Efficiency**: Streaming-friendly architecture for large result sets
- **Connection Reuse**: Proper connection pooling minimizes connection overhead
- **Query Optimization**: Index-aware query construction with optimal ordering

## Usage Patterns

### CLI Interface (Recommended for End Users)
```bash
# Query daily OHLCV data
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31

# Multiple symbols with CSV output
python main.py query --symbols ES.c.0,NQ.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-format csv

# Trades data with file output
python main.py query -s ES.c.0 --schema trades --start-date 2024-01-01 --end-date 2024-01-01 --output-file trades.json --output-format json
```

### Programmatic API Usage
```python
from src.querying import QueryBuilder
from datetime import date

with QueryBuilder() as qb:
    results = qb.query_daily_ohlcv(
        symbols=["ES.c.0"],
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31)
    )
    df = qb.to_dataframe(results)
```

### Symbol Discovery
```python
with QueryBuilder() as qb:
    symbols = qb.get_available_symbols(asset="ES", exchange="XCME")
```

### Error Handling
```python
from src.querying.exceptions import SymbolResolutionError

try:
    with QueryBuilder() as qb:
        results = qb.query_daily_ohlcv(symbols=["INVALID"])
except SymbolResolutionError as e:
    print(f"Symbol not found: {e}")
```

## Testing

Comprehensive test coverage includes:

- **Unit Tests**: 20 test cases covering all query methods and error scenarios
- **Integration Tests**: 8 test cases validating database integration and performance
- **Mocking Strategy**: Complete database interaction mocking for isolated testing
- **Performance Testing**: Query construction validation and execution time monitoring

## Documentation

- **Module README**: Comprehensive usage guide at `src/querying/README.md`
- **API Documentation**: Detailed docstrings in all source files
- **Integration Examples**: CLI and analysis tool integration patterns 