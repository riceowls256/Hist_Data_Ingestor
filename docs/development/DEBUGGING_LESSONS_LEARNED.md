# Debugging Lessons Learned

## Overview
This document captures the debugging process and lessons learned while fixing validation schema failures in the Historical Data Ingestor project.

## The Debugging Journey

### Initial Problem
The user reported three specific issues:
1. Trade schema validation failing due to extra fields
2. TBBO schema expecting different field names (bid_px vs bid_px_00)
3. Statistics and null field tests failing

### Investigation Process

#### 1. **Understanding the Error Messages**
```
FAILED tests/transformation/test_trade_validation.py::test_validate_trades_with_defaults
FAILED tests/transformation/test_tbbo_validation.py::test_validate_tbbo_records
FAILED tests/transformation/test_statistics_validation.py::test_validate_statistics_null_fields
```

**Lesson**: Always start by carefully reading the full error messages and stack traces.

#### 2. **Tracing the Data Flow**
We traced the data flow through multiple layers:
```
API Response → Adapter → Pydantic Model → Transformation → Pandera Validation → Storage
```

**Lesson**: Understanding the complete data pipeline is crucial for debugging validation issues.

#### 3. **Identifying Root Causes**

##### Issue 1: Extra Fields in Trade Schema
- **Symptom**: Pandera validation failing on unexpected fields
- **Root Cause**: Test fixtures included default fields not present in actual data
- **Solution**: Set `strict = False` in BaseDatabentoSchema

##### Issue 2: Field Name Mismatches
- **Symptom**: Tests expecting bid_px but receiving bid_px_00
- **Root Cause**: Inconsistent field naming between API and internal models
- **Solution**: Standardized on shorter field names (bid_px, ask_px)

##### Issue 3: Type Mismatches
- **Symptom**: Statistics schema expecting integer for update_action but receiving string
- **Root Cause**: Test data using wrong types
- **Solution**: Fixed test data to use correct types

### Debugging Techniques Used

#### 1. **Incremental Testing**
```bash
# Run specific test file
pytest tests/unit/transformation/test_databento_validators.py -xvs

# Run specific test
pytest tests/unit/transformation/test_databento_validators.py::test_validate_cross_field_consistency_ohlcv -xvs
```

#### 2. **Print Debugging**
We examined actual vs expected field names:
```python
# In the test
print(f"DataFrame columns: {df.columns.tolist()}")
print(f"Expected: open_price, Actual: {df.columns[2]}")
```

#### 3. **Reading Source Code**
- Examined validation schemas to understand field expectations
- Traced through adapter code to see field transformations
- Checked test fixtures for data inconsistencies

#### 4. **Git Diff Analysis**
Compared working vs failing states to identify what changed:
```bash
git diff src/storage/models.py
```

## Key Discoveries

### 1. **The Cascade Effect**
Changing field names in one place (models) required updates in:
- Adapter field mappings
- Validation schemas
- Test fixtures
- Test assertions
- Documentation

**Lesson**: Field name changes have wide-reaching impacts. Use find-and-replace carefully.

### 2. **Schema Design Principles**
- **Flexibility**: Use `strict = False` for schemas that might receive extra fields
- **Nullability**: Mark optional fields as `nullable=True`
- **Coercion**: Enable `coerce=True` for automatic type conversion
- **Alternatives**: Support multiple field names when dealing with external APIs

### 3. **Test Data Management**
- Test fixtures should mirror production data structures
- Keep test data minimal but realistic
- Document why specific test values are chosen
- Update test data when schemas change

## Best Practices Established

### 1. **Systematic Approach**
1. Identify failing tests
2. Understand expected vs actual behavior
3. Trace data flow backwards from failure point
4. Fix root cause, not symptoms
5. Verify fix doesn't break other tests

### 2. **Documentation**
- Document field mappings clearly
- Explain validation rules
- Note any special cases or exceptions
- Keep examples up to date

### 3. **Testing Strategy**
- Test valid and invalid cases
- Test edge cases (nulls, empty values)
- Test type conversions
- Test field name variations

### 4. **Code Organization**
- Keep validation logic centralized
- Use consistent naming patterns
- Make schemas reusable
- Provide clear error messages

## Common Pitfalls to Avoid

1. **Assuming Field Names**
   - Don't assume external API field names match internal names
   - Always check actual API responses

2. **Overlooking Type Differences**
   - Python types vs Pandas types vs database types
   - String "1" vs integer 1
   - Nullable vs non-nullable fields

3. **Incomplete Updates**
   - Changing models without updating validators
   - Fixing tests without fixing underlying issues
   - Updating code without updating documentation

4. **Over-constraining Schemas**
   - Being too strict about extra fields
   - Requiring all fields when some are optional
   - Not allowing for API variations

## Debugging Workflow Template

When facing similar validation issues:

1. **Gather Information**
   ```bash
   # Run failing test with verbose output
   pytest path/to/test.py::test_name -xvs
   ```

2. **Examine the Error**
   - What field is causing the issue?
   - What is expected vs actual?
   - At what layer does it fail?

3. **Check the Data Flow**
   - How is the field named in the source?
   - How is it transformed?
   - What does the validator expect?

4. **Make Minimal Changes**
   - Fix one issue at a time
   - Run tests after each change
   - Commit working states

5. **Verify Comprehensively**
   ```bash
   # Run all related tests
   pytest tests/unit/ -x
   ```

6. **Document the Fix**
   - Update relevant documentation
   - Add comments explaining non-obvious changes
   - Create migration guides if needed

## Tools and Commands

### Useful pytest options:
- `-x`: Stop on first failure
- `-v`: Verbose output
- `-s`: Show print statements
- `--tb=short`: Shorter traceback
- `--tb=no`: No traceback
- `-k pattern`: Run tests matching pattern

### Useful grep patterns:
```bash
# Find all occurrences of a field name
grep -r "open_price" src/ tests/

# Find field definitions in models
grep -r "Field(" src/storage/models.py

# Find validation schemas
grep -r "pa.Field" src/transformation/validators/
```

## Advanced Debugging Scenarios (2025-06-18)

### Pandera DataFrame Dtype Coercion Issues

#### Symptom Recognition
```
ERROR: coerce_dtype('int64') failure_case=object
Schema validation fails during transformation stage
Mixed integer/None values in source data
```

#### Debugging Methodology
1. **Check DataFrame dtypes after creation**:
   ```python
   df = pd.DataFrame(transformed_batch)
   print(df.dtypes)  # Look for float64 where you expect Int64
   ```

2. **Examine data patterns**:
   ```python
   print(df['trade_count'].apply(type).value_counts())
   # Output might show: <class 'int'> and <class 'NoneType'>
   ```

3. **Test explicit conversion**:
   ```python
   df['trade_count'].astype('Int64')  # Should succeed
   ```

#### Root Cause Pattern
- **Data Source**: Mixed integer and None values
- **Pandas Inference**: Chooses `float64` (converts None → NaN)
- **Pandera Expectation**: `pd.Int64Dtype` (nullable integer)
- **Coercion Failure**: Can't directly convert `float64` with NaN to regular `int64`

#### Solution Pattern
```python
# Before Pandera validation
if 'nullable_int_column' in df.columns:
    df['nullable_int_column'] = df['nullable_int_column'].astype('Int64')
```

### Schema Consistency Debugging

#### Symptom Recognition
```
ERROR: Field required [type=missing] for symbol field
Different error handling patterns across schemas
Inconsistent repair statistics logging
```

#### Investigation Process
1. **Compare schema implementations**:
   ```bash
   # Find all schema storage implementations
   rg -A 20 "schema.*ohlcv|schema.*trades" src/core/pipeline_orchestrator.py
   ```

2. **Check validation pattern consistency**:
   ```python
   # Look for validation/repair calls
   rg "_validate_and_repair_record_dict" src/core/pipeline_orchestrator.py
   ```

3. **Verify repair statistics**:
   ```python
   # Check for repair logging
   rg "repair_stats" src/core/pipeline_orchestrator.py
   ```

#### Solution Approach
- Apply the same validation/repair pattern to all schemas
- Ensure consistent error handling and logging
- Test all schemas with the same problematic data patterns

## Updated Best Practices

### Data Type Handling
1. **Nullable Numeric Fields**:
   - Use pandas extension types: `pd.Int64Dtype`, `pd.Float64Dtype`, `pd.BooleanDtype`
   - Never rely on pandas inference + Pandera coercion for mixed-type data
   - Explicitly convert dtypes before validation

2. **Mixed Data Validation**:
   - Test with realistic data patterns (integers, floats, None, strings)
   - Use `strict = False` in Pandera schemas for external data
   - Enable `coerce = True` but don't depend on it for complex conversions

### Schema Architecture
1. **Consistency Requirements**:
   - All schemas must use the same validation/repair pattern
   - Standardize error handling and logging across all data types
   - Apply symbol field repair universally

2. **Error Recovery**:
   - Implement repair statistics for monitoring data quality
   - Log meaningful error messages with context
   - Provide fallback values for recoverable errors

## Updated Debugging Toolkit

### New Diagnostic Commands
```python
# Check for pandas extension types
df.select_dtypes(include=['Int64', 'Float64', 'boolean']).columns

# Test Pandera coercion manually
import pandera as pa
schema = pa.DataFrameSchema({'col': pa.Column(pa.Int64Dtype, coerce=True, nullable=True)})
schema.validate(df)

# Verify nullable integer conversion
pd.Series([1, 2, None, 4]).astype('Int64')
```

### Performance Monitoring
```bash
# Monitor validation performance
rg -n "validation.*time|repair.*stats" logs/

# Track dtype conversion overhead
rg -n "astype.*Int64" src/
```

## Framework-Specific Lessons

### Pandas + Pandera Integration
- **Mixed-type inference**: Pandas chooses the most permissive type (often float64)
- **Pandera coercion limitations**: Not all dtype conversions work seamlessly
- **Solution**: Explicit dtype management before validation

### Pydantic + Pipeline Integration  
- **Model validation timing**: Dict-to-model conversion happens after transformation
- **Field repair necessity**: Symbol fields can be lost during transformation
- **Consistency requirement**: All schemas need the same repair logic

## Conclusion

Debugging validation issues requires:
- Patience and systematic investigation
- Understanding of the complete data pipeline
- Attention to detail in field names and types
- Knowledge of pandas/Pandera integration limitations
- Awareness of data type inference patterns
- Comprehensive testing after changes
- Good documentation of solutions

**Key Addition**: Understanding the subtle interactions between pandas dtype inference and Pandera validation is crucial for debugging modern data pipelines. The explicit dtype management pattern established here should be applied proactively to prevent similar issues.

The time invested in proper debugging and documentation pays dividends in maintaining a robust data pipeline. The new debugging patterns and solutions documented here provide a foundation for handling complex validation scenarios in production systems.