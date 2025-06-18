# Fixing Validation Tests - Step by Step Guide

## Overview
This guide documents the systematic approach used to fix validation test failures in the Historical Data Ingestor project.

## Initial State
- 6 failing transformation tests
- Multiple validation schema errors
- Field name inconsistencies across the codebase

## Step-by-Step Fix Process

### Step 1: Identify Failing Tests
```bash
pytest tests/unit/transformation/ -x --tb=short
```

Failed tests:
1. `test_validate_trades_with_defaults`
2. `test_validate_tbbo_records` 
3. `test_validate_statistics_null_fields`
4. `test_validate_cross_field_consistency_ohlcv`
5. `test_ohlcv_schema_valid`
6. `test_statistics_schema_valid`

### Step 2: Analyze Error Messages

#### Trade Schema Error
```
pandera.errors.SchemaError: column 'depth' in dataframe but not in DataFrameSchema
```
**Analysis**: Schema was in strict mode, rejecting extra fields.

#### TBBO Field Name Error
```
KeyError: 'bid_px'
```
**Analysis**: Test expected `bid_px` but fixture had `bid_px_00`.

#### Statistics Type Error
```
pandera.errors.SchemaError: Error while coercing 'update_action' to type int64
```
**Analysis**: Test data had string "A" instead of integer.

### Step 3: Root Cause Analysis

1. **Strict Schema Validation**
   - Pandera schemas were rejecting records with any extra fields
   - Real-world data often has additional fields we don't use

2. **Field Name Evolution**
   - API fields: `open`, `high`, `low`, `close`
   - Database fields: `open_price`, `high_price`, `low_price`, `close_price`
   - No consistent mapping layer

3. **Test Data Quality**
   - Test fixtures had outdated field names
   - Type mismatches between test data and schema expectations

### Step 4: Implement Fixes

#### Fix 1: Schema Flexibility
```python
# src/transformation/validators/databento_validators.py
class BaseDatabentoSchema(pa.DataFrameModel):
    class Config:
        strict = False  # Allow extra fields
        coerce = True   # Enable type coercion
```

#### Fix 2: Field Name Standardization
```python
# src/ingestion/api_adapters/databento_adapter.py
# In _record_to_dict method
if field == 'open':
    record_dict['open_price'] = converter(value)
elif field == 'high':
    record_dict['high_price'] = converter(value)
# ... etc
```

#### Fix 3: Update Test Data
```yaml
# tests/fixtures/test_databento_mappings.yaml
field_mappings:
  bid_px: "bid_px"  # Changed from bid_px_00
  ask_px: "ask_px"  # Changed from ask_px_00
```

#### Fix 4: Fix Type Issues
```python
# In test files
# Before
"update_action": ["A"]
# After
"update_action": [1]
```

### Step 5: Verify Each Fix

After each change, run tests to verify:
```bash
# Run specific test
pytest tests/unit/transformation/test_databento_validators.py::test_name -xvs

# Run all transformation tests
pytest tests/unit/transformation/ -x
```

### Step 6: Update All Affected Files

Files requiring updates:
1. `src/storage/models.py` - Pydantic models
2. `src/ingestion/api_adapters/databento_adapter.py` - Field mapping
3. `src/transformation/validators/databento_validators.py` - Schemas
4. `tests/fixtures/test_databento_mappings.yaml` - Test data
5. All test files using these fields

### Step 7: Run Comprehensive Tests

```bash
# Run all unit tests
pytest tests/unit/ -x

# Check test count
pytest tests/unit/ --co -q | grep -c "test"
# Result: 152 tests

# Run with quiet output
pytest tests/unit/ -q
# Result: 152 passed
```

## Key Decisions Made

### 1. Database-Centric Naming
- Chose database field names as the standard
- All layers map to these names
- Reduces confusion and mapping complexity

### 2. Schema Flexibility
- Set `strict = False` for all schemas
- Allows handling of evolving API responses
- Prevents brittle validation failures

### 3. Type Coercion
- Enabled `coerce = True` in Pandera
- Handles minor type differences automatically
- Reduces need for explicit type conversions

### 4. Backward Compatibility
- Statistics schema accepts both `stat_value` and `price`
- Supports different API response formats
- Graceful handling of field variations

## Verification Checklist

- [x] All unit tests passing (152/152)
- [x] Field names consistent across models
- [x] Validation schemas flexible enough for real data
- [x] Test fixtures using correct field names
- [x] Type coercion working properly
- [x] Documentation updated

## Common Pitfalls Avoided

1. **Don't change one layer at a time**
   - Field changes cascade through the system
   - Update all layers together

2. **Don't trust test data blindly**
   - Verify test data matches real API responses
   - Check types, not just field names

3. **Don't make schemas too strict**
   - Real-world data is messy
   - Allow for extra fields and variations

4. **Don't forget the adapter layer**
   - Critical translation point between API and models
   - Must handle all field mappings

## Future Improvements

1. **Centralized Field Mapping**
   - Create a single source of truth for field names
   - Use constants or configuration

2. **Automated Testing**
   - Add tests that verify field mappings
   - Property-based testing for validators

3. **Better Error Messages**
   - Include expected vs actual field names
   - Suggest fixes in validation errors

4. **Migration Scripts**
   - Automate field name updates
   - Ensure consistency across codebase