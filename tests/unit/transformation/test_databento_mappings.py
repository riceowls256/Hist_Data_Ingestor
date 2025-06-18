import pytest
from decimal import Decimal
from datetime import datetime, timezone
from src.storage.models import (
    DatabentoOHLCVRecord, DatabentoTradeRecord, DatabentoTBBORecord, DatabentoStatisticsRecord
)
from src.transformation.rule_engine.engine import RuleEngine, TransformationError, ValidationRuleError
import os

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), '../../fixtures/test_databento_mappings.yaml')

@pytest.fixture(scope='module')
def rule_engine():
    return RuleEngine(FIXTURE_PATH)

# 1. OHLCV record transformation
def test_ohlcv_transformation(rule_engine):
    record = DatabentoOHLCVRecord(
        ts_event=datetime(2024, 6, 13, 12, 0, tzinfo=timezone.utc),
        ts_init=datetime(2024, 6, 13, 11, 59, tzinfo=timezone.utc),
        instrument_id=1,
        symbol='AAPL',
        open_price=Decimal('100.0'),
        high_price=Decimal('105.0'),
        low_price=Decimal('95.0'),
        close_price=Decimal('102.0'),
        volume=1000,
        vwap=Decimal('101.0'),
        trade_count=10
    )
    result = rule_engine.transform_record(record, 'ohlcv-1d')
    assert result['open_price'] == Decimal('100.0')
    assert result['high_price'] == Decimal('105.0')
    assert result['low_price'] == Decimal('95.0')
    assert result['close_price'] == Decimal('102.0')
    assert result['vwap'] == Decimal('101.0')
    assert result['volume'] == 1000
    assert result['granularity'] == '1d'
    assert result['data_source'] == 'databento'

# 2. Trade record transformation
def test_trade_transformation(rule_engine):
    record = DatabentoTradeRecord(
        ts_event=datetime(2024, 6, 13, 12, 1, tzinfo=timezone.utc),
        ts_recv=datetime(2024, 6, 13, 12, 1, 1, tzinfo=timezone.utc),
        instrument_id=2,
        symbol='MSFT',
        price=Decimal('250.5'),
        size=50,
        side='A',
        trade_id='T123',
        order_id='O456'
    )
    result = rule_engine.transform_record(record, 'trades')
    assert result['price'] == Decimal('250.5')
    assert result['size'] == 50
    assert result['side'] == 'A'
    assert result['publisher_id'] == 1
    assert result['action'] == 'T'

# 3. TBBO record transformation
def test_tbbo_transformation(rule_engine):
    record = DatabentoTBBORecord(
        ts_event=datetime(2024, 6, 13, 12, 2, tzinfo=timezone.utc),
        ts_recv=datetime(2024, 6, 13, 12, 2, 1, tzinfo=timezone.utc),
        instrument_id=3,
        symbol='GOOG',
        bid_px=Decimal('100.1'),
        bid_sz=10,
        bid_ct=1,
        ask_px=Decimal('100.2'),
        ask_sz=12,
        ask_ct=2,
        sequence=123,
        flags=0
    )
    result = rule_engine.transform_record(record, 'tbbo')
    assert result['bid_px'] == Decimal('100.1')
    assert result['ask_px'] == Decimal('100.2')
    assert result['bid_sz'] == 10
    assert result['ask_sz'] == 12
    assert result['sequence'] == 123
    assert result['flags'] == 0
    assert result['action'] == 'Q'
    assert result['side'] == 'N'

# 4. Statistics record transformation (conditional mapping)
def test_statistics_transformation_settlement(rule_engine):
    record = DatabentoStatisticsRecord(
        ts_event=datetime(2024, 6, 13, 12, 3, tzinfo=timezone.utc),
        ts_recv=datetime(2024, 6, 13, 12, 3, 1, tzinfo=timezone.utc),
        instrument_id=4,
        symbol='TSLA',
        stat_type=1,  # Settlement price
        stat_value=Decimal('300.0'),
        open_interest=1000,
        settlement_price=Decimal('300.0'),
        high_limit=None,
        low_limit=None,
        sequence=456,
        flags=1
    )
    result = rule_engine.transform_record(record, 'statistics')
    assert result['price'] == Decimal('300.0')  # settlement_price mapped to price via conditional mapping
    assert result['stat_type'] == 1
    assert result['sequence'] == 456
    assert result['stat_flags'] == 1  # flags mapped to stat_flags in fixture
    assert result['ts_ref'] == 'ts_event'  # Default value from fixture

# 5. Error handling for invalid mapping/config
def test_invalid_schema_raises(rule_engine):
    record = DatabentoOHLCVRecord(
        ts_event=datetime(2024, 6, 13, 12, 0, tzinfo=timezone.utc),
        ts_init=datetime(2024, 6, 13, 11, 59, tzinfo=timezone.utc),
        instrument_id=1,
        symbol='AAPL',
        open_price=Decimal('100.0'),
        high_price=Decimal('105.0'),
        low_price=Decimal('95.0'),
        close_price=Decimal('102.0'),
        volume=1000,
        vwap=Decimal('101.0'),
        trade_count=10
    )
    with pytest.raises(Exception):
        rule_engine.transform_record(record, 'nonexistent_schema')

# 6. Edge cases (nulls, missing fields, type mismatches)
def test_null_fields_and_type_mismatch(rule_engine):
    # TBBO with null bid/ask
    record = DatabentoTBBORecord(
        ts_event=datetime(2024, 6, 13, 12, 2, tzinfo=timezone.utc),
        ts_recv=datetime(2024, 6, 13, 12, 2, 1, tzinfo=timezone.utc),
        instrument_id=3,
        symbol='GOOG',
        bid_px=None,
        bid_sz=None,
        bid_ct=None,
        ask_px=None,
        ask_sz=None,
        ask_ct=None,
        sequence=None,
        flags=None
    )
    result = rule_engine.transform_record(record, 'tbbo')
    assert result['bid_px'] is None
    assert result['ask_px'] is None
    assert result['bid_sz'] is None
    assert result['ask_sz'] is None
    # OHLCV with type mismatch (string instead of Decimal)
    import pytest
    with pytest.raises(Exception):
        DatabentoOHLCVRecord(
            ts_event=datetime(2024, 6, 13, 12, 0, tzinfo=timezone.utc),
            ts_init=datetime(2024, 6, 13, 11, 59, tzinfo=timezone.utc),
            instrument_id=1,
            symbol='AAPL',
            open='not_a_decimal',  # type: ignore
            high=Decimal('105.0'),
            low=Decimal('95.0'),
            close=Decimal('102.0'),
            volume=1000,
            vwap=Decimal('101.0'),
            count=10
        ) 