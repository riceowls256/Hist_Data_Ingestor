# Databento API Testing Guide

## Overview
This guide provides comprehensive testing procedures for validating Databento API integration, based on live testing sessions that verified production readiness and CME Globex compliance.

## Quick Start Testing

### Environment Setup
```bash
# Ensure virtual environment is active
source venv/bin/activate

# Verify databento installation
pip show databento  # Should show databento-0.57.0

# Set required environment variables
export DATABENTO_API_KEY="your_key_here"
export DATABENTO_API_URL="https://hist.databento.com"
```

### Core Connectivity Test
```bash
python tests/hist_api/test_api_connection.py
```
**Expected Output:**
- ✅ Environment variables loaded
- ✅ Databento client created 
- ✅ Successfully connected and retrieved data
- ✅ Data processing successful

## Available Test Scripts

### 1. `test_api_connection.py`
**Purpose:** Basic connectivity and authentication validation
**Usage:** `python tests/hist_api/test_api_connection.py`
**Validates:**
- Environment variable configuration
- API authentication
- Basic data retrieval
- Record processing functionality

### 2. `test_futures_api.py` 
**Purpose:** Comprehensive futures contract testing across multiple schemas
**Configuration Variables (edit at top of file):**
```python
SYMBOL = "ES.c.0"           # Contract symbol
DATASET = "GLBX.MDP3"       # CME Globex dataset
CONTRACT_NAME = "E-mini S&P 500"  # Display name
```

**Supported Contracts:**
- `ES.c.0` - E-mini S&P 500
- `CL.c.0` - Crude Oil WTI
- `NG.c.0` - Natural Gas
- `GC.c.0` - Gold
- `ZN.c.0` - 10-Year Treasury Notes
- `6E.c.0` - Euro FX

**Testing Schemas:**
- **OHLCV Daily (1d):** Single daily bar
- **OHLCV Hourly (1h):** ~23 hourly bars
- **Trades:** 400K+ individual trade records
- **TBBO:** 400K+ top-of-book quotes

### 3. `test_statistics_schema.py`
**Purpose:** Statistics schema exploration and validation
**Returns:** Session statistics (highs, lows, open interest)

### 4. `analyze_stats_fields.py`
**Purpose:** Comprehensive statistics field analysis
**Output:** Complete documentation of all 20 statistics data fields

### 5. `test_cme_statistics.py`
**Purpose:** CME Globex MDP 3.0 publisher compliance verification
**Validates:** All 10 expected CME statistics types

## CME Statistics Coverage Verification

### Expected Statistics Types (All ✅ Confirmed)
1. **Opening Price** - Session opening values
2. **Settlement Price** - Daily settlement values
3. **Open Interest** - Outstanding contract positions  
4. **Session High Price** - Intraday maximum prices
5. **Session Low Price** - Intraday minimum prices
6. **Cleared Volume** - Total cleared trading volume
7. **Lowest Offer** - Best ask prices available
8. **Highest Bid** - Best bid prices available
9. **Fixing Price** - Reference/benchmark prices
10. **Settlement Price (alt)** - Alternative settlement calculations

### Production Volume Validation
- **30-day statistics:** 12,100+ total records
- **60-day settlements:** 125+ settlement records
- **Coverage:** 100% of expected CME statistics types

## Performance Benchmarks

| Schema | Time Period | Record Count | Response Time |
|--------|-------------|--------------|---------------|
| ohlcv-1d | 30 days | 1 | < 1 second |
| ohlcv-1h | 30 days | 23 | < 1 second |
| trades | 1 day | 493,000+ | ~10 seconds |
| tbbo | 1 day | 493,000+ | ~10 seconds |
| statistics | 30 days | 6-12 | < 1 second |

## Common Issues and Solutions

### 1. Symbol Format Errors
**Problem:** No data returned for `ES.FUT` format
**Solution:** Use continuous contract format `ES.c.0`
**Rule:** Always use `.c.0` suffix for current front month

### 2. Date Range Errors  
**Problem:** `ValidationError: end must be after start`
**Cause:** Accidentally reversed start/end dates
**Solution:** Verify date order in script configuration

### 3. Virtual Environment Issues
**Symptoms:** Import errors, package not found
**Solution:**
```bash
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Authentication Failures
**Problem:** API key rejection
**Check:** Environment variable setting
```bash
echo $DATABENTO_API_KEY  # Should return your key
```

## Data Validation Checklist

### OHLCV Data Quality
- ✅ Realistic price ranges (ES: $5000-6000 range)
- ✅ Proper OHLC relationships (High ≥ Open,Close ≥ Low)
- ✅ Non-zero volume for active contracts
- ✅ Accurate timestamp formatting

### Statistics Data Quality  
- ✅ All 10 CME statistics types present
- ✅ Reasonable value ranges for each type
- ✅ Proper timestamp alignment
- ✅ Non-null values for active trading sessions

### Trade/Quote Data Quality
- ✅ High-frequency data (400K+ records/day)
- ✅ Microsecond timestamp precision
- ✅ Realistic bid/ask spreads
- ✅ Proper trade size distributions

## Testing Best Practices

### 1. Progressive Testing
1. Start with basic connectivity (`tests/hist_api/test_api_connection.py`)
2. Test single schema with small date range
3. Expand to multiple schemas
4. Test high-volume data retrieval
5. Validate statistics compliance

### 2. Environment Validation
- Always activate virtual environment first
- Verify databento version compatibility
- Test with fresh environment when issues arise

### 3. Data Validation
- Cross-check data ranges for reasonableness
- Verify schema compliance with expected fields
- Test edge cases (weekends, holidays)

### 4. Performance Testing
- Monitor response times for different data volumes
- Test timeout handling for large requests
- Validate retry logic with network interruptions

## Integration Testing

### DatabentoAdapter Validation
```python
from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter

# Test adapter initialization
adapter = DatabentoAdapter()

# Test context manager
with adapter as client:
    data = client.fetch_timeseries_data(
        symbols=["ES.c.0"],
        schema="ohlcv-1d", 
        start="2024-01-01",
        end="2024-01-02"
    )
    print(f"Retrieved {len(data)} records")
```

### Model Validation
```python
from src.storage.models import OHLCVData

# Verify Pydantic model processing
for record in data:
    ohlcv_model = OHLCVData(
        ts_recv=record.ts_recv,
        open=record.open,
        high=record.high,
        low=record.low,
        close=record.close,
        volume=record.volume
    )
    assert ohlcv_model.open <= ohlcv_model.high
    assert ohlcv_model.low <= ohlcv_model.close
```

## Production Readiness Checklist

- ✅ Authentication working with production API keys
- ✅ All four schemas (OHLCV, Trades, TBBO, Statistics) tested
- ✅ CME Globex compliance verified (10/10 statistics types)
- ✅ High-volume data handling validated (400K+ records)
- ✅ Error handling and retry logic confirmed
- ✅ Data quality validation automated
- ✅ Environment setup documented and tested
- ✅ Performance benchmarks established

## Next Steps

After successful testing:
1. Update configuration management for multiple contracts
2. Implement automated data quality monitoring  
3. Set up production data ingestion pipelines
4. Create alerting for API failures or data quality issues
5. Document operational procedures for contract rollovers 