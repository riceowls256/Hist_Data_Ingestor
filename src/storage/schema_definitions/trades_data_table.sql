-- ================================================================================================
-- Databento Trade Data - TimescaleDB Hypertable Schema
-- ================================================================================================
-- This schema defines the trades_data hypertable for storing individual trade executions
-- from Databento API. Captures price, volume, and trade metadata at microsecond granularity.
--
-- Story: Future enhancement - Trade-level data support
-- Component: Trade tick data storage for execution analysis
-- ================================================================================================

-- Drop table if exists (for development/testing)
DROP TABLE IF EXISTS trades_data CASCADE;

-- Create the trades_data table
CREATE TABLE trades_data (
    -- ========================================================================================
    -- TIME AND IDENTIFICATION FIELDS (Required)
    -- ========================================================================================
    ts_event TIMESTAMPTZ NOT NULL,          -- Trade execution timestamp
    instrument_id INTEGER NOT NULL,          -- Databento numeric instrument ID
    
    -- ========================================================================================
    -- TRADE DATA (Required)
    -- ========================================================================================
    price DECIMAL(20,8) NOT NULL CHECK (price > 0),  -- Trade execution price
    size BIGINT NOT NULL CHECK (size > 0),           -- Trade size/quantity
    
    -- ========================================================================================
    -- TRADE METADATA (Optional)
    -- ========================================================================================
    side CHAR(1) CHECK (side IN ('A', 'B', 'N')),    -- Trade side: A=Ask, B=Bid, N=None
    trade_id VARCHAR(100),                            -- Unique trade identifier
    order_id VARCHAR(100),                            -- Associated order identifier
    symbol VARCHAR(50),                               -- Human-readable symbol
    
    -- ========================================================================================
    -- DATABENTO HEADER FIELDS (Optional)
    -- ========================================================================================
    ts_recv TIMESTAMPTZ,                    -- Databento receipt timestamp
    rtype INTEGER,                          -- Databento record type
    publisher_id INTEGER,                   -- Databento publisher ID
    
    -- ========================================================================================
    -- DERIVED FIELDS
    -- ========================================================================================
    notional_value DECIMAL(20,8) GENERATED ALWAYS AS (price * size) STORED,  -- Trade value
    
    -- ========================================================================================
    -- METADATA FIELDS
    -- ========================================================================================
    data_source VARCHAR(50) NOT NULL DEFAULT 'databento',  -- Data provider source
    sequence BIGINT,                        -- Sequence number for ordering
    flags INTEGER,                          -- Trade condition flags
    
    -- ========================================================================================
    -- AUDIT FIELDS
    -- ========================================================================================
    created_at TIMESTAMPTZ DEFAULT NOW(),   -- Record creation timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW()    -- Record update timestamp
);

-- ================================================================================================
-- CREATE HYPERTABLE
-- ================================================================================================
-- Convert to TimescaleDB hypertable partitioned by ts_event
-- Using 1-hour chunks for high-frequency trade data
SELECT create_hypertable('trades_data', 'ts_event',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ================================================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================================================

-- Primary lookup index for instrument time series queries
CREATE INDEX idx_trades_instrument_time ON trades_data (instrument_id, ts_event DESC);

-- Symbol lookup for human-readable queries
CREATE INDEX idx_trades_symbol_time ON trades_data (symbol, ts_event DESC);

-- Trade side analysis
CREATE INDEX idx_trades_side ON trades_data (side) WHERE side IS NOT NULL;

-- Large trade detection
CREATE INDEX idx_trades_large_size ON trades_data (size) WHERE size > 1000;

-- Price level analysis
CREATE INDEX idx_trades_price_levels ON trades_data (instrument_id, price);

-- Trade ID lookup (if provided)
CREATE INDEX idx_trades_trade_id ON trades_data (trade_id) WHERE trade_id IS NOT NULL;

-- Data source filtering
CREATE INDEX idx_trades_source ON trades_data (data_source);

-- Notional value analysis
CREATE INDEX idx_trades_notional ON trades_data (notional_value) WHERE notional_value > 100000;

-- ================================================================================================
-- PERFORMANCE OPTIMIZATION
-- ================================================================================================

-- Enable compression on older chunks (data older than 1 day)
ALTER TABLE trades_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'instrument_id',
    timescaledb.compress_orderby = 'ts_event DESC, sequence'
);

-- Set compression policy (compress chunks older than 1 day)
SELECT add_compression_policy('trades_data', INTERVAL '1 day');

-- Set retention policy (keep data for 1 year)
SELECT add_retention_policy('trades_data', INTERVAL '1 year');

-- ================================================================================================
-- CONTINUOUS AGGREGATES (Optional - for performance)
-- ================================================================================================

-- 1-minute trade aggregates
CREATE MATERIALIZED VIEW trades_1min_agg
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', ts_event) AS bucket,
    instrument_id,
    symbol,
    COUNT(*) AS trade_count,
    SUM(size) AS total_volume,
    SUM(notional_value) AS total_notional,
    MIN(price) AS min_price,
    MAX(price) AS max_price,
    FIRST(price, ts_event) AS open_price,
    LAST(price, ts_event) AS close_price,
    AVG(price) AS avg_price,
    COUNT(*) FILTER (WHERE side = 'B') AS buy_count,
    COUNT(*) FILTER (WHERE side = 'A') AS sell_count,
    SUM(size) FILTER (WHERE side = 'B') AS buy_volume,
    SUM(size) FILTER (WHERE side = 'A') AS sell_volume
FROM trades_data
GROUP BY bucket, instrument_id, symbol;

-- Add refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('trades_1min_agg',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

-- ================================================================================================
-- COMMENTS AND DOCUMENTATION
-- ================================================================================================

COMMENT ON TABLE trades_data IS 
'TimescaleDB hypertable for storing individual trade executions from financial markets. Captures every trade with price, size, and metadata at microsecond precision.';

COMMENT ON COLUMN trades_data.ts_event IS 'Trade execution timestamp (partition key)';
COMMENT ON COLUMN trades_data.instrument_id IS 'Databento numeric instrument identifier';
COMMENT ON COLUMN trades_data.price IS 'Trade execution price';
COMMENT ON COLUMN trades_data.size IS 'Number of contracts/shares traded';
COMMENT ON COLUMN trades_data.side IS 'Trade aggressor side: A=Ask(sell), B=Bid(buy), N=None/Unknown';
COMMENT ON COLUMN trades_data.trade_id IS 'Exchange-provided unique trade identifier';
COMMENT ON COLUMN trades_data.notional_value IS 'Calculated trade value (price * size)';
COMMENT ON COLUMN trades_data.sequence IS 'Sequence number for maintaining order within same timestamp';
COMMENT ON COLUMN trades_data.flags IS 'Bit flags for trade conditions (exchange-specific)';

-- ================================================================================================
-- VERIFICATION QUERIES
-- ================================================================================================

-- Verify table structure
\d trades_data

-- Verify hypertable creation
SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'trades_data';

-- Verify indexes
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'trades_data' ORDER BY indexname;

-- Verify continuous aggregate
\d trades_1min_agg