"""
Pydantic models for all data provider structures.

This module defines the data models for different data provider schemas including
Databento OHLCV, Trades, TBBO, and Statistics data. These models serve as the
common data contracts throughout the entire pipeline.
"""

from datetime import datetime, timezone
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
    ts_init: Optional[datetime] = Field(None, description="Initial timestamp (when the bar period started)")
    
    # Symbol information
    instrument_id: int = Field(..., description="Databento instrument ID")
    symbol: str = Field(..., description="Symbol string")
    
    # OHLCV data
    open: Decimal = Field(..., description="Opening price for the period")
    high: Decimal = Field(..., description="Highest price during the period")
    low: Decimal = Field(..., description="Lowest price during the period")
    close: Decimal = Field(..., description="Closing price for the period")
    volume: int = Field(..., description="Total volume traded during the period")
    
    # Additional fields
    vwap: Optional[Decimal] = Field(None, description="Volume-weighted average price")
    count: Optional[int] = Field(None, description="Number of trades in the period")
    
    @field_serializer('ts_event', 'ts_init', when_used='json')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime fields to ISO format."""
        return value.isoformat() if value else None
    
    @field_serializer('open', 'high', 'low', 'close', 'vwap', when_used='json')
    def serialize_decimal(self, value: Optional[Decimal]) -> Optional[str]:
        """Serialize Decimal fields to string."""
        return str(value) if value is not None else None
    
    @field_validator('ts_event', 'ts_init')
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
}
