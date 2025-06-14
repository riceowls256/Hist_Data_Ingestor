-- ================================================================================================
-- Databento Instrument Definition Data - TimescaleDB Hypertable Schema
-- ================================================================================================
-- This schema defines the definitions_data hypertable for storing instrument definition metadata
-- from Databento API. Supports the complete 73-field DatabentoDefinitionRecord model.
--
-- Story: 2.4 - Add Support for Databento Instrument Definition Schema
-- AC3: Database Table Created - definitions_data hypertable in TimescaleDB
-- ================================================================================================

-- Drop table if exists (for development/testing)
DROP TABLE IF EXISTS definitions_data CASCADE;

-- Create the definitions_data table
CREATE TABLE definitions_data (
    -- ========================================================================================
    -- HEADER FIELDS (Required)
    -- ========================================================================================
    ts_event TIMESTAMPTZ NOT NULL,
    ts_recv TIMESTAMPTZ NOT NULL,
    rtype INTEGER NOT NULL DEFAULT 19,  -- Always 19 for definition records
    publisher_id INTEGER NOT NULL,
    instrument_id INTEGER NOT NULL,
    
    -- ========================================================================================
    -- CORE DEFINITION FIELDS (Required)
    -- ========================================================================================
    raw_symbol TEXT NOT NULL,
    security_update_action CHAR(1) NOT NULL CHECK (security_update_action IN ('A', 'M', 'D')),
    instrument_class TEXT NOT NULL,
    min_price_increment DECIMAL(20,8) NOT NULL CHECK (min_price_increment > 0),
    display_factor DECIMAL(20,8) NOT NULL CHECK (display_factor > 0),
    expiration TIMESTAMPTZ NOT NULL,
    activation TIMESTAMPTZ NOT NULL,
    high_limit_price DECIMAL(20,8) NOT NULL,
    low_limit_price DECIMAL(20,8) NOT NULL,
    max_price_variation DECIMAL(20,8) NOT NULL CHECK (max_price_variation >= 0),
    unit_of_measure_qty DECIMAL(20,8) NOT NULL CHECK (unit_of_measure_qty > 0),
    min_price_increment_amount DECIMAL(20,8) NOT NULL CHECK (min_price_increment_amount >= 0),
    price_ratio DECIMAL(20,8) NOT NULL,
    inst_attrib_value INTEGER NOT NULL CHECK (inst_attrib_value >= 0),
    
    -- ========================================================================================
    -- OPTIONAL IDENTIFIERS
    -- ========================================================================================
    underlying_id INTEGER,
    raw_instrument_id INTEGER,
    
    -- ========================================================================================
    -- MARKET DEPTH AND TRADING PARAMETERS (Required)
    -- ========================================================================================
    market_depth_implied INTEGER NOT NULL CHECK (market_depth_implied >= 0),
    market_depth INTEGER NOT NULL CHECK (market_depth >= 0),
    market_segment_id INTEGER NOT NULL CHECK (market_segment_id >= 0),
    max_trade_vol INTEGER NOT NULL CHECK (max_trade_vol >= 0),
    min_lot_size INTEGER NOT NULL CHECK (min_lot_size >= 0),
    min_lot_size_block INTEGER NOT NULL CHECK (min_lot_size_block >= 0),
    min_lot_size_round_lot INTEGER NOT NULL CHECK (min_lot_size_round_lot >= 0),
    min_trade_vol INTEGER NOT NULL CHECK (min_trade_vol >= 0),
    
    -- ========================================================================================
    -- CONTRACT SPECIFICATIONS (Optional)
    -- ========================================================================================
    contract_multiplier INTEGER,
    decay_quantity INTEGER,
    original_contract_size INTEGER,
    appl_id INTEGER,
    maturity_year INTEGER,
    decay_start_date DATE,
    channel_id INTEGER NOT NULL DEFAULT 0,
    
    -- ========================================================================================
    -- CURRENCY AND CLASSIFICATION
    -- ========================================================================================
    currency TEXT NOT NULL,
    settl_currency TEXT,
    secsubtype TEXT,
    group_code TEXT NOT NULL,
    exchange TEXT NOT NULL,
    asset TEXT NOT NULL,
    cfi TEXT,
    security_type TEXT,
    unit_of_measure TEXT,
    underlying TEXT,
    
    -- ========================================================================================
    -- OPTIONS-SPECIFIC FIELDS
    -- ========================================================================================
    strike_price_currency TEXT,
    strike_price DECIMAL(20,8),
    
    -- ========================================================================================
    -- MARKET STRUCTURE FIELDS
    -- ========================================================================================
    match_algorithm TEXT,
    main_fraction INTEGER,
    price_display_format INTEGER,
    sub_fraction INTEGER,
    underlying_product INTEGER,
    maturity_month INTEGER CHECK (maturity_month BETWEEN 1 AND 12),
    maturity_day INTEGER CHECK (maturity_day BETWEEN 1 AND 31),
    maturity_week INTEGER CHECK (maturity_week BETWEEN 1 AND 53),
    user_defined_instrument TEXT,
    contract_multiplier_unit INTEGER,
    flow_schedule_type INTEGER,
    tick_rule INTEGER,
    
    -- ========================================================================================
    -- LEG FIELDS (For spreads and strategies)
    -- ========================================================================================
    leg_count INTEGER NOT NULL DEFAULT 0 CHECK (leg_count >= 0),
    leg_index INTEGER,
    leg_instrument_id INTEGER,
    leg_raw_symbol TEXT,
    leg_instrument_class TEXT,
    leg_side TEXT,
    leg_price DECIMAL(20,8),
    leg_delta DECIMAL(20,8),
    leg_ratio_price_numerator INTEGER,
    leg_ratio_price_denominator INTEGER,
    leg_ratio_qty_numerator INTEGER,
    leg_ratio_qty_denominator INTEGER,
    leg_underlying_id INTEGER,
    
    -- ========================================================================================
    -- METADATA AND TRACKING
    -- ========================================================================================
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- ========================================================================================
    -- CONSTRAINTS
    -- ========================================================================================
    -- Primary constraint: unique instrument per event time
    CONSTRAINT pk_definitions_data PRIMARY KEY (instrument_id, ts_event),
    
    -- Business logic constraints
    CONSTRAINT chk_price_limits CHECK (high_limit_price >= low_limit_price),
    CONSTRAINT chk_lot_sizes CHECK (min_lot_size_block >= min_lot_size),
    CONSTRAINT chk_leg_fields CHECK (
        (leg_count = 0 AND leg_index IS NULL) OR 
        (leg_count > 0 AND leg_index IS NOT NULL)
    )
);

-- ================================================================================================
-- CREATE HYPERTABLE
-- ================================================================================================
-- Convert to TimescaleDB hypertable partitioned by ts_event
SELECT create_hypertable('definitions_data', 'ts_event');

-- ================================================================================================
-- INDEXES FOR PERFORMANCE
-- ================================================================================================

-- Primary lookup indexes
CREATE INDEX idx_definitions_instrument_time ON definitions_data (instrument_id, ts_event DESC);
CREATE INDEX idx_definitions_raw_symbol_time ON definitions_data (raw_symbol, ts_event DESC);

-- Product family and classification indexes
CREATE INDEX idx_definitions_asset_class ON definitions_data (asset, instrument_class);
CREATE INDEX idx_definitions_exchange_asset ON definitions_data (exchange, asset);
CREATE INDEX idx_definitions_group_asset ON definitions_data (group_code, asset);

-- Expiration and maturity indexes for futures analysis
CREATE INDEX idx_definitions_expiration ON definitions_data (expiration);
CREATE INDEX idx_definitions_maturity ON definitions_data (maturity_year, maturity_month);
CREATE INDEX idx_definitions_active_contracts ON definitions_data (asset, expiration) 
    WHERE expiration > NOW();

-- Spread and leg analysis indexes
CREATE INDEX idx_definitions_spreads ON definitions_data (asset, leg_count) 
    WHERE leg_count > 0;
CREATE INDEX idx_definitions_leg_lookup ON definitions_data (leg_instrument_id, ts_event)
    WHERE leg_instrument_id IS NOT NULL;

-- Options-specific indexes
CREATE INDEX idx_definitions_options ON definitions_data (asset, strike_price)
    WHERE instrument_class = 'OPT';

-- Update action and currency indexes
CREATE INDEX idx_definitions_update_action ON definitions_data (security_update_action, ts_event);
CREATE INDEX idx_definitions_currency ON definitions_data (currency);

-- ================================================================================================
-- PERFORMANCE OPTIMIZATION
-- ================================================================================================

-- Enable compression on older chunks (data older than 7 days)
ALTER TABLE definitions_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'instrument_id, asset',
    timescaledb.compress_orderby = 'ts_event DESC'
);

-- Set compression policy (compress chunks older than 7 days)
SELECT add_compression_policy('definitions_data', INTERVAL '7 days');

-- Set retention policy (keep data for 2 years)
SELECT add_retention_policy('definitions_data', INTERVAL '2 years');

-- ================================================================================================
-- COMMENTS AND DOCUMENTATION
-- ================================================================================================

COMMENT ON TABLE definitions_data IS 
'Databento instrument definition data stored as TimescaleDB hypertable. Contains point-in-time reference information about financial instruments including futures, options, and spreads.';

COMMENT ON COLUMN definitions_data.ts_event IS 'Matching-engine-received timestamp (partition key)';
COMMENT ON COLUMN definitions_data.instrument_id IS 'Databento numeric instrument ID (primary key component)';
COMMENT ON COLUMN definitions_data.raw_symbol IS 'Exchange-native symbol format';
COMMENT ON COLUMN definitions_data.leg_count IS 'Number of legs (0 for outrights, >0 for spreads)';
COMMENT ON COLUMN definitions_data.asset IS 'Underlying asset/product code (e.g., ES, CL, NG)';

-- ================================================================================================
-- VERIFICATION QUERIES
-- ================================================================================================

-- Verify table structure
\d definitions_data

-- Verify hypertable creation
SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'definitions_data';

-- Verify indexes
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'definitions_data' ORDER BY indexname; 