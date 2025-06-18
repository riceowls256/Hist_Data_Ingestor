-- ================================================================================================
-- Databento OHLCV Data - TimescaleDB Hypertable Schema
-- ================================================================================================
-- This schema defines the daily_ohlcv_data hypertable for storing Open-High-Low-Close-Volume
-- bar data from Databento API. Supports various time granularities with default of 1 day.
--
-- Story: 3.5 - Databento API Adapter Development and Integration
-- Component: OHLCV data storage for financial time series analysis
-- ================================================================================================

-- Drop table if exists (for development/testing)
DROP TABLE IF EXISTS daily_ohlcv_data CASCADE;

-- Create the daily_ohlcv_data table
CREATE TABLE daily_ohlcv_data (
    -- ========================================================================================
    -- TIME AND IDENTIFICATION FIELDS (Required)
    -- ========================================================================================
    ts_event TIMESTAMPTZ NOT NULL,          -- Event timestamp (price bar close time)
    instrument_id INTEGER NOT NULL,          -- Databento numeric instrument ID
    
    -- ========================================================================================
    -- OHLCV PRICE DATA (Required)
    -- ========================================================================================
    open_price DECIMAL(20,8) NOT NULL,      -- Opening price of the bar
    high_price DECIMAL(20,8) NOT NULL,      -- Highest price during the bar
    low_price DECIMAL(20,8) NOT NULL,       -- Lowest price during the bar
    close_price DECIMAL(20,8) NOT NULL,     -- Closing price of the bar
    volume BIGINT NOT NULL CHECK (volume >= 0),  -- Total volume traded
    
    -- ========================================================================================
    -- ADDITIONAL METRICS (Optional)
    -- ========================================================================================
    trade_count INTEGER CHECK (trade_count >= 0),     -- Number of trades in the bar
    vwap DECIMAL(20,8),                               -- Volume-weighted average price
    
    -- ========================================================================================
    -- METADATA FIELDS (Required)
    -- ========================================================================================
    granularity VARCHAR(10) NOT NULL DEFAULT '1d',    -- Time granularity (1d, 1h, 5m, etc.)
    data_source VARCHAR(50) NOT NULL DEFAULT 'databento',  -- Data provider source
    symbol VARCHAR(50),                               -- Human-readable symbol
    
    -- ========================================================================================
    -- DATABENTO HEADER FIELDS (Optional)
    -- ========================================================================================
    ts_recv TIMESTAMPTZ,                    -- Databento receipt timestamp
    rtype INTEGER,                          -- Databento record type
    publisher_id INTEGER,                   -- Databento publisher ID
    
    -- ========================================================================================
    -- AUDIT FIELDS
    -- ========================================================================================
    created_at TIMESTAMPTZ DEFAULT NOW(),   -- Record creation timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW(),   -- Record update timestamp
    
    -- ========================================================================================
    -- CONSTRAINTS
    -- ========================================================================================
    -- Price validation constraints
    CONSTRAINT chk_price_relationships CHECK (
        high_price >= low_price AND 
        high_price >= open_price AND 
        high_price >= close_price AND
        low_price <= open_price AND 
        low_price <= close_price
    ),
    
    -- VWAP validation (must be within high/low range if present)
    CONSTRAINT chk_vwap_range CHECK (
        vwap IS NULL OR (vwap >= low_price AND vwap <= high_price)
    ),
    
    -- Unique constraint to prevent duplicate bars
    CONSTRAINT uq_daily_ohlcv_unique UNIQUE (ts_event, instrument_id, granularity, data_source)
);

-- ================================================================================================
-- CREATE HYPERTABLE
-- ================================================================================================
-- Convert to TimescaleDB hypertable partitioned by ts_event
-- Using 1-day chunks for daily data (adjust chunk_time_interval for other granularities)
SELECT create_hypertable('daily_ohlcv_data', 'ts_event', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ================================================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================================================

-- Primary lookup index for instrument time series queries
CREATE INDEX idx_daily_ohlcv_instrument_time ON daily_ohlcv_data (instrument_id, ts_event DESC);

-- Symbol lookup for human-readable queries
CREATE INDEX idx_daily_ohlcv_symbol ON daily_ohlcv_data (symbol);

-- Data source filtering
CREATE INDEX idx_daily_ohlcv_source ON daily_ohlcv_data (data_source);

-- Granularity filtering for multi-timeframe analysis
CREATE INDEX idx_daily_ohlcv_granularity ON daily_ohlcv_data (granularity);

-- Composite index for common query patterns
CREATE INDEX idx_daily_ohlcv_symbol_gran_time ON daily_ohlcv_data (symbol, granularity, ts_event DESC);

-- Volume analysis index
CREATE INDEX idx_daily_ohlcv_volume ON daily_ohlcv_data (volume) WHERE volume > 0;

-- ================================================================================================
-- PERFORMANCE OPTIMIZATION
-- ================================================================================================

-- Enable compression on older chunks (data older than 7 days)
ALTER TABLE daily_ohlcv_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'instrument_id, granularity',
    timescaledb.compress_orderby = 'ts_event DESC'
);

-- Set compression policy (compress chunks older than 7 days)
SELECT add_compression_policy('daily_ohlcv_data', INTERVAL '7 days');

-- Set retention policy (keep data for 5 years)
SELECT add_retention_policy('daily_ohlcv_data', INTERVAL '5 years');

-- ================================================================================================
-- COMMENTS AND DOCUMENTATION
-- ================================================================================================

COMMENT ON TABLE daily_ohlcv_data IS 
'TimescaleDB hypertable for storing OHLCV (Open-High-Low-Close-Volume) bar data from financial markets. Supports multiple time granularities and data sources.';

COMMENT ON COLUMN daily_ohlcv_data.ts_event IS 'Bar closing timestamp (partition key)';
COMMENT ON COLUMN daily_ohlcv_data.instrument_id IS 'Databento numeric instrument identifier';
COMMENT ON COLUMN daily_ohlcv_data.open_price IS 'Opening price at the start of the bar period';
COMMENT ON COLUMN daily_ohlcv_data.high_price IS 'Highest traded price during the bar period';
COMMENT ON COLUMN daily_ohlcv_data.low_price IS 'Lowest traded price during the bar period';
COMMENT ON COLUMN daily_ohlcv_data.close_price IS 'Closing price at the end of the bar period';
COMMENT ON COLUMN daily_ohlcv_data.volume IS 'Total volume traded during the bar period';
COMMENT ON COLUMN daily_ohlcv_data.trade_count IS 'Number of individual trades during the bar period';
COMMENT ON COLUMN daily_ohlcv_data.vwap IS 'Volume-weighted average price for the bar period';
COMMENT ON COLUMN daily_ohlcv_data.granularity IS 'Time granularity of the bar (1d=daily, 1h=hourly, etc.)';
COMMENT ON COLUMN daily_ohlcv_data.symbol IS 'Human-readable symbol for easier querying';

-- ================================================================================================
-- VERIFICATION QUERIES
-- ================================================================================================

-- Verify table structure
\d daily_ohlcv_data

-- Verify hypertable creation
SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'daily_ohlcv_data';

-- Verify indexes
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'daily_ohlcv_data' ORDER BY indexname;