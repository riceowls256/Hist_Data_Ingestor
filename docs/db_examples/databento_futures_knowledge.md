# Databento Futures API - Knowledge Base

## Overview

This document captures key insights and patterns from Databento's futures data handling, based on their official documentation examples.

## Key Concepts

### 1. Dataset Identification
- **Dataset ID**: `GLBX.MDP3` (CME Globex MDP 3.0)
- **Usage**: Must be passed as the `dataset` parameter in all API calls
- **Source**: Available from Databento's data catalog detail pages

### 2. Volume-Based Contract Discovery

**Pattern**: Use OHLCV-1d schema to find actively traded contracts
```python
# High-level approach
data = client.timeseries.get_range(
    dataset="GLBX.MDP3",
    symbols="ALL_SYMBOLS",  # Gets all available symbols
    schema="ohlcv-1d",
    start="2023-08-15"
)
```

**Key Insight**: `ALL_SYMBOLS` can be expensive - consider using parent symbology for efficiency (as demonstrated in our Story 2.4 work).

### 3. Instrument Definition Schema

**Critical Fields**:
- `instrument_id`: Numeric ID from exchange (tag 48-SecurityID for CME)
- `raw_symbol`: Exchange-native symbol format
- `min_price_increment`: Tick size for the instrument
- `match_algorithm`: Exchange matching algorithm (F, A, K, etc.)
- `expiration`: Contract expiration timestamp

**Usage Pattern**:
```python
data = client.timeseries.get_range(
    dataset="GLBX.MDP3",
    stype_in="instrument_id",  # Query by instrument ID
    symbols=instrument_id_list,
    schema="definition",
    start="2023-08-15",
)
```

### 4. Symbology Types

#### Parent Symbology (`stype_in="parent"`)
- **Purpose**: Efficiently fetch all child instruments for a product family
- **Example**: `ZB.FUT` → returns all ZB futures and spreads
- **Performance**: Dramatically more efficient than `ALL_SYMBOLS`
- **Our Implementation**: We use `ES.FUT` with 14,743x efficiency gain

#### Continuous Contract Symbology (`stype_in="continuous"`)
- **Purpose**: Track lead month contracts automatically
- **Examples**:
  - `ES.n.0`: Lead month by open interest
  - `ES.n.1`: Second month by open interest
  - `ES.c.0`: Lead month by calendar
  - `ES.v.0`: Lead month by volume
- **Key Feature**: No back-adjustment - shows actual tradable prices

### 5. Live Data Streaming

**BBO-1s Schema**: Best bid/offer subsampled at 1-second intervals
```python
live_client.subscribe(
    dataset="GLBX.MDP3",
    schema="bbo-1s",
    symbols="NQ.c.0",
    stype_in="continuous",
)
```

**Requirements**: Live license to GLBX.MDP3

## Special CME Globex Conventions

### 1. Weekly Trading Session
- Unlike other venues, CME Globex has weekly sessions
- **Impact**: Affects MBO data processing
- **Solution**: Databento provides synthetic snapshots at start of each UTC day

### 2. User-Defined Instruments (UDI)
- **Scope**: Large number of user-defined instruments and spreads
- **Coverage**: Databento includes all UDI (many vendors exclude these)
- **Rationale**: Many UDI are highly liquid and active

### 3. Asynchronous Trade Publication
- **Behavior**: Fills published before corresponding order deletions
- **Difference**: Most venues treat fill+deletion as atomic
- **Handling Options**:
  - Preemptively update book on trades
  - Wait for deletion events (action C)

### 4. Implied Book Trading
- **Feature**: CME has implied matching
- **Representation**: Full trade quantity shown, but only direct book fills
- **Identifier**: Implied trades have side 'N'

### 5. Market Structure Features
- **Inverted Spreads**: Possible during trading halts
- **Price Limits**: Various circuit breakers active
- **No Rollover Adjustments**: Continuous contracts show actual prices

## Integration with Our System

### Existing Capabilities
✅ **Parent Symbology**: Implemented in Story 2.4 with ES.FUT
✅ **Definition Schema**: DatabentoDefinitionRecord with 67 fields
✅ **Performance Optimization**: 14,743x efficiency demonstrated
✅ **Validation**: Comprehensive validation schema implemented

### New Insights from Documentation

#### 1. Volume-Based Discovery Pattern
**Status**: 🆕 **NEW INSIGHT**
- We haven't implemented volume-based contract discovery
- Could be valuable for dynamic contract selection
- OHLCV-1d schema usage pattern is new to our implementation

#### 2. Continuous Contract Symbology
**Status**: 🆕 **NEW INSIGHT** 
- We haven't implemented continuous contract handling
- `.n.0`, `.c.0`, `.v.0` patterns are new
- Could be very valuable for time-series analysis

#### 3. Live Streaming Implementation
**Status**: 🆕 **NEW INSIGHT**
- BBO-1s schema usage pattern
- Live client callback patterns
- Could complement our historical data pipeline

#### 4. CME-Specific Conventions
**Status**: 🔄 **PARTIAL KNOWLEDGE**
- We knew about UDI from our definition schema work
- Asynchronous trade publication is new insight
- Implied book handling is new insight

### Recommended Next Steps

1. **Continuous Contract Support**: Implement continuous contract symbology handling
2. **Volume Discovery**: Add volume-based contract discovery utilities
3. **Live Data Integration**: Consider live streaming capabilities
4. **CME Convention Handling**: Update transformation rules for CME-specific behaviors

## Code Examples Location

All executable code examples are available in:
- `docs/db_examples/futures_overview_example.py`

## References

- Databento Official Documentation
- Our Story 2.4 Implementation
- CME Globex MDP 3.0 Specifications 