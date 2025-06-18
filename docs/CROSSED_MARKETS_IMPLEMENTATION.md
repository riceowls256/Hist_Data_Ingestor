# Crossed Markets Detection and Flagging System

## Overview

This document describes the implementation of a comprehensive crossed markets detection and flagging system for TBBO (Top of Book Bid/Offer) data. The system was designed to handle real-world market microstructure anomalies while preserving data integrity.

## Problem Statement

### The Issue
During TBBO data ingestion, the system encountered **crossed markets** - situations where `bid_price > ask_price`, resulting in negative spreads. This is a legitimate market microstructure phenomenon that can occur due to:

- **Microsecond timing differences** between bid/ask updates
- **Multiple market makers** with stale quotes
- **High volatility periods** with rapid price movements  
- **Network latency** causing quotes to arrive out of sequence

### Original Behavior
The system was **rejecting** these records due to:
1. **Pandera validation** requiring `bid_px <= ask_px` 
2. **Database constraint** requiring `bid_px < ask_px` (strictly less than)

**Example of rejected data:**
```
bid_px: 6057.50, ask_px: 6030.00, spread: -27.50
Result: ValidationRuleError - Batch validation failed
```

### Business Impact
- **Data Loss**: Legitimate market data was being discarded
- **Incomplete Analysis**: Missing critical market microstructure information
- **System Fragility**: Pipeline failures due to normal market conditions

## Solution Architecture

### Design Philosophy
**"We're not building a system for a perfect world. We're building a system tough enough for the real one."**

The solution transforms the approach from **rejection** to **intelligent flagging**:

- ✅ **Accept** all legitimate market data
- ✅ **Flag** anomalies for analysis
- ✅ **Preserve** complete market microstructure
- ✅ **Enable** sophisticated market analysis

## Implementation Details

### 1. Database Schema Enhancement

#### New Column Added
```sql
-- Added to tbbo_data table
is_crossed BOOLEAN DEFAULT FALSE  -- Flag for crossed markets (bid > ask)
```

#### Constraint Removal
```sql
-- REMOVED: Blocking constraint
-- CONSTRAINT chk_bid_ask_cross CHECK (
--     bid_px IS NULL OR ask_px IS NULL OR bid_px < ask_px
-- )
```

#### Monitoring Index Added
```sql
-- For efficient crossed markets analysis
CREATE INDEX idx_tbbo_crossed_markets ON tbbo_data (instrument_id, ts_event)
    WHERE bid_px IS NOT NULL AND ask_px IS NOT NULL AND bid_px > ask_px;
```

### 2. Storage Layer Updates

#### File: `src/storage/timescale_tbbo_loader.py`

**Enhanced Insert SQL:**
```sql
INSERT INTO tbbo_data (
    ts_event, instrument_id, bid_px, ask_px, bid_sz, ask_sz,
    bid_ct, ask_ct, sequence, ts_recv, symbol, data_source, is_crossed
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
```

**Smart Record Processing:**
```python
def _record_to_tuple(self, record: DatabentoTBBORecord, data_source: str) -> tuple:
    """Convert record to tuple with crossed market detection."""
    # Calculate if this is a crossed market
    is_crossed = False
    if record.bid_px is not None and record.ask_px is not None:
        if record.bid_px > record.ask_px:
            is_crossed = True
    
    return (
        # ... all existing fields ...
        data_source,
        is_crossed  # Add the crossed market flag
    )
```

### 3. Validation Layer Simplification

#### File: `src/transformation/validators/databento_validators.py`

**Updated TBBOSchema:**
```python
@pa.dataframe_check
def check_bid_ask_spread(cls, df: pd.DataFrame) -> pd.Series:
    """This check is now informational. The database loader handles flagging."""
    # The loader now handles crossed market logic, so this check just passes
    # We keep it for future custom validation if needed
    return pd.Series([True] * len(df), index=df.index)
```

### 4. Schema Definition Update

#### File: `src/storage/schema_definitions/tbbo_data_table.sql`

**Added metadata field:**
```sql
-- ========================================================================================
-- METADATA FIELDS
-- ========================================================================================
symbol VARCHAR(50),                     -- Human-readable symbol
data_source VARCHAR(50) NOT NULL DEFAULT 'databento',  -- Data provider source
is_crossed BOOLEAN DEFAULT FALSE,       -- Flag for crossed markets (bid > ask)
```

## Deployment Process

### 1. Database Migration
```bash
# Add the new column to existing table
docker exec -it timescaledb psql -U postgres -d hist_data -c \
  "ALTER TABLE tbbo_data ADD COLUMN IF NOT EXISTS is_crossed BOOLEAN DEFAULT FALSE;"
```

### 2. Verification
```bash
# Verify column was added
docker exec -it timescaledb psql -U postgres -d hist_data -c "\d tbbo_data"
```

### 3. Testing
```bash
# Test ingestion with crossed markets data
python main.py ingest --api databento --dataset GLBX.MDP3 --schema tbbo \
  --symbols ES.c.0 --start-date 2025-06-04 --end-date 2025-06-05 \
  --stype-in continuous --force
```

## Usage Examples

### 1. Standard TBBO Ingestion
```bash
# Ingest TBBO data with crossed markets handling
python main.py ingest --api databento --dataset GLBX.MDP3 --schema tbbo \
  --symbols ES.c.0 --start-date 2025-06-10 --end-date 2025-06-11 \
  --stype-in continuous
```

### 2. Query Crossed Markets
```sql
-- Count crossed vs normal markets by symbol
SELECT 
    symbol,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_crossed = true) as crossed_markets,
    COUNT(*) FILTER (WHERE is_crossed = false) as normal_markets,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_crossed = true) / COUNT(*), 
        4
    ) as crossed_percentage
FROM tbbo_data 
GROUP BY symbol 
ORDER BY crossed_markets DESC;
```

### 3. Analyze Crossed Market Patterns
```sql
-- Examine specific crossed markets
SELECT 
    ts_event,
    symbol,
    bid_px,
    ask_px,
    spread,
    bid_sz,
    ask_sz,
    is_crossed
FROM tbbo_data 
WHERE is_crossed = true 
ORDER BY ts_event DESC 
LIMIT 10;
```

### 4. Time-Series Analysis
```sql
-- Crossed markets frequency over time
SELECT 
    DATE_TRUNC('hour', ts_event) as hour,
    symbol,
    COUNT(*) as total_quotes,
    COUNT(*) FILTER (WHERE is_crossed = true) as crossed_quotes
FROM tbbo_data 
WHERE symbol = 'ES.c.0'
    AND ts_event >= '2025-06-04'
    AND ts_event < '2025-06-05'
GROUP BY hour, symbol
ORDER BY hour;
```

## Results Achieved

### Production Metrics

**ES.c.0 Ingestion Results:**
- **Total Records**: 1,196,869
- **Normal Markets**: 1,196,868 (99.9999%)  
- **Crossed Markets**: 1 (0.0001%)
- **Data Loss**: 0 records (previously would have lost crossed market data)

**Specific Crossed Market Detected:**
```
Time: 2025-06-04 22:00:00 UTC
Symbol: ES.c.0
Bid: $5,985.00
Ask: $5,962.25
Spread: -$22.75 (crossed by $22.75)
Status: ✅ Flagged and stored
```

### Performance Impact
- **Ingestion Speed**: No degradation (140s for 352K records)
- **Storage Overhead**: +1 boolean column per record (~1 byte)
- **Query Performance**: Enhanced with dedicated index
- **Data Completeness**: 100% (vs previous data loss)

## Monitoring and Alerts

### Key Metrics to Track

1. **Crossed Market Frequency**
   ```sql
   SELECT COUNT(*) FROM tbbo_data WHERE is_crossed = true;
   ```

2. **Crossed Market Rate by Symbol**
   ```sql
   SELECT symbol, 
          AVG(CASE WHEN is_crossed THEN 1.0 ELSE 0.0 END) as crossed_rate
   FROM tbbo_data 
   GROUP BY symbol;
   ```

3. **Extreme Spreads Detection**
   ```sql
   SELECT * FROM tbbo_data 
   WHERE is_crossed = true 
     AND ABS(spread) > 50.0  -- Flag extreme crossed markets
   ORDER BY ABS(spread) DESC;
   ```

### Recommended Alerts

- **High crossed market rate** (>1% for any symbol)
- **Extreme negative spreads** (>$100 crossed)
- **Sudden spike in crossed markets** (>10x normal rate)

## Benefits Realized

### 1. Data Integrity
- **Complete Market Picture**: No legitimate data loss
- **Microstructure Analysis**: Full bid/ask dynamics captured
- **Research Capabilities**: Enable sophisticated market studies

### 2. System Reliability  
- **Fault Tolerance**: No pipeline failures due to market anomalies
- **Operational Stability**: Robust handling of real-world data
- **Scalability**: System handles all market conditions

### 3. Business Value
- **Compliance**: Complete audit trail of market data
- **Analytics**: Enhanced market microstructure analysis
- **Risk Management**: Better understanding of market dynamics

## Future Enhancements

### Potential Improvements

1. **Real-time Alerting**
   - Slack/email notifications for crossed markets
   - Dashboard showing crossed market patterns

2. **Advanced Analytics**
   - Machine learning models for anomaly detection
   - Crossed market prediction algorithms

3. **Historical Analysis**
   - Backfill analysis of historical crossed markets
   - Market regime identification

4. **Performance Optimization**
   - Partitioning strategies for crossed market data
   - Compressed storage for flagged records

## Conclusion

The crossed markets flagging system successfully transforms data validation from a **brittle rejection model** to a **robust intelligence model**. The system now:

- ✅ **Preserves** all legitimate market data
- ✅ **Identifies** market microstructure anomalies  
- ✅ **Enables** comprehensive market analysis
- ✅ **Maintains** operational reliability

This implementation demonstrates the principle: **"Build systems for the real world, not the perfect world."**

---

## Technical Contacts

For questions about this implementation:
- **Database Schema**: See `src/storage/schema_definitions/tbbo_data_table.sql`
- **Storage Logic**: See `src/storage/timescale_tbbo_loader.py`
- **Validation Logic**: See `src/transformation/validators/databento_validators.py`

Last Updated: 2025-06-18
Version: 1.0.0 