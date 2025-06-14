# API Reference

This section provides a comprehensive reference for the external Databento API consumed by the system.

External APIs Consumed

## Databento Historical API

- **Purpose:** To acquire historical market data across a wide variety of schemas, including OHLCV, trades, top-of-book, and venue-published statistics.
- **Client Library:** databento-python.
- **Authentication:** Handled via a 32-character API key (starting with db-), which should be provided through a secure environment variable (DATABENTO_API_KEY).
- **Key Method Used:** The primary interaction for historical data is the timeseries.get_range() method from the databento-python client library.
- **Data Format:** The API returns data in the Databento Binary Encoding (DBN) format, a highly efficient, zero-copy serialization format that is decoded by the client library.

Supported Schemas

The system will interact with several key Databento schemas. A schema is a specific data record format.

OHLCV (Open, High, Low, Close, Volume)

- **Description:** Provides aggregated bar data for open, high, low, and close prices, along with the total volume traded during a specified interval. The schema name indicates the interval, such as ohlcv-1s (1-second), ohlcv-1m (1-minute), ohlcv-1h (1-hour), and ohlcv-1d (1-day).
- **Key Fields:**

| Field | Type | Description |
| :--- | :--- | :--- |
| ts_event | uint64_t | The inclusive start time of the bar aggregation period, as nanoseconds since the UNIX epoch. |
| open | int64_t | The open price for the bar, scaled by 1e-9. |
| high | int64_t | The high price for the bar, scaled by 1e-9. |
| low | int64_t | The low price for the bar, scaled by 1e-9. |
| close | int64_t | The close price for the bar, scaled by 1e-9. |
| volume | uint64_t | The total volume traded during the aggregation period. |

- **Notes:** The ts_event timestamp marks the beginning of the interval. If no trades occur within an interval, no OHLCV record is generated for that period. While convenient, it is recommended to construct OHLCV bars from the trades schema for maximum transparency and consistency, as vendor implementations can differ.

Trades

- **Description:** Provides a record for every individual trade event, often referred to as "time and sales" or "tick data". This schema is a subset of the more granular Market by Order (MBO) data.
- **Key Fields:**

| Field | Type | Description |
| :--- | :--- | :--- |
| ts_event | uint64_t | The matching-engine-received timestamp as nanoseconds since the UNIX epoch. |
| price | int64_t | The trade price, scaled by 1e-9. |
| size | uint32_t | The quantity of the trade. |
| action | char | The event action, which is always 'T' for the trades schema. |
| side | char | The side that initiated the trade (e.g., 'A' for ask, 'B' for bid). |
| flags | uint8_t | A bit field indicating event characteristics and data quality. |
| depth | uint8_t | The book level where the trade occurred. |
| sequence | uint32_t | The message sequence number from the venue. |

- **Notes:** This schema is fundamental and can be used to derive less granular schemas like OHLCV. For some venues, the highest level of detail is achieved by combining the trades feed with the MBO feed.

TBBO (BBO on Trade)

- **Description:** Provides every trade event along with the Best Bid and Offer (BBO) that was present on the book immediately before the trade occurred. This schema operates in "trade space," meaning a record is generated only when a trade happens. It is a subset of the MBP-1 schema.
- **Key Fields:**

| Field | Type | Description |
| :--- | :--- | :--- |
| ts_event | uint64_t | The matching-engine-received timestamp as nanoseconds since the UNIX epoch. |
| price | int64_t | The trade price, scaled by 1e-9. |
| size | uint32_t | The trade quantity. |
| action | char | The event action. Always 'T' (Trade) in the TBBO schema. |
| side | char | The side that initiated the trade. |
| flags | uint8_t | A bit field indicating event characteristics. |
| depth | uint8_t | The book level where the update occurred. |

- **Notes:** The fields are similar to the trades schema, but the record also contains the state of the BBO at the time of the trade. This is useful for constructing trading signals based on trade events without the higher volume of data from a full top-of-book feed like MBP-1.

Statistics

- **Description:** Provides official summary statistics for an instrument as published by the venue. This can include daily volume, open interest, settlement prices (preliminary and final), and official open, high, and low prices.
- **Key Fields:**

| Field | Type | Description |
| :--- | :--- | :--- |
| ts_event | uint64_t | The matching-engine-received timestamp as nanoseconds since the UNIX epoch. |
| ts_ref | uint64_t | The reference timestamp for the statistic (e.g., the time the settlement price applies to). |
| price | int64_t | The value for a price-based statistic, scaled by 1e-9. Unused fields contain INT64_MAX. |
| quantity | int32_t | The value for a quantity-based statistic. Unused fields contain INT32_MAX. |
| stat_type | uint16_t | An enum indicating the type of statistic (e.g., 1: Opening price, 3: Settlement price, 9: Open interest). |
| update_action | uint8_t | Indicates if the statistic is new (1) or a deletion (2). |
| stat_flags | uint8_t | Additional flags associated with the statistic (e.g., indicating a final vs. preliminary price). |

- **Notes:** This schema is the correct source for official settlement data, which may differ from data derived from electronic trading sessions (like the ohlcv-1d schema) because it can include block trades or other adjustments. The meaning of the price and quantity fields depends on the stat_type.

## Live API Testing Results & Production Validation

### Symbol Format Requirements
**Critical Finding:** Databento futures symbols require specific continuous contract notation.
- **Incorrect:** `ES.FUT` (returns no data)
- **Correct:** `ES.c.0` (returns current front month data)
- **Pattern:** Always use `.c.0` suffix for continuous front month contracts

### Record Access Pattern
**Implementation Detail:** Databento records use direct attribute access, not dictionary methods.
```python
# Correct approach
price = record.open
volume = record.volume

# Incorrect approach (method doesn't exist)
data = record.as_dict()  # AttributeError
```

### Performance Characteristics (ES.c.0 on GLBX.MDP3)

| Schema | Time Period | Record Count | Response Time | Use Case |
|--------|-------------|--------------|---------------|-----------|
| ohlcv-1d | 30 days | 1 | < 1 second | Daily analysis |
| ohlcv-1h | 30 days | 23 | < 1 second | Intraday patterns |
| trades | 1 day | 493,000+ | ~10 seconds | High-frequency analysis |
| tbbo | 1 day | 493,000+ | ~10 seconds | Spread analysis |
| statistics | 30 days | 6-12 | < 1 second | Settlement/OI data |
| definition | 2 months | 36.6M+ | ~3 minutes* | Contract specs |
| status | 7 days | 33 | < 1 second | Market state |

**\*Critical Note:** Definition schema requires special handling - see Schema-Specific Issues below.

### CME Globex MDP 3.0 Statistics Coverage
**Compliance Verification:** Successfully confirmed all 10 expected CME statistics types:

| Stat Type | Description | Production Volume |
|-----------|-------------|-------------------|
| 1 | Opening Price | Daily |
| 3 | Settlement Price | Daily |  
| 9 | Open Interest | Daily |
| 4 | Session High Price | Daily |
| 5 | Session Low Price | Daily |
| 12 | Cleared Volume | Daily |
| 14 | Lowest Offer | Intraday |
| 15 | Highest Bid | Intraday |
| 16 | Fixing Price | As needed |
| 18 | Settlement Price (alt) | As needed |

**Production Data Volumes:**
- 30-day statistics: 12,100+ total records
- 60-day settlements: 125+ settlement records
- Coverage: 100% of expected CME statistics types

### Supported Futures Contracts (Tested)
```python
# Contract examples with symbols
CONTRACTS = {
    "ES.c.0": "E-mini S&P 500",      # Equity Index
    "CL.c.0": "Crude Oil WTI",       # Energy
    "NG.c.0": "Natural Gas",         # Energy  
    "GC.c.0": "Gold",                # Metals
    "ZN.c.0": "10-Year Treasury",    # Interest Rates
    "6E.c.0": "Euro FX"              # Currencies
}
```

### Data Quality Validation Results
**OHLCV Data (ES.c.0):**
- ✅ Price ranges: $5,000-6,000 (realistic for ES)
- ✅ OHLC relationships: High ≥ Open,Close ≥ Low
- ✅ Volume: Non-zero for active trading periods
- ✅ Timestamps: Proper UTC formatting

**Statistics Data:**
- ✅ All 10 CME statistics types validated
- ✅ Reasonable settlement price ranges
- ✅ Open interest values align with CME reports
- ✅ Proper timestamp/session alignment

**High-Frequency Data (Trades/TBBO):**
- ✅ 400K+ records per day validated
- ✅ Microsecond timestamp precision
- ✅ Realistic bid/ask spreads (0.25-1.00 points)
- ✅ Trade size distributions match market patterns

### Authentication & Environment Setup
**Required Environment Variables:**
```bash
export DATABENTO_API_KEY="db-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export DATABENTO_API_URL="https://hist.databento.com"
```

**Validation Command:**
```bash
python tests/hist_api/test_api_connection.py
```

### Common Production Issues & Solutions

1. **Date Range Errors**
   - Error: `ValidationError: end must be after start`
   - Cause: Reversed start/end dates
   - Prevention: Validate date order in code

2. **Symbol Format Issues**
   - Problem: No data returned
   - Check: Use `.c.0` format for continuous contracts
   - Verify: Symbol exists in dataset

3. **Environment Setup**
   - Issue: Import/package errors
   - Solution: Recreate virtual environment
   - Command: `pip install -r requirements.txt`

### Schema-Specific Issues

#### ⚠️ Definition Schema: Symbol Filtering Broken
**Critical Finding:** The `definition` schema contains 36.6M+ rich instrument metadata records, but symbol filtering does not work.

**Problem:**
```python
# This returns 0 records (incorrectly)
data = client.timeseries.get_range(
    dataset="GLBX.MDP3",
    schema="definition",
    symbols=["ES.c.0"],  # ← Filtering fails!
    start="2024-12-01",
    end="2024-12-31"
)
```

**Solution:**
```python
# Query all records, filter by instrument_id manually
data = client.timeseries.get_range(
    dataset="GLBX.MDP3",
    schema="definition",
    # No symbols parameter
    start="2024-12-01", 
    end="2024-12-31"
)

# Filter manually
for record in data:
    if record.instrument_id == 4916:  # ES instrument ID
        # Process ES definition record
        pass
```

**Definition Record Example (ES):**
- Instrument ID: 4916
- Symbol: ESM5 (June 2025 contract)
- Exchange: XCME, Currency: USD
- Tick Size: 0.25, Multiplier: $50
- Daily Limits: 5757.5 - 6602.0
- Expiration: June 20, 2025

**Getting Instrument IDs:**
1. Use `status` schema to find IDs for symbols
2. Use Databento symbology API
3. Cross-reference between schemas

### Integration Testing Framework
**Available Test Scripts:**
- `tests/hist_api/test_api_connection.py` - Basic connectivity validation
- `tests/hist_api/test_futures_api.py` - Multi-schema contract testing
- `tests/hist_api/test_statistics_schema.py` - Statistics exploration
- `tests/hist_api/test_cme_statistics.py` - CME compliance verification
- `tests/hist_api/analyze_stats_fields.py` - Field structure analysis

**Reference:** See `docs/api/databento_testing_guide.md` for comprehensive testing procedures.

## Internal APIs Provided

For the MVP, which is a monolithic application, there are no internal APIs exposed in the sense of separate network services. All internal component interactions occur via direct Python method calls.
