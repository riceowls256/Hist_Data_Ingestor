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

Internal APIs Provided

For the MVP, which is a monolithic application, there are no internal APIs exposed in the sense of separate network services. All internal component interactions occur via direct Python method calls.
