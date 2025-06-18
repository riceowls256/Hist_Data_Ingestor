# Databento Historical API Testing Suite

## 📁 Organized Test Structure

This directory contains a comprehensive suite of tests and tools for validating Databento Historical API integration. All files have been organized into logical categories for easier navigation and maintenance.

## 🗂️ Folder Structure

### 📡 `basic_connectivity/`
**Core connection and authentication tests**
- `test_api_connection.py` - Basic connectivity validation
- `debug_databento_record.py` - Record structure debugging

### 🔍 `schema_testing/`
**Schema-specific validation tests**
- `test_statistics_schema.py` - Statistics schema testing
- `test_definitions_schema.py` - Definitions schema comprehensive testing
- `test_status_schema.py` - Status schema validation
- `test_cme_statistics.py` - CME Globex statistics verification
- `analyze_stats_fields.py` - Statistics fields analysis

### 🎯 `symbology/`
**Advanced symbology implementation and testing**
- `debug_definition_schema.py` - **Parent symbology** demonstration (ES.FUT)
- `test_continuous_contracts.py` - **Continuous contracts** testing (ES.v.0)
- `test_futures_api.py` - Futures contract testing across multiple products

### 🔬 `analysis_tools/`
**Research and analysis utilities**
- `complete_workflow_demo.py` - End-to-end workflow demonstration
- `simple_symbol_discovery.py` - Basic symbol discovery tools
- `dataset_symbol_discovery.py` - Advanced dataset exploration
- `es_liquidity_analysis.py` - E-mini S&P 500 liquidity analysis
- `es_liquidity_focused.py` - Focused liquidity research
- `tick_size_demo.py` - Tick size and price increment analysis
- `analyze_contract_endings.py` - Contract naming pattern analysis

### 🧪 `definition_research/`
**Definition schema research and utilities**
- `test_definitions_*` (multiple files) - Various definition schema approaches
- `definition_schema_utility.py` - Definition schema helper functions
- `contract_mapping_utils.py` - Contract mapping utilities

### 📊 `csv_data/`
**Generated data files and analysis results**
- `es_symbols_discovered.csv` - ES symbol discovery results
- `all_symbols_glbx_mdp3.csv` - Complete GLBX symbol list
- `contract_endings_analysis.csv` - Contract naming analysis
- `es_futures_contracts.csv` - ES futures contract details
- `futures_contracts_sample.csv` - Sample contract data
- `definition_samples.csv` - Definition schema samples

### 📚 `documentation/`
**Analysis summaries and guides**
- `sample_data_structure.md` - Data structure documentation
- `COMPREHENSIVE_ANALYSIS_SUMMARY.md` - Complete analysis overview
- `SYMBOL_DISCOVERY_ANALYSIS.md` - Symbol discovery findings
- `COMPLETE_ANALYSIS_SUMMARY.md` - Analysis summary
- `DEFINITION_SCHEMA_ANALYSIS_SUMMARY.md` - Definition schema insights

## 🚀 Quick Start

### Essential Tests (Start Here)
```bash
# 1. Basic connectivity
python basic_connectivity/test_api_connection.py

# 2. Parent symbology (RECOMMENDED)
python symbology/debug_definition_schema.py

# 3. Continuous contracts (RECOMMENDED) 
python symbology/test_continuous_contracts.py

# 4. Schema validation
python schema_testing/test_statistics_schema.py
```

### Advanced Analysis
```bash
# Comprehensive workflow
python analysis_tools/complete_workflow_demo.py

# Liquidity analysis
python analysis_tools/es_liquidity_analysis.py

# Contract research
python analysis_tools/analyze_contract_endings.py
```

## 🎯 Key Capabilities Validated

### ✅ **Parent Symbology** (Recommended)
- **Efficiency:** 14,743x data reduction vs ALL_SYMBOLS
- **Coverage:** Complete product families (futures + spreads)
- **Usage:** `ES.FUT` + `stype_in="parent"`

### ✅ **Continuous Contracts** (Recommended)
- **Purpose:** Automatic rollover tracking for time-series
- **Validation:** Real rollover behavior during expiry weeks
- **Usage:** `ES.v.0` + `stype_in="continuous"`

### ✅ **Multi-Product Support**
- E-mini S&P 500 (ES), Crude Oil (CL), Natural Gas (NG), Gold (GC)
- All schemas: OHLCV, Trades, TBBO, Statistics, Definitions, Status
- Production-tested with real market data

## 🏗️ Project Integration

These tests support the main project's ingestion pipeline:
- **Source:** `src/ingestion/api_adapters/databento_adapter.py`
- **Config:** `configs/api_specific/databento_config.yaml`
- **Mappings:** `src/transformation/mapping_configs/databento_mappings.yaml`

## 📈 Performance Benchmarks

| Approach | Records | Time | Use Case |
|----------|---------|------|----------|
| Parent symbology | 41 (ES.FUT) | ~2.2s | Product family analysis |
| Continuous contracts | 12 (ES.v.0) | <1s | Time-series tracking |
| Schema testing | Various | <10s | Validation |

## 🛠️ Maintenance

- **Core files:** Keep `symbology/` tests updated with new products
- **Documentation:** Update `docs/api/databento_testing_guide.md` with findings
- **Data files:** Archive old CSV files periodically
- **Research:** Move experimental files to `analysis_tools/` or `definition_research/`

## 💡 Best Practices

1. **Start with symbology tests** for new products
2. **Use parent symbology** for comprehensive analysis
3. **Use continuous contracts** for time-series applications
4. **Validate schema changes** with schema_testing suite
5. **Document findings** in the main testing guide 