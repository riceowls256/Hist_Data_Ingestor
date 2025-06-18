# Storage Module

The storage module provides a high-performance, scalable data persistence layer optimized for time-series financial data using TimescaleDB. It implements efficient storage patterns, connection pooling, and schema management for handling large volumes of market data.

## Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Transformed     │────│ Storage Loaders  │────│ TimescaleDB     │
│ Data            │    │                  │    │ (Hypertables)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Connection Pool  │
                       │ Manager          │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Schema           │
                       │ Management       │
                       └──────────────────┘
```

#### Storage Loaders

Specialized classes for efficient bulk loading of different data types into TimescaleDB.

**Available Loaders:**
- `OHLCVLoader`: Optimized for OHLCV data with compression and indexing
- `TradesLoader`: High-throughput loader for trade data
- `TBBOLoader`: Specialized for bid/ask quote data
- `StatisticsLoader`: Market statistics and derived data
- `DefinitionsLoader`: Instrument definitions and metadata

#### Connection Management

Advanced connection pooling and transaction management for high-performance data operations.

**Features:**
- **Connection Pooling**: SQLAlchemy-based connection pool with optimization
- **Transaction Management**: Atomic operations with rollback capabilities
- **Health Monitoring**: Connection health checks and automatic recovery
- **Performance Tuning**: Configurable pool settings for different workloads

#### Schema Management

Automated schema creation, migration, and optimization for TimescaleDB hypertables.

**Capabilities:**
- **Hypertable Creation**: Automatic time-series partitioning
- **Index Management**: Optimized indexes for common query patterns
- **Compression Policies**: Automatic data compression for older data
- **Retention Policies**: Configurable data retention and cleanup

## Usage Examples

### Basic Data Storage

```python
from src.storage.loaders.ohlcv_loader import OHLCVLoader
from datetime import datetime

# Initialize loader
loader = OHLCVLoader()

# Sample OHLCV data
ohlcv_data = [
    {
        "timestamp": datetime(2024, 1, 1, 10, 0, 0),
        "instrument_id": 1001,
        "symbol": "ES.c.0",
        "open_price": 5000.25,
        "high_price": 5010.75,
        "low_price": 4995.50,
        "close_price": 5005.00,
        "volume": 125000,
        "granularity": "1d"
    }
]

# Store data with automatic batching
result = loader.store_batch(ohlcv_data)
print(f"Stored {result.records_inserted} records")
print(f"Processing time: {result.processing_time_ms}ms")
```

### High-Performance Bulk Loading

```python
from src.storage.loaders.trades_loader import TradesLoader

# Initialize for high-volume data
loader = TradesLoader(
    batch_size=10000,
    enable_compression=True,
    parallel_workers=4
)

# Stream large dataset
def trade_data_generator():
    # Generator yielding trade records
    for batch in large_trade_dataset:
        yield batch

# Bulk load with progress tracking
result = loader.bulk_load(
    data_generator=trade_data_generator(),
    progress_callback=lambda completed, total: print(f"Progress: {completed}/{total}")
)

print(f"Bulk load completed: {result.total_records} records")
print(f"Average throughput: {result.records_per_second} records/sec")
```

### Advanced Storage Configuration

```python
# Custom loader configuration
config = {
    "connection": {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 3600
    },
    "performance": {
        "batch_size": 5000,
        "enable_compression": True,
        "use_copy_from": True,  # PostgreSQL COPY for performance
        "parallel_inserts": True
    },
    "optimization": {
        "create_indexes": True,
        "analyze_tables": True,
        "enable_hypertable_compression": True
    }
}

loader = OHLCVLoader(config)
```

## TimescaleDB Schema

### Hypertable Structure

#### OHLCV Data (`ohlcv_data`)

```sql
CREATE TABLE ohlcv_data (
    timestamp TIMESTAMPTZ NOT NULL,
    instrument_id INTEGER NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume BIGINT NOT NULL,
    granularity VARCHAR(10) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT ohlcv_price_check CHECK (
        high_price >= low_price AND
        low_price <= open_price AND open_price <= high_price AND
        low_price <= close_price AND close_price <= high_price
    ),
    CONSTRAINT ohlcv_volume_check CHECK (volume >= 0)
);

-- Convert to hypertable with 1-day chunks
SELECT create_hypertable('ohlcv_data', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Create indexes for common queries
CREATE INDEX idx_ohlcv_symbol_time ON ohlcv_data (symbol, timestamp DESC);
CREATE INDEX idx_ohlcv_instrument_time ON ohlcv_data (instrument_id, timestamp DESC);
CREATE INDEX idx_ohlcv_granularity ON ohlcv_data (granularity, timestamp DESC);
```

#### Trades Data (`trades_data`)

```sql
CREATE TABLE trades_data (
    timestamp TIMESTAMPTZ NOT NULL,
    instrument_id INTEGER NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    price DECIMAL(20,8) NOT NULL,
    size BIGINT NOT NULL,
    side CHAR(1) NOT NULL,  -- 'B' for buy, 'S' for sell
    trade_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT trades_price_check CHECK (price > 0),
    CONSTRAINT trades_size_check CHECK (size > 0),
    CONSTRAINT trades_side_check CHECK (side IN ('B', 'S'))
);

-- Convert to hypertable with 1-hour chunks (high volume)
SELECT create_hypertable('trades_data', 'timestamp', chunk_time_interval => INTERVAL '1 hour');

-- Optimized indexes for trade analysis
CREATE INDEX idx_trades_symbol_time ON trades_data (symbol, timestamp DESC);
CREATE INDEX idx_trades_side_time ON trades_data (side, timestamp DESC);
CREATE INDEX idx_trades_price_range ON trades_data (symbol, price, timestamp DESC);
```

#### TBBO Data (`tbbo_data`)

```sql
CREATE TABLE tbbo_data (
    timestamp TIMESTAMPTZ NOT NULL,
    instrument_id INTEGER NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    bid_px_00 DECIMAL(20,8),
    ask_px_00 DECIMAL(20,8),
    bid_sz_00 BIGINT,
    ask_sz_00 BIGINT,
    spread DECIMAL(20,8) GENERATED ALWAYS AS (ask_px_00 - bid_px_00) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT tbbo_prices_check CHECK (
        (bid_px_00 IS NULL OR bid_px_00 > 0) AND
        (ask_px_00 IS NULL OR ask_px_00 > 0) AND
        (bid_px_00 IS NULL OR ask_px_00 IS NULL OR ask_px_00 >= bid_px_00)
    ),
    CONSTRAINT tbbo_sizes_check CHECK (
        (bid_sz_00 IS NULL OR bid_sz_00 > 0) AND
        (ask_sz_00 IS NULL OR ask_sz_00 > 0)
    )
);

-- Convert to hypertable with 1-hour chunks
SELECT create_hypertable('tbbo_data', 'timestamp', chunk_time_interval => INTERVAL '1 hour');

-- Indexes for spread analysis and market making
CREATE INDEX idx_tbbo_symbol_time ON tbbo_data (symbol, timestamp DESC);
CREATE INDEX idx_tbbo_spread ON tbbo_data (symbol, spread, timestamp DESC);
```

#### Instrument Definitions (`instrument_definitions`)

```sql
CREATE TABLE instrument_definitions (
    instrument_id INTEGER PRIMARY KEY,
    symbol VARCHAR(50) NOT NULL,
    raw_symbol VARCHAR(100) NOT NULL,
    asset VARCHAR(20) NOT NULL,
    exchange VARCHAR(20) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    tick_size DECIMAL(20,8) NOT NULL,
    multiplier DECIMAL(20,8) NOT NULL,
    expiration_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique symbols
    CONSTRAINT unique_symbol UNIQUE (symbol),
    CONSTRAINT positive_tick_size CHECK (tick_size > 0),
    CONSTRAINT positive_multiplier CHECK (multiplier > 0)
);

-- Indexes for symbol resolution
CREATE INDEX idx_definitions_symbol ON instrument_definitions (symbol);
CREATE INDEX idx_definitions_asset ON instrument_definitions (asset, is_active);
CREATE INDEX idx_definitions_exchange ON instrument_definitions (exchange, is_active);
```

### Performance Optimizations

#### Compression Policies

```sql
-- Enable compression for older OHLCV data (7+ days old)
SELECT add_compression_policy('ohlcv_data', INTERVAL '7 days');

-- Enable compression for trades data (1+ days old due to high volume)
SELECT add_compression_policy('trades_data', INTERVAL '1 day');

-- Compression for TBBO data (3+ days old)
SELECT add_compression_policy('tbbo_data', INTERVAL '3 days');
```

#### Retention Policies

```sql
-- Retain OHLCV data for 5 years
SELECT add_retention_policy('ohlcv_data', INTERVAL '5 years');

-- Retain trade data for 2 years (high volume)
SELECT add_retention_policy('trades_data', INTERVAL '2 years');

-- Retain TBBO data for 1 year
SELECT add_retention_policy('tbbo_data', INTERVAL '1 year');
```

#### Continuous Aggregates

```sql
-- Create hourly OHLCV aggregates for faster queries
CREATE MATERIALIZED VIEW ohlcv_hourly
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', timestamp) AS hour,
       instrument_id,
       symbol,
       FIRST(open_price, timestamp) AS open_price,
       MAX(high_price) AS high_price,
       MIN(low_price) AS low_price,
       LAST(close_price, timestamp) AS close_price,
       SUM(volume) AS volume
FROM ohlcv_data
WHERE granularity = '1m'  -- Aggregate from minute data
GROUP BY hour, instrument_id, symbol;

-- Add refresh policy
SELECT add_continuous_aggregate_policy('ohlcv_hourly',
    start_offset => INTERVAL '1 month',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

## Storage Loaders Implementation

### OHLCV Loader

```python
from src.storage.loaders.base_loader import BaseLoader
from sqlalchemy import text
import pandas as pd

class OHLCVLoader(BaseLoader):
    def __init__(self, config=None):
        super().__init__(config)
        self.table_name = "ohlcv_data"
        self.required_columns = [
            "timestamp", "instrument_id", "symbol", 
            "open_price", "high_price", "low_price", 
            "close_price", "volume", "granularity"
        ]
    
    def store_batch(self, data):
        """Store OHLCV data batch with optimization"""
        try:
            # Convert to DataFrame for efficient processing
            df = pd.DataFrame(data)
            
            # Validate required columns
            self._validate_columns(df)
            
            # Optimize data types
            df = self._optimize_dtypes(df)
            
            # Use PostgreSQL COPY for high performance
            if self.config.get("use_copy_from", True):
                result = self._copy_from_dataframe(df)
            else:
                result = self._insert_batch(df)
                
            # Update statistics
            self._update_table_statistics()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to store OHLCV batch: {e}")
            raise
    
    def _optimize_dtypes(self, df):
        """Optimize DataFrame data types for storage"""
        optimizations = {
            "timestamp": "datetime64[ns, UTC]",
            "instrument_id": "int32",
            "open_price": "float64",
            "high_price": "float64", 
            "low_price": "float64",
            "close_price": "float64",
            "volume": "int64"
        }
        
        for col, dtype in optimizations.items():
            if col in df.columns:
                df[col] = df[col].astype(dtype)
                
        return df
    
    def _copy_from_dataframe(self, df):
        """Use PostgreSQL COPY for high-performance insertion"""
        from io import StringIO
        
        # Prepare CSV data
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, header=False)
        csv_buffer.seek(0)
        
        # Execute COPY command
        with self.get_connection() as conn:
            copy_sql = f"""
                COPY {self.table_name} 
                ({', '.join(self.required_columns)})
                FROM STDIN WITH CSV
            """
            
            cursor = conn.connection.cursor()
            cursor.copy_expert(copy_sql, csv_buffer)
            conn.commit()
            
            return {"records_inserted": len(df)}
```

### High-Volume Trades Loader

```python
class TradesLoader(BaseLoader):
    def __init__(self, config=None):
        super().__init__(config)
        self.table_name = "trades_data"
        
    def bulk_load(self, data_generator, progress_callback=None):
        """Bulk load trades data with streaming"""
        total_records = 0
        start_time = time.time()
        
        with self.get_connection() as conn:
            # Begin transaction
            trans = conn.begin()
            
            try:
                for batch_num, batch in enumerate(data_generator):
                    # Process batch
                    df = pd.DataFrame(batch)
                    
                    # Store using COPY
                    self._copy_from_dataframe(df, conn)
                    
                    total_records += len(df)
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(total_records, None)
                    
                    # Commit every 100 batches
                    if batch_num % 100 == 0:
                        trans.commit()
                        trans = conn.begin()
                
                # Final commit
                trans.commit()
                
                # Calculate performance metrics
                end_time = time.time()
                processing_time = end_time - start_time
                records_per_second = total_records / processing_time
                
                return {
                    "total_records": total_records,
                    "processing_time_seconds": processing_time,
                    "records_per_second": records_per_second
                }
                
            except Exception as e:
                trans.rollback()
                raise
```

## Connection Management

### Connection Pool Configuration

```python
from src.storage.connection_manager import ConnectionManager

# Production configuration
production_config = {
    "database_url": "postgresql://user:pass@host:5432/dbname",
    "pool_size": 20,           # Base connections
    "max_overflow": 10,        # Additional connections
    "pool_timeout": 30,        # Connection timeout
    "pool_recycle": 3600,      # Recycle connections hourly
    "pool_pre_ping": True,     # Test connections
    "echo": False              # Disable SQL echo
}

# Initialize connection manager
conn_manager = ConnectionManager(production_config)

# Use connection pool
with conn_manager.get_connection() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM ohlcv_data"))
    print(f"Total OHLCV records: {result.scalar()}")
```

### Health Monitoring

```python
class HealthMonitor:
    def __init__(self, connection_manager):
        self.conn_manager = connection_manager
    
    def check_database_health(self):
        """Comprehensive database health check"""
        health_status = {
            "database_connectivity": False,
            "pool_status": {},
            "table_accessibility": {},
            "performance_metrics": {}
        }
        
        try:
            # Test basic connectivity
            with self.conn_manager.get_connection() as conn:
                result = conn.execute(text("SELECT 1"))
                health_status["database_connectivity"] = True
            
            # Check connection pool
            pool = self.conn_manager.engine.pool
            health_status["pool_status"] = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
            
            # Test table accessibility
            tables = ["ohlcv_data", "trades_data", "tbbo_data"]
            for table in tables:
                try:
                    with self.conn_manager.get_connection() as conn:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table} LIMIT 1"))
                        health_status["table_accessibility"][table] = True
                except Exception as e:
                    health_status["table_accessibility"][table] = f"Error: {e}"
            
            return health_status
            
        except Exception as e:
            health_status["error"] = str(e)
            return health_status
```

## Performance Best Practices

### Batch Size Optimization

```python
# Optimize batch sizes based on data type
OPTIMAL_BATCH_SIZES = {
    "ohlcv_data": 5000,      # Moderate volume, complex records
    "trades_data": 10000,    # High volume, simple records
    "tbbo_data": 15000,      # Very high volume, simple records
    "statistics_data": 1000,  # Low volume, complex records
    "definitions_data": 100   # Very low volume, reference data
}

def get_optimal_batch_size(table_name, record_size_bytes):
    """Calculate optimal batch size based on table and record characteristics"""
    base_size = OPTIMAL_BATCH_SIZES.get(table_name, 1000)
    
    # Adjust based on record size
    if record_size_bytes > 1000:  # Large records
        return max(base_size // 2, 100)
    elif record_size_bytes < 200:  # Small records  
        return min(base_size * 2, 20000)
    else:
        return base_size
```

### Query Optimization

```python
# Optimized queries for common patterns
OPTIMIZED_QUERIES = {
    "recent_ohlcv": """
        SELECT * FROM ohlcv_data 
        WHERE symbol = %s 
        AND timestamp >= %s 
        ORDER BY timestamp DESC 
        LIMIT %s
    """,
    
    "aggregated_volume": """
        SELECT 
            time_bucket('1 hour', timestamp) as hour,
            symbol,
            SUM(volume) as total_volume,
            COUNT(*) as trade_count
        FROM trades_data 
        WHERE symbol = %s 
        AND timestamp BETWEEN %s AND %s
        GROUP BY hour, symbol
        ORDER BY hour
    """,
    
    "spread_analysis": """
        SELECT 
            symbol,
            AVG(spread) as avg_spread,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY spread) as median_spread,
            MAX(spread) as max_spread
        FROM tbbo_data 
        WHERE symbol = %s 
        AND timestamp BETWEEN %s AND %s
        AND spread IS NOT NULL
        GROUP BY symbol
    """
}
```

### Maintenance Operations

```python
def perform_maintenance(table_name):
    """Perform routine maintenance on TimescaleDB tables"""
    maintenance_ops = [
        # Update table statistics
        f"ANALYZE {table_name}",
        
        # Reindex if needed
        f"REINDEX TABLE {table_name}",
        
        # Update hypertable statistics
        f"SELECT refresh_continuous_aggregate('{table_name}_hourly', NULL, NULL)",
        
        # Check compression effectiveness
        f"""
        SELECT 
            chunk_name,
            before_compression_bytes,
            after_compression_bytes,
            compression_ratio
        FROM timescaledb_information.compressed_chunk_stats
        WHERE hypertable_name = '{table_name}'
        """
    ]
    
    return maintenance_ops
```

## Best Practices

### Data Modeling
- Use appropriate data types (DECIMAL for prices, BIGINT for volume)
- Implement check constraints for data quality
- Design indexes based on query patterns
- Use hypertable partitioning for time-series data

### Performance
- Use PostgreSQL COPY for bulk loading
- Batch operations for efficiency
- Monitor connection pool usage
- Implement compression policies for older data

### Reliability
- Use transactions for data consistency
- Implement proper error handling and rollback
- Monitor database health and performance
- Regular backup and recovery testing

### Scalability
- Configure connection pooling appropriately
- Use continuous aggregates for common queries
- Implement data retention policies
- Monitor and tune TimescaleDB settings 