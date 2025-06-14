# Definition Schema Analysis Summary

## Overview
This document summarizes our comprehensive analysis of the Databento definition schema for ES (E-mini S&P 500) futures contracts, conducted by scanning 500,000+ records from the GLBX.MDP3 dataset.

## Key Findings

### 📊 Dataset Scale
- **Total Records Processed**: 500,000+ definition records
- **ES-Related Contracts Found**: 422 contracts
- **Security Type Distribution**:
  - Options on Futures (OOF): 443,404 records (88.7%)
  - Futures (FUT): 56,553 records (11.3%)
  - Interest Rate Swaps (IRS): 43 records (0.0%)

### 🎯 ES Contract Categories

#### Standard ES Futures (21 contracts)
Traditional quarterly E-mini S&P 500 futures following CME naming conventions:
- **Pattern**: ES + Month Code + Year
- **Examples**: ESH5, ESM5, ESU5, ESZ5, ESH6, ESM6, etc.
- **Tick Size**: $0.25
- **Asset Code**: ES
- **Key Instrument IDs**: 4916 (ESM5), 14160 (ESU5), 294973 (ESZ5)

#### Spread Contracts (247 contracts)
Calendar spreads between different ES contract months:
- **Pattern**: ES[Month][Year]-ES[Month][Year]
- **Examples**: ESZ5-ESM6, ESZ4-ESM5, ESH6-ESM6
- **Tick Size**: $0.05
- **Purpose**: Inter-contract spread trading

#### Micro Variants (132 contracts)
Alternative ES product variants with different specifications:
- **ESR**: 300 contracts (71.1%) - Micro E-mini futures
- **EST**: 21 contracts (5.0%) - E-mini S&P 500 Total Return
- **ESQ**: 21 contracts (5.0%) - Quarterly contracts
- **ESG**: 15 contracts (3.6%) - Green/ESG variant
- **ESX**: 2 contracts (0.5%) - Extended hours variant

#### Other Variants (22 contracts)
Complex products with special naming:
- **ES1/ES2**: Daily settlement contracts
- **Special Patterns**: :BF, :DF, :CF (butterfly, double fly, condor spreads)

### 📅 Expiration Patterns

#### Years Distribution
- **2025**: 205 contracts (48.6%) - Primary trading year
- **2026**: 82 contracts (19.4%)
- **2024**: 70 contracts (16.6%)
- **2027**: 39 contracts (9.2%)
- **2028**: 14 contracts (3.3%)
- **2029**: 12 contracts (2.8%)

#### Months Distribution
- **December**: 126 contracts (29.9%) - Z contracts
- **March**: 93 contracts (22.0%) - H contracts
- **June**: 72 contracts (17.1%) - M contracts
- **September**: 66 contracts (15.6%) - U contracts
- **Other months**: 65 contracts (15.4%)

### 🔤 Contract Ending Patterns

#### Most Common 2-Character Endings
1. **Z7**: 33 contracts (7.8%) - December 2027
2. **U7**: 32 contracts (7.6%) - September 2027
3. **Z6**: 32 contracts (7.6%) - December 2026
4. **U6**: 31 contracts (7.3%) - September 2026
5. **Z5**: 30 contracts (7.1%) - December 2025

#### Most Common 3-Character Endings
1. **RZ7**: 18 contracts (4.3%) - ESR December 2027
2. **RU7**: 17 contracts (4.0%) - ESR September 2027
3. **RM7**: 16 contracts (3.8%) - ESR June 2027
4. **RH7**: 15 contracts (3.6%) - ESR March 2027
5. **RZ6**: 14 contracts (3.3%) - ESR December 2026

### 💰 Tick Size Distribution
- **$0.0025**: 198 contracts (46.9%) - Micro products
- **$0.25**: 93 contracts (22.0%) - Standard ES futures
- **$0.05**: 86 contracts (20.4%) - Spread contracts
- **$0.00125**: 19 contracts (4.5%) - Ultra-micro products
- **Other sizes**: 26 contracts (6.2%)

## CME Month Code Conventions

| Month | Code | Season |
|-------|------|---------|
| March | H | Spring |
| June | M | Summer |
| September | U | Fall |
| December | Z | Winter |

## Critical Insights for Trading Systems

### ✅ Symbol Filtering Issues
- **Symbol filtering is BROKEN** for definition schema
- All tested symbol formats (ES.c.0, ESM5, ES, etc.) return "422 symbology_invalid_request"
- **Workaround**: Use manual filtering without symbols parameter

### ✅ Efficient Data Access Strategy
Instead of scanning 36.6M records:
1. **Cache Definition Data**: Build instrument_id → definition mapping
2. **Use Instrument IDs**: Filter other schemas by instrument_id (e.g., 4916 for ESM5)
3. **Target Date Ranges**: Query smaller date windows for definition updates
4. **Asset-Based Filtering**: Filter by asset='ES' after data retrieval

### ✅ Key Instrument IDs for ES
- **ESM5** (June 2025): 4916
- **ESU5** (September 2025): 14160
- **ESZ5** (December 2025): 294973
- **ESZ4** (December 2024): 183748

## Files Generated

1. **definition_samples.csv** - First 10 definition records
2. **es_futures_contracts.csv** - All 422 ES-related contracts
3. **futures_contracts_sample.csv** - Sample of all futures types
4. **contract_endings_analysis.csv** - Detailed pattern breakdown

## Recommendations

### For Production Systems
1. **Build Definition Cache**: Create a local mapping of instrument_id → contract details
2. **Use Instrument ID Filtering**: More reliable than symbol filtering
3. **Implement Fallback Logic**: Handle symbol resolution failures gracefully
4. **Monitor Contract Rollover**: Track expiration dates for active contracts

### For Data Analysis
1. **Focus on Standard ES**: Use asset='ES' for core E-mini S&P 500 analysis
2. **Understand Product Variants**: ESR, EST, ESQ have different characteristics
3. **Consider Spread Relationships**: Calendar spreads provide arbitrage insights
4. **Track Quarterly Cycles**: H, M, U, Z pattern for quarterly expirations

## Testing Scripts Available

- `test_definitions_analysis_csv.py` - Main analysis with CSV export
- `test_definitions_targeted_search.py` - Security type analysis
- `analyze_contract_endings.py` - Pattern analysis
- `test_definitions_symbol_formats.py` - Symbol filtering tests
- `test_definitions_symbology_mapping.py` - Symbology API tests

---

**Generated**: December 2024  
**Dataset**: GLBX.MDP3 Definition Schema  
**Date Range**: 2024-12-01 to 2025-01-31  
**Records Analyzed**: 500,000+ 