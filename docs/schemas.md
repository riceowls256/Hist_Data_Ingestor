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
