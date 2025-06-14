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

This table stores instrument definitions and metadata for all market instruments, including contract specifications, trading parameters, and multi-leg instrument details.

```sql
CREATE TABLE IF NOT EXISTS definitions_data (
   ts_event TIMESTAMPTZ NOT NULL,
   ts_recv TIMESTAMPTZ NOT NULL,
   rtype SMALLINT NOT NULL,
   publisher_id SMALLINT NOT NULL,
   instrument_id INTEGER NOT NULL,
   raw_symbol VARCHAR(255) NOT NULL,
   security_update_action CHAR(1) NOT NULL,
   instrument_class CHAR(2) NOT NULL,
   min_price_increment NUMERIC NOT NULL,
   display_factor NUMERIC NOT NULL,
   expiration TIMESTAMPTZ NOT NULL,
   activation TIMESTAMPTZ NOT NULL,
   high_limit_price NUMERIC NOT NULL,
   low_limit_price NUMERIC NOT NULL,
   max_price_variation NUMERIC NOT NULL,
   unit_of_measure_qty NUMERIC,
   min_price_increment_amount NUMERIC,
   price_ratio NUMERIC,
   inst_attrib_value INTEGER NOT NULL,
   underlying_id INTEGER,
   raw_instrument_id BIGINT,
   market_depth_implied INTEGER NOT NULL,
   market_depth INTEGER NOT NULL,
   market_segment_id INTEGER NOT NULL,
   max_trade_vol BIGINT NOT NULL,
   min_lot_size INTEGER NOT NULL,
   min_lot_size_block INTEGER,
   min_lot_size_round_lot INTEGER,
   min_trade_vol BIGINT NOT NULL,
   contract_multiplier INTEGER,
   decay_quantity INTEGER,
   original_contract_size INTEGER,
   appl_id SMALLINT,
   maturity_year SMALLINT,
   decay_start_date DATE,
   channel_id SMALLINT NOT NULL,
   currency VARCHAR(4) NOT NULL,
   settl_currency VARCHAR(4),
   secsubtype VARCHAR(6),
   security_group VARCHAR(21) NOT NULL,
   exchange VARCHAR(5) NOT NULL,
   asset VARCHAR(11) NOT NULL,
   cfi VARCHAR(7),
   security_type VARCHAR(7),
   unit_of_measure VARCHAR(31),
   underlying VARCHAR(21),
   strike_price_currency VARCHAR(4),
   strike_price NUMERIC,
   match_algorithm CHAR(1),
   main_fraction SMALLINT,
   price_display_format SMALLINT,
   sub_fraction SMALLINT,
   underlying_product SMALLINT,
   maturity_month SMALLINT,
   maturity_day SMALLINT,
   maturity_week SMALLINT,
   user_defined_instrument CHAR(1),
   contract_multiplier_unit SMALLINT,
   flow_schedule_type SMALLINT,
   tick_rule SMALLINT,
   leg_count SMALLINT NOT NULL,
   leg_index SMALLINT,
   leg_instrument_id INTEGER,
   leg_raw_symbol VARCHAR(255),
   leg_instrument_class CHAR(2),
   leg_side CHAR(1),
   leg_price NUMERIC,
   leg_delta NUMERIC,
   leg_ratio_price_numerator INTEGER,
   leg_ratio_price_denominator INTEGER,
   leg_ratio_qty_numerator INTEGER,
   leg_ratio_qty_denominator INTEGER,
   leg_underlying_id INTEGER,
   PRIMARY KEY (instrument_id, ts_event, leg_index)
);
SELECT create_hypertable('definitions_data', by_range('ts_event', INTERVAL '90 days'), if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_definitions_instrument_time ON definitions_data (instrument_id, ts_event DESC);
```
