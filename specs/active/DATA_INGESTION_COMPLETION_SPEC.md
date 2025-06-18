# Data Ingestion System Completion Specification

**Document Version:** 1.0  
**Date:** 2025-06-17  
**Status:** Draft  
**Priority:** High

## Executive Summary

This specification outlines the remaining work to complete the Historical Data Ingestor system after the successful implementation of the symbol field mapping fix. The work is organized into four phases: TBBO Critical Fixes, CLI Progress Bar Enhancement, Testing & Quality Assurance, and Integration & Verification.

## Background

### Current State
- ✅ **Symbol Field Mapping Fix**: Successfully implemented robust symbol field validation and repair system
- ✅ **Trade Records**: 100% ingestion success rate (3,459/3,459 records)
- ✅ **Statistics Data**: Fixed field mapping and SQL constraints
- ❌ **TBBO Data**: Field mapping and SQL constraint issues identified
- ❌ **CLI Experience**: Verbose logging causes terminal spam during ingestion
- ❌ **Test Coverage**: Missing tests for new symbol validation logic

### Success Metrics from Symbol Field Fix
- Eliminated 315,493 validation errors
- 0 "Field required [type=missing]" errors for symbol field
- Zero performance impact (2-3 seconds for thousands of records)
- Comprehensive logging and monitoring

## Phase 1: TBBO Critical Fixes

### P1.1: TBBO Field Mapping Issues

#### Problem Statement
TBBO records are failing Pandera validation because the Databento API returns fields with `_00` suffixes that don't match the expected model fields:

**API Response Fields → Model Fields:**
- `bid_px_00` → `bid_px`
- `ask_px_00` → `ask_px` 
- `bid_sz_00` → `bid_sz`
- `ask_sz_00` → `ask_sz`

#### 🎯 **ROOT CAUSE IDENTIFIED**: Wrong Record Type Expected
**Investigation Results** (2025-06-17):
- Field mapping code found in `databento_adapter.py` lines 350-385 ✅
- TBBO test with ZR.c.0 shows validation still failing ❌
- **DEBUG BREAKTHROUGH**: TBBO records are `MBP1Msg` with `rtype=1` ⚠️
- **ACTUAL FIELDS**: `['price', 'side', 'size', 'action', 'levels', ...]` ❌
- **EXPECTED FIELDS**: `['bid_px_00', 'ask_px_00', 'bid_sz_00', 'ask_sz_00']` ❌
- **Root Cause**: TBBO schema returns Market-By-Price format, not simple TBBO format!

#### Acceptance Criteria
- [ ] TBBO records ingest successfully without field validation errors
- [ ] All TBBO records have properly mapped bid/ask price and size fields
- [ ] Field mapping follows the same pattern as the successful symbol field fix
- [ ] Zero Pandera validation failures for TBBO field names

#### ✅ VALIDATION TESTING RESULTS
- **Test Command**: `python main.py ingest --api databento --dataset GLBX.MDP3 --schema tbbo --symbols ZR.c.0 --start-date 2024-01-10 --end-date 2024-01-11 --stype-in continuous --force`
- **Records Fetched**: 20 ✅
- **Validation Errors**: 5 Pandera failures ❌
- **Storage Success**: 0/20 records stored ❌

#### Technical Implementation

**File:** `src/ingestion/api_adapters/databento_adapter.py`

**Method Enhancement:** `_record_to_dict()`

```python
# Add TBBO-specific field mapping after existing logic
if hasattr(record, 'bid_px_00'):
    record_dict['bid_px'] = getattr(record, 'bid_px_00')
if hasattr(record, 'ask_px_00'):
    record_dict['ask_px'] = getattr(record, 'ask_px_00')
if hasattr(record, 'bid_sz_00'):
    record_dict['bid_sz'] = getattr(record, 'bid_sz_00')
if hasattr(record, 'ask_sz_00'):
    record_dict['ask_sz'] = getattr(record, 'ask_sz_00')
```

**Validation Enhancement:** Extend `_validate_required_fields()` for TBBO
```python
'tbbo': ['ts_event', 'instrument_id', 'symbol']  # bid/ask fields optional
```

#### Testing Strategy
1. Create test case with mock TBBO record containing `_00` suffix fields
2. Verify `_record_to_dict()` correctly maps all fields
3. Confirm TBBO model validation passes with mapped fields
4. End-to-end test with real TBBO API data

### P1.2: TBBO SQL Constraint Issues

#### Problem Statement
TBBO insertions fail with SQL error: "there is no unique or exclusion constraint matching the ON CONFLICT specification"

**Current ON CONFLICT clause:**
```sql
ON CONFLICT (ts_event, instrument_id, sequence, data_source) DO UPDATE SET...
```

**Issue:** The `tbbo_data` table schema doesn't define a unique constraint matching these exact fields.

#### Analysis of Table Schema
From `src/storage/schema_definitions/tbbo_data_table.sql`:
- No explicit UNIQUE constraint defined
- Primary key not specified
- TimescaleDB hypertable partitioned by `ts_event`

#### Acceptance Criteria
- [ ] TBBO records insert successfully without SQL constraint errors
- [ ] ON CONFLICT behavior works correctly for duplicate handling
- [ ] Database schema supports the intended conflict resolution strategy
- [ ] No data loss or corruption during insertion

#### Technical Implementation Options

**Option A: Remove ON CONFLICT (Simplest)**
```sql
INSERT INTO tbbo_data (...) VALUES (...) 
-- Remove ON CONFLICT clause entirely
```

**Option B: Add Unique Constraint to Table Schema**
```sql
-- Add to tbbo_data_table.sql
ALTER TABLE tbbo_data ADD CONSTRAINT tbbo_unique_key 
UNIQUE (ts_event, instrument_id, sequence, data_source);
```

**Option C: Use Different Conflict Resolution Fields**
```sql
ON CONFLICT (ts_event, instrument_id) DO UPDATE SET...
```

#### ✅ **IMPLEMENTED SOLUTION: Option A**
**Resolution** (2025-06-17):
- Removed `ON CONFLICT` clause entirely from `timescale_tbbo_loader.py` ✅
- Aligns with successful trades loader implementation ✅
- Simplest and most reliable approach ✅
- SQL constraint error resolved ✅

#### Testing Strategy
1. Test insertion with duplicate records (same ts_event, instrument_id)
2. Verify no SQL errors during batch insertion ✅
3. Confirm all valid records are stored correctly
4. Performance test with large TBBO datasets

## Phase 2: CLI Progress Bar Enhancement

### P2.1: Progress Bar Implementation

#### Problem Statement
The current CLI streams detailed logs for every record processed, causing terminal spam and poor user experience:

```
[INFO] Processing record 1/3459: {'ts_event': '2024-01-01 09:30:00', ...}
[INFO] Processing record 2/3459: {'ts_event': '2024-01-01 09:30:01', ...}
[INFO] Processing record 3/3459: {'ts_event': '2024-01-01 09:30:02', ...}
...
```

#### Acceptance Criteria
- [ ] Clean, professional progress bar display during ingestion
- [ ] Meaningful progress information (chunk progress, record counts, ETA)
- [ ] Configurable verbosity levels (--verbose flag for detailed logs)
- [ ] No performance degradation from progress tracking
- [ ] Professional CLI experience matching production tools

#### Technical Implementation

**Enhanced CLI with Rich Progress Bars:**

**File:** `src/main.py`

```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

@app.command()
def ingest(
    # ... existing parameters ...
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable detailed logging")
):
    """Enhanced ingest command with progress bars."""
    
    # Configure logging level based on verbose flag
    if not verbose:
        # Suppress detailed record-level logging
        logging.getLogger('databento_adapter').setLevel(logging.WARNING)
        logging.getLogger('pipeline_orchestrator').setLevel(logging.INFO)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("[blue]ETA: {task.fields[eta]}"),
        console=console
    ) as progress:
        
        # Track overall ingestion progress
        main_task = progress.add_task(
            f"[green]Ingesting {schema} data...", 
            total=None  # Will be updated when total chunks known
        )
        
        # Pass progress callback to orchestrator
        orchestrator = PipelineOrchestrator(config, progress_callback=progress)
        # ... rest of ingestion logic
```

**File:** `src/core/pipeline_orchestrator.py`

```python
class PipelineOrchestrator:
    def __init__(self, config: Dict[str, Any], progress_callback=None):
        # ... existing initialization ...
        self.progress = progress_callback
        self.current_task_id = None
    
    def run_pipeline(self, job_config: Dict[str, Any]) -> PipelineStats:
        """Enhanced pipeline with progress tracking."""
        
        if self.progress:
            self.current_task_id = self.progress.add_task(
                f"[cyan]Processing {job_config.get('schema', 'unknown')} data",
                total=100  # Will update with actual progress
            )
        
        # ... existing pipeline logic with progress updates ...
        
        if self.progress:
            self.progress.update(
                self.current_task_id, 
                advance=10, 
                description=f"[cyan]Fetching data from {api_name}"
            )
```

#### Progress Information Display
```
📊 Historical Data Ingestor - Ingestion Progress

🔄 Fetching TBBO data from Databento API...                     ████████░░ 80% ETA: 0:02:15
📝 Processing chunk 8/10                                        ████████████ 100%  
💾 Storing 1,247 records in TimescaleDB...                     ████████░░ 85%   

Summary:
  Records Fetched: 8,439 / 10,000 (estimated)
  Records Stored:  7,192 
  Errors:         3
  Processing Speed: 2,847 records/second
  Time Elapsed: 0:02:45
```

#### CLI Verbosity Levels

**Default Mode (--verbose=False):**
- Clean progress bars
- Summary statistics only
- Errors and warnings displayed
- Final completion summary

**Verbose Mode (--verbose=True):**
- Progress bars + detailed logs
- Record-level processing information
- Debug information available
- Full error stack traces

### P2.2: Enhanced User Experience Features

#### Real-time Statistics Display
```python
# Add to progress display
stats_text = f"Speed: {records_per_second:.0f} rec/sec | Errors: {error_count} | Memory: {memory_usage}MB"
```

#### Completion Summary
```python
def display_completion_summary(stats: PipelineStats):
    """Display comprehensive completion summary."""
    
    console.print("\n🎉 [bold green]Ingestion Complete![/bold green]")
    
    table = Table(title="Ingestion Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Records Processed", f"{stats.records_processed:,}")
    table.add_row("Successfully Stored", f"{stats.records_stored:,}")
    table.add_row("Errors Encountered", f"{stats.errors_encountered:,}")
    table.add_row("Processing Time", f"{stats.total_time:.2f} seconds")
    table.add_row("Average Speed", f"{stats.records_per_second:.0f} records/second")
    
    console.print(table)
```

## Phase 3: Testing & Quality Assurance

### P3.1: Symbol Field Validation Tests

#### Test Coverage Requirements
- [ ] Unit tests for `_ensure_symbol_field()` method
- [ ] Unit tests for `_validate_and_repair_record_dict()` method  
- [ ] Integration tests for symbol field repair statistics
- [ ] Edge case testing (missing symbols, invalid data, etc.)

#### Test Implementation

**File:** `tests/unit/ingestion/test_databento_adapter_symbol_validation.py`

```python
import pytest
from unittest.mock import Mock, patch
from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter

class TestSymbolFieldValidation:
    """Test suite for symbol field validation and repair logic."""
    
    def test_ensure_symbol_field_single_symbol(self):
        """Test symbol field mapping with single symbol."""
        adapter = DatabentoAdapter({})
        record_dict = {'instrument_id': 12345}
        symbols = ['ES.c.0']
        
        result = adapter._ensure_symbol_field(record_dict, symbols)
        
        assert result['symbol'] == 'ES.c.0'
    
    def test_ensure_symbol_field_multi_symbol_fallback(self):
        """Test symbol field mapping with multiple symbols falls back to instrument_id."""
        adapter = DatabentoAdapter({})
        record_dict = {'instrument_id': 12345}
        symbols = ['ES.c.0', 'NQ.c.0']
        
        result = adapter._ensure_symbol_field(record_dict, symbols)
        
        assert result['symbol'] == 'ES.c.0'  # First symbol fallback
    
    def test_ensure_symbol_field_raw_symbol_extraction(self):
        """Test symbol extraction from record raw_symbol attribute."""
        adapter = DatabentoAdapter({})
        record_dict = {'instrument_id': 12345}
        
        mock_record = Mock()
        mock_record.raw_symbol = 'CL.FUT'
        
        result = adapter._ensure_symbol_field(record_dict, None, mock_record)
        
        assert result['symbol'] == 'CL.FUT'
    
    def test_ensure_symbol_field_instrument_id_fallback(self):
        """Test fallback to instrument_id based naming."""
        adapter = DatabentoAdapter({})
        record_dict = {'instrument_id': 12345}
        
        result = adapter._ensure_symbol_field(record_dict, None, None)
        
        assert result['symbol'] == 'INSTRUMENT_12345'
    
    def test_ensure_symbol_field_unknown_fallback(self):
        """Test final fallback to UNKNOWN_SYMBOL."""
        adapter = DatabentoAdapter({})
        record_dict = {}
        
        result = adapter._ensure_symbol_field(record_dict, None, None)
        
        assert result['symbol'] == 'UNKNOWN_SYMBOL'
```

**File:** `tests/unit/core/test_pipeline_orchestrator_validation.py`

```python
import pytest
from unittest.mock import Mock, patch
from src.core.pipeline_orchestrator import PipelineOrchestrator

class TestPipelineOrchestratorValidation:
    """Test suite for pipeline orchestrator validation and repair logic."""
    
    def test_validate_and_repair_record_dict_success(self):
        """Test successful validation and repair of record dictionary."""
        config = {}
        orchestrator = PipelineOrchestrator(config)
        
        record_dict = {'ts_event': '2024-01-01T09:30:00Z', 'instrument_id': 12345}
        job_config = {'symbols': ['ES.c.0'], 'schema': 'trades'}
        
        result = orchestrator._validate_and_repair_record_dict(record_dict, 'trades', job_config)
        
        assert result is not None
        assert result['symbol'] == 'ES.c.0'
    
    def test_validate_and_repair_record_dict_missing_required_field(self):
        """Test handling of missing required fields."""
        config = {}
        orchestrator = PipelineOrchestrator(config)
        
        record_dict = {'symbol': 'ES.c.0'}  # Missing ts_event, instrument_id
        job_config = {'symbols': ['ES.c.0'], 'schema': 'trades'}
        
        result = orchestrator._validate_and_repair_record_dict(record_dict, 'trades', job_config)
        
        assert result is None  # Should fail validation
    
    def test_get_required_fields_for_schema(self):
        """Test required fields mapping for different schemas."""
        config = {}
        orchestrator = PipelineOrchestrator(config)
        
        trades_fields = orchestrator._get_required_fields_for_schema('trades')
        tbbo_fields = orchestrator._get_required_fields_for_schema('tbbo')
        
        assert 'ts_event' in trades_fields
        assert 'instrument_id' in trades_fields
        assert 'price' in trades_fields
        assert 'size' in trades_fields
        assert 'symbol' in trades_fields
        
        assert 'ts_event' in tbbo_fields
        assert 'instrument_id' in tbbo_fields
        assert 'symbol' in tbbo_fields
```

### P3.2: Schema Testing for MBO & Definition

#### Test Strategy
1. **Identify Available Schemas**: Determine which schemas are actually supported
2. **Create Mock Data**: Generate representative test data for each schema
3. **Field Mapping Tests**: Verify field mapping works correctly
4. **Symbol Validation Tests**: Ensure symbol field validation applies to all schemas

#### Test Implementation

**File:** `tests/unit/ingestion/test_schema_compatibility.py`

```python
import pytest
from src.ingestion.api_adapters.databento_adapter import DatabentoAdapter
from src.storage.models import DATABENTO_SCHEMA_MODEL_MAPPING

class TestSchemaCompatibility:
    """Test field mapping and validation across all supported schemas."""
    
    @pytest.mark.parametrize("schema", DATABENTO_SCHEMA_MODEL_MAPPING.keys())
    def test_schema_field_mapping(self, schema):
        """Test field mapping works for all supported schemas."""
        adapter = DatabentoAdapter({})
        
        # Create mock record for each schema type
        mock_record = self._create_mock_record_for_schema(schema)
        
        result = adapter._record_to_dict(mock_record, symbols=['TEST.SYMBOL'])
        
        # All schemas should have symbol field after mapping
        assert 'symbol' in result
        assert result['symbol'] == 'TEST.SYMBOL'
    
    def _create_mock_record_for_schema(self, schema):
        """Create appropriate mock record for each schema type."""
        base_attrs = {
            'ts_event': 1640995200000000000,  # 2022-01-01 in nanoseconds
            'instrument_id': 12345,
            'raw_symbol': 'TEST.RAW'
        }
        
        schema_specific_attrs = {
            'ohlcv-1d': {
                'open': 4500.0, 'high': 4510.0, 'low': 4490.0, 'close': 4505.0,
                'volume': 1000000
            },
            'trades': {
                'price': 4500.0, 'size': 100, 'side': 'A'
            },
            'tbbo': {
                'bid_px_00': 4499.5, 'ask_px_00': 4500.5,
                'bid_sz_00': 50, 'ask_sz_00': 75
            },
            'statistics': {
                'price': 4500.0, 'stat_type': 'last_price'
            }
        }
        
        attrs = {**base_attrs, **schema_specific_attrs.get(schema, {})}
        
        mock_record = Mock()
        for attr, value in attrs.items():
            setattr(mock_record, attr, value)
        
        return mock_record
```

## Phase 4: Integration & Verification

### P4.1: End-to-End Testing

#### Comprehensive System Verification
- [ ] Full ingestion pipeline test with all schemas
- [ ] Performance regression testing
- [ ] CLI progress bar functionality testing
- [ ] Error handling and recovery testing

#### Test Scenarios

**Scenario 1: Multi-Schema Ingestion**
```bash
# Test all schemas work with new fixes
python main.py ingest --api databento --schema trades --symbols ES.c.0 --start-date 2024-01-01 --end-date 2024-01-02
python main.py ingest --api databento --schema tbbo --symbols ES.c.0 --start-date 2024-01-01 --end-date 2024-01-02
python main.py ingest --api databento --schema ohlcv-1d --symbols ES.c.0 --start-date 2024-01-01 --end-date 2024-01-02
```

**Scenario 2: Progress Bar Testing**
```bash
# Test CLI progress bar with verbose and non-verbose modes
python main.py ingest --api databento --schema trades --symbols ES.c.0,NQ.c.0 --start-date 2024-01-01 --end-date 2024-01-07
python main.py ingest --verbose --api databento --schema trades --symbols ES.c.0 --start-date 2024-01-01 --end-date 2024-01-02
```

**Scenario 3: Error Recovery Testing**
- Test ingestion with invalid symbols
- Test network interruption handling
- Test database connection failures
- Verify progress bar handles errors gracefully

### P4.2: Final Documentation Updates

#### CLAUDE.md Updates
Add sections for:
- TBBO field mapping fix
- CLI progress bar enhancement  
- Testing improvements
- Updated CLI usage examples

#### Performance Benchmarks
Document before/after metrics:
- Ingestion speed (records/second)
- Memory usage during ingestion
- CLI responsiveness
- Error recovery time

## Success Metrics & Acceptance Criteria

### Overall System Success Criteria
- [ ] **Zero Critical Errors**: All schemas ingest without validation or SQL errors
- [ ] **Professional CLI Experience**: Clean progress bars, no terminal spam
- [ ] **Comprehensive Test Coverage**: >95% coverage for new functionality  
- [ ] **No Performance Regression**: Maintain current ingestion speeds
- [ ] **Complete Documentation**: All changes documented in CLAUDE.md

### Phase-Specific Success Metrics

**Phase 1 - TBBO Fixes:**
- [ ] 0 TBBO field mapping validation errors
- [ ] 0 TBBO SQL constraint errors  
- [ ] 100% TBBO record ingestion success rate
- [ ] Field mapping follows established patterns

**Phase 2 - CLI Enhancement:**
- [ ] Clean, professional progress display
- [ ] Configurable verbosity levels working
- [ ] No performance impact from progress tracking
- [ ] User feedback confirms improved experience

**Phase 3 - Testing:**
- [ ] Symbol field validation: 100% test coverage
- [ ] All schemas tested for field mapping issues
- [ ] Integration tests pass for all workflows
- [ ] Edge cases handled appropriately

**Phase 4 - Integration:**
- [ ] End-to-end tests pass for all schemas
- [ ] No regressions in existing functionality
- [ ] Documentation updated and accurate
- [ ] System ready for production use

## Risk Assessment & Mitigation

### High Risk Items
1. **TBBO SQL Constraint Changes**: Could affect existing data
   - **Mitigation**: Test on development database first, backup before changes

2. **Progress Bar Performance Impact**: Could slow ingestion
   - **Mitigation**: Benchmark before/after, optimize update frequency

3. **Breaking Changes in CLI**: Could disrupt existing users
   - **Mitigation**: Maintain backward compatibility, add new flags only

### Medium Risk Items
1. **Field Mapping Errors**: Could cause data corruption
   - **Mitigation**: Comprehensive testing with real data samples

2. **Test Coverage Gaps**: Could miss edge cases
   - **Mitigation**: Systematic testing approach, code review

## Implementation Timeline

**Total Estimated Time: 6-8 hours**

- **Phase 1 (TBBO Fixes)**: 2-3 hours
- **Phase 2 (CLI Progress Bar)**: 2-3 hours  
- **Phase 3 (Testing)**: 2-3 hours
- **Phase 4 (Integration)**: 1 hour

**Dependencies:**
- Phase 2 can start in parallel with Phase 1
- Phase 3 depends on Phase 1 completion
- Phase 4 depends on all previous phases

## Conclusion

This specification provides a comprehensive roadmap to complete the Historical Data Ingestor system. Building on the successful symbol field mapping implementation, these remaining fixes will deliver a production-ready system with robust data ingestion, professional CLI experience, and comprehensive test coverage.

The structured approach ensures systematic progress while maintaining system reliability and user experience quality standards established by the project.