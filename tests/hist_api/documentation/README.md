# Historical API Testing Framework

## Overview
Comprehensive testing suite for validating Databento API integration, schema compliance, and production readiness. Contains specialized test scripts for different data types and schemas.

## Quick Start
```bash
# Ensure environment is configured
source venv/bin/activate
export DATABENTO_API_KEY="your_key_here"

# Run basic connectivity test
python tests/hist_api/test_api_connection.py
```

## Test Scripts

### Core Tests
- **`test_api_connection.py`** - Basic connectivity and authentication validation
- **`test_futures_api.py`** - Comprehensive futures testing across multiple schemas

### Schema-Specific Tests  
- **`test_statistics_schema.py`** - Statistics schema exploration
- **`analyze_stats_fields.py`** - Complete statistics field documentation
- **`test_cme_statistics.py`** - CME Globex compliance verification
- **`test_status_schema.py`** - Market status and trading state validation

### Definition Schema Tests (Special Handling Required)
- **`test_definitions_schema.py`** - Standard definition testing (shows 0 results)
- **`test_definitions_broad.py`** - Discovers 36.6M+ records exist
- **`test_definitions_analysis.py`** - Record structure analysis
- **`test_definitions_detailed.py`** - Symbology mapping attempts  
- **`test_definitions_fixed.py`** - **WORKING SOLUTION** with manual filtering

## ⚠️ Critical Discovery: Definition Schema

### Problem
Symbol filtering is **broken** for the definition schema:
```python
# This returns 0 records (incorrectly)
data = client.timeseries.get_range(
    schema="definition",
    symbols=["ES.c.0"]  # ← Filtering doesn't work!
)
```

### Solution
Query all records, then filter manually by instrument_id:
```python
# Correct approach
data = client.timeseries.get_range(
    schema="definition",
    # No symbols parameter!
    start="2024-12-01",
    end="2024-12-31"
)

# Filter manually
for record in data:
    if record.instrument_id == 4916:  # ES instrument ID
        # Process definition record
        pass
```

### Results
- **Total Records**: 36.6M+ definition records available
- **ES Definitions**: 53 records with complete contract specifications
- **Data Quality**: Rich metadata (tick sizes, multipliers, limits, expiration)

### Getting Instrument IDs
1. Use `status` schema: `instrument_id: 4916` for ES
2. Use symbology API to map symbols to IDs
3. Cross-reference between schemas

## Validated Schemas & Performance

| Schema | Records | Time | Use Case |
|--------|---------|------|----------|
| ohlcv-1d | 1 | < 1s | Daily analysis |
| ohlcv-1h | 23 | < 1s | Intraday patterns |
| trades | 493K+ | ~10s | High-frequency analysis |
| tbbo | 493K+ | ~10s | Spread analysis |
| statistics | 6-12 | < 1s | Settlement/OI data |
| **definition** | **36.6M+** | **~3min** | **Contract specs** |
| status | 33 | < 1s | Market state |

## CME Globex Compliance ✅
Successfully validated all 10/10 expected CME statistics types:
- Opening Price, Settlement Price, Open Interest
- Session High/Low, Cleared Volume
- Bid/Offer levels, Fixing Price

## Common Issues & Solutions

### Symbol Format
- ❌ Wrong: `ES.FUT` 
- ✅ Correct: `ES.c.0`

### Environment Issues
```bash
# Fix broken environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Date Range Errors
- Error: `end must be after start`
- Fix: Verify date order in script configuration

## Production Ready ✅
- Authentication and connection management
- Multi-schema data retrieval  
- CME Globex compliance (10/10 statistics)
- High-volume data handling (493K+ records)
- Comprehensive error handling and retry logic

## Configuration

Most scripts use configurable variables at the top for easy modification:

```python
# Example from test_futures_api.py
SYMBOL = "ES.c.0"           # Contract symbol
DATASET = "GLBX.MDP3"       # CME Globex dataset
CONTRACT_NAME = "E-mini S&P 500"  # Display name
```

## Supported Contracts

- `ES.c.0` - E-mini S&P 500
- `CL.c.0` - Crude Oil WTI  
- `NG.c.0` - Natural Gas
- `GC.c.0` - Gold
- `ZN.c.0` - 10-Year Treasury Notes
- `6E.c.0` - Euro FX

## Schema Coverage

✅ **OHLCV (Daily & Hourly):** Price/volume bars  
✅ **Trades:** Individual trade events  
✅ **TBBO:** Top-of-book quotes with trades  
✅ **Statistics:** Settlement prices, open interest, session highs/lows  
✅ **Definitions:** Instrument metadata and contract specifications  

## Expected Results

✅ **CME Statistics Coverage:** 10/10 statistics types confirmed  
✅ **Performance Benchmarks:** Up to 493K records in ~10 seconds  
✅ **Data Quality:** All validation checks pass  
✅ **Schema Support:** OHLCV, Trades, TBBO, Statistics, Definitions

## Documentation

See `docs/api/databento_testing_guide.md` for comprehensive testing procedures and troubleshooting. 