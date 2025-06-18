-- ================================================================================================
-- Databento TBBO Data - TimescaleDB Hypertable Schema
-- ================================================================================================
-- This schema defines the tbbo_data hypertable for storing Top of Book Bid/Offer data
-- from Databento API. Captures best bid/ask prices and sizes at microsecond granularity.
--
-- Story: Future enhancement - Market depth data support
-- Component: TBBO (Level 1 quote) data storage for spread analysis
-- ================================================================================================

-- Drop table if exists (for development/testing)
DROP TABLE IF EXISTS tbbo_data CASCADE;

-- Create the tbbo_data table
CREATE TABLE tbbo_data (
    -- ========================================================================================
    -- TIME AND IDENTIFICATION FIELDS (Required)
    -- ========================================================================================
    ts_event TIMESTAMPTZ NOT NULL,          -- Quote update timestamp
    instrument_id INTEGER NOT NULL,          -- Databento numeric instrument ID
    
    -- ========================================================================================
    -- BID DATA (Optional - can be NULL if no bid)
    -- ========================================================================================
    bid_px DECIMAL(20,8),                   -- Best bid price
    bid_sz BIGINT CHECK (bid_sz >= 0),     -- Size available at best bid
    bid_ct INTEGER CHECK (bid_ct >= 0),     -- Number of orders at best bid
    
    -- ========================================================================================
    -- ASK/OFFER DATA (Optional - can be NULL if no ask)
    -- ========================================================================================
    ask_px DECIMAL(20,8),                   -- Best ask/offer price
    ask_sz BIGINT CHECK (ask_sz >= 0),     -- Size available at best ask
    ask_ct INTEGER CHECK (ask_ct >= 0),     -- Number of orders at best ask
    
    -- ========================================================================================
    -- DERIVED FIELDS
    -- ========================================================================================
    spread DECIMAL(20,8) GENERATED ALWAYS AS (
        CASE 
            WHEN bid_px IS NOT NULL AND ask_px IS NOT NULL THEN ask_px - bid_px
            ELSE NULL
        END
    ) STORED,                               -- Bid-ask spread
    
    mid_price DECIMAL(20,8) GENERATED ALWAYS AS (
        CASE 
            WHEN bid_px IS NOT NULL AND ask_px IS NOT NULL THEN (bid_px + ask_px) / 2
            ELSE NULL
        END
    ) STORED,                               -- Mid-point price
    
    -- ========================================================================================
    -- METADATA FIELDS
    -- ========================================================================================
    symbol VARCHAR(50),                     -- Human-readable symbol
    data_source VARCHAR(50) NOT NULL DEFAULT 'databento',  -- Data provider source
    is_crossed BOOLEAN DEFAULT FALSE,       -- Flag for crossed markets (bid > ask)
    
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
    flags INTEGER,                          -- Quote condition flags
    
    -- ========================================================================================
    -- AUDIT FIELDS
    -- ========================================================================================
    created_at TIMESTAMPTZ DEFAULT NOW(),   -- Record creation timestamp
    updated_at TIMESTAMPTZ DEFAULT NOW(),   -- Record update timestamp
    
    -- ========================================================================================
    -- CONSTRAINTS
    -- ========================================================================================
    -- Allow crossed markets - handle in application layer
    -- CONSTRAINT chk_bid_ask_cross CHECK (
    --     bid_px IS NULL OR ask_px IS NULL OR bid_px < ask_px
    -- ),
    
    -- Ensure at least one side has data
    CONSTRAINT chk_has_quote_data CHECK (
        bid_px IS NOT NULL OR ask_px IS NOT NULL
    )
);

-- ================================================================================================
-- CREATE HYPERTABLE
-- ================================================================================================
-- Convert to TimescaleDB hypertable partitioned by ts_event
-- Using 1-hour chunks for high-frequency quote data
SELECT create_hypertable('tbbo_data', 'ts_event',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ================================================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================================================

-- Primary lookup index for instrument time series queries
CREATE INDEX idx_tbbo_instrument_time ON tbbo_data (instrument_id, ts_event DESC);

-- Symbol lookup for human-readable queries
CREATE INDEX idx_tbbo_symbol_time ON tbbo_data (symbol, ts_event DESC);

-- Spread analysis
CREATE INDEX idx_tbbo_spread ON tbbo_data (spread) WHERE spread IS NOT NULL;

-- Wide spread detection
CREATE INDEX idx_tbbo_wide_spread ON tbbo_data (instrument_id, spread) 
    WHERE spread > 0.01;

-- Quote imbalance detection
CREATE INDEX idx_tbbo_imbalance ON tbbo_data (instrument_id, ts_event)
    WHERE bid_sz > ask_sz * 2 OR ask_sz > bid_sz * 2;

-- Data source filtering
CREATE INDEX idx_tbbo_source ON tbbo_data (data_source);

-- Mid-price analysis
CREATE INDEX idx_tbbo_mid_price ON tbbo_data (instrument_id, mid_price) 
    WHERE mid_price IS NOT NULL;

-- ================================================================================================
-- PERFORMANCE OPTIMIZATION
-- ================================================================================================

-- Enable compression on older chunks (data older than 1 day)
ALTER TABLE tbbo_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'instrument_id',
    timescaledb.compress_orderby = 'ts_event DESC, sequence'
);

-- Set compression policy (compress chunks older than 1 day)
SELECT add_compression_policy('tbbo_data', INTERVAL '1 day');

-- Set retention policy (keep data for 6 months)
SELECT add_retention_policy('tbbo_data', INTERVAL '6 months');

-- ================================================================================================
-- CONTINUOUS AGGREGATES (Optional - for performance)
-- ================================================================================================

-- 1-minute TBBO aggregates
CREATE MATERIALIZED VIEW tbbo_1min_agg
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', ts_event) AS bucket,
    instrument_id,
    symbol,
    COUNT(*) AS quote_count,
    -- Bid statistics
    MIN(bid_px) AS min_bid,
    MAX(bid_px) AS max_bid,
    AVG(bid_px) AS avg_bid,
    AVG(bid_sz) AS avg_bid_size,
    -- Ask statistics
    MIN(ask_px) AS min_ask,
    MAX(ask_px) AS max_ask,
    AVG(ask_px) AS avg_ask,
    AVG(ask_sz) AS avg_ask_size,
    -- Spread statistics
    MIN(spread) AS min_spread,
    MAX(spread) AS max_spread,
    AVG(spread) AS avg_spread,
    -- Time-weighted averages
    AVG(mid_price) AS avg_mid_price,
    -- Quote presence
    COUNT(*) FILTER (WHERE bid_px IS NOT NULL) AS bid_quote_count,
    COUNT(*) FILTER (WHERE ask_px IS NOT NULL) AS ask_quote_count
FROM tbbo_data
GROUP BY bucket, instrument_id, symbol;

-- Add refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('tbbo_1min_agg',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute');

-- ================================================================================================
-- COMMENTS AND DOCUMENTATION
-- ================================================================================================

COMMENT ON TABLE tbbo_data IS 
'TimescaleDB hypertable for storing Top of Book Bid/Offer (Level 1 quote) data from financial markets. Captures best bid/ask prices and sizes at microsecond precision.';

COMMENT ON COLUMN tbbo_data.ts_event IS 'Quote update timestamp (partition key)';
COMMENT ON COLUMN tbbo_data.instrument_id IS 'Databento numeric instrument identifier';
COMMENT ON COLUMN tbbo_data.bid_px IS 'Best bid price (highest price buyers willing to pay)';
COMMENT ON COLUMN tbbo_data.bid_sz IS 'Total size available at best bid price';
COMMENT ON COLUMN tbbo_data.bid_ct IS 'Number of orders at best bid price level';
COMMENT ON COLUMN tbbo_data.ask_px IS 'Best ask/offer price (lowest price sellers willing to accept)';
COMMENT ON COLUMN tbbo_data.ask_sz IS 'Total size available at best ask price';
COMMENT ON COLUMN tbbo_data.ask_ct IS 'Number of orders at best ask price level';
COMMENT ON COLUMN tbbo_data.spread IS 'Bid-ask spread (ask_px - bid_px)';
COMMENT ON COLUMN tbbo_data.mid_price IS 'Mid-point between bid and ask prices';
COMMENT ON COLUMN tbbo_data.sequence IS 'Sequence number for maintaining order within same timestamp';
COMMENT ON COLUMN tbbo_data.flags IS 'Bit flags for quote conditions (exchange-specific)';

-- ================================================================================================
-- VERIFICATION QUERIES
-- ================================================================================================

-- Verify table structure
\d tbbo_data

-- Verify hypertable creation
SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'tbbo_data';

-- Verify indexes
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'tbbo_data' ORDER BY indexname;

-- Verify continuous aggregate
\d tbbo_1min_agg