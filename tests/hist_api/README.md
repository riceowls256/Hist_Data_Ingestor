# Historical API Tests

This directory contains comprehensive test scripts for validating the Databento Historical API integration.

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export DATABENTO_API_KEY="your_key_here"
export DATABENTO_API_URL="https://hist.databento.com"

# Run basic connectivity test
python tests/hist_api/test_api_connection.py
```

## Test Scripts

| Script | Purpose | Runtime |
|--------|---------|---------|
| `test_api_connection.py` | Basic connectivity validation | < 5 seconds |
| `test_futures_api.py` | Multi-schema contract testing | 30-60 seconds |
| `test_statistics_schema.py` | Statistics exploration | < 10 seconds |
| `analyze_stats_fields.py` | Field structure analysis | < 10 seconds |
| `test_cme_statistics.py` | CME compliance verification | 60-120 seconds |
| `debug_databento_record.py` | Record debugging utilities | < 5 seconds |

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

## Expected Results

✅ **CME Statistics Coverage:** 10/10 statistics types confirmed  
✅ **Performance Benchmarks:** Up to 493K records in ~10 seconds  
✅ **Data Quality:** All validation checks pass  
✅ **Schema Support:** OHLCV, Trades, TBBO, Statistics

## Documentation

See `docs/api/databento_testing_guide.md` for comprehensive testing procedures and troubleshooting. 