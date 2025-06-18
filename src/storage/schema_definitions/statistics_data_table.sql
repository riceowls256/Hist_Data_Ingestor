-- ================================================================================================
-- Databento Statistics Data - TimescaleDB Hypertable Schema
-- ================================================================================================
-- This schema defines the statistics_data hypertable for storing various statistical data
-- from Databento API including settlement prices, open interest, and price limits.
--
-- Story: Future enhancement - Market statistics data support
-- Component: Statistics data storage for market analysis and risk management
-- ================================================================================================

-- Drop table if exists (for development/testing)
DROP TABLE IF EXISTS statistics_data CASCADE;

-- Create the statistics_data table
CREATE TABLE statistics_data (
    -- ========================================================================================
    -- TIME AND IDENTIFICATION FIELDS (Required)
    -- ========================================================================================
    ts_event TIMESTAMPTZ NOT NULL,          -- Statistic publication timestamp
    instrument_id INTEGER NOT NULL,          -- Databento numeric instrument ID
    
    -- ========================================================================================
    -- STATISTIC TYPE AND VALUE (Required)
    -- ========================================================================================
    stat_type INTEGER NOT NULL,             -- Type of statistic (exchange-specific codes)
    stat_value DECIMAL(20,8),               -- Statistical value (meaning depends on stat_type)
    
    -- ========================================================================================
    -- COMMON STATISTICS FIELDS (Optional - populated based on stat_type)
    -- ========================================================================================
    open_interest BIGINT CHECK (open_interest >= 0),      -- Open interest (contracts)
    settlement_price DECIMAL(20,8),                        -- Settlement/closing price
    high_limit DECIMAL(20,8),                              -- Daily high price limit
    low_limit DECIMAL(20,8),                               -- Daily low price limit
    
    -- Previous values for change calculation
    prev_open_interest BIGINT CHECK (prev_open_interest >= 0),
    prev_settlement_price DECIMAL(20,8),
    
    -- ========================================================================================
    -- CALCULATED FIELDS
    -- ========================================================================================
    open_interest_change INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN open_interest IS NOT NULL AND prev_open_interest IS NOT NULL 
            THEN open_interest - prev_open_interest
            ELSE NULL
        END
    ) STORED,
    
    settlement_change DECIMAL(20,8) GENERATED ALWAYS AS (
        CASE 
            WHEN settlement_price IS NOT NULL AND prev_settlement_price IS NOT NULL 
            THEN settlement_price - prev_settlement_price
            ELSE NULL
        END
    ) STORED,
    
    -- ========================================================================================
    -- METADATA FIELDS
    -- ========================================================================================
    symbol VARCHAR(50),                     -- Human-readable symbol
    stat_type_desc VARCHAR(100),            -- Description of statistic type
    data_source VARCHAR(50) NOT NULL DEFAULT 'databento',  -- Data provider source
    
    -- ========================================================================================
    -- DATABENTO HEADER FIELDS (Optional)
    -- ========================================================================================
    ts_recv TIMESTAMPTZ,                    -- Databento receipt timestamp
    rtype INTEGER,                          -- Databento record type
    publisher_id INTEGER,                   -- Databento publisher ID
    
    -- ========================================================================================
    -- ADDITIONAL FIELDS
    -- ========================================================================================
    sequence BIGINT,                        -- Sequence number for ordering
    flags INTEGER,                          -- Statistic flags/conditions
    update_action CHAR(1) CHECK (update_action IN ('A', 'U', 'D')),  -- Add/Update/Delete
    
    -- ========================================================================================
    -- AUDIT FIELDS
    -- ========================================================================================
    created_at TIMESTAMPTZ DEFAULT NOW(),   -- Record creation timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW(),   -- Record update timestamp
    
    -- ========================================================================================
    -- CONSTRAINTS
    -- ========================================================================================
    -- Ensure price limits are logical when both present
    CONSTRAINT chk_price_limits CHECK (
        high_limit IS NULL OR low_limit IS NULL OR high_limit >= low_limit
    ),
    
    -- Primary key for unique statistics
    CONSTRAINT pk_statistics_data PRIMARY KEY (instrument_id, stat_type, ts_event)
);

-- ================================================================================================
-- CREATE HYPERTABLE
-- ================================================================================================
-- Convert to TimescaleDB hypertable partitioned by ts_event
-- Using 1-day chunks as statistics are typically daily
SELECT create_hypertable('statistics_data', 'ts_event',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- ================================================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================================================

-- Symbol and time lookup
CREATE INDEX idx_statistics_symbol_time ON statistics_data (symbol, ts_event DESC);

-- Statistic type filtering
CREATE INDEX idx_statistics_type ON statistics_data (stat_type, ts_event DESC);

-- Settlement price queries
CREATE INDEX idx_statistics_settlement ON statistics_data (instrument_id, ts_event DESC)
    WHERE settlement_price IS NOT NULL;

-- Open interest analysis
CREATE INDEX idx_statistics_open_interest ON statistics_data (instrument_id, ts_event DESC)
    WHERE open_interest IS NOT NULL;

-- Large open interest positions
CREATE INDEX idx_statistics_large_oi ON statistics_data (open_interest)
    WHERE open_interest > 10000;

-- Open interest changes
CREATE INDEX idx_statistics_oi_change ON statistics_data (open_interest_change)
    WHERE open_interest_change IS NOT NULL;

-- Price limit analysis
CREATE INDEX idx_statistics_limits ON statistics_data (instrument_id, ts_event)
    WHERE high_limit IS NOT NULL OR low_limit IS NOT NULL;

-- Data source filtering
CREATE INDEX idx_statistics_source ON statistics_data (data_source);

-- ================================================================================================
-- PERFORMANCE OPTIMIZATION
-- ================================================================================================

-- Enable compression on older chunks (data older than 7 days)
ALTER TABLE statistics_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'instrument_id, stat_type',
    timescaledb.compress_orderby = 'ts_event DESC'
);

-- Set compression policy (compress chunks older than 7 days)
SELECT add_compression_policy('statistics_data', INTERVAL '7 days');

-- Set retention policy (keep data for 5 years)
SELECT add_retention_policy('statistics_data', INTERVAL '5 years');

-- ================================================================================================
-- VIEWS FOR COMMON QUERIES
-- ================================================================================================

-- Latest settlement prices view
CREATE VIEW latest_settlements AS
SELECT DISTINCT ON (instrument_id)
    instrument_id,
    symbol,
    ts_event,
    settlement_price,
    settlement_change,
    prev_settlement_price
FROM statistics_data
WHERE settlement_price IS NOT NULL
ORDER BY instrument_id, ts_event DESC;

-- Latest open interest view
CREATE VIEW latest_open_interest AS
SELECT DISTINCT ON (instrument_id)
    instrument_id,
    symbol,
    ts_event,
    open_interest,
    open_interest_change,
    prev_open_interest
FROM statistics_data
WHERE open_interest IS NOT NULL
ORDER BY instrument_id, ts_event DESC;

-- Current price limits view
CREATE VIEW current_price_limits AS
SELECT DISTINCT ON (instrument_id)
    instrument_id,
    symbol,
    ts_event,
    high_limit,
    low_limit,
    settlement_price,
    (high_limit - settlement_price) AS upside_limit,
    (settlement_price - low_limit) AS downside_limit
FROM statistics_data
WHERE high_limit IS NOT NULL AND low_limit IS NOT NULL
ORDER BY instrument_id, ts_event DESC;

-- ================================================================================================
-- STATISTIC TYPE REFERENCE TABLE (Optional)
-- ================================================================================================

-- Create reference table for statistic types
CREATE TABLE IF NOT EXISTS statistic_type_ref (
    stat_type INTEGER PRIMARY KEY,
    stat_name VARCHAR(50) NOT NULL,
    stat_description VARCHAR(200),
    unit VARCHAR(20),
    exchange VARCHAR(20)
);

-- Insert common statistic types (exchange-specific)
INSERT INTO statistic_type_ref (stat_type, stat_name, stat_description, unit, exchange) VALUES
    (1, 'SETTLEMENT', 'Daily settlement price', 'price', 'ALL'),
    (2, 'OPEN_INTEREST', 'Total open interest', 'contracts', 'ALL'),
    (3, 'HIGH_LIMIT', 'Daily high price limit', 'price', 'ALL'),
    (4, 'LOW_LIMIT', 'Daily low price limit', 'price', 'ALL'),
    (5, 'VOLUME', 'Daily trading volume', 'contracts', 'ALL'),
    (6, 'VWAP', 'Volume-weighted average price', 'price', 'ALL'),
    (7, 'IMPLIED_VOL', 'Implied volatility', 'percentage', 'ALL'),
    (8, 'DELTA', 'Option delta', 'decimal', 'ALL'),
    (9, 'GAMMA', 'Option gamma', 'decimal', 'ALL'),
    (10, 'THETA', 'Option theta', 'decimal', 'ALL')
ON CONFLICT (stat_type) DO NOTHING;

-- ================================================================================================
-- COMMENTS AND DOCUMENTATION
-- ================================================================================================

COMMENT ON TABLE statistics_data IS 
'TimescaleDB hypertable for storing various market statistics including settlement prices, open interest, price limits, and other exchange-published statistics.';

COMMENT ON COLUMN statistics_data.ts_event IS 'Statistic publication timestamp (partition key)';
COMMENT ON COLUMN statistics_data.instrument_id IS 'Databento numeric instrument identifier';
COMMENT ON COLUMN statistics_data.stat_type IS 'Type of statistic (see statistic_type_ref table)';
COMMENT ON COLUMN statistics_data.stat_value IS 'Generic statistic value (interpretation depends on stat_type)';
COMMENT ON COLUMN statistics_data.open_interest IS 'Total number of outstanding contracts';
COMMENT ON COLUMN statistics_data.settlement_price IS 'Official daily settlement/closing price';
COMMENT ON COLUMN statistics_data.high_limit IS 'Maximum allowed price for the trading session';
COMMENT ON COLUMN statistics_data.low_limit IS 'Minimum allowed price for the trading session';
COMMENT ON COLUMN statistics_data.open_interest_change IS 'Change in open interest from previous value';
COMMENT ON COLUMN statistics_data.settlement_change IS 'Change in settlement price from previous value';

-- ================================================================================================
-- VERIFICATION QUERIES
-- ================================================================================================

-- Verify table structure
\d statistics_data

-- Verify hypertable creation
SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'statistics_data';

-- Verify indexes
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'statistics_data' ORDER BY indexname;

-- Verify views
\d latest_settlements
\d latest_open_interest
\d current_price_limits