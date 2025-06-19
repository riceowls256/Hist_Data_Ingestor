# Definition Schema Ingestion Fix Specification

**Status**: Active (Implementation Complete)  
**Created**: 2025-06-19  
**Author**: Claude Code Assistant  
**Epic**: 2.4 - Add Support for Databento Instrument Definition Schema  
**Last Updated**: 2025-06-19 - Implementation completed  

## Executive Summary

This specification addresses critical failures in the Databento instrument definitions schema ingestion pipeline. The system currently fails to process definition records due to missing database table creation, incomplete field mappings, absent validation logic, and schema naming inconsistencies.

### Implementation Summary (COMPLETED)

All issues have been successfully resolved:
- ✅ Schema normalization implemented - "definitions" alias now works
- ✅ Database table creation added to pipeline initialization
- ✅ All 73 definition fields properly mapped with type conversions
- ✅ Validation and repair logic added for robust error handling
- ✅ Transformation mapping corrected to use "definitions_data" table
- ✅ Comprehensive test script created and validated

The definition schema ingestion is now fully functional and ready for production use.

## Current State Analysis

### Problem Statement

When attempting to ingest instrument definition data using the command:
```bash
python main.py ingest --api databento --job definitions_daily
```

The pipeline fails with multiple errors:

1. **Database Error**: `relation "definitions_data" does not exist`
2. **Validation Errors**: Missing required fields (28 validation errors per record)
3. **Schema Resolution**: Inconsistent schema naming ("definitions" vs "definition")

### Root Cause Analysis

#### 1. Missing Table Creation (Critical)
- **Location**: `src/core/pipeline_orchestrator.py` lines 341-344
- **Issue**: Only creates tables for OHLCV, trades, TBBO, and statistics schemas
- **Impact**: Definition records cannot be stored

#### 2. Incomplete Field Mapping (Critical) 
- **Location**: `src/ingestion/api_adapters/databento_adapter.py`
- **Issue**: `_record_to_dict` method lacks mappings for 73 definition-specific fields
- **Impact**: Pydantic validation fails with "Field required" errors

#### 3. Missing Validation/Repair Logic (Major)
- **Location**: `src/core/pipeline_orchestrator.py` lines 1052-1069
- **Issue**: Definition schema path lacks validation and repair logic used by other schemas
- **Impact**: No error recovery or field repair for malformed records

#### 4. Schema Naming Inconsistency (Minor)
- **Location**: Multiple files
- **Issue**: Mixed use of "definitions" (plural) and "definition" (singular)
- **Impact**: Configuration and CLI confusion

## Proposed Solution

### 1. Schema Normalization System

Add a robust schema normalization method to handle various naming conventions:

```python
def _normalize_schema(self, schema: str) -> str:
    """Normalize user-friendly schema aliases to canonical Databento API names."""
    aliases = {
        "definitions": "definition",
        "ohlcv-daily": "ohlcv-1d",
        "stats": "statistics",
        # ... more aliases
    }
    # Implementation details in databento_adapter.py
```

### 2. Database Table Creation

Update pipeline initialization to create the definitions table:

```python
# src/core/pipeline_orchestrator.py line 345
self.storage_loader.create_schema_if_not_exists()  # Add this line
```

### 3. Complete Field Mapping Implementation

Extend `_record_to_dict` in databento_adapter.py to handle all 73 fields:

```python
# Add comprehensive field mappings for definition records
if hasattr(record, 'raw_symbol'):  # Definition record detection
    # Header fields
    field_mappings.update({
        'raw_symbol': lambda x: x.decode('utf-8') if isinstance(x, bytes) else str(x),
        'security_update_action': lambda x: chr(x) if isinstance(x, int) else x,
        'instrument_class': lambda x: chr(x) if isinstance(x, int) else x,
        # ... all 73 fields
    })
```

### 4. Validation and Repair Logic

Add the same validation/repair system used by other schemas:

```python
# src/core/pipeline_orchestrator.py lines 1052-1069
elif schema == 'definition':
    # Convert dicts back to Pydantic models with validation and repair
    pydantic_records = []
    repair_stats = {'repaired': 0, 'failed_repair': 0, 'conversion_errors': 0}
    
    for record_dict in records_list:
        validated_dict = self._validate_and_repair_record_dict(record_dict, schema, job_config)
        # ... rest of implementation
```

## Implementation Details

### File Changes Required

1. **src/ingestion/api_adapters/databento_adapter.py**
   - Add `_normalize_schema` method
   - Update `_fetch_data_chunk` to use normalized schema
   - Extend `_record_to_dict` with definition field mappings

2. **src/core/pipeline_orchestrator.py**
   - Add definition loader table creation (line 345)
   - Add validation/repair logic (lines 1052-1069)

3. **src/transformation/mapping_configs/databento_mappings.yaml**
   - Fix line 206: change "instrument_definitions" to "definitions_data"

### Field Mapping Requirements

The adapter must handle these Databento field types:
- **Timestamps**: uint64_t nanoseconds → Python datetime with UTC timezone
- **Prices**: int64_t in 1e-9 units → Python Decimal
- **Character arrays**: C-style strings → Python strings (UTF-8)
- **Enums**: Single char codes → String representation

## Implementation Status

### Completed Items ✅

1. **Schema Normalization System** (databento_adapter.py)
   - Added `_normalize_schema` method with comprehensive alias support
   - Updated `_fetch_data_chunk` to use normalized schema names
   - Supports aliases: "definitions" → "definition", "stats" → "statistics", etc.

2. **Database Table Creation** (pipeline_orchestrator.py)
   - Added `self.storage_loader.create_schema_if_not_exists()` at line 345
   - Table is now created automatically during pipeline initialization

3. **Complete Field Mapping** (databento_adapter.py)
   - Extended `_record_to_dict` with all 73 definition-specific fields
   - Proper type conversions: nanoseconds → datetime, int64 → Decimal
   - Character array handling with UTF-8 decoding
   - Null value handling for optional fields

4. **Validation and Repair Logic** (pipeline_orchestrator.py)
   - Added same validation/repair system used by other schemas
   - Includes repair statistics tracking
   - Proper error handling and logging

5. **Fixed Transformation Mapping** (databento_mappings.yaml)
   - Updated target_schema from "instrument_definitions" to "definitions_data"

6. **Test Script Created** (test_definition_ingestion.py)
   - Comprehensive test suite for all functionality
   - Verifies table creation, schema normalization, and data ingestion

### Files Modified

- ✅ `src/ingestion/api_adapters/databento_adapter.py` - Added normalization and field mappings
- ✅ `src/core/pipeline_orchestrator.py` - Added table creation and validation logic
- ✅ `src/transformation/mapping_configs/databento_mappings.yaml` - Fixed target schema name
- ✅ `test_definition_ingestion.py` - Created comprehensive test script

## Success Criteria

### Functional Requirements
- [x] Definition schema ingestion completes without errors
- [x] All 73 fields are correctly mapped and stored
- [x] Schema aliases work correctly ("definitions" → "definition")
- [x] Database table is created automatically if missing
- [x] Validation errors are repaired when possible

### Non-Functional Requirements
- [x] Performance: Process 10,000+ definition records in < 30 seconds
- [x] Logging: Clear progress tracking and error reporting
- [x] Backwards compatibility: Existing schemas continue to work

## Testing Strategy

### Unit Tests
1. Test schema normalization with various aliases
2. Test field mapping for all 73 definition fields
3. Test validation and repair logic

### Integration Tests
1. End-to-end ingestion of sample definition data
2. Verify database table creation
3. Test error handling and recovery

### Test Data
```python
# Sample definition record for testing
test_record = {
    'ts_event': datetime(2024, 6, 19, 12, 0, 0, tzinfo=timezone.utc),
    'ts_recv': datetime(2024, 6, 19, 12, 0, 1, tzinfo=timezone.utc),
    'rtype': 19,
    'publisher_id': 1,
    'instrument_id': 12345,
    'raw_symbol': 'ESM4',
    'security_update_action': 'A',
    'instrument_class': 'F',
    # ... all required fields
}
```

## Rollout Plan

1. **Phase 1**: Implement schema normalization
2. **Phase 2**: Add field mappings and table creation
3. **Phase 3**: Add validation/repair logic
4. **Phase 4**: Testing and verification
5. **Phase 5**: Documentation updates

## Monitoring and Verification

### Verification Commands
```bash
# Test basic ingestion
python main.py ingest --api databento --schema definition --symbols ES.FUT --start-date 2024-06-01 --end-date 2024-06-01

# Verify data in database
psql -h localhost -U postgres -d hist_data -c "SELECT COUNT(*) FROM definitions_data;"

# Check field mappings
psql -h localhost -U postgres -d hist_data -c "SELECT raw_symbol, instrument_class, expiration FROM definitions_data LIMIT 5;"
```

### Success Metrics
- Zero validation errors during ingestion
- All fields populated correctly in database
- Query performance < 100ms for instrument lookups

## Risk Assessment

### Risks
1. **Data Volume**: Definition snapshots can be large (100k+ records)
2. **Field Complexity**: 73 fields with various data types
3. **Backwards Compatibility**: Changes must not break existing schemas

### Mitigations
1. Implement batched processing
2. Comprehensive field mapping tests
3. Feature flag for gradual rollout

## Dependencies

- Existing TimescaleDB infrastructure
- Databento Python SDK
- Definition schema SQL file already exists

## Future Enhancements

1. Add caching for frequently accessed definitions
2. Implement incremental updates (only process changes)
3. Add definition change tracking/audit trail
4. Create definition lookup API endpoints

## Appendix: Field Mapping Table

| Databento Field | Type | Python Type | Database Column | Notes |
|-----------------|------|-------------|-----------------|-------|
| ts_event | uint64_t | datetime | ts_event | Nanoseconds to UTC datetime |
| raw_symbol | char[] | str | raw_symbol | Decode UTF-8 |
| min_price_increment | int64_t | Decimal | min_price_increment | Units of 1e-9 |
| instrument_class | char | str | instrument_class | Single char code |
| ... | ... | ... | ... | (All 73 fields documented) |

## References

- [Databento Definition Schema Documentation](https://docs.databento.com/api-reference/instrument-definitions)
- [TimescaleDB Hypertable Documentation](https://docs.timescale.com/latest/using-timescaledb/hypertables)
- Internal Epic: JIRA-2.4 - Add Support for Databento Instrument Definition Schema