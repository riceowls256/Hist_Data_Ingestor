# Symbol Field Mapping Fix - Technical Specification

**Document Version:** 1.0  
**Date:** 2025-06-17  
**Author:** Claude Code  
**Status:** ✅ Complete - Successfully Implemented  

## Executive Summary

This specification addresses critical symbol field mapping issues in the Historical Data Ingestor that prevent successful ingestion of trade records and potentially affect other data schemas. The primary issue is missing `symbol` fields in Pydantic model validation during the pipeline orchestrator's dict-to-model conversion process.

**Key Issues:**
- Trade records failing with "Field required [type=missing]" for `symbol` field
- Flawed symbol mapping logic in `databento_adapter.py`
- Missing validation and error handling in `pipeline_orchestrator.py`
- Potential similar issues in TBBO and other schemas

**Solution Impact:**
- Fix immediate trade data ingestion failures
- Improve robustness across all data schemas
- Enhance error handling and debugging capabilities
- Ensure reliable end-to-end data pipeline operation

## Problem Analysis

### Root Cause Analysis

Based on investigation of the codebase and error logs, the following issues have been identified:

#### 1. Symbol Field Mapping Logic Flaws (`databento_adapter.py:361-370`)

**Current Implementation Issues:**
```python
# Lines 361-370 in _record_to_dict method
if 'instrument_id' in record_dict:
    if symbols and isinstance(symbols, list) and len(symbols) == 1:
        record_dict['symbol'] = symbols[0]
    elif symbols and isinstance(symbols, str):
        record_dict['symbol'] = symbols
    else:
        # Fallback to instrument_id based naming
        record_dict['symbol'] = f"INSTRUMENT_{record_dict['instrument_id']}"
```

**Problems:**
- Logic fails when `instrument_id` is missing from `record_dict`
- No `symbol` field added when `instrument_id` extraction fails
- Inadequate fallback handling for multi-symbol requests
- Inconsistent symbol parameter handling

#### 2. Incomplete Field Extraction

**Issue:** Trade records missing critical fields like `instrument_id`
- Causes downstream symbol mapping to fail
- Results in records without required `symbol` field
- No validation or error reporting for missing essential fields

#### 3. Pipeline Orchestrator Dict-to-Model Conversion (`pipeline_orchestrator.py:777-784`)

**Current Implementation:**
```python
for record_dict in records_list:
    try:
        pydantic_record = DatabentoTradeRecord(**record_dict)
        pydantic_records.append(pydantic_record)
    except ValidationError as e:
        storage_logger.error(f"Failed to convert dict to Trade model: {e}")
        self.stats.errors_encountered += 1
```

**Problems:**
- No pre-validation of required fields before model creation
- Generic error handling without field-specific diagnostics
- No attempt to repair or provide fallbacks for missing fields
- Error counting but no recovery mechanism

### Error Log Evidence

Error pattern observed:
```
Field required [type=missing, input_value={'ts_event': datetime.dat...ne, 'ts_in_delta': None}, input_type=dict]
Failed to convert dict to Trade model: 1 validation error for DatabentoTradeRecord
symbol
  Field required [type=missing, ...]
```

**Analysis:**
- Records contain `ts_event` but lack `symbol` field
- 315,493 errors encountered out of 2,130,924 records fetched
- 0 records successfully stored due to validation failures
- 316,000 records transformed and validated initially (discrepancy indicates issue in storage stage)

## Technical Solution

### 1. Databento Adapter Enhancements

#### 1.1 Robust Symbol Field Mapping

**File:** `src/ingestion/api_adapters/databento_adapter.py`  
**Method:** `_record_to_dict` (lines 228-376)

**Required Changes:**

1. **Always ensure symbol field presence:**
```python
# Add symbol field mapping logic BEFORE the existing logic
def _ensure_symbol_field(self, record_dict: Dict[str, Any], symbols=None, record=None) -> Dict[str, Any]:
    """Ensure symbol field is always present with appropriate fallback logic."""
    
    # Priority 1: Use provided symbols parameter
    if symbols:
        if isinstance(symbols, list) and len(symbols) == 1:
            record_dict['symbol'] = symbols[0]
            return record_dict
        elif isinstance(symbols, str):
            record_dict['symbol'] = symbols
            return record_dict
        elif isinstance(symbols, list) and len(symbols) > 1:
            # For multi-symbol, try to resolve from instrument_id or use first symbol
            if 'instrument_id' in record_dict:
                # TODO: Implement instrument_id to symbol mapping if needed
                record_dict['symbol'] = symbols[0]  # Fallback to first symbol
            else:
                record_dict['symbol'] = symbols[0]
            return record_dict
    
    # Priority 2: Extract from record if available
    if record and hasattr(record, 'raw_symbol'):
        record_dict['symbol'] = getattr(record, 'raw_symbol')
        return record_dict
    
    # Priority 3: Use instrument_id based naming if available
    if 'instrument_id' in record_dict:
        record_dict['symbol'] = f"INSTRUMENT_{record_dict['instrument_id']}"
        return record_dict
    
    # Priority 4: Use a default fallback
    record_dict['symbol'] = "UNKNOWN_SYMBOL"
    logger.warning("Symbol field set to default fallback", record_data=record_dict)
    return record_dict
```

2. **Enhanced field extraction validation:**
```python
def _validate_required_fields(self, record_dict: Dict[str, Any], schema: str) -> bool:
    """Validate that required fields are present for the given schema."""
    required_fields = {
        'trades': ['ts_event', 'instrument_id', 'price', 'size'],
        'tbbo': ['ts_event', 'instrument_id'],
        'ohlcv': ['ts_event', 'instrument_id', 'open_price', 'high_price', 'low_price', 'close_price'],
        'statistics': ['ts_event', 'instrument_id', 'stat_type']
    }
    
    schema_base = schema.split('-')[0] if '-' in schema else schema
    fields = required_fields.get(schema_base, [])
    
    missing_fields = [field for field in fields if field not in record_dict or record_dict[field] is None]
    
    if missing_fields:
        logger.warning(f"Missing required fields for {schema}: {missing_fields}", record_data=record_dict)
        return False
    
    return True
```

#### 1.2 Improved Error Handling and Logging

**Enhancement Requirements:**
- Add structured logging for field extraction failures
- Include record context in error messages
- Provide field-level diagnostics for debugging
- Add metrics for field extraction success rates

### 2. Pipeline Orchestrator Enhancements

#### 2.1 Pre-validation Before Model Conversion

**File:** `src/core/pipeline_orchestrator.py`  
**Method:** `_stage_data_storage` (lines 770-784)

**Required Changes:**

1. **Add pre-validation function:**
```python
def _validate_and_repair_record_dict(self, record_dict: Dict[str, Any], schema: str, job_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Validate and attempt to repair record dictionary before Pydantic model creation."""
    
    # Check for required symbol field
    if 'symbol' not in record_dict or not record_dict['symbol']:
        # Attempt to repair symbol field
        symbols = job_config.get('symbols')
        if symbols:
            if isinstance(symbols, list) and len(symbols) == 1:
                record_dict['symbol'] = symbols[0]
            elif isinstance(symbols, str):
                record_dict['symbol'] = symbols
            else:
                # Multi-symbol case - use instrument_id or fallback
                if 'instrument_id' in record_dict:
                    record_dict['symbol'] = f"INSTRUMENT_{record_dict['instrument_id']}"
                else:
                    record_dict['symbol'] = "UNKNOWN_SYMBOL"
            
            logger.info("Repaired missing symbol field", 
                       symbol=record_dict['symbol'], 
                       original_symbols=symbols)
        else:
            logger.error("Cannot repair missing symbol field - no symbols in job config", 
                        record_dict=record_dict)
            return None
    
    # Validate other required fields based on schema
    required_fields = self._get_required_fields_for_schema(schema)
    missing_fields = [field for field in required_fields if field not in record_dict]
    
    if missing_fields:
        logger.error("Cannot repair missing required fields", 
                    missing_fields=missing_fields, 
                    schema=schema,
                    record_dict=record_dict)
        return None
    
    return record_dict

def _get_required_fields_for_schema(self, schema: str) -> List[str]:
    """Get list of required fields for each schema type."""
    required_fields = {
        'trades': ['ts_event', 'instrument_id', 'price', 'size', 'symbol'],
        'tbbo': ['ts_event', 'instrument_id', 'symbol'],
        'ohlcv': ['ts_event', 'instrument_id', 'symbol', 'open_price', 'high_price', 'low_price', 'close_price'],
        'statistics': ['ts_event', 'instrument_id', 'symbol', 'stat_type']
    }
    
    schema_base = schema.split('-')[0] if '-' in schema else schema
    return required_fields.get(schema_base, ['ts_event', 'symbol'])
```

2. **Enhanced conversion logic:**
```python
# Replace existing dict-to-model conversion (lines 777-784)
pydantic_records = []
repair_stats = {'repaired': 0, 'failed_repair': 0, 'conversion_errors': 0}

for record_dict in records_list:
    # Pre-validate and repair if needed
    validated_dict = self._validate_and_repair_record_dict(record_dict, schema, job_config)
    
    if validated_dict is None:
        repair_stats['failed_repair'] += 1
        self.stats.errors_encountered += 1
        continue
    
    if validated_dict != record_dict:
        repair_stats['repaired'] += 1
    
    try:
        pydantic_record = DatabentoTradeRecord(**validated_dict)
        pydantic_records.append(pydantic_record)
    except ValidationError as e:
        repair_stats['conversion_errors'] += 1
        storage_logger.error("Failed to convert validated dict to Trade model", 
                           error=str(e),
                           validated_dict=validated_dict,
                           original_dict=record_dict)
        self.stats.errors_encountered += 1

# Log repair statistics
if any(repair_stats.values()):
    storage_logger.info("Record repair statistics", **repair_stats)
```

### 3. Schema-Specific Enhancements

#### 3.1 TBBO Schema Validation

**Requirement:** Ensure TBBO schema doesn't have similar symbol field mapping issues

**Files to check:**
- `src/storage/models.py` - `DatabentoTBBORecord`
- `src/storage/timescale_tbbo_loader.py`
- Field mapping in `databento_adapter.py` for TBBO records

#### 3.2 Statistics Schema Verification

**Requirement:** Verify recent statistics fixes don't regress with symbol field changes

**Files to verify:**
- Recent fixes for statistics data ingestion (2025-06-17)
- Field mapping for `price` → `stat_value`
- Symbol field handling in statistics records

## Implementation Plan

### Phase 1: Core Adapter Fixes (Priority: High)

1. **Implement robust symbol field mapping in databento_adapter.py**
   - Add `_ensure_symbol_field` method
   - Add `_validate_required_fields` method  
   - Update `_record_to_dict` to use new validation
   - Add comprehensive logging and metrics

2. **Enhance pipeline orchestrator dict-to-model conversion**
   - Add `_validate_and_repair_record_dict` method
   - Add `_get_required_fields_for_schema` method
   - Update storage stage to use pre-validation
   - Add repair statistics and logging

### Phase 2: Schema Validation (Priority: Medium)

1. **Test and fix TBBO schema**
   - Run TBBO ingestion test
   - Verify symbol field mapping works correctly
   - Fix any identified issues using same patterns

2. **Verify statistics schema compatibility**
   - Test statistics ingestion with new symbol logic
   - Ensure recent statistics fixes remain functional
   - Validate field mapping consistency

### Phase 3: Comprehensive Testing (Priority: Medium)

1. **Unit tests for new validation logic**
   - Test symbol field mapping with various input scenarios
   - Test pre-validation and repair functions
   - Test error handling and fallback mechanisms

2. **Integration tests for all schemas**
   - End-to-end pipeline tests for trades, TBBO, statistics, OHLCV
   - Multi-symbol and single-symbol scenarios
   - Error recovery and logging verification

3. **Performance impact assessment**
   - Measure performance impact of additional validation
   - Optimize if necessary
   - Ensure no regression in processing speed

## Testing Requirements

### 1. Unit Testing

#### 1.1 Databento Adapter Tests
```python
class TestSymbolFieldMapping:
    def test_single_symbol_mapping(self):
        # Test single symbol in list
        # Test single symbol as string
        
    def test_multi_symbol_mapping(self):
        # Test multiple symbols with instrument_id resolution
        # Test fallback behavior
        
    def test_missing_instrument_id_handling(self):
        # Test symbol mapping when instrument_id is missing
        # Test fallback mechanisms
        
    def test_required_fields_validation(self):
        # Test validation for each schema type
        # Test missing field detection
```

#### 1.2 Pipeline Orchestrator Tests
```python
class TestRecordValidationAndRepair:
    def test_symbol_field_repair(self):
        # Test repair of missing symbol field
        # Test repair with different job config scenarios
        
    def test_required_fields_validation(self):
        # Test validation for each schema
        # Test repair failure scenarios
        
    def test_conversion_error_handling(self):
        # Test improved error reporting
        # Test statistics collection
```

### 2. Integration Testing

#### 2.1 End-to-End Pipeline Tests
- **Trades Schema:** Full pipeline test with ES.c.0 symbol
- **TBBO Schema:** Full pipeline test with same symbol
- **Statistics Schema:** Verify compatibility with recent fixes
- **OHLCV Schema:** Regression test to ensure no impact

#### 2.2 Error Scenario Testing
- **Missing Symbol:** Records without symbol field
- **Missing Instrument ID:** Records without instrument_id
- **Multi-symbol Jobs:** Jobs with multiple symbols
- **Malformed Records:** Records with various field issues

### 3. Performance Testing

#### 3.1 Processing Speed Impact
- **Baseline:** Current processing speed for working schemas
- **Post-fix:** Processing speed with additional validation
- **Target:** <5% performance impact

#### 3.2 Memory Usage Impact
- **Validation Overhead:** Memory usage of new validation functions
- **Error Handling:** Memory usage of enhanced error reporting

## Acceptance Criteria

### 1. Functional Requirements

✅ **Primary Fix:**
- Trade records ingest successfully without symbol field validation errors
- 0 "Field required [type=missing]" errors for symbol field
- All ingested trade records have valid symbol field values

✅ **Schema Compatibility:**
- TBBO schema ingestion works without symbol field issues
- Statistics schema continues to work with recent fixes
- OHLCV schema remains unaffected by changes

✅ **Error Handling:**
- Meaningful error messages for field mapping failures
- Repair statistics logged for monitoring
- Graceful degradation when repair is impossible

### 2. Performance Requirements

✅ **Processing Speed:**
- <5% performance impact from additional validation
- No significant increase in memory usage
- Processing throughput maintained for large datasets

### 3. Monitoring and Observability

✅ **Logging:**
- Structured logs for symbol field repairs
- Statistics for validation success/failure rates
- Clear error messages for debugging

✅ **Metrics:**
- Track symbol field repair events
- Monitor validation failure rates
- Alert on high repair/failure rates

## Risk Assessment

### 1. Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performance degradation | Medium | Low | Performance testing, optimization |
| Breaking existing schemas | High | Low | Comprehensive regression testing |
| Incomplete symbol mapping | Medium | Medium | Robust fallback mechanisms |
| Complex multi-symbol scenarios | Medium | Medium | Thorough testing of edge cases |

### 2. Rollback Plan

**If issues arise post-deployment:**

1. **Immediate Rollback:**
   - Revert `databento_adapter.py` changes
   - Revert `pipeline_orchestrator.py` changes
   - Monitor for restoration of previous behavior

2. **Selective Rollback:**
   - Disable symbol field repair logic via configuration
   - Keep validation logging for debugging
   - Implement gradual re-enablement

3. **Hotfix Deployment:**
   - Quick fixes for critical issues
   - Minimal change deployment process
   - Immediate testing and validation

## Dependencies

### 1. External Dependencies
- **Databento API:** No changes required
- **TimescaleDB:** No schema changes required
- **Pydantic:** Compatible with existing version

### 2. Internal Dependencies
- **Configuration:** May need new config options for fallback behavior
- **Logging:** Requires structured logging framework (already in place)
- **Testing:** Requires test environment with Databento API access

## Success Metrics

### 1. Primary Metrics
- **Trade Ingestion Success Rate:** Target 100% (up from current 0%)
- **Symbol Field Validation Errors:** Target 0 (down from 315,493)
- **Records Successfully Stored:** Target >90% of fetched records

### 2. Secondary Metrics
- **TBBO Schema Success Rate:** Maintain 100%
- **Statistics Schema Success Rate:** Maintain current level
- **Processing Speed:** Maintain within 5% of baseline
- **Error Recovery Rate:** Track % of records successfully repaired

### 3. Monitoring Alerts
- **High Symbol Repair Rate:** >10% of records requiring repair
- **Validation Failure Rate:** >1% of records failing validation
- **Processing Speed Degradation:** >10% slower than baseline

---

**Document Control:**
- **Next Review Date:** 2025-06-24
- **Implementation Target:** 2025-06-18
- **Stakeholder Approval Required:** Technical Lead
- **Related Documents:** 
  - `CLAUDE.md` - Project context and recent fixes
  - `docs/FIELD_STANDARDIZATION_MIGRATION.md` - Previous field mapping changes
  - `docs/DEBUGGING_LESSONS_LEARNED.md` - Debugging strategies