"""
Pydantic models for all data provider structures.

This module defines the data models for different data provider schemas including
Databento OHLCV, Trades, TBBO, and Statistics data. These models serve as the
common data contracts throughout the entire pipeline.
"""

from datetime import datetime, timezone, date
from decimal import Decimal
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_serializer, field_validator


class DatabentoOHLCVRecord(BaseModel):
    """
    Pydantic model for Databento OHLCV (Open, High, Low, Close, Volume) records.

    Represents aggregated price and volume data for a specific time period.
    """

    # Timestamp fields
    ts_event: datetime = Field(..., description="Event timestamp (when the bar period ended)")
    ts_recv: Optional[datetime] = Field(None, description="Receive timestamp (fallback to ts_event if not available)")
    ts_init: Optional[datetime] = Field(None, description="Initial timestamp (when the bar period started)")

    # Symbol information
    instrument_id: int = Field(..., description="Databento instrument ID")
    symbol: str = Field(..., description="Symbol string")

    # Required fields for storage compatibility
    rtype: Optional[int] = Field(None, description="Record type (for storage compatibility)")
    publisher_id: Optional[int] = Field(None, description="Publisher ID (for storage compatibility)")

    # OHLCV data
    open_price: Decimal = Field(..., description="Opening price for the period")
    high_price: Decimal = Field(..., description="Highest price during the period")
    low_price: Decimal = Field(..., description="Lowest price during the period")
    close_price: Decimal = Field(..., description="Closing price for the period")
    volume: int = Field(..., description="Total volume traded during the period")

    # Additional fields
    vwap: Optional[Decimal] = Field(None, description="Volume-weighted average price")
    trade_count: Optional[int] = Field(None, description="Number of trades in the period")

    @field_serializer('ts_event', 'ts_recv', 'ts_init', when_used='json')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format."""
        return value.isoformat() if value else None

    @field_serializer('open_price', 'high_price', 'low_price', 'close_price', 'vwap', when_used='json')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serialize Decimal fields to string."""
        return str(value) if value is not None else None

    @field_validator('ts_event', 'ts_recv', 'ts_init')
    @classmethod
    def ensure_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime fields are timezone-aware (UTC)."""
        if v is None:
            return v
        if v.tzinfo is None:
            # Naive datetime - assume it's UTC and make it timezone-aware
            return v.replace(tzinfo=timezone.utc)
        return v


class DatabentoTradeRecord(BaseModel):
    """
    Pydantic model for Databento Trade records.

    Represents individual trade executions.
    """

    # Timestamp fields
    ts_event: datetime = Field(..., description="Event timestamp (when the trade occurred)")
    ts_recv: Optional[datetime] = Field(None, description="Receive timestamp")

    # Symbol information
    instrument_id: int = Field(..., description="Databento instrument ID")
    symbol: str = Field(..., description="Symbol string")

    # Trade data
    price: Decimal = Field(..., description="Trade price")
    size: int = Field(..., description="Trade size/quantity")
    
    # Additional fields expected by the loader
    quantity: Optional[int] = Field(None, description="Trade quantity (alias for size)")
    trade_type: Optional[str] = Field(None, description="Type of trade")
    conditions: Optional[str] = Field(None, description="Trade conditions")
    sale_condition: Optional[str] = Field(None, description="Sale condition code")
    sequence: Optional[int] = Field(None, description="Sequence number")

    # Trade metadata
    side: Optional[str] = Field(None, description="Trade side (A=Ask, B=Bid, N=None)")
    trade_id: Optional[str] = Field(None, description="Unique trade identifier")
    order_id: Optional[str] = Field(None, description="Order identifier")

    @field_serializer('ts_event', 'ts_recv', when_used='json')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format."""
        return value.isoformat() if value else None

    @field_serializer('price', when_used='json')
    def serialize_decimal(self, value: Decimal) -> str:
        """Serialize Decimal fields to string."""
        return str(value)

    @field_validator('ts_event', 'ts_recv')
    @classmethod
    def ensure_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime fields are timezone-aware (UTC)."""
        if v is None:
            return v
        if v.tzinfo is None:
            # Naive datetime - assume it's UTC and make it timezone-aware
            return v.replace(tzinfo=timezone.utc)
        return v

    def __init__(self, **data):
        """Initialize the trade record and set quantity = size if not provided."""
        super().__init__(**data)
        # Set quantity to size if not explicitly provided
        if self.quantity is None and self.size is not None:
            self.quantity = self.size


class DatabentoTBBORecord(BaseModel):
    """
    Pydantic model for Databento TBBO (Top of Book Bid/Offer) records.

    Represents the best bid and offer prices and sizes.
    """

    # Timestamp fields
    ts_event: datetime = Field(..., description="Event timestamp")
    ts_recv: Optional[datetime] = Field(None, description="Receive timestamp")

    # Symbol information
    instrument_id: int = Field(..., description="Databento instrument ID")
    symbol: str = Field(..., description="Symbol string")

    # Bid data
    bid_px: Optional[Decimal] = Field(None, description="Best bid price")
    bid_sz: Optional[int] = Field(None, description="Best bid size")
    bid_ct: Optional[int] = Field(None, description="Number of orders at best bid")

    # Ask/Offer data
    ask_px: Optional[Decimal] = Field(None, description="Best ask/offer price")
    ask_sz: Optional[int] = Field(None, description="Best ask/offer size")
    ask_ct: Optional[int] = Field(None, description="Number of orders at best ask")

    # Additional fields
    sequence: Optional[int] = Field(None, description="Sequence number")
    flags: Optional[int] = Field(None, description="Record flags")

    @field_serializer('ts_event', 'ts_recv', when_used='json')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format."""
        return value.isoformat() if value else None

    @field_serializer('bid_px', 'ask_px', when_used='json')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serialize Decimal fields to string."""
        return str(value) if value is not None else None

    @field_validator('ts_event', 'ts_recv')
    @classmethod
    def ensure_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime fields are timezone-aware (UTC)."""
        if v is None:
            return v
        if v.tzinfo is None:
            # Naive datetime - assume it's UTC and make it timezone-aware
            return v.replace(tzinfo=timezone.utc)
        return v


class DatabentoStatisticsRecord(BaseModel):
    """
    Pydantic model for Databento Statistics records.

    Represents various statistical data like settlement prices, open interest, etc.
    """

    # Timestamp fields
    ts_event: datetime = Field(..., description="Event timestamp")
    ts_recv: Optional[datetime] = Field(None, description="Receive timestamp")

    # Symbol information
    instrument_id: int = Field(..., description="Databento instrument ID")
    symbol: str = Field(..., description="Symbol string")

    # Statistical data
    stat_type: int = Field(..., description="Type of statistic")
    stat_value: Optional[Decimal] = Field(None, description="Statistical value")

    # Common statistics fields
    open_interest: Optional[int] = Field(None, description="Open interest")
    settlement_price: Optional[Decimal] = Field(None, description="Settlement price")
    high_limit: Optional[Decimal] = Field(None, description="High price limit")
    low_limit: Optional[Decimal] = Field(None, description="Low price limit")

    # Additional fields
    sequence: Optional[int] = Field(None, description="Sequence number")
    flags: Optional[int] = Field(None, description="Record flags")

    @field_serializer('ts_event', 'ts_recv', when_used='json')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format."""
        return value.isoformat() if value else None

    @field_serializer('stat_value', 'settlement_price', 'high_limit', 'low_limit', when_used='json')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serialize Decimal fields to string."""
        return str(value) if value is not None else None

    @field_validator('ts_event', 'ts_recv')
    @classmethod
    def ensure_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime fields are timezone-aware (UTC)."""
        if v is None:
            return v
        if v.tzinfo is None:
            # Naive datetime - assume it's UTC and make it timezone-aware
            return v.replace(tzinfo=timezone.utc)
        return v


class DatabentoDefinitionRecord(BaseModel):
    """
    Pydantic model for the complete Databento Instrument Definition record.
    Represents point-in-time reference information about an instrument.
    """
    # Header fields
    ts_event: datetime = Field(..., description="The matching-engine-received timestamp.")
    ts_recv: datetime = Field(..., description="The Databento gateway-received timestamp.")
    rtype: int = Field(..., description="A sentinel value indicating the record type (always 19).")
    publisher_id: int = Field(..., description="The publisher ID assigned by Databento.")
    instrument_id: int = Field(..., description="The numeric instrument ID.")

    # Core Definition Fields
    raw_symbol: str = Field(..., description="The instrument name (symbol) provided by the publisher.")
    security_update_action: str = Field(..., description="Indicates if the definition is Added, Modified, or Deleted.")
    instrument_class: str = Field(..., description="The classification of the instrument (e.g., 'FUT').")
    min_price_increment: Decimal = Field(..., description="The minimum constant tick for the instrument.")
    display_factor: Decimal = Field(..., description="The multiplier to convert display price to conventional price.")
    expiration: datetime = Field(..., description="The last eligible trade time.")
    activation: datetime = Field(..., description="The time of instrument activation.")
    high_limit_price: Decimal = Field(..., description="Allowable high limit price for the trading day.")
    low_limit_price: Decimal = Field(..., description="Allowable low limit price for the trading day.")
    max_price_variation: Decimal = Field(..., description="Differential value for price banding.")
    unit_of_measure_qty: Decimal = Field(..., description="The contract size for each instrument.")
    min_price_increment_amount: Decimal = Field(..., description="The value currently under development by the venue.")
    price_ratio: Decimal = Field(..., description="The value used for price calculation in spread and leg pricing.")
    inst_attrib_value: int = Field(..., description="A bitmap of instrument eligibility attributes.")
    underlying_id: Optional[int] = Field(None, description="The instrument_id of the first underlying instrument.")
    raw_instrument_id: Optional[int] = Field(None, description="The instrument ID assigned by the publisher.")
    market_depth_implied: int = Field(..., description="The implied book depth on the price level data feed.")
    market_depth: int = Field(..., description="The (outright) book depth on the price level data feed.")
    market_segment_id: int = Field(..., description="The market segment of the instrument.")
    max_trade_vol: int = Field(..., description="The maximum trading volume for the instrument.")
    min_lot_size: int = Field(..., description="The minimum order entry quantity for the instrument.")
    min_lot_size_block: int = Field(..., description="The minimum quantity required for a block trade.")
    min_lot_size_round_lot: int = Field(..., description="The minimum quantity required for a round lot.")
    min_trade_vol: int = Field(..., description="The minimum trading volume for the instrument.")
    contract_multiplier: Optional[int] = Field(None, description="The number of deliverables per instrument.")
    decay_quantity: Optional[int] = Field(None, description="The quantity that a contract will decay daily.")
    original_contract_size: Optional[int] = Field(
        None, description="The fixed contract value assigned to each instrument.")
    appl_id: Optional[int] = Field(None, description="The channel ID assigned at the venue.")
    maturity_year: Optional[int] = Field(None, description="The calendar year reflected in the instrument symbol.")
    decay_start_date: Optional[date] = Field(None, description="The date at which a contract will begin to decay.")
    channel_id: int = Field(..., description="The channel ID assigned by Databento.")
    currency: str = Field(..., description="The currency used for price fields.")
    settl_currency: Optional[str] = Field(None, description="The currency used for settlement.")
    secsubtype: Optional[str] = Field(None, description="The strategy type of the spread.")
    group: str = Field(..., description="The security group code of the instrument.")
    exchange: str = Field(..., description="The exchange used to identify the instrument.")
    asset: str = Field(..., description="The underlying asset code (product code).")
    cfi: Optional[str] = Field(None, description="The ISO standard instrument categorization code.")
    security_type: Optional[str] = Field(None, description="The type of the instrument.")
    unit_of_measure: Optional[str] = Field(
        None, description="The unit of measure for the instrument’s original contract size.")
    underlying: Optional[str] = Field(None, description="The symbol of the first underlying instrument.")
    strike_price_currency: Optional[str] = Field(None, description="The currency used for strike_price.")
    strike_price: Optional[Decimal] = Field(None, description="The exercise price if the instrument is an option.")
    match_algorithm: Optional[str] = Field(None, description="The matching algorithm used for the instrument.")
    main_fraction: Optional[int] = Field(None, description="The price denominator of the main fraction.")
    price_display_format: Optional[int] = Field(None, description="The number of digits to the right of the tick mark.")
    sub_fraction: Optional[int] = Field(None, description="The price denominator of the sub fraction.")
    underlying_product: Optional[int] = Field(None, description="The product complex of the instrument.")
    maturity_month: Optional[int] = Field(None, description="The calendar month reflected in the instrument symbol.")
    maturity_day: Optional[int] = Field(None, description="The calendar day reflected in the instrument symbol.")
    maturity_week: Optional[int] = Field(None, description="The calendar week reflected in the instrument symbol.")
    user_defined_instrument: Optional[str] = Field(None, description="Indicates if the instrument is user defined.")
    contract_multiplier_unit: Optional[int] = Field(None, description="The type of contract_multiplier.")
    flow_schedule_type: Optional[int] = Field(None, description="The schedule for delivering electricity.")
    tick_rule: Optional[int] = Field(None, description="The tick rule of the spread.")

    # Leg fields for spreads/strategies
    leg_count: int = Field(..., description="The number of legs in the strategy (0 for outrights).")
    leg_index: Optional[int] = Field(None, description="The 0-based index of the leg.")
    leg_instrument_id: Optional[int] = Field(None, description="The numeric ID assigned to the leg instrument.")
    leg_raw_symbol: Optional[str] = Field(None, description="The leg instrument's raw symbol.")
    leg_instrument_class: Optional[str] = Field(None, description="The leg instrument's classification.")
    leg_side: Optional[str] = Field(None, description="The side taken for the leg.")
    leg_price: Optional[Decimal] = Field(None, description="The tied price (if any) of the leg.")
    leg_delta: Optional[Decimal] = Field(None, description="The associated delta (if any) of the leg.")
    leg_ratio_price_numerator: Optional[int] = Field(None, description="The numerator of the price ratio of the leg.")
    leg_ratio_price_denominator: Optional[int] = Field(
        None, description="The denominator of the price ratio of the leg.")
    leg_ratio_qty_numerator: Optional[int] = Field(None, description="The numerator of the quantity ratio of the leg.")
    leg_ratio_qty_denominator: Optional[int] = Field(
        None, description="The denominator of the quantity ratio of the leg.")
    leg_underlying_id: Optional[int] = Field(
        None, description="The numeric ID of the leg instrument's underlying instrument.")

    # --- SERIALIZERS ---
    @field_serializer(
        'ts_event', 'ts_recv', 'expiration', 'activation',
        when_used='json'
    )
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format."""
        return value.isoformat() if value else None

    @field_serializer(
        'min_price_increment', 'display_factor', 'high_limit_price', 'low_limit_price',
        'max_price_variation', 'unit_of_measure_qty', 'min_price_increment_amount',
        'price_ratio', 'strike_price', 'leg_price', 'leg_delta',
        when_used='json'
    )
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serialize Decimal fields to string to preserve precision."""
        return str(value) if value is not None else None

    # --- VALIDATORS ---
    @field_validator('ts_event', 'ts_recv', 'expiration', 'activation')
    @classmethod
    def ensure_timezone_aware(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure datetime fields are timezone-aware (UTC)."""
        if v is None:
            return v
        if v.tzinfo is None:
            # Naive datetime - assume it's UTC and make it timezone-aware
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


# Schema mapping for easy lookup
DATABENTO_SCHEMA_MODEL_MAPPING = {
    "ohlcv-1s": DatabentoOHLCVRecord,
    "ohlcv-1m": DatabentoOHLCVRecord,
    "ohlcv-5m": DatabentoOHLCVRecord,
    "ohlcv-15m": DatabentoOHLCVRecord,
    "ohlcv-1h": DatabentoOHLCVRecord,
    "ohlcv-1d": DatabentoOHLCVRecord,
    "trades": DatabentoTradeRecord,
    "tbbo": DatabentoTBBORecord,
    "statistics": DatabentoStatisticsRecord,
    "definition": DatabentoDefinitionRecord,
}
