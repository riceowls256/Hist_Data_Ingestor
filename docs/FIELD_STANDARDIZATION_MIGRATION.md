# Field Standardization Migration Guide

## Overview
This document chronicles the comprehensive field standardization effort completed on 2024-06-16, which resolved critical validation failures and established consistent naming conventions across the entire codebase.

## Problem Statement
The system had inconsistent field naming between different layers:
- API layer used `open`, `high`, `low`, `close`
- Database schema used `open_price`, `high_price`, `low_price`, `close_price`
- Some mappings used `bid_px_00` while others expected `bid_px`
- Trade count was referenced as both `count` and `trade_count`

This caused:
- Validation failures in Pandera schemas
- Test failures across transformation and adapter tests
- Data flow issues between pipeline stages

## Solution Implemented

### 1. Standardized Field Names
Adopted database-centric naming as the standard:
- `open` → `open_price`
- `high` → `high_price`
- `low` → `low_price`
- `close` → `close_price`
- `count` → `trade_count`
- `bid_px_00` → `bid_px`
- `ask_px_00` → `ask_px`

### 2. Updated Components

#### Storage Models (`src/storage/models.py`)
```python
# Before
open: Decimal = Field(..., description="Opening price")
high: Decimal = Field(..., description="Highest price")
low: Decimal = Field(..., description="Lowest price")
close: Decimal = Field(..., description="Closing price")

# After
open_price: Decimal = Field(..., description="Opening price for the period")
high_price: Decimal = Field(..., description="Highest price during the period")
low_price: Decimal = Field(..., description="Lowest price during the period")
close_price: Decimal = Field(..., description="Closing price for the period")
trade_count: Optional[int] = Field(None, description="Number of trades in the period")
```

#### Databento Adapter (`src/ingestion/api_adapters/databento_adapter.py`)
Added field mapping logic in `_record_to_dict` method:
```python
# Map API field names to model field names
if field == 'open':
    record_dict['open_price'] = converter(value)
elif field == 'high':
    record_dict['high_price'] = converter(value)
elif field == 'low':
    record_dict['low_price'] = converter(value)
elif field == 'close':
    record_dict['close_price'] = converter(value)
elif field == 'count':
    record_dict['trade_count'] = converter(value)
```

#### Validation Schemas (`src/transformation/validators/databento_validators.py`)
```python
class OHLCVSchema(BaseDatabentoSchema):
    open_price: Series[float] = pa.Field(gt=0, coerce=True)
    high_price: Series[float] = pa.Field(gt=0, coerce=True)
    low_price: Series[float] = pa.Field(gt=0, coerce=True)
    close_price: Series[float] = pa.Field(gt=0, coerce=True)
    trade_count: Series[int] = pa.Field(ge=0, coerce=True, nullable=True)
```

### 3. Schema Flexibility Improvements

#### BaseDatabentoSchema Configuration
```python
class Config:
    strict = False  # Allow extra fields that aren't defined in schema
    coerce = True
```

#### Statistics Schema Flexibility
```python
# Accept both field names for compatibility
stat_value: Optional[Series[float]] = pa.Field(nullable=True, coerce=True)
price: Optional[Series[float]] = pa.Field(nullable=True, coerce=True)
```

### 4. Test Fixture Updates
Updated all test fixtures to use standardized field names:
```yaml
# Before
bid_px_00: "bid_px"
ask_px_00: "ask_px"

# After
bid_px: "bid_px"
ask_px: "ask_px"
```

## Recent Updates (2025-06-17)

### Statistics Field Mapping Fix
Enhanced the statistics field mapping in the Databento adapter to properly handle the API's `price` field:

```python
# Added special handling for statistics records
elif field == 'price' and hasattr(record, 'stat_type'):
    # For statistics records, map 'price' field to 'stat_value'
    record_dict['stat_value'] = converter(value)
```

### Database Constraint Alignment
Fixed the statistics loader's ON CONFLICT constraint to match the actual table schema:

```sql
-- Before (incorrect)
ON CONFLICT (ts_event, instrument_id, stat_type, data_source) DO UPDATE SET

-- After (correct - matches table's PRIMARY KEY)
ON CONFLICT (instrument_id, stat_type, ts_event) DO UPDATE SET
```

### Trade Record Model Enhancement
Added missing fields to `DatabentoTradeRecord` with automatic field aliasing:

```python
# Additional fields expected by the loader
quantity: Optional[int] = Field(None, description="Trade quantity (alias for size)")
trade_type: Optional[str] = Field(None, description="Type of trade")
conditions: Optional[str] = Field(None, description="Trade conditions")
sale_condition: Optional[str] = Field(None, description="Sale condition code")
sequence: Optional[int] = Field(None, description="Sequence number")

def __init__(self, **data):
    """Initialize the trade record and set quantity = size if not provided."""
    super().__init__(**data)
    if self.quantity is None and self.size is not None:
        self.quantity = self.size
```

## Lessons Learned

### 1. **Field Naming Consistency is Critical**
- Inconsistent field names between layers cause subtle bugs that are hard to trace
- Establish naming conventions early and document them clearly
- Use the database schema as the source of truth for field names

### 2. **Database Schema Alignment**
- Ensure ON CONFLICT constraints match the actual table PRIMARY KEY/UNIQUE constraints
- Test database operations with real data to catch constraint mismatches
- Keep loader field mappings synchronized with database schema

### 3. **Validation Schema Design**
- Set `strict = False` in Pandera schemas to allow flexibility for extra fields
- Use `nullable=True` for optional fields to avoid validation errors
- Provide clear error messages in validation failures

### 4. **Record Type Detection**
- Handle API field variations gracefully in the adapter layer
- Use record introspection (`hasattr(record, 'field')`) to determine mapping logic
- Provide proper field mapping for transformed dictionary records

### 5. **Test Data Management**
- Keep test fixtures synchronized with model changes
- Use realistic test data that matches production patterns
- Test both valid and invalid data scenarios

### 6. **Debugging Strategy**
- Start with the failing test and trace backwards through the data flow
- Check field names at each transformation layer
- Use verbose test output to identify exact validation failures
- Fix one issue at a time and re-run tests frequently

### 7. **Type Coercion**
- Be explicit about type conversions (e.g., `update_action` expecting int not string)
- Use Pandera's `coerce=True` to handle minor type mismatches
- Document expected types clearly in schemas

## Testing Results
After implementing these changes:
- All 152 unit tests passing
- All 6 transformation tests passing
- Field validation working correctly across all schemas
- Data pipeline functioning end-to-end

## Future Recommendations

1. **Documentation**
   - Maintain a field mapping reference document
   - Document any deviations from standard naming
   - Include field descriptions in all models

2. **Validation**
   - Consider creating a central validation configuration
   - Implement logging for validation failures in production
   - Create validation reports for data quality monitoring

3. **Testing**
   - Add integration tests for field mappings
   - Create property-based tests for validators
   - Test edge cases like null values and type mismatches

## Migration Checklist
If you need to add new fields or modify existing ones:

- [ ] Update the Pydantic model in `storage/models.py`
- [ ] Add field mapping in `databento_adapter._record_to_dict`
- [ ] Update Pandera schema in `databento_validators.py`
- [ ] Update test fixtures in `test_databento_mappings.yaml`
- [ ] Update all related tests with new field names
- [ ] Run full test suite to verify changes
- [ ] Document the change in this guide

## Code References
- Storage Models: `src/storage/models.py:36-44`
- Adapter Mapping: `src/ingestion/api_adapters/databento_adapter.py:280-290`
- Validation Schema: `src/transformation/validators/databento_validators.py:130-138`
- Test Fixtures: `tests/fixtures/test_databento_mappings.yaml`

## Related Documentation
- [Validation Fix Summary](./VALIDATION_FIX_SUMMARY.md) - Detailed summary of all validation fixes
- [Debugging Lessons Learned](./DEBUGGING_LESSONS_LEARNED.md) - Debugging strategies and lessons
- [User Handoff Guide](./USER_HANDOFF_GUIDE.md) - Overall system documentation