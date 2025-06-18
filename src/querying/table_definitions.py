"""
SQLAlchemy table definitions for TimescaleDB schemas.

This module defines all database tables using SQLAlchemy Core for use in the
QueryBuilder. These definitions match the TimescaleDB schema definitions.
"""

from sqlalchemy import (
    Table, Column, Integer, String, TIMESTAMP, DECIMAL, BIGINT,
    SMALLINT, CHAR, DATE, MetaData, Index
)
from sqlalchemy.dialects.postgresql import TIMESTAMP as TIMESTAMPTZ

metadata = MetaData()

# Daily OHLCV Data Table
daily_ohlcv_data = Table(
    'daily_ohlcv_data', metadata,
    Column('ts_event', TIMESTAMPTZ(timezone=True), nullable=False, primary_key=True),
    Column('instrument_id', Integer, nullable=False, primary_key=True),
    Column('open_price', DECIMAL, nullable=False),
    Column('high_price', DECIMAL, nullable=False),
    Column('low_price', DECIMAL, nullable=False),
    Column('close_price', DECIMAL, nullable=False),
    Column('volume', BIGINT, nullable=False),
    Column('trade_count', Integer, nullable=True),
    Column('vwap', DECIMAL, nullable=True),
    Column('granularity', String(10), nullable=False, primary_key=True),
    Column('data_source', String(50), nullable=False),
    Column('symbol', String, nullable=False),  # Symbol field for direct queries
    Column('ts_recv', TIMESTAMPTZ(timezone=True), nullable=False),
    Column('rtype', Integer, nullable=False),
    Column('publisher_id', Integer, nullable=False),
    Column('created_at', TIMESTAMPTZ(timezone=True), nullable=False),
    Column('updated_at', TIMESTAMPTZ(timezone=True), nullable=False),

    # Indexes
    Index('idx_daily_ohlcv_instrument_time', 'instrument_id', 'ts_event'),
    Index('idx_daily_ohlcv_symbol_time', 'symbol', 'ts_event'),  # Index for symbol queries
)

# Trades Data Table
trades_data = Table(
    'trades_data', metadata,
    Column('ts_event', TIMESTAMPTZ(timezone=True), nullable=False, primary_key=True),
    Column('ts_recv', TIMESTAMPTZ(timezone=True), nullable=False),
    Column('publisher_id', SMALLINT, nullable=False),
    Column('instrument_id', Integer, nullable=False, primary_key=True),
    Column('price', DECIMAL, nullable=False, primary_key=True),
    Column('size', Integer, nullable=False, primary_key=True),
    Column('action', CHAR(1), nullable=False),
    Column('side', CHAR(1), nullable=False, primary_key=True),
    Column('flags', SMALLINT, nullable=False),
    Column('depth', SMALLINT, nullable=False),
    Column('sequence', Integer, nullable=True, primary_key=True),
    Column('ts_in_delta', Integer, nullable=True),

    # Indexes
    Index('idx_trades_instrument_time', 'instrument_id', 'ts_event'),
)

# TBBO Data Table
tbbo_data = Table(
    'tbbo_data', metadata,
    Column('ts_event', TIMESTAMPTZ(timezone=True), nullable=False, primary_key=True),
    Column('ts_recv', TIMESTAMPTZ(timezone=True), nullable=False),
    Column('publisher_id', SMALLINT, nullable=False),
    Column('instrument_id', Integer, nullable=False, primary_key=True),
    Column('price', DECIMAL, nullable=False, primary_key=True),
    Column('size', Integer, nullable=False, primary_key=True),
    Column('action', CHAR(1), nullable=False),
    Column('side', CHAR(1), nullable=False, primary_key=True),
    Column('flags', SMALLINT, nullable=False),
    Column('depth', SMALLINT, nullable=False),
    Column('sequence', Integer, nullable=True, primary_key=True),
    Column('ts_in_delta', Integer, nullable=True),
    Column('bid_px_00', DECIMAL, nullable=True),
    Column('ask_px_00', DECIMAL, nullable=True),
    Column('bid_sz_00', Integer, nullable=True),
    Column('ask_sz_00', Integer, nullable=True),
    Column('bid_ct_00', Integer, nullable=True),
    Column('ask_ct_00', Integer, nullable=True),

    # Indexes
    Index('idx_tbbo_instrument_time', 'instrument_id', 'ts_event'),
)

# Statistics Data Table
statistics_data = Table(
    'statistics_data', metadata,
    Column('ts_event', TIMESTAMPTZ(timezone=True), nullable=False, primary_key=True),
    Column('ts_recv', TIMESTAMPTZ(timezone=True), nullable=False),
    Column('ts_ref', TIMESTAMPTZ(timezone=True), nullable=False),
    Column('publisher_id', SMALLINT, nullable=False),
    Column('instrument_id', Integer, nullable=False, primary_key=True),
    Column('price', DECIMAL, nullable=True),
    Column('quantity', Integer, nullable=True),
    Column('sequence', Integer, nullable=False, primary_key=True),
    Column('ts_in_delta', Integer, nullable=False),
    Column('stat_type', SMALLINT, nullable=False, primary_key=True),
    Column('channel_id', SMALLINT, nullable=False),
    Column('update_action', SMALLINT, nullable=False),
    Column('stat_flags', SMALLINT, nullable=False),

    # Indexes
    Index('idx_statistics_instrument_time_type', 'instrument_id', 'ts_event', 'stat_type'),
)

# Definitions Data Table
definitions_data = Table(
    'definitions_data', metadata,
    # Header fields
    Column('ts_event', TIMESTAMPTZ(timezone=True), nullable=False, primary_key=True),
    Column('ts_recv', TIMESTAMPTZ(timezone=True), nullable=False),
    Column('rtype', Integer, nullable=False, default=19),
    Column('publisher_id', Integer, nullable=False),
    Column('instrument_id', Integer, nullable=False, primary_key=True),

    # Core definition fields
    Column('raw_symbol', String, nullable=False),
    Column('security_update_action', CHAR(1), nullable=False),
    Column('instrument_class', String, nullable=False),
    Column('min_price_increment', DECIMAL(20, 8), nullable=False),
    Column('display_factor', DECIMAL(20, 8), nullable=False),
    Column('expiration', TIMESTAMPTZ(timezone=True), nullable=False),
    Column('activation', TIMESTAMPTZ(timezone=True), nullable=False),
    Column('high_limit_price', DECIMAL(20, 8), nullable=False),
    Column('low_limit_price', DECIMAL(20, 8), nullable=False),
    Column('max_price_variation', DECIMAL(20, 8), nullable=False),
    Column('unit_of_measure_qty', DECIMAL(20, 8), nullable=False),
    Column('min_price_increment_amount', DECIMAL(20, 8), nullable=False),
    Column('price_ratio', DECIMAL(20, 8), nullable=False),
    Column('inst_attrib_value', Integer, nullable=False),

    # Optional identifiers
    Column('underlying_id', Integer, nullable=True),
    Column('raw_instrument_id', Integer, nullable=True),

    # Market depth and trading parameters
    Column('market_depth_implied', Integer, nullable=False),
    Column('market_depth', Integer, nullable=False),
    Column('market_segment_id', Integer, nullable=False),
    Column('max_trade_vol', Integer, nullable=False),
    Column('min_lot_size', Integer, nullable=False),
    Column('min_lot_size_block', Integer, nullable=False),
    Column('min_lot_size_round_lot', Integer, nullable=False),
    Column('min_trade_vol', Integer, nullable=False),

    # Contract specifications
    Column('contract_multiplier', Integer, nullable=True),
    Column('decay_quantity', Integer, nullable=True),
    Column('original_contract_size', Integer, nullable=True),
    Column('appl_id', Integer, nullable=True),
    Column('maturity_year', Integer, nullable=True),
    Column('decay_start_date', DATE, nullable=True),
    Column('channel_id', Integer, nullable=False, default=0),

    # Currency and classification
    Column('currency', String, nullable=False),
    Column('settl_currency', String, nullable=True),
    Column('secsubtype', String, nullable=True),
    Column('group_code', String, nullable=False),
    Column('exchange', String, nullable=False),
    Column('asset', String, nullable=False),
    Column('cfi', String, nullable=True),
    Column('security_type', String, nullable=True),
    Column('unit_of_measure', String, nullable=True),
    Column('underlying', String, nullable=True),

    # Additional fields (abbreviated for brevity - full 73 fields available)
    Column('strike_price_currency', String, nullable=True),
    Column('strike_price', DECIMAL(20, 8), nullable=True),
    Column('match_algorithm', String, nullable=True),
    Column('main_fraction', Integer, nullable=True),
    Column('price_display_format', Integer, nullable=True),
    Column('sub_fraction', Integer, nullable=True),
    Column('underlying_product', Integer, nullable=True),
    Column('maturity_month', Integer, nullable=True),
    Column('maturity_day', Integer, nullable=True),
    Column('maturity_week', Integer, nullable=True),
    Column('user_defined_instrument', CHAR(1), nullable=True),
    Column('contract_multiplier_unit', Integer, nullable=True),
    Column('flow_schedule_type', Integer, nullable=True),
    Column('tick_rule', Integer, nullable=True),

    # Leg fields for spreads
    Column('leg_count', Integer, nullable=True),
    Column('leg_index', Integer, nullable=True),
    Column('leg_instrument_id', Integer, nullable=True),
    Column('leg_raw_symbol', String, nullable=True),
    Column('leg_instrument_class', String, nullable=True),
    Column('leg_side', CHAR(1), nullable=True),
    Column('leg_price', DECIMAL(20, 8), nullable=True),
    Column('leg_delta', DECIMAL(20, 8), nullable=True),
    Column('leg_ratio_price_numerator', Integer, nullable=True),
    Column('leg_ratio_price_denominator', Integer, nullable=True),
    Column('leg_ratio_qty_numerator', Integer, nullable=True),
    Column('leg_ratio_qty_denominator', Integer, nullable=True),
    Column('leg_underlying_id', Integer, nullable=True),

    # Indexes
    Index('idx_definitions_instrument_time', 'instrument_id', 'ts_event'),
    Index('idx_definitions_symbol', 'raw_symbol'),
    Index('idx_definitions_asset_exchange', 'asset', 'exchange'),
)

# Schema mapping for easy access
SCHEMA_TABLES = {
    'daily_ohlcv': daily_ohlcv_data,
    'trades': trades_data,
    'tbbo': tbbo_data,
    'statistics': statistics_data,
    'definitions': definitions_data,
}

# Primary key mappings for each table
PRIMARY_KEYS = {
    'daily_ohlcv': ['instrument_id', 'ts_event', 'granularity'],
    'trades': ['instrument_id', 'ts_event', 'sequence', 'price', 'size', 'side'],
    'tbbo': ['instrument_id', 'ts_event', 'sequence', 'price', 'size', 'side'],
    'statistics': ['instrument_id', 'ts_event', 'stat_type', 'sequence'],
    'definitions': ['instrument_id', 'ts_event'],
}

# Index mappings for query optimization
INDEX_COLUMNS = {
    'daily_ohlcv': ['instrument_id', 'ts_event'],
    'trades': ['instrument_id', 'ts_event'],
    'tbbo': ['instrument_id', 'ts_event'],
    'statistics': ['instrument_id', 'ts_event', 'stat_type'],
    'definitions': ['instrument_id', 'ts_event', 'raw_symbol', 'asset', 'exchange'],
}
