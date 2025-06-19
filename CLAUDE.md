# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Historical Data Ingestor is a production-ready Python system for ingesting, processing, and querying historical financial market data. It uses a modular monolith architecture with a plugin-based design for API providers (currently Databento).

## Common Development Commands

### Important Note on Date Ranges
When using the `ingest` command, the start date and end date **MUST** be different. The Databento API returns an error if start_date equals end_date. Always use at least a 1-day range (e.g., 2024-01-01 to 2024-01-02).

#### Recommended Date Range Guidelines
For reliable data retrieval and optimal performance:

**✅ Recommended Ranges:**
- **Definitions Schema**: 2-3 weeks for comprehensive instrument coverage
- **OHLCV Data**: 1 week to 1 month for analysis
- **Trades/TBBO**: 1-3 days maximum (high-volume data)
- **Statistics**: 1-2 weeks for pattern analysis

**⚠️ Performance Considerations:**
- Narrow ranges (1-2 days) may return sparse data for definitions
- Very wide ranges (>1 month) may cause timeouts for high-frequency data
- ALL_SYMBOLS queries require wider date ranges for meaningful results

**💡 Production Examples:**
```bash
# Optimal definitions ingestion (2-3 weeks)
python main.py ingest --api databento --dataset GLBX.MDP3 --schema definitions --symbols ES.FUT,CL.FUT --stype-in parent --start-date 2024-04-15 --end-date 2024-05-05

# OHLCV analysis (1 week)
python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d --symbols ES.c.0,CL.c.0 --start-date 2024-04-15 --end-date 2024-04-22

# High-frequency data (short range)
python main.py ingest --api databento --dataset GLBX.MDP3 --schema trades --symbols ES.c.0 --start-date 2024-04-15 --end-date 2024-04-16
```

### Running the Application

```bash
# Basic CLI usage
python main.py --help
python main.py status
python main.py version

# Data ingestion
python main.py ingest --api databento --job ohlcv_1d
python main.py ingest --api databento --dataset GLBX.MDP3 --schema ohlcv-1d --symbols CL.FUT,ES.FUT --start-date 2023-01-01 --end-date 2023-12-31

# Definition schema ingestion (production-ready as of 2025-06-19)
python main.py ingest --api databento --dataset GLBX.MDP3 --schema definitions --symbols ES.FUT,CL.FUT --stype-in parent --start-date 2024-04-15 --end-date 2024-05-05

# Data querying
python main.py query -s ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31
python main.py query --symbols ES.c.0,NQ.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --output-format csv

# Enhanced CLI commands (post-refactoring)
python main.py groups --list                    # List symbol groups
python main.py symbols --category Energy        # Browse symbols by category  
python main.py symbol-lookup ES.c.0 --fuzzy     # Advanced symbol lookup
python main.py exchange-mapping --list          # List exchange calendars
python main.py market-calendar 2024-01-01 2024-01-31 --exchange NYSE  # Market calendar analysis
python main.py validate ES.c.0 --type symbol    # Smart symbol validation
python main.py examples ingest                  # Show practical examples
python main.py troubleshoot ingestion           # Get troubleshooting help
python main.py status-dashboard                 # Live status monitoring
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_databento_adapter.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run E2E tests
source .env.test
python tests/integration/test_databento_e2e_pipeline.py

# MVP verification
python run_mvp_verification.py
```

### Linting and Type Checking

```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type check with MyPy
mypy src/
```

### Docker Operations

```bash
# Start services
docker-compose up --build -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Execute commands in container
docker-compose exec app python main.py status
```

## High-Level Architecture

The system follows a modular monolith pattern with these key components:

### Core Pipeline Flow
```
CLI → PipelineOrchestrator → APIAdapter → RuleEngine → Validator → StorageLoader → TimescaleDB
```

### Key Design Patterns

1. **Adapter Pattern**: Each API provider implements `BaseAdapter` for API-agnostic design
2. **Pipeline Pattern**: `PipelineOrchestrator` manages the ETL flow with centralized error handling
3. **Rule Engine Pattern**: YAML-based declarative transformations via `RuleEngine`
4. **Repository Pattern**: Storage abstraction through `TimescaleLoader` classes

### Component Responsibilities

- **src/cli/**: Modular CLI architecture with focused command modules
  - **commands/**: Individual command modules (system, help, ingestion, querying, workflow, validation, symbols)
  - **core/**: Shared CLI infrastructure and base classes
  - **common/**: Shared utilities, constants, and formatters
- **src/core/**: Framework components (config, pipeline orchestration)
- **src/ingestion/**: API adapters and data fetching
- **src/transformation/**: Data transformation rules and validation
- **src/storage/**: TimescaleDB interaction layer
- **src/querying/**: Query building with intelligent symbol resolution
- **src/utils/**: Logging and utilities

### Important Architectural Decisions

1. **TimescaleDB**: Optimized hypertables for time-series data with automatic partitioning
2. **Schema-Based Routing**: Different storage strategies for OHLCV vs Definitions data
3. **Intelligent Symbol Resolution**: Automatic mapping between symbols and instrument IDs
4. **Structured Logging**: JSON-formatted logs with contextual information using structlog
5. **Configuration Hierarchy**: YAML configs for system, API-specific, and transformation rules

### Error Handling Strategy

- Retry logic with exponential backoff for transient failures
- Dead Letter Queue (DLQ) for persistent failures at `dlq/`
- Transaction-based writes with rollback capability
- Graceful degradation with quarantine for problematic records

## Important Context

- The project has reached MVP status with 98.7% test coverage
- Currently focused on Databento API integration (databento_only branch)
- **Definitions schema is production-ready** (2025-06-19) with excellent performance
- Uses Pydantic for data validation throughout the pipeline
- Follows PEP 8 standards and uses Black/Ruff for code formatting
- Docker-ready with containerized deployment
- Environment variables manage sensitive configuration (API keys, passwords)
- BMad Method orchestrator configuration available for AI-assisted development

## Troubleshooting Guide

### Common Issues and Solutions

#### 🔧 Definitions Schema Issues

**Problem**: "Invalid symbols for stype_in='native': ALL_SYMBOLS"  
**Solution**: This has been fixed. ALL_SYMBOLS now works with any stype_in parameter.

**Problem**: Date range returns no data  
**Solution**: Use wider date ranges (2-3 weeks) for definitions. Narrow ranges often have sparse coverage.

**Problem**: Database constraint violations  
**Solution**: These have been resolved. The pipeline now handles all database constraints automatically.

#### 🔧 General Ingestion Issues

**Problem**: API timeout errors  
**Solution**: 
- Reduce date range size
- Use fewer symbols per request
- Check network connectivity

**Problem**: "Start date must be different from end date"  
**Solution**: Always use at least a 1-day range (e.g., 2024-01-01 to 2024-01-02)

**Problem**: Memory issues with large datasets  
**Solution**: 
- Use shorter date ranges
- Process symbols in smaller batches
- Monitor system resources

#### 🔧 Database Connection Issues

**Problem**: "Database connection error"  
**Solution**: 
1. Check TimescaleDB is running: `docker-compose ps`
2. Verify environment variables are set
3. Check database credentials in `.env`
4. Restart services: `docker-compose restart`

**Problem**: Schema/table not found  
**Solution**: 
- Run `python main.py status` to check database
- Create tables: `docker-compose up --build`

#### 🔧 Performance Optimization

**Best Practices**:
- Use appropriate date ranges for each schema type
- Monitor processing speed (aim for 1000+ records/second)
- Use batch processing for large symbol lists
- Enable database compression for historical data

**Monitoring Commands**:
```bash
# Check system status
python main.py status

# View recent ingestion jobs
python main.py query --symbols ES.c.0 --start-date 2024-01-01 --end-date 2024-01-31 --limit 10

# Monitor database size
docker-compose exec timescaledb psql -U postgres -d hist_data -c "SELECT pg_size_pretty(pg_database_size('hist_data'));"
```

## Recent Changes & Updates

### 🎉 Definitions Schema Production Success (2025-06-19)
**MAJOR BREAKTHROUGH**: Successfully transformed definitions schema from completely non-functional to production-ready.

**Achievement: Production-Ready Performance**
- **33,829 records processed in 9.16 seconds** (3,693 records/second)
- **Zero validation errors** across entire pipeline
- **All 73+ definition fields** properly mapped and validated
- **Complete end-to-end pipeline** working (API → Transform → Validate → Storage)

**Key Technical Implementations:**
- **Field Mapping Resolution**: Added comprehensive field name mapping in both `databento_adapter.py` and `pipeline_orchestrator.py` to handle API field names → Pydantic model field names
- **Schema Normalization**: "definitions" → "definition" alias working perfectly end-to-end
- **Pipeline Architecture**: Complete validation and repair logic working consistently
- **Performance Optimization**: Excellent processing speed with comprehensive error handling

**Production Status**: The definitions schema is now **production-ready** and can be used for live data ingestion with excellent performance.

**Remaining Polish Items**: 
- Advanced validation for complex symbol patterns (low priority)
- Additional monitoring and alerting integrations (enhancement)
- Extended historical data coverage (expansion)

### 🎉 CLI Architecture Refactoring Success (2025-06-19)
**MAJOR ACHIEVEMENT**: Complete CLI refactoring with 100% feature parity and enhanced capabilities.

**Architecture Transformation**:
- **Before**: Monolithic 3,055-line `cli_commands.py` file
- **After**: Modular architecture with 7 focused command modules
- **Implementation**: Complete modular redesign with enhanced features

**Final Results**:
- ✅ **26 Commands Migrated**: 100% feature parity achieved
- ✅ **7 Command Modules**: System, Help, Ingestion, Query, Workflow, Validation, Symbol commands
- ✅ **Enhanced Capabilities**: Market calendar integration, rich formatting, improved validation
- ✅ **100% Test Coverage**: 160+ comprehensive tests with 100% success rate
- ✅ **Production Ready**: Immediate deployment capability

**New CLI Architecture**:
```
src/cli/
├── main.py                    # Main CLI entry point
├── commands/                  # Modular command architecture
│   ├── system.py             # status, version, config, monitor, list-jobs, status-dashboard
│   ├── help.py               # examples, troubleshoot, tips, schemas, quickstart, help-menu, cheatsheet
│   ├── ingestion.py          # ingest, backfill
│   ├── querying.py           # query with multi-format output
│   ├── workflow.py           # workflows, workflow management
│   ├── validation.py         # validate, market-calendar (with pandas integration)
│   └── symbols.py            # groups, symbols, symbol-lookup, exchange-mapping
├── core/                     # Shared CLI infrastructure
├── common/                   # Shared utilities and constants
└── [utility modules]         # Enhanced help, validation, progress tracking
```

**Key Improvements**:
- **📅 Market Calendar Integration**: Real pandas_market_calendars with 160+ exchanges
- **🎨 Rich Terminal Formatting**: Beautiful tables, progress bars, colored output  
- **🔍 Smart Symbol Validation**: Advanced validation with fuzzy matching
- **📊 Multi-Format Output**: Table, CSV, JSON with file export
- **🛡️ Enhanced Error Handling**: Graceful degradation and meaningful messages

**Performance Metrics**:
- ✅ CLI startup time: < 500ms (target met)
- ✅ All commands functional with enhanced capabilities
- ✅ Test execution: 100% success rate across all modules
- ✅ Memory efficient with optimized imports

**Documentation**: See `docs/prd/complete/CLI_REFACTORING_PRD.md` for complete implementation details and test results.

### CLI Job Naming (2025-06-17)
When using custom ingestion commands (without predefined job names), the system now automatically generates job names based on schema and symbols:
- Pattern: `cli_{schema}_{symbols}`
- Example: `cli_ohlcv-1d_ES.c.0_CL.c.0`
- This prevents "missing name field" validation errors

### Statistics Data Ingestion Fix (2025-06-17)
Fixed critical issue where statistics records were failing with "Unknown record type, cannot store":
- Enhanced databento_adapter.py to properly map API `price` field to model `stat_value` field
- Fixed statistics loader ON CONFLICT constraint to match table schema
- Added comprehensive field mapping for TBBO records (bid_px_00 → bid_px, etc.)
- Enhanced TradeRecord model with missing fields and automatic quantity mapping
- Statistics ingestion now works correctly end-to-end

### Table Creation Handling (2025-06-17)
The TimescaleOHLCVLoader now gracefully handles existing tables:
- Uses `CREATE TABLE IF NOT EXISTS` for all table creation
- Logs informational messages instead of errors when tables already exist
- Continues execution without interruption

### Symbol Field Mapping Fix (2025-06-17)
Implemented robust symbol field validation and repair system to eliminate Pydantic validation failures:

**Problem Resolved:**
- Fixed critical issue where trade records were failing with "Field required [type=missing]" errors for symbol field
- Eliminated 315,493 validation errors, achieving 100% successful trade record ingestion (3,459/3,459 records stored)

**Technical Implementation:**
- Added `_ensure_symbol_field` method in `databento_adapter.py` for proactive symbol field mapping and validation
- Added `_validate_and_repair_record_dict` method in `pipeline_orchestrator.py` for dict-to-model conversion validation and repair
- Enhanced error handling with meaningful repair statistics logging
- Applied validation logic to both trades and TBBO schemas

**Key Features:**
- Automatic symbol field mapping from Databento API response fields
- Fallback logic using instrument_id and raw_symbol when symbol field is missing
- Comprehensive logging of validation failures and successful repairs
- Zero performance impact (processing remains at 2-3 seconds for thousands of records)

**Success Metrics:**
- ✅ 0 "Field required [type=missing]" errors for symbol field (down from 315,493)
- ✅ 100% trade record ingestion success rate
- ✅ All ingested records have valid symbol field values
- ✅ Fast processing with comprehensive monitoring

### Field Standardization (2024-06-16)

### Critical: Field Naming Convention
The codebase underwent comprehensive field standardization to resolve validation issues:

**OHLCV Fields:**
- `open` → `open_price`
- `high` → `high_price`
- `low` → `low_price`
- `close` → `close_price`
- `count` → `trade_count`

**TBBO Fields:**
- `bid_px_00` → `bid_px`
- `ask_px_00` → `ask_px`
- `bid_sz_00` → `bid_sz`
- `ask_sz_00` → `ask_sz`

### Validation Schema Updates
- All Pandera schemas now use `strict = False` to allow extra fields
- Statistics schema accepts both `stat_value` and `price` fields for compatibility
- Type coercion enabled (`coerce = True`) for flexible type handling

### Affected Components
When working with these fields, be aware of updates in:
- `src/storage/models.py` - Pydantic models
- `src/ingestion/api_adapters/databento_adapter.py` - Field mapping logic
- `src/transformation/validators/databento_validators.py` - Validation schemas
- All test fixtures and test files

### Documentation
For detailed information about this migration:
- See `docs/FIELD_STANDARDIZATION_MIGRATION.md` for migration details
- See `docs/DEBUGGING_LESSONS_LEARNED.md` for debugging strategies

### Testing Status
As of 2024-06-16:
- All 152 unit tests passing
- All transformation tests passing
- Field validation working correctly across all schemas

### Pandera DataFrame Dtype Coercion Fix (2025-06-18)
Fixed critical Pandera validation error that was blocking OHLCV data ingestion:

**Problem Resolved:**
- Fixed `coerce_dtype('int64')` failures for `trade_count` column in OHLCV data
- Error occurred when pandas inferred `float64` dtype for mixed integer/None values, then Pandera failed to coerce to `pd.Int64Dtype`

**Root Cause:**
When `pd.DataFrame(transformed_batch)` creates DataFrames with mixed integer and `None` values for `trade_count`, pandas automatically infers `float64` dtype (converting `None` to `NaN`). Later, when Pandera tries to validate and coerce this to `pd.Int64Dtype`, it fails because pandas cannot directly coerce `float64` with `NaN` to regular `int64`.

**Technical Solution:**
Enhanced `src/transformation/rule_engine/engine.py` to explicitly convert nullable integer columns to proper pandas extension dtypes before Pandera validation:

```python
# Fix nullable integer columns that pandas infers as float64
# This prevents Pandera coercion errors when validating nullable int columns
if 'trade_count' in df.columns:
    df['trade_count'] = df['trade_count'].astype('Int64')
```

**Impact:**
- ✅ OHLCV ingestion now processes without validation errors
- ✅ All 506 records processed successfully in test runs
- ✅ Maintains existing functionality while fixing the validation pipeline

### Schema Validation Consistency Enhancement (2025-06-18)
Standardized validation and repair logic across all data schemas:

**Problem Identified:**
- OHLCV and Statistics schemas lacked the validation/repair system that Trades and TBBO schemas already had
- Inconsistent error handling and missing symbol field repair for OHLCV data

**Solution Implemented:**
Updated `src/core/pipeline_orchestrator.py` to apply consistent validation and repair logic across all schemas:

```python
# Pre-validate and repair if needed
validated_dict = self._validate_and_repair_record_dict(record_dict, schema, job_config)

if validated_dict is None:
    repair_stats['failed_repair'] += 1
    self.stats.errors_encountered += 1
    continue

if validated_dict != record_dict:
    repair_stats['repaired'] += 1
```

**Schemas Enhanced:**
- ✅ OHLCV schema now includes validation and repair logic
- ✅ Statistics schema updated with consistent error handling
- ✅ All schemas now log repair statistics for monitoring
- ✅ Symbol field repair works consistently across all data types

**Testing Validation:**
- ✅ All 30 transformation tests passing
- ✅ All 51 core functionality tests passing
- ✅ Updated trade schema test to reflect negative price support for spread instruments
- ✅ Updated job config test to expect automatic name generation

**Files Modified:**
- `src/transformation/rule_engine/engine.py` - DataFrame dtype conversion fix
- `src/core/pipeline_orchestrator.py` - Consistent validation/repair logic
- `tests/unit/transformation/test_databento_validators.py` - Updated negative price test
- `tests/unit/core/test_pipeline_orchestrator.py` - Updated job config test

## Documentation Maintenance Patterns

### 🎯 Live Documentation and Testing Results Initiative

During the CLI refactoring project (2025-06-19), we established comprehensive documentation maintenance patterns for keeping documentation current with real test execution results and project evidence. **These patterns should be followed for all major development work.**

### Key Documentation Patterns

#### 1. **Live PRD Updates with Real Test Results**
**Pattern**: Update PRDs immediately with actual test execution results, not just planned tests.

**Implementation**:
```markdown
**Test Execution Results**:
```
✅ All 32 tests passed in 0.96 seconds
✅ 100% success rate across all validation functions
✅ pandas_market_calendars integration working correctly
✅ Market calendar analysis: < 1 second for typical ranges
```

**Benefits**:
- Provides evidence-based progress tracking
- Enables team transparency and confidence
- Creates historical record of actual performance
- Facilitates project reviews and decision-making

#### 2. **Documentation with Execution Evidence**
**Pattern**: Include actual command outputs, test results, and performance metrics in documentation.

**Example Structure**:
```markdown
### Feature Implementation Results
**Command**: `python main.py market-calendar 2024-01-01 2024-01-05 --exchange NYSE`
**Output**: 
```
✅ NYSE analysis: 4/5 trading days (80% coverage)
✅ 1 holiday detected (New Year's Day)
✅ Analysis completed in 0.34 seconds
```

**Performance Metrics**:
- Execution time: < 1 second
- Memory usage: < 50MB
- Success rate: 100%
```

#### 3. **Team Review Documentation Standards**
**Required Elements for Major Features**:
- ✅ **Real Test Results**: Actual pytest output with pass/fail counts
- ✅ **Performance Evidence**: Timing and resource usage data
- ✅ **Feature Demonstrations**: Working command examples with outputs
- ✅ **Progress Tracking**: Percentage completion with specific metrics
- ✅ **Quality Assurance**: Test coverage and validation results

#### 4. **PRD Maintenance Workflow**
**Process for Major Development Work**:

1. **Initial Planning**: Create PRD with estimated scope and success criteria
2. **Development Phase**: Update PRD with real progress and test results
3. **Testing Phase**: Document actual test execution with full output
4. **Completion Phase**: Update PRD with final results and evidence
5. **Team Review**: Ensure PRD contains all evidence for project assessment

**PRD Update Frequency**: After each major milestone or daily for complex projects

#### 5. **Documentation File Organization**
**Structure for Project Documentation**:
```
docs/
├── prd/
│   ├── active/           # Current project PRDs with live updates
│   ├── completed/        # Completed PRDs with final results
│   └── templates/        # PRD templates with required sections
├── results/
│   ├── test_results/     # Saved test execution outputs
│   ├── performance/      # Performance benchmarking data
│   └── evidence/         # Screenshots, logs, and proof materials
└── maintenance/
    ├── patterns/         # Documentation patterns and templates
    └── guidelines/       # Team documentation guidelines
```

### 🎯 Success Story: CLI Refactoring Documentation

**Achievement**: The CLI refactoring project demonstrated excellence in documentation maintenance:

- **Live PRD Updates**: 6 major sections updated with real test results
- **1,400+ Lines of Evidence**: Comprehensive documentation with actual execution results
- **100% Test Result Documentation**: Every test run documented with full output
- **Performance Metrics**: All timing and resource usage documented
- **Team Transparency**: Complete project visibility through evidence-based documentation

**Key Metrics**:
- 79% completion documented with real evidence (19/24 commands migrated)
- 157 test methods documented with actual execution results
- 3,011 lines of test code with comprehensive coverage documentation
- < 1 second execution time for all validation commands (documented)

### 🔧 Implementation Guidelines

#### For Claude Code Users:
1. **Always Update Documentation**: When completing tasks, update relevant documentation with real results
2. **Include Evidence**: Add actual command outputs, test results, and performance data
3. **Maintain PRDs**: Keep PRDs current with live updates during development
4. **Document Patterns**: Record successful approaches for future reference

#### For Development Teams:
1. **Evidence-Based Reviews**: Require actual test results and performance data in all reviews
2. **Documentation Standards**: Enforce documentation patterns for consistency
3. **Live Updates**: Update documentation throughout development, not just at completion
4. **Quality Assurance**: Verify documentation accuracy with real execution results

**This pattern ensures documentation remains current, accurate, and valuable for team decision-making and project assessment.**