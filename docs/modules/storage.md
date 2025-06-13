# Storage Module

The storage module is responsible for defining the data contracts (Pydantic models) used throughout the pipeline and handling the persistence of data to the database (e.g., TimescaleDB). It ensures data integrity, consistency, and provides a clear schema for all system components.

## Overview

The storage module serves two primary purposes:
1.  **Data Modeling**: Defines the canonical Pydantic models for all data provider schemas, serving as a single source of truth for data structures.
2.  **Data Persistence**: Provides the logic for loading transformed data into the database (future implementation).

### Key Features
- **Centralized Data Models**: A single location for all data contracts.
- **Data Validation**: Pydantic models enforce data types and constraints.
- **Serialization**: Custom serializers for data types like `Decimal` and `datetime`.
- **Timezone Normalization**: Ensures all timestamps are timezone-aware (UTC).
- **Schema Mapping**: Clear mapping from provider schemas to Pydantic models.

## Architecture
The Pydantic models defined in this module are used as data transfer objects (DTOs) across the entire pipeline:
```
┌───────────┐    ┌────────────────┐    ┌────────────┐
│ Ingestion │    │ Transformation │    │  Storage   │
│ (Adapter) │───▶│    (Engine)    │───▶│ (Loader)   │
└───────────┘    └────────────────┘    └────────────┘
      │                  │                   │
      ▼                  ▼                   ▼
┌──────────────────────────────────────────────────┐
│              src/storage/models.py               │
│ (DatabentoOHLCVRecord, DatabentoTradeRecord, etc)│
└──────────────────────────────────────────────────┘
```

## Key Components

### 1. `models.py` - Pydantic Data Models
This file contains all Pydantic models that represent data from various providers. These models are the primary data contracts used by the ingestion, transformation, and storage layers.

#### Databento Models
The following models are defined for the Databento API:

- **`DatabentoOHLCVRecord`**: Represents OHLCV (Open, High, Low, Close, Volume) data.
- **`DatabentoTradeRecord`**: Represents individual trade events.
- **`DatabentoTBBORecord`**: Represents Top-of-Book (best bid/offer) data.
- **`DatabentoStatisticsRecord`**: Represents various market statistics (e.g., settlement price, open interest).

#### Model Features
- **Type Hinting**: All fields are strongly typed (e.g., `Decimal` for price, `datetime` for timestamps).
- **Field Descriptions**: Clear descriptions for every field.
- **Custom Serializers**:
  - `datetime` fields are serialized to ISO 8601 strings.
  - `Decimal` fields are serialized to strings to preserve precision.
- **Custom Validators**:
  - `@field_validator('ts_event', 'ts_recv')`: Ensures that all timestamp fields are timezone-aware and normalized to UTC.

#### Schema to Model Mapping
A dictionary `DATABENTO_SCHEMA_MODEL_MAPPING` provides an easy lookup from the Databento schema string to the corresponding Pydantic model. This is used by the `DatabentoAdapter` to dynamically validate incoming records.

```python
# From src/storage/models.py
DATABENTO_SCHEMA_MODEL_MAPPING = {
    "ohlcv-1s": DatabentoOHLCVRecord,
    "ohlcv-1m": DatabentoOHLCVRecord,
    "ohlcv-1d": DatabentoOHLCVRecord,
    "trades": DatabentoTradeRecord,
    "tbbo": DatabentoTBBORecord,
    "statistics": DatabentoStatisticsRecord,
}
```

### 2. `timescale_loader.py` - Database Loader (Future)
This component is reserved for the implementation of the database loading logic. It will be responsible for taking the transformed data dictionaries and efficiently inserting them into the appropriate TimescaleDB hypertables.

## Pydantic Model Examples

### `DatabentoOHLCVRecord`
```python
class DatabentoOHLCVRecord(BaseModel):
    """Pydantic model for Databento OHLCV records."""
    ts_event: datetime = Field(..., description="Event timestamp")
    instrument_id: int = Field(..., description="Databento instrument ID")
    symbol: str = Field(..., description="Symbol string")
    open: Decimal = Field(..., description="Opening price")
    high: Decimal = Field(..., description="Highest price")
    low: Decimal = Field(..., description="Lowest price")
    close: Decimal = Field(..., description="Closing price")
    volume: int = Field(..., description="Total volume")
    # ... with custom validators and serializers
```

### `DatabentoTradeRecord`
```python
class DatabentoTradeRecord(BaseModel):
    """Pydantic model for Databento Trade records."""
    ts_event: datetime = Field(..., description="Event timestamp")
    instrument_id: int = Field(..., description="Databento instrument ID")
    symbol: str = Field(..., description="Symbol string")
    price: Decimal = Field(..., description="Trade price")
    size: int = Field(..., description="Trade size")
    side: Optional[str] = Field(None, description="Trade side (A=Ask, B=Bid, N=None)")
    # ... with custom validators and serializers
```

## Usage in the Pipeline

1.  **Ingestion**: The `DatabentoAdapter` fetches raw records and uses `DATABENTO_SCHEMA_MODEL_MAPPING` to validate each record into the correct Pydantic model instance. This ensures that only well-formed data enters the system.

2.  **Transformation**: The `RuleEngine` receives these Pydantic model instances. It reads their attributes to apply mapping and validation rules defined in the YAML configuration.

3.  **Storage (Future)**: The `TimescaleLoader` will receive the final transformed dictionaries (which are aligned with the database schema) and perform the `INSERT` operations.

## Best Practices

- **Immutability**: Treat Pydantic models as immutable data contracts. Once created by the ingestion layer, they should not be modified.
- **Single Source of Truth**: `models.py` should be the only place where data structures are defined.
- **Precision**: Use the `Decimal` type for all financial data (prices, etc.) to avoid floating-point inaccuracies.
- **Timezones**: Always ensure timestamps are timezone-aware (UTC) to prevent ambiguity.
- **Extensibility**: When adding a new data provider, create a new set of Pydantic models for its schemas in `models.py`.

This storage module provides a robust and type-safe foundation for the entire data pipeline, ensuring data quality and consistency from ingestion to final storage. 