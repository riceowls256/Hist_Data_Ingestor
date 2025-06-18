# Database Schemas (TimescaleDB)

The standardized data is persisted in TimescaleDB hypertables, optimized for time-series workloads. Each supported schema will have a dedicated table.

daily_ohlcv_data Hypertable

This table stores daily OHLCV data, as defined in the initial MVP scope.

```sql
CREATE TABLE IF NOT EXISTS daily_ohlcv_data (
   ts_event TIMESTAMPTZ NOT NULL,
   instrument_id INTEGER NOT NULL,
   open_price NUMERIC NOT NULL,
   high_price NUMERIC NOT NULL,
   low_price NUMERIC NOT NULL,
   close_price NUMERIC NOT NULL,
   volume BIGINT NOT NULL,
   trade_count INTEGER NULL,
   vwap NUMERIC NULL,
   granularity VARCHAR(10) NOT NULL,
   data_source VARCHAR(50) NOT NULL,
   PRIMARY KEY (instrument_id, ts_event, granularity)
);
SELECT create_hypertable('daily_ohlcv_data', by_range('ts_event', chunk_time_interval => INTERVAL '7 days'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_daily_ohlcv_instrument_time ON daily_ohlcv_data (instrument_id, ts_event DESC);
```

trades_data Hypertable

This table stores individual trade events from the trades schema.

```sql
CREATE TABLE IF NOT EXISTS trades_data (
   ts_event TIMESTAMPTZ NOT NULL,
   ts_recv TIMESTAMPTZ NOT NULL,
   publisher_id SMALLINT NOT NULL,
   instrument_id INTEGER NOT NULL,
   price NUMERIC NOT NULL,
   size INTEGER NOT NULL,
   action CHAR(1) NOT NULL,
   side CHAR(1) NOT NULL,
   flags SMALLINT NOT NULL,
   depth SMALLINT NOT NULL,
   sequence INTEGER NULL,
   ts_in_delta INTEGER NULL,
   PRIMARY KEY (instrument_id, ts_event, sequence, price, size, side)
);
SELECT create_hypertable('trades_data', by_range('ts_event', INTERVAL '1 day'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_trades_instrument_time ON trades_data (instrument_id, ts_event DESC);
```

tbbo_data Hypertable

This table stores trade events along with the corresponding top-of-book quote from the tbbo schema.

```sql
CREATE TABLE IF NOT EXISTS tbbo_data (
   ts_event TIMESTAMPTZ NOT NULL,
   ts_recv TIMESTAMPTZ NOT NULL,
   publisher_id SMALLINT NOT NULL,
   instrument_id INTEGER NOT NULL,
   price NUMERIC NOT NULL,
   size INTEGER NOT NULL,
   action CHAR(1) NOT NULL,
   side CHAR(1) NOT NULL,
   flags SMALLINT NOT NULL,
   depth SMALLINT NOT NULL,
   sequence INTEGER NULL,
   ts_in_delta INTEGER NULL,
   bid_px_00 NUMERIC NULL,
   ask_px_00 NUMERIC NULL,
   bid_sz_00 INTEGER NULL,
   ask_sz_00 INTEGER NULL,
   bid_ct_00 INTEGER NULL,
   ask_ct_00 INTEGER NULL,
   PRIMARY KEY (instrument_id, ts_event, sequence, price, size, side)
);
SELECT create_hypertable('tbbo_data', by_range('ts_event', INTERVAL '1 day'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_tbbo_instrument_time ON tbbo_data (instrument_id, ts_event DESC);
```

statistics_data Hypertable

This table stores official summary statistics from the statistics schema.

```sql
CREATE TABLE IF NOT EXISTS statistics_data (
   ts_event TIMESTAMPTZ NOT NULL,
   ts_recv TIMESTAMPTZ NOT NULL,
   ts_ref TIMESTAMPTZ NOT NULL,
   publisher_id SMALLINT NOT NULL,
   instrument_id INTEGER NOT NULL,
   price NUMERIC NULL,
   quantity INTEGER NULL,
   sequence INTEGER NOT NULL,
   ts_in_delta INTEGER NOT NULL,
   stat_type SMALLINT NOT NULL,
   channel_id SMALLINT NOT NULL,
   update_action SMALLINT NOT NULL,
   stat_flags SMALLINT NOT NULL,
   PRIMARY KEY (instrument_id, ts_event, stat_type, sequence)
);
SELECT create_hypertable('statistics_data', by_range('ts_event', INTERVAL '7 days'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_statistics_instrument_time_type ON statistics_data (instrument_id, ts_event DESC, stat_type);
```

## definitions_data Hypertable

**Status: ✅ IMPLEMENTED in Story 2.4**

This table stores comprehensive instrument definition metadata from Databento's definition schema. Supports the complete 73-field DatabentoDefinitionRecord model with all header fields, core specifications, contract parameters, leg data for spreads, and optional metadata.

**Key Features:**
- **Complete Field Coverage:** All 73 fields from DatabentoDefinitionRecord model
- **Multi-Asset Support:** Futures, options, spreads, and combination instruments
- **TimescaleDB Optimization:** Hypertable with compression and retention policies
- **Business Logic Constraints:** Price limits, lot sizes, and leg field validation
- **Performance Indexes:** Optimized for asset, expiration, and instrument lookups

```sql
-- ================================================================================================
-- Databento Instrument Definition Data - TimescaleDB Hypertable Schema
-- ================================================================================================
-- This schema defines the definitions_data hypertable for storing instrument definition metadata
-- from Databento API. Supports the complete 73-field DatabentoDefinitionRecord model.
--
-- Story: 2.4 - Add Support for Databento Instrument Definition Schema
-- ================================================================================================

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
    CONSTRAINT pk_definitions_data PRIMARY KEY (instrument_id, ts_event),
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
SELECT create_hypertable('definitions_data', 'ts_event');

-- ================================================================================================
-- PERFORMANCE INDEXES
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
-- Enable compression (compress chunks older than 7 days)
ALTER TABLE definitions_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'instrument_id, asset',
    timescaledb.compress_orderby = 'ts_event DESC'
);

SELECT add_compression_policy('definitions_data', INTERVAL '7 days');
SELECT add_retention_policy('definitions_data', INTERVAL '2 years');
```

**Usage Examples:**
```sql
-- Get latest ES futures definitions
SELECT * FROM definitions_data 
WHERE asset = 'ES' AND instrument_class = 'FUT' 
ORDER BY expiration LIMIT 10;

-- Find all active spreads
SELECT raw_symbol, leg_count, expiration 
FROM definitions_data 
WHERE leg_count > 0 AND expiration > NOW()
ORDER BY asset, expiration;

-- Contract specification analysis
SELECT asset, currency, min_price_increment, contract_multiplier, unit_of_measure_qty
FROM definitions_data 
WHERE instrument_class = 'FUT' 
GROUP BY asset, currency, min_price_increment, contract_multiplier, unit_of_measure_qty;
```
